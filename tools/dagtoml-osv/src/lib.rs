#![forbid(unsafe_code)]

pub mod archive;
pub mod digest;
mod formats;
pub mod https;
mod https_identity;
pub mod locks;
pub mod model;
pub mod process;
pub mod records;
pub mod source;
pub mod versions;
mod zip_records;

#[path = "../build_support.rs"]
pub mod build_support;

include!(concat!(env!("OUT_DIR"), "/source_identity.rs"));

pub fn require_current_instrument(root: &std::path::Path) -> Result<(), String> {
    let records =
        build_support::snapshot(root).map_err(|_| "cannot enumerate advisory instrument source")?;
    let digest = build_support::tree_digest(&records)
        .map_err(|_| "cannot identify advisory instrument source")?;
    if digest != BUILD_TREE_SHA256 {
        return Err(
            "advisory executable differs from its complete current source; rebuild before scanning"
                .into(),
        );
    }
    Ok(())
}
