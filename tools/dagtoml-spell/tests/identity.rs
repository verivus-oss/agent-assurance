#![forbid(unsafe_code)]

use dagtoml_spell::identity::verify;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct Temporary {
    path: PathBuf,
}

impl Temporary {
    fn new() -> Self {
        let time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!(
            "spelling-identity-{}-{time}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        let mut builder = std::fs::DirBuilder::new();
        #[cfg(unix)]
        {
            use std::os::unix::fs::DirBuilderExt;
            builder.mode(0o700);
        }
        builder.create(&path).unwrap();
        Self { path }
    }
}

impl Drop for Temporary {
    fn drop(&mut self) {
        if let Err(error) = std::fs::remove_dir_all(&self.path) {
            if !std::thread::panicking() {
                panic!("owned spelling fixture cleanup failed: {error}");
            }
        }
    }
}

fn copy(source: &Path, destination: &Path, root: &Path) {
    for entry in std::fs::read_dir(source).unwrap() {
        let entry = entry.unwrap();
        let path = entry.path();
        if path == root.join("target") || path == root.join(".git") {
            continue;
        }
        let target = destination.join(entry.file_name());
        let kind = entry.file_type().unwrap();
        if kind.is_dir() {
            std::fs::create_dir(&target).unwrap();
            copy(&path, &target, root);
        } else {
            assert!(kind.is_file());
            std::fs::copy(path, target).unwrap();
        }
    }
}

#[test]
fn current_binary_rejects_changed_added_removed_and_absent_sources() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    verify(&root).unwrap();
    let temporary = Temporary::new();
    copy(&root, &temporary.path, &root);
    verify(&temporary.path).unwrap();
    let source = temporary.path.join("data/project.toml");
    let original = std::fs::read(&source).unwrap();
    let mut changed = original.clone();
    changed.extend_from_slice(b"\n# ordinary additional prose\n");
    std::fs::write(&source, changed).unwrap();
    assert!(
        verify(&temporary.path)
            .unwrap_err()
            .contains("executable differs")
    );
    std::fs::write(&source, &original).unwrap();
    verify(&temporary.path).unwrap();
    let extra = temporary.path.join("src/additional.rs");
    std::fs::write(&extra, b"// ordinary additional source\n").unwrap();
    assert!(
        verify(&temporary.path)
            .unwrap_err()
            .contains("executable differs")
    );
    std::fs::remove_file(extra).unwrap();
    verify(&temporary.path).unwrap();
    let nested = temporary.path.join("src/target");
    std::fs::create_dir(&nested).unwrap();
    std::fs::write(
        nested.join("additional.rs"),
        b"// ordinary additional source\n",
    )
    .unwrap();
    assert!(
        verify(&temporary.path)
            .unwrap_err()
            .contains("executable differs")
    );
    std::fs::remove_dir_all(nested).unwrap();
    verify(&temporary.path).unwrap();
    #[cfg(unix)]
    {
        let ambiguous = temporary.path.join("src/ambiguous\\name.rs");
        std::fs::write(&ambiguous, b"// ordinary additional source\n").unwrap();
        assert!(
            verify(&temporary.path)
                .unwrap_err()
                .contains("population is unavailable")
        );
        std::fs::remove_file(ambiguous).unwrap();
        let linked = temporary.path.join("src/linked.rs");
        std::os::unix::fs::symlink(temporary.path.join("src/lib.rs"), &linked).unwrap();
        assert!(
            verify(&temporary.path)
                .unwrap_err()
                .contains("population is unavailable")
        );
        std::fs::remove_file(linked).unwrap();
        verify(&temporary.path).unwrap();
    }
    std::fs::remove_file(source).unwrap();
    assert!(
        verify(&temporary.path)
            .unwrap_err()
            .contains("executable differs")
    );
    assert!(verify(&temporary.path.join("absent")).is_err());
}
