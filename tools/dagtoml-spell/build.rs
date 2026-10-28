#![forbid(unsafe_code)]

mod build_support;
#[path = "src/digest.rs"]
mod digest;

use std::io::Write;
use std::path::PathBuf;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let root = PathBuf::from(
        std::env::var_os("CARGO_MANIFEST_DIR").ok_or("spelling build root is absent")?,
    );
    let records = build_support::snapshot(&root)?;
    let digest = build_support::tree_digest(&records)?;
    let output =
        PathBuf::from(std::env::var_os("OUT_DIR").ok_or("spelling build output is absent")?);
    let mut file = std::fs::File::create(output.join("source_identity.rs"))?;
    writeln!(file, "pub const BUILD_TREE_SHA256: &str = {digest:?};")?;
    for (path, _) in records {
        println!("cargo:rerun-if-changed={}", root.join(path).display());
    }
    for directory in ["src", "data", "tests"] {
        println!("cargo:rerun-if-changed={}", root.join(directory).display());
    }
    Ok(())
}
