use std::collections::{BTreeMap, BTreeSet};
use std::path::{Component, Path, PathBuf};
use std::process::Command;
use std::time::Duration;

use serde::Serialize;

use crate::{digest::sha256, formats, formats::Kind, locks, model::Package, process};

const MAX_SOURCE: u64 = 16 * 1024 * 1024;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct Manifest {
    pub path: String,
    pub source_sha256: String,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct Subject {
    pub path: String,
    pub source_sha256: String,
    pub manifest: Option<Manifest>,
    pub packages: BTreeSet<Package>,
    pub local_packages: BTreeSet<Package>,
}

#[derive(Debug, Eq, PartialEq, Serialize)]
pub struct Snapshot {
    pub source_commit: String,
    pub tree_state: String,
    pub index_sha256: String,
    pub tracked_population: usize,
    pub subjects: Vec<Subject>,
}

#[derive(Debug, Serialize)]
pub struct Git {
    pub path: PathBuf,
    pub executable_sha256: String,
}

fn program(name: &str) -> Result<PathBuf, String> {
    let paths = std::env::var_os("PATH").ok_or("executable search path is absent")?;
    for directory in std::env::split_paths(&paths) {
        if !directory.is_absolute() {
            continue;
        }
        let candidate = directory.join(name);
        if candidate.is_file() {
            return candidate
                .canonicalize()
                .map_err(|_| "cannot resolve native executable".into());
        }
    }
    Err(format!("required native executable is absent: {name}"))
}

pub fn find_curl() -> Result<PathBuf, String> {
    program("curl")
}

impl Git {
    pub fn new() -> Result<Self, String> {
        let path = program("git")?;
        let executable_sha256 =
            sha256(&std::fs::read(&path).map_err(|_| "cannot identify Git executable")?);
        Ok(Self {
            path,
            executable_sha256,
        })
    }

    pub fn require_unchanged(&self) -> Result<(), String> {
        if sha256(&std::fs::read(&self.path).map_err(|_| "cannot identify Git executable")?)
            != self.executable_sha256
        {
            return Err("Git executable moved during advisory scan".into());
        }
        Ok(())
    }

    fn run(&self, root: &Path, arguments: &[&str], input: Vec<u8>) -> Result<Vec<u8>, String> {
        self.require_unchanged()?;
        let mut command = Command::new(&self.path);
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
            .env("GIT_CONFIG_GLOBAL", "/dev/null")
            .args(arguments);
        let output = process::run(
            &mut command,
            input,
            MAX_SOURCE as usize,
            Duration::from_secs(30),
        )?;
        self.require_unchanged()?;
        if !output.status.success() {
            return Err("read-only advisory Git operation failed".into());
        }
        Ok(output.stdout)
    }
}

fn relative(path: &str) -> bool {
    !path.is_empty()
        && !path.contains('\\')
        && !path.chars().any(char::is_control)
        && path
            .split('/')
            .all(|part| !part.is_empty() && part != "." && part != "..")
        && Path::new(path)
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

#[derive(Debug)]
struct Entry {
    object: String,
    regular: bool,
}

fn entries(raw: &[u8]) -> Result<BTreeMap<String, Entry>, String> {
    if raw.is_empty() || !raw.ends_with(&[0]) {
        return Err("Git index population has absent or incomplete framing".into());
    }
    let mut entries = BTreeMap::new();
    for row in raw[..raw.len() - 1].split(|byte| *byte == 0) {
        let row = std::str::from_utf8(row).map_err(|_| "Git index path is not UTF-8")?;
        let (fields, path) = row
            .split_once('\t')
            .ok_or("Git index entry has no path delimiter")?;
        let fields: Vec<_> = fields.split(' ').collect();
        if fields.len() != 3
            || !matches!(fields[0], "100644" | "100755" | "120000" | "160000")
            || fields[2] != "0"
            || !matches!(fields[1].len(), 40 | 64)
            || !fields[1]
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
            || !relative(path)
            || entries
                .insert(
                    path.into(),
                    Entry {
                        object: fields[1].into(),
                        regular: matches!(fields[0], "100644" | "100755"),
                    },
                )
                .is_some()
        {
            return Err("Git index entry has an invalid, unmerged or repeated identity".into());
        }
    }
    Ok(entries)
}

fn read(root: &Path, path: &str) -> Result<Vec<u8>, String> {
    if !relative(path) {
        return Err("advisory source path is outside its root".into());
    }
    let mut current = root.to_owned();
    let components: Vec<_> = Path::new(path).components().collect();
    for (index, component) in components.iter().enumerate() {
        current.push(component);
        let metadata =
            std::fs::symlink_metadata(&current).map_err(|_| "advisory source is absent")?;
        if metadata.file_type().is_symlink()
            || (index + 1 < components.len() && !metadata.is_dir())
            || (index + 1 == components.len()
                && (!metadata.is_file() || metadata.len() > MAX_SOURCE))
        {
            return Err("advisory source is symlinked, nonregular or exceeds its bound".into());
        }
    }
    let bytes = std::fs::read(current).map_err(|_| "cannot read advisory source")?;
    if bytes.len() as u64 > MAX_SOURCE {
        return Err("advisory source grew beyond its bound".into());
    }
    Ok(bytes)
}

impl Snapshot {
    pub fn capture(root: &Path, git: &Git) -> Result<Self, String> {
        let actual = git.run(root, &["rev-parse", "--show-toplevel"], vec![])?;
        let actual = std::str::from_utf8(&actual)
            .map_err(|_| "Git root is not UTF-8")?
            .strip_suffix('\n')
            .ok_or("Git root has incomplete framing")?;
        if Path::new(actual) != root {
            return Err("advisory checkout root does not match Git".into());
        }
        let raw_commit = git.run(root, &["rev-parse", "--verify", "HEAD^{commit}"], vec![])?;
        let source_commit = std::str::from_utf8(&raw_commit)
            .map_err(|_| "Git commit is not ASCII")?
            .strip_suffix('\n')
            .ok_or("Git commit has incomplete framing")?
            .to_owned();
        if !matches!(source_commit.len(), 40 | 64)
            || !source_commit
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        {
            return Err("advisory source is not a named commit".into());
        }
        let raw = git.run(root, &["ls-files", "--stage", "-z"], vec![])?;
        let index = entries(&raw)?;
        let clean = git
            .run(
                root,
                &["status", "--porcelain", "-z", "--untracked-files=normal"],
                vec![],
            )?
            .is_empty();
        let mut subjects = Vec::new();
        for (path, entry) in &index {
            let Some(kind) = formats::classify(path) else {
                continue;
            };
            if kind == Kind::Unsupported {
                return Err(format!(
                    "advisory source format needs an implemented extractor: {path}"
                ));
            }
            if !entry.regular {
                return Err("indexed advisory source is not a regular file".into());
            }
            let source = read(root, path)?;
            if clean {
                let object = git.run(
                    root,
                    &["hash-object", "--stdin", "--no-filters"],
                    source.clone(),
                )?;
                if object.strip_suffix(b"\n") != Some(entry.object.as_bytes()) {
                    return Err("clean advisory source differs from its indexed object".into());
                }
            }
            let mut manifest = None;
            let extracted = match kind {
                Kind::Cargo => {
                    let parent = Path::new(path).parent().ok_or("Cargo lock has no parent")?;
                    let manifest_path = parent
                        .join("Cargo.toml")
                        .to_str()
                        .ok_or("Cargo manifest path is not UTF-8")?
                        .to_owned();
                    let owner = index
                        .get(&manifest_path)
                        .filter(|entry| entry.regular)
                        .ok_or("Cargo lock has no tracked regular owning manifest")?;
                    let bytes = read(root, &manifest_path)?;
                    if clean {
                        let object = git.run(
                            root,
                            &["hash-object", "--stdin", "--no-filters"],
                            bytes.clone(),
                        )?;
                        if object.strip_suffix(b"\n") != Some(owner.object.as_bytes()) {
                            return Err(
                                "clean Cargo manifest differs from its indexed object".into()
                            );
                        }
                    }
                    let extracted = locks::cargo(&source, &bytes)?;
                    manifest = Some(Manifest {
                        path: manifest_path,
                        source_sha256: sha256(&bytes),
                    });
                    extracted
                }
                Kind::Go => locks::go(&source)?,
                Kind::Python => locks::python(&source)?,
                Kind::Unsupported => return Err("unimplemented advisory source kind".into()),
            };
            subjects.push(Subject {
                path: path.clone(),
                source_sha256: sha256(&source),
                manifest,
                packages: extracted.packages,
                local_packages: extracted.local_packages,
            });
        }
        let snapshot = Self {
            source_commit,
            tree_state: if clean { "clean" } else { "dirty" }.into(),
            index_sha256: sha256(&raw),
            tracked_population: index.len(),
            subjects,
        };
        if snapshot.subjects.is_empty() || snapshot.packages().is_empty() {
            return Err("advisory source or external package population is absent".into());
        }
        Ok(snapshot)
    }

    pub fn packages(&self) -> BTreeSet<Package> {
        self.subjects
            .iter()
            .flat_map(|subject| subject.packages.iter().cloned())
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn index_records_accept_exact_ids_and_reject_ambiguous_paths_and_states() {
        let object = "a".repeat(40);
        let raw = format!("100644 {object} 0\trequirements.txt\0");
        let accepted = entries(raw.as_bytes()).unwrap();
        assert_eq!(accepted["requirements.txt"].object, object);
        assert!(accepted["requirements.txt"].regular);
        let symlink = entries(format!("120000 {object} 0\trequirements.txt\0").as_bytes()).unwrap();
        assert!(!symlink["requirements.txt"].regular);
        for raw in [
            String::new(),
            format!("100644 {object} 0\trequirements.txt"),
            format!("100644 {object} 1\trequirements.txt\0"),
            format!("100644 {} 0\trequirements.txt\0", "g".repeat(40)),
            format!("100644 {object} 0\t../requirements.txt\0"),
            format!("100644 {object} 0\t/requirements.txt\0"),
            format!("100644 {object} 0\trequirements.txt\0").repeat(2),
        ] {
            assert!(entries(raw.as_bytes()).is_err());
        }
        for path in [
            "requirements.txt",
            "requirements/database.txt",
            "tools/control/Cargo.lock",
        ] {
            assert!(relative(path));
        }
        for path in [
            "",
            ".",
            "../outside",
            "root/../outside",
            "/outside",
            "root\\outside",
            "root\nname",
            "root//name",
            "root/./name",
        ] {
            assert!(!relative(path));
        }
        assert_eq!(
            formats::classify("new/package-lock.json"),
            Some(Kind::Unsupported)
        );
        assert_eq!(formats::classify("new/uv.lock"), Some(Kind::Unsupported));
        assert_eq!(
            formats::classify("reference/database/engine-lock.toml"),
            None
        );
    }
}
