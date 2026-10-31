use std::io;
use std::path::Path;

use crate::digest::sha256;

pub fn snapshot(root: &Path) -> io::Result<Vec<(String, String)>> {
    let mut pending = vec![root.to_owned()];
    let mut records = Vec::new();
    while let Some(directory) = pending.pop() {
        for entry in std::fs::read_dir(directory)? {
            let entry = entry?;
            let path = entry.path();
            let kind = entry.file_type()?;
            if path == root.join(".git") {
                continue;
            }
            if kind.is_dir() {
                if path != root.join("target") {
                    pending.push(path);
                }
            } else if kind.is_file() {
                let relative = path
                    .strip_prefix(root)
                    .map_err(|_| io::Error::other("advisory build source escaped its root"))?;
                let mut components = Vec::new();
                for component in relative.components() {
                    let std::path::Component::Normal(component) = component else {
                        return Err(io::Error::other(
                            "advisory build path has an unsupported component",
                        ));
                    };
                    let component = component.to_str().ok_or_else(|| {
                        io::Error::other("advisory build source path is not UTF-8")
                    })?;
                    if component.contains(['/', '\\']) || component.chars().any(char::is_control) {
                        return Err(io::Error::other(
                            "advisory build source name has unsupported bytes",
                        ));
                    }
                    components.push(component);
                }
                let name = components.join("/");
                records.push((name, sha256(&std::fs::read(path)?)));
            } else {
                return Err(io::Error::other(
                    "advisory build source must be a regular file or directory",
                ));
            }
        }
    }
    records.sort();
    if records.is_empty() || records.windows(2).any(|pair| pair[0].0 == pair[1].0) {
        return Err(io::Error::other("advisory build source is absent"));
    }
    Ok(records)
}

pub fn tree_digest(records: &[(String, String)]) -> io::Result<String> {
    let mut framed = b"advisory-build-source-v1\0".to_vec();
    for (path, digest) in records {
        let size = u64::try_from(path.len())
            .map_err(|_| io::Error::other("advisory build path is too large"))?;
        framed.extend_from_slice(&size.to_be_bytes());
        framed.extend_from_slice(path.as_bytes());
        framed.extend_from_slice(digest.as_bytes());
    }
    Ok(sha256(&framed))
}
