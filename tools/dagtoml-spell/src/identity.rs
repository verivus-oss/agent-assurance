use std::path::Path;

#[path = "../build_support.rs"]
mod build_support;

include!(concat!(env!("OUT_DIR"), "/source_identity.rs"));

pub fn verify(package_root: &Path) -> Result<(), &'static str> {
    let records = build_support::snapshot(package_root)
        .map_err(|_| "spelling instrument source population is unavailable")?;
    let actual = build_support::tree_digest(&records)
        .map_err(|_| "spelling instrument source digest is unavailable")?;
    if actual != BUILD_TREE_SHA256 {
        return Err(
            "spelling executable differs from the current source tree; rebuild it before validation",
        );
    }
    Ok(())
}
