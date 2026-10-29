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
    pub filesystem_directories: BTreeSet<String>,
    pub ignored_directory_roots: BTreeSet<String>,
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
        let unmatched_ignore_query = arguments == ["check-ignore", "--no-index", "-z", "--stdin"]
            && output.status.code() == Some(1);
        if !output.status.success() && !unmatched_ignore_query {
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
    gitlink: bool,
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
                        gitlink: fields[0] == "160000",
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

fn directory_population(
    root: &Path,
    git: &Git,
) -> Result<(BTreeSet<String>, BTreeSet<String>), String> {
    // Discover actual directories, then ask Git about each literal path.
    // ls-files --ignored --directory is insufficient: it also lists visible
    // parents whose children are all ignored, hiding a selected vendor root.
    let mut ignored = BTreeSet::new();
    let mut directories = BTreeSet::new();
    let mut pending = vec![PathBuf::new()];
    let deadline = std::time::Instant::now() + Duration::from_secs(30);
    let mut entries = 0usize;
    while !pending.is_empty() {
        let mut candidates = BTreeSet::new();
        for parent in pending.drain(..) {
            let listing = std::fs::read_dir(root.join(&parent))
                .map_err(|_| "cannot enumerate advisory filesystem directories")?;
            for entry in listing {
                entries += 1;
                if entries > 1_000_000 || std::time::Instant::now() > deadline {
                    return Err("advisory filesystem discovery exceeded its bound".into());
                }
                let entry = entry.map_err(|_| "advisory directory entry is unreadable")?;
                let path = parent.join(entry.file_name());
                let name = path
                    .to_str()
                    .ok_or("advisory filesystem path is not UTF-8")?;
                if !relative(name) {
                    return Err("advisory filesystem path is invalid".into());
                }
                // Repository metadata is not a source subject. Nested repositories
                // are not followed through links; tracked gitlinks are refused.
                if entry.file_name() == ".git" {
                    continue;
                }
                let kind = entry
                    .file_type()
                    .map_err(|_| "advisory filesystem type is unreadable")?;
                if kind.is_symlink() && formats::vendored_directory(name) {
                    return Err(format!(
                        "advisory vendored directory needs an implemented extractor: {name}"
                    ));
                }
                if kind.is_dir() {
                    candidates.insert(name.to_owned());
                }
            }
        }
        if candidates.is_empty() {
            break;
        }
        let mut input = Vec::new();
        for name in &candidates {
            input.extend_from_slice(name.as_bytes());
            input.extend_from_slice(b"/\0");
        }
        let raw = git.run(
            root,
            &["check-ignore", "--no-index", "-z", "--stdin"],
            input,
        )?;
        if !raw.is_empty() && !raw.ends_with(&[0]) {
            return Err("ignored directory query has incomplete framing".into());
        }
        for name in raw.split(|byte| *byte == 0).filter(|name| !name.is_empty()) {
            let name = std::str::from_utf8(name).map_err(|_| "ignored directory is not UTF-8")?;
            let name = name
                .strip_suffix('/')
                .ok_or("ignored directory lost its type marker")?;
            if !candidates.remove(name) || !ignored.insert(name.to_owned()) {
                return Err(
                    "ignored directory query returned an unknown or repeated identity".into(),
                );
            }
        }
        for name in candidates {
            if formats::vendored_directory(&name) {
                return Err(format!(
                    "advisory vendored directory needs an implemented extractor: {name}"
                ));
            }
            pending.push(PathBuf::from(&name));
            directories.insert(name);
        }
    }
    Ok((directories, ignored))
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
        for (path, entry) in &index {
            if entry.gitlink {
                return Err(format!(
                    "advisory Git submodule needs an implemented directory extractor: {path}"
                ));
            }
            // Indexed descendants establish a directory even when its own
            // name is absent from the index. Never treat that directory as an
            // unrelated file merely because it has no lockfile basename.
            let mut parent = Path::new(path).parent();
            while let Some(directory) = parent {
                let directory = directory
                    .to_str()
                    .ok_or("advisory directory is not UTF-8")?;
                if formats::vendored_directory(directory) {
                    return Err(format!(
                        "advisory vendored directory needs an implemented extractor: {directory}"
                    ));
                }
                parent = Path::new(directory).parent();
            }
            if !entry.regular && formats::vendored_directory(path) {
                return Err(format!(
                    "advisory vendored directory needs an implemented extractor: {path}"
                ));
            }
        }
        let (filesystem_directories, ignored_directory_roots) = directory_population(root, git)?;
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
            filesystem_directories,
            ignored_directory_roots,
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
        assert!(!accepted["requirements.txt"].gitlink);
        let symlink = entries(format!("120000 {object} 0\trequirements.txt\0").as_bytes()).unwrap();
        assert!(!symlink["requirements.txt"].regular);
        assert!(!symlink["requirements.txt"].gitlink);
        let submodule = entries(format!("160000 {object} 0\tlibrary\0").as_bytes()).unwrap();
        assert!(submodule["library"].gitlink);
        assert!(!submodule["library"].regular);
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
