use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::{digest, https_identity, model::Ecosystem, process, records};

const MAX_ARCHIVE: usize = 256 * 1024 * 1024;
const FOOTER: &[u8] = b"\nDAGTOML_HTTP_META:";
const MAX_AGE: u64 = 48 * 60 * 60;
const CLOCK_TOLERANCE: u64 = 300;
const MAX_CACHE_AGE: u64 = 3600;

#[derive(Debug, Serialize)]
pub struct Native {
    pub artifact: https_identity::Executable,
    #[serde(skip)]
    root: PathBuf,
}

#[derive(Debug, Serialize)]
pub struct Retrieval {
    pub url: String,
    pub generation: String,
    pub etag: String,
    pub archive_sha256: String,
    pub archive_bytes: usize,
    pub received_unix_seconds: u64,
    pub server_unix_seconds: u64,
    pub cache_age_seconds: u64,
    pub modified_unix_seconds: u64,
    pub maximum_age_seconds: u64,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Response {
    status: u16,
    url: String,
    headers: BTreeMap<String, Vec<String>>,
}

fn decimal(value: &str) -> Option<u64> {
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    value.parse().ok()
}

// HTTP IMF-fixdate, interpreted without locale, a date library or a matcher.
fn http_date(value: &str) -> Option<u64> {
    let b = value.as_bytes();
    if b.len() != 29
        || b[3..5] != *b", "
        || b[7] != b' '
        || b[11] != b' '
        || b[16] != b' '
        || b[19] != b':'
        || b[22] != b':'
        || b[25..] != *b" GMT"
    {
        return None;
    }
    let month = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    .iter()
    .position(|month| month.as_bytes() == &b[8..11])? as u64
        + 1;
    let year = decimal(std::str::from_utf8(&b[12..16]).ok()?)?;
    let day = decimal(std::str::from_utf8(&b[5..7]).ok()?)?;
    let hour = decimal(std::str::from_utf8(&b[17..19]).ok()?)?;
    let minute = decimal(std::str::from_utf8(&b[20..22]).ok()?)?;
    let second = decimal(std::str::from_utf8(&b[23..25]).ok()?)?;
    let leap = |y: u64| y % 4 == 0 && (y % 100 != 0 || y % 400 == 0);
    let days = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 if leap(year) => 29,
        2 => 28,
        _ => return None,
    };
    if !(1970..=9999).contains(&year)
        || day == 0
        || day > days
        || hour > 23
        || minute > 59
        || second > 59
    {
        return None;
    }
    let mut elapsed = (1970..year)
        .map(|y| if leap(y) { 366 } else { 365 })
        .sum::<u64>();
    for m in 1..month {
        elapsed += match m {
            1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
            4 | 6 | 9 | 11 => 30,
            2 if leap(year) => 29,
            _ => 28,
        };
    }
    elapsed += day - 1;
    let weekday = ["Thu", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed"][(elapsed % 7) as usize];
    if &b[..3] != weekday.as_bytes() {
        return None;
    }
    Some(elapsed * 86400 + hour * 3600 + minute * 60 + second)
}

fn header<'a>(response: &'a Response, key: &str) -> Result<&'a str, String> {
    let values = response
        .headers
        .get(key)
        .ok_or_else(|| format!("HTTPS archive header is absent: {key}"))?;
    let [value] = values.as_slice() else {
        return Err(format!("HTTPS archive header is repeated: {key}"));
    };
    Ok(value)
}

fn decode(mut bytes: Vec<u8>, url: &str, now: u64) -> Result<(Vec<u8>, Retrieval), String> {
    let split = bytes
        .windows(FOOTER.len())
        .rposition(|value| value == FOOTER)
        .ok_or("HTTPS archive receipt is absent")?;
    if split == 0 || split > MAX_ARCHIVE || bytes.len() - split > 65536 {
        return Err("HTTPS archive or receipt exceeds its bound".into());
    }
    let response: Response = serde_json::from_slice(&bytes[split + FOOTER.len()..])
        .map_err(|_| "invalid HTTPS archive receipt")?;
    if response.status != 200 || response.url != url {
        return Err("HTTPS archive status or source differs from the required object".into());
    }
    if header(&response, "content-type")? != "application/zip"
        || response.headers.contains_key("content-encoding")
        || response.headers.contains_key("content-range")
    {
        return Err("HTTPS archive encoding or media type is unsupported".into());
    }
    let length =
        decimal(header(&response, "content-length")?).ok_or("invalid HTTPS archive length")?;
    if length != split as u64
        || decimal(header(&response, "x-goog-stored-content-length")?) != Some(length)
        || header(&response, "x-goog-stored-content-encoding")? != "identity"
    {
        return Err("HTTPS archive declared byte population differs".into());
    }
    let server = http_date(header(&response, "date")?).ok_or("invalid HTTPS server date")?;
    let modified =
        http_date(header(&response, "last-modified")?).ok_or("invalid HTTPS modification date")?;
    let cache_age = if response.headers.contains_key("age") {
        decimal(header(&response, "age")?).ok_or("invalid HTTPS cache age")?
    } else {
        0
    };
    let response_time = server
        .checked_add(cache_age)
        .ok_or("HTTPS response clock exceeds its bound")?;
    if cache_age > MAX_CACHE_AGE
        || response_time.abs_diff(now) > CLOCK_TOLERANCE
        || modified > server
        || now.saturating_sub(modified) > MAX_AGE
    {
        return Err("HTTPS archive is stale or its clock evidence is inconsistent".into());
    }
    let generation = header(&response, "x-goog-generation")?;
    if decimal(generation).is_none_or(|value| value == 0) {
        return Err("invalid HTTPS object generation".into());
    }
    let etag = header(&response, "etag")?;
    if etag.len() < 3
        || etag.len() > 256
        || !etag.starts_with('"')
        || !etag.ends_with('"')
        || etag.chars().any(char::is_control)
    {
        return Err("invalid HTTPS object entity identity".into());
    }
    let receipt = Retrieval {
        url: url.into(),
        generation: generation.into(),
        etag: etag.into(),
        archive_sha256: digest::sha256(&bytes[..split]),
        archive_bytes: split,
        received_unix_seconds: now,
        server_unix_seconds: server,
        cache_age_seconds: cache_age,
        modified_unix_seconds: modified,
        maximum_age_seconds: MAX_AGE,
    };
    bytes.truncate(split);
    Ok((bytes, receipt))
}

impl Native {
    pub fn new(root: &Path) -> Result<Self, String> {
        let artifact = https_identity::verify(root)?;
        Ok(Self {
            artifact,
            root: root.to_owned(),
        })
    }

    pub fn require_unchanged(&self) -> Result<(), String> {
        if https_identity::verify(&self.root)? != self.artifact {
            return Err(
                "HTTPS executable or complete producer/builder identity moved during assessment"
                    .into(),
            );
        }
        Ok(())
    }

    pub fn archive(&self, ecosystem: &Ecosystem) -> Result<(Vec<u8>, Retrieval), String> {
        let url = format!(
            "https://storage.googleapis.com/osv-vulnerabilities/{}/all.zip",
            records::label(ecosystem)
        );
        self.require_unchanged()?;
        let result = process::run(
            Command::new(&self.artifact.path).arg(&url),
            vec![],
            MAX_ARCHIVE + 65536,
            Duration::from_secs(100),
        )?;
        self.require_unchanged()?;
        if !result.status.success() {
            return Err(format!(
                "HTTPS archive retrieval failed with native status {:?}",
                result.status.code()
            ));
        }
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|_| "system clock predates archive epoch")?
            .as_secs();
        decode(result.stdout, &url, now)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn response() -> serde_json::Value {
        serde_json::json!({"status":200,"url":"https://control.invalid/data","headers":{
            "content-type":["application/zip"],"content-length":["3"],"x-goog-stored-content-length":["3"],
            "x-goog-stored-content-encoding":["identity"],"date":["Wed, 28 Oct 2026 10:00:00 GMT"],
            "last-modified":["Wed, 28 Oct 2026 00:00:00 GMT"],"x-goog-generation":["123"],"etag":["\"abc\""]}})
    }

    fn encoded(value: &serde_json::Value) -> Vec<u8> {
        let mut bytes = b"ZIP".to_vec();
        bytes.extend_from_slice(FOOTER);
        bytes.extend(serde_json::to_vec(value).unwrap());
        bytes
    }

    #[test]
    fn independent_http_date_and_freshness_boundaries() {
        assert_eq!(http_date("Thu, 01 Jan 1970 00:00:00 GMT"), Some(0));
        assert_eq!(http_date("Sat, 29 Feb 2020 00:00:00 GMT"), Some(1582934400));
        for date in [
            "Fri, 29 Feb 2020 00:00:00 GMT",
            "Wed, 30 Feb 2026 00:00:00 GMT",
            "Wed, 28 Oct 2026 24:00:00 GMT",
            "",
        ] {
            assert_eq!(http_date(date), None);
        }
        let now = http_date("Wed, 28 Oct 2026 10:00:00 GMT").unwrap();
        let (bytes, receipt) =
            decode(encoded(&response()), "https://control.invalid/data", now).unwrap();
        assert_eq!(bytes, b"ZIP");
        assert_eq!(receipt.archive_bytes, 3);
        assert_eq!(receipt.maximum_age_seconds, 172800);
        for delta in [301, 172801] {
            assert!(
                decode(
                    encoded(&response()),
                    "https://control.invalid/data",
                    now + delta
                )
                .is_err()
            );
        }
        let mut cached = response();
        cached["headers"]["age"] = serde_json::json!(["2969"]);
        assert_eq!(
            decode(encoded(&cached), "https://control.invalid/data", now + 2969)
                .unwrap()
                .1
                .cache_age_seconds,
            2969
        );
        for age in ["-1", "unknown", "3601", "18446744073709551615"] {
            cached["headers"]["age"] = serde_json::json!([age]);
            assert!(decode(encoded(&cached), "https://control.invalid/data", now).is_err());
        }
        let mut stale = response();
        stale["headers"]["last-modified"] = serde_json::json!(["Sun, 25 Oct 2026 00:00:00 GMT"]);
        assert!(decode(encoded(&stale), "https://control.invalid/data", now).is_err());
    }

    #[test]
    fn incomplete_or_wrong_http_evidence_fails() {
        let now = http_date("Wed, 28 Oct 2026 10:00:00 GMT").unwrap();
        for key in response()["headers"].as_object().unwrap().keys() {
            let mut value = response();
            value["headers"].as_object_mut().unwrap().remove(key);
            assert!(
                decode(encoded(&value), "https://control.invalid/data", now).is_err(),
                "missing {key}"
            );
        }
        for (key, value) in [
            ("content-length", serde_json::json!(["4"])),
            ("date", serde_json::json!(["invalid"])),
            (
                "content-type",
                serde_json::json!(["application/zip", "application/zip"]),
            ),
            ("x-goog-generation", serde_json::json!(["0"])),
        ] {
            let mut record = response();
            record["headers"][key] = value;
            assert!(decode(encoded(&record), "https://control.invalid/data", now).is_err());
        }
        let mut value = response();
        value["status"] = serde_json::json!(206);
        assert!(decode(encoded(&value), "https://control.invalid/data", now).is_err());
        assert!(decode(encoded(&response()), "https://different.invalid/data", now).is_err());
        assert!(decode(b"ZIP".to_vec(), "https://control.invalid/data", now).is_err());
    }

    #[test]
    fn native_transport_requires_the_complete_retained_identity() {
        assert!(Native::new(Path::new("/nonexistent/dagtoml-osv-native-root")).is_err());
        assert!(Native::new(Path::new("/bin/true")).is_err());
    }
}
