#![forbid(unsafe_code)]

use std::collections::BTreeSet;
use std::path::PathBuf;

use dagtoml_osv::{archive, https::Curl, require_current_instrument, source};

fn main() -> Result<(), String> {
    let arguments: Vec<_> = std::env::args_os().skip(1).collect();
    if arguments.len() != 1 {
        return Err("development probe requires CHECKOUT".into());
    }
    let instrument = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    require_current_instrument(&instrument)?;
    let root = PathBuf::from(&arguments[0])
        .canonicalize()
        .map_err(|_| "development source root is absent")?;
    let git = source::Git::new()?;
    let before = source::Snapshot::capture(&root, &git)?;
    let required = before.packages();
    let ecosystems: BTreeSet<_> = required
        .iter()
        .map(|package| package.ecosystem.clone())
        .collect();
    let curl = Curl::new(&source::find_curl()?)?;
    let mut results = Vec::new();
    for ecosystem in ecosystems {
        let (bytes, retrieval) = curl.archive(&ecosystem)?;
        let evaluated = archive::evaluate(&ecosystem, &bytes, &required)?;
        if evaluated.archive_sha256 != retrieval.archive_sha256
            || evaluated.archive_bytes != retrieval.archive_bytes
        {
            return Err("retrieved and evaluated archive identities differ".into());
        }
        results.push(serde_json::json!({"retrieval":retrieval,"evaluation":evaluated}));
    }
    if source::Snapshot::capture(&root, &git)? != before {
        return Err("development subjects moved".into());
    }
    curl.require_unchanged()?;
    require_current_instrument(&instrument)?;
    let output = serde_json::json!({"status":"online-development-evaluation","source":before,"transport":curl,"datasets":results,
        "skipped":["complete dependency/generated-source audit","required workflow integration","clean final candidate validation and independent review"],
        "comparison":"Complete HTTPS-retrieved ecosystem archives with object generation, byte identity and clock bounds; exact typed version/interval predicates and independent affected/unaffected historical record controls. This remains a development observation."});
    println!(
        "{}",
        serde_json::to_string_pretty(&output)
            .map_err(|_| "cannot encode development observation")?
    );
    Ok(())
}
