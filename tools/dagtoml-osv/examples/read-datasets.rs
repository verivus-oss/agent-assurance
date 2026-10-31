#![forbid(unsafe_code)]

use std::collections::BTreeSet;
use std::path::PathBuf;

use dagtoml_osv::{archive, model::Ecosystem, records, require_current_instrument, source};

fn main() -> Result<(), String> {
    let arguments: Vec<_> = std::env::args_os().skip(1).collect();
    if arguments.len() != 2 {
        return Err("development probe requires CHECKOUT DATA_DIRECTORY".into());
    }
    require_current_instrument(&PathBuf::from(env!("CARGO_MANIFEST_DIR")))?;
    let root = PathBuf::from(&arguments[0])
        .canonicalize()
        .map_err(|_| "development source root is absent")?;
    let data = PathBuf::from(&arguments[1]);
    let git = source::Git::new()?;
    let before = source::Snapshot::capture(&root, &git)?;
    let required = before.packages();
    let ecosystems: BTreeSet<_> = required
        .iter()
        .map(|package| package.ecosystem.clone())
        .collect();
    let mut results = Vec::new();
    for ecosystem in ecosystems {
        let filename = match ecosystem {
            Ecosystem::Go => "Go.zip",
            Ecosystem::PyPI => "PyPI.zip",
            Ecosystem::Crates => "crates.io.zip",
        };
        let bytes =
            std::fs::read(data.join(filename)).map_err(|_| "development dataset is absent")?;
        let result = archive::evaluate(&ecosystem, &bytes, &required)
            .map_err(|error| format!("{} dataset: {error}", records::label(&ecosystem)))?;
        results.push(result);
    }
    if source::Snapshot::capture(&root, &git)? != before {
        return Err("development subjects moved".into());
    }
    require_current_instrument(&PathBuf::from(env!("CARGO_MANIFEST_DIR")))?;
    let output = serde_json::json!({"status":"offline-development-evaluation","source":before,"datasets":results,
        "skipped":["network retrieval and dataset freshness","complete dependency/generated-source audit","required workflow integration","current clean candidate validation and independent review"],
        "comparison":"Complete supplied archive records and exact typed version/interval predicates; independent historical affected/unaffected controls; this is not a current advisory verdict"});
    println!(
        "{}",
        serde_json::to_string_pretty(&output)
            .map_err(|_| "cannot encode development observation")?
    );
    Ok(())
}
