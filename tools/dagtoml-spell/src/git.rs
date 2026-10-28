use std::collections::BTreeSet;
use std::path::Path;
use std::process::Command;

use crate::project::Failure;

pub fn run(root: &Path, arguments: &[&str]) -> Result<Vec<u8>, Failure> {
    let mut command = Command::new("git");
    command
        .current_dir(root)
        .args(["--no-pager", "-c", "core.fsmonitor=false"]);
    for (key, _) in std::env::vars_os() {
        if key.to_string_lossy().starts_with("GIT_") {
            command.env_remove(key);
        }
    }
    command
        .env("GIT_NO_REPLACE_OBJECTS", "1")
        .env("GIT_NO_LAZY_FETCH", "1")
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env(
            "GIT_CONFIG_GLOBAL",
            if cfg!(windows) { "NUL" } else { "/dev/null" },
        );
    let output = command.args(arguments).output().map_err(|_| {
        Failure::at(
            "<repository>",
            None,
            "spelling Git operation could not start",
        )
    })?;
    if !output.status.success() {
        return Err(Failure::at(
            "<repository>",
            None,
            "spelling Git operation did not complete",
        ));
    }
    Ok(output.stdout)
}

pub fn object_id(value: &[u8]) -> bool {
    matches!(value.len(), 40 | 64) && value.iter().all(|byte| b"0123456789abcdef".contains(byte))
}

pub fn head(root: &Path) -> Result<String, Failure> {
    let output = run(root, &["rev-parse", "--verify", "HEAD^{commit}"])?;
    let value = output.strip_suffix(b"\n").ok_or_else(|| {
        Failure::at(
            "<repository>",
            Some(&output),
            "spelling HEAD identity has incomplete framing",
        )
    })?;
    if !object_id(value) {
        return Err(Failure::at(
            "<repository>",
            Some(&output),
            "spelling HEAD is not a named commit",
        ));
    }
    String::from_utf8(value.to_vec()).map_err(|_| {
        Failure::at(
            "<repository>",
            Some(&output),
            "spelling HEAD identity is not ASCII",
        )
    })
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Kind {
    File,
    Symlink,
    Gitlink,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Entry {
    pub path: String,
    pub kind: Kind,
    pub object: String,
}

pub fn entries(output: &[u8]) -> Result<Vec<Entry>, Failure> {
    if output.is_empty() {
        return Err(Failure::at(
            "<Git index>",
            Some(output),
            "spelling source population is absent",
        ));
    }
    if !output.ends_with(b"\0") {
        return Err(Failure::at(
            "<Git index>",
            Some(output),
            "spelling source population has incomplete byte framing",
        ));
    }
    let mut result = Vec::new();
    let mut paths = BTreeSet::new();
    for record in output[..output.len() - 1].split(|byte| *byte == 0) {
        if record.is_empty() {
            return Err(Failure::at(
                "<Git index>",
                Some(output),
                "spelling source population has a blank record",
            ));
        }
        let tab = record
            .iter()
            .position(|byte| *byte == b'\t')
            .ok_or_else(|| {
                Failure::at(
                    "<Git index>",
                    Some(output),
                    "spelling source record has no path delimiter",
                )
            })?;
        let fields: Vec<_> = record[..tab].split(|byte| *byte == b' ').collect();
        if fields.len() != 3 || !object_id(fields[1]) || fields[2] != b"0" {
            return Err(Failure::at(
                "<Git index>",
                Some(output),
                "spelling requires distinct staged source identities without an unresolved merge",
            ));
        }
        let path_bytes = &record[tab + 1..];
        let path = std::str::from_utf8(path_bytes).map_err(|_| {
            Failure::at(
                "<Git path bytes>",
                Some(path_bytes),
                "spelling source path is not UTF-8",
            )
        })?;
        crate::scope::classify(path)
            .map_err(|message| Failure::at(path, Some(path_bytes), message))?;
        if !paths.insert(path.to_owned()) {
            return Err(Failure::at(
                path,
                Some(path_bytes),
                "spelling source population repeats a path",
            ));
        }
        let kind = match fields[0] {
            b"100644" | b"100755" => Kind::File,
            b"120000" => Kind::Symlink,
            b"160000" => Kind::Gitlink,
            _ => {
                return Err(Failure::at(
                    path,
                    Some(record),
                    "spelling source has an unsupported Git entry kind",
                ));
            }
        };
        result.push(Entry {
            path: path.to_owned(),
            kind,
            object: String::from_utf8(fields[1].to_vec()).map_err(|_| {
                Failure::at(path, Some(record), "spelling object identity is not ASCII")
            })?,
        });
    }
    result.sort_by(|a, b| a.path.cmp(&b.path));
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::{Kind, entries};

    #[test]
    fn typed_index_population_and_malformed_records() {
        let sha = "a".repeat(40);
        let raw = format!("100644 {sha} 0\tpath with space.py\0");
        let population = entries(raw.as_bytes()).unwrap();
        assert_eq!(population.len(), 1);
        assert_eq!(population[0].path, "path with space.py");
        assert_eq!(population[0].kind, Kind::File);
        for (mode, kind) in [
            ("100755", Kind::File),
            ("120000", Kind::Symlink),
            ("160000", Kind::Gitlink),
        ] {
            assert_eq!(
                entries(format!("{mode} {sha} 0\titem\0").as_bytes()).unwrap()[0].kind,
                kind
            );
        }
        for raw in [
            String::new(),
            "\0".to_owned(),
            format!("100644 {sha} 0\titem"),
            format!("100644 {sha} 1\titem\0"),
            format!("100644 {sha} 0\t\0"),
            format!("100644 {sha} 0\titem\0\0"),
            format!("100644 {sha} 0\titem\0\0hidden\0"),
            format!("100644 {sha} 0\titem\0") + &format!("100644 {sha} 0\titem\0"),
            format!("040000 {sha} 0\titem\0"),
            format!("100644 {sha} 0\t../outside\0"),
        ] {
            assert!(
                entries(raw.as_bytes()).is_err(),
                "malformed Git population accepted: {raw:?}"
            );
        }
    }
}
