use std::collections::BTreeMap;
use std::io::Read;
use std::path::{Component, Path, PathBuf};
use std::process::Command;
use std::time::Duration;

use serde::{Deserialize, Serialize};

use crate::{digest, process};

const SOURCE_LIMIT: usize = 64 * 1024 * 1024;
const FILE_LIMIT: usize = 32 * 1024 * 1024;
const BINARY: &str = ".local/osv-https/dagtoml-osv-http-go";

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Identity {
    pub protocol: String,
    pub go_version: String,
    pub source_sha256: String,
    pub builder_sha256: String,
    pub compiled_graph_sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct FileIdentity {
    path: String,
    sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Build {
    protocol: String,
    go_version: String,
    source_sha256: String,
    builder_sha256: String,
    compiled_graph_sha256: String,
    sources: Vec<FileIdentity>,
    builder_sources: Vec<FileIdentity>,
    compiled_packages: Vec<String>,
    binary_sha256: String,
}

#[derive(Debug, Serialize, PartialEq, Eq)]
pub struct Executable {
    pub path: PathBuf,
    pub executable_sha256: String,
    pub identity: Identity,
}

fn regular(path: &Path, limit: usize) -> Result<Vec<u8>, String> {
    let metadata = std::fs::symlink_metadata(path).map_err(|_| "HTTPS identity file is absent")?;
    if !metadata.file_type().is_file() || metadata.len() > limit as u64 {
        return Err("HTTPS identity requires a bounded regular file".into());
    }
    let file = std::fs::File::open(path).map_err(|_| "HTTPS identity file cannot be opened")?;
    let mut data = Vec::new();
    file.take(limit as u64 + 1)
        .read_to_end(&mut data)
        .map_err(|_| "HTTPS identity file cannot be captured")?;
    if data.len() > limit || data.len() as u64 != metadata.len() {
        return Err("HTTPS identity file changed or exceeded its bound".into());
    }
    Ok(data)
}

fn frame(output: &mut Vec<u8>, value: &[u8]) -> Result<(), String> {
    let size = u64::try_from(value.len()).map_err(|_| "HTTPS source identity is oversized")?;
    output.extend_from_slice(&size.to_be_bytes());
    output.extend_from_slice(value);
    Ok(())
}

fn source(root: &Path) -> Result<(String, BTreeMap<String, String>), String> {
    let metadata = std::fs::symlink_metadata(root).map_err(|_| "HTTPS source module is absent")?;
    if !metadata.file_type().is_dir() {
        return Err("HTTPS source module must be an unlinked directory".into());
    }
    let mut pending = vec![root.to_owned()];
    let mut files = BTreeMap::new();
    let mut total = 0usize;
    let mut entries = 0usize;
    while let Some(directory) = pending.pop() {
        for entry in
            std::fs::read_dir(directory).map_err(|_| "HTTPS source directory is unreadable")?
        {
            let entry = entry.map_err(|_| "HTTPS source directory entry is unreadable")?;
            entries += 1;
            if entries > 100000 {
                return Err("HTTPS source entry population exceeds its bound".into());
            }
            let kind = entry
                .file_type()
                .map_err(|_| "HTTPS source type is unavailable")?;
            if kind.is_dir() {
                pending.push(entry.path());
            } else if kind.is_file() {
                let path = entry.path();
                let relative = path
                    .strip_prefix(root)
                    .map_err(|_| "HTTPS source escaped its root")?;
                let mut components = Vec::new();
                for component in relative.components() {
                    let Component::Normal(component) = component else {
                        return Err("HTTPS source component is invalid".into());
                    };
                    let component = component.to_str().ok_or("HTTPS source name is not UTF-8")?;
                    if component.contains(['/', '\\']) || component.chars().any(char::is_control) {
                        return Err("HTTPS source name contains unsupported bytes".into());
                    }
                    components.push(component);
                }
                let data = regular(&path, FILE_LIMIT)?;
                total = total
                    .checked_add(data.len())
                    .ok_or("HTTPS source population is oversized")?;
                if total > SOURCE_LIMIT
                    || files.len() >= 100000
                    || files.insert(components.join("/"), data).is_some()
                {
                    return Err("HTTPS source population is oversized or repeated".into());
                }
            } else {
                return Err("HTTPS source retains a linked or nonregular entry".into());
            }
        }
    }
    if files.is_empty() {
        return Err("HTTPS source population is absent".into());
    }
    let mut framed = b"dagtoml-postgres-source-v1\0".to_vec();
    let mut hashes = BTreeMap::new();
    for (name, data) in files {
        frame(&mut framed, name.as_bytes())?;
        frame(&mut framed, &data)?;
        hashes.insert(name, digest::sha256(&data));
    }
    Ok((digest::sha256(&framed), hashes))
}

fn roster(values: Vec<FileIdentity>) -> Result<BTreeMap<String, String>, String> {
    let mut files = BTreeMap::new();
    for file in values {
        if file.path.is_empty()
            || file.sha256.len() != 64
            || !file
                .sha256
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
            || files.insert(file.path, file.sha256).is_some()
        {
            return Err("HTTPS retained source roster is invalid or repeated".into());
        }
    }
    if files.is_empty() {
        return Err("HTTPS retained source roster is absent".into());
    }
    Ok(files)
}

pub fn verify(root: &Path) -> Result<Executable, String> {
    let binary = root.join(BINARY);
    for path in [
        root.join(".local"),
        root.join(".local/osv-https"),
        root.join("tools"),
    ] {
        if !std::fs::symlink_metadata(path)
            .map_err(|_| "HTTPS artifact directory is absent")?
            .file_type()
            .is_dir()
        {
            return Err("HTTPS artifact directory is not regular".into());
        }
    }
    let record: Build = serde_json::from_slice(&regular(
        &root.join(format!("{BINARY}.build.json")),
        4 * 1024 * 1024,
    )?)
    .map_err(|_| "HTTPS build declaration is invalid")?;
    if record.protocol != "dagtoml-stdlib-capsule-v1" || record.go_version != "go1.26.10" {
        return Err("HTTPS build protocol or Go version is unsupported".into());
    }
    let (source_sha256, sources) = source(&root.join("tools/dagtoml-osv-http-go"))?;
    let (builder_sha256, builder_sources) = source(&root.join("tools/dagtoml-postgres-go"))?;
    if record.source_sha256 != source_sha256
        || record.builder_sha256 != builder_sha256
        || roster(record.sources)? != sources
        || roster(record.builder_sources)? != builder_sources
    {
        return Err(
            "HTTPS producer or builder differs from its complete retained source population".into(),
        );
    }
    if record.compiled_packages.is_empty()
        || record
            .compiled_packages
            .windows(2)
            .any(|pair| pair[0] >= pair[1])
        || !record
            .compiled_packages
            .iter()
            .any(|name| name == "github.com/verivus-oss/agent-assurance/tools/dagtoml-osv-http-go")
    {
        return Err("HTTPS compiled package population is absent, repeated or noncanonical".into());
    }
    let mut graph = b"dagtoml-stdlib-capsule-graph-v1\0".to_vec();
    for name in &record.compiled_packages {
        if name.is_empty()
            || name == "regexp"
            || name.starts_with("regexp/")
            || name.chars().any(char::is_control)
        {
            return Err("HTTPS compiled graph retains an unsupported package".into());
        }
        frame(&mut graph, name.as_bytes())?;
    }
    let compiled_graph_sha256 = digest::sha256(&graph);
    if record.compiled_graph_sha256 != compiled_graph_sha256 {
        return Err("HTTPS compiled graph differs from its retained identity".into());
    }
    let executable_sha256 = digest::sha256(&regular(&binary, 64 * 1024 * 1024)?);
    if record.binary_sha256 != executable_sha256 {
        return Err("HTTPS executable differs from its retained build identity".into());
    }
    let expected = Identity {
        protocol: "dagtoml-osv-https-v1".into(),
        go_version: record.go_version,
        source_sha256,
        builder_sha256,
        compiled_graph_sha256,
    };
    let result = process::run(
        Command::new(&binary).arg("--identity"),
        vec![],
        65536,
        Duration::from_secs(10),
    )?;
    let actual: Identity = serde_json::from_slice(&result.stdout)
        .map_err(|_| "HTTPS executable identity is invalid")?;
    if !result.status.success() || !result.stderr.is_empty() || actual != expected {
        return Err("HTTPS executed identity differs from its complete build inputs".into());
    }
    Ok(Executable {
        path: binary,
        executable_sha256,
        identity: actual,
    })
}
