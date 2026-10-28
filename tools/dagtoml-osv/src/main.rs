#![forbid(unsafe_code)]

use std::collections::BTreeSet;
use std::path::PathBuf;
use std::process::ExitCode;

use dagtoml_osv::{archive, https::Curl, require_current_instrument, source};

fn evaluate() -> Result<bool, String> {
    let arguments: Vec<_> = std::env::args_os().skip(1).collect();
    let [root] = arguments.as_slice() else {
        return Err("usage: dagtoml-osv CHECKOUT".into());
    };
    let root = PathBuf::from(root)
        .canonicalize()
        .map_err(|_| "advisory checkout is absent")?;
    let instrument = root.join("tools/dagtoml-osv");
    require_current_instrument(&instrument)?;
    let git = source::Git::new()?;
    let before = source::Snapshot::capture(&root, &git)?;
    if before.tree_state != "clean" {
        return Err("advisory verdict requires an empty Git porcelain status".into());
    }
    let packages = before.packages();
    let ecosystems: BTreeSet<_> = packages
        .iter()
        .map(|package| package.ecosystem.clone())
        .collect();
    let curl = Curl::new(&source::find_curl()?)?;
    let mut datasets = Vec::new();
    let mut measured = BTreeSet::new();
    let mut affected = BTreeSet::new();
    for ecosystem in &ecosystems {
        let (bytes, retrieval) = curl.archive(ecosystem)?;
        let evaluation = archive::evaluate(ecosystem, &bytes, &packages)?;
        if evaluation.archive_sha256 != retrieval.archive_sha256
            || evaluation.archive_bytes != retrieval.archive_bytes
        {
            return Err("retrieved and evaluated archive identities differ".into());
        }
        for assessment in &evaluation.assessments {
            if !measured.insert(assessment.package.clone()) {
                return Err("advisory subject was evaluated repeatedly".into());
            }
            if !assessment.advisories.is_empty() {
                affected.insert(assessment.package.clone());
            }
        }
        datasets.push(serde_json::json!({"retrieval":retrieval,"evaluation":evaluation}));
    }
    if measured != packages || datasets.len() != ecosystems.len() || datasets.is_empty() {
        return Err(
            "advisory verdict does not cover its complete derived subject population".into(),
        );
    }
    if source::Snapshot::capture(&root, &git)? != before {
        return Err("advisory subjects moved during evaluation".into());
    }
    git.require_unchanged()?;
    curl.require_unchanged()?;
    require_current_instrument(&instrument)?;
    let clear = affected.is_empty();
    let output = serde_json::json!({"status":if clear {"no-listed-advisories"} else {"affected-packages"},
        "source":before,"instrument_sha256":dagtoml_osv::BUILD_TREE_SHA256,"git":git,"transport":curl,
        "packages_evaluated":measured.len(),"affected_packages":affected,"datasets":datasets,
        "comparison":"Every external package identity from the complete derived tracked lock population against every applicable record in the complete retrieved ecosystem archives. Typed release equality and range boundaries are evaluated locally. Independent affected/unaffected controls must agree.",
        "outside_subject":["unregistered local package roots are identified but have no registry advisory claim","commit ancestry, function reachability, exploitability and installation environments","upstream unpublished advisories, unparseable package names disclosed in each dataset, and provider ingestion completeness"]});
    println!(
        "{}",
        serde_json::to_string_pretty(&output).map_err(|_| "cannot encode advisory result")?
    );
    Ok(clear)
}

fn main() -> ExitCode {
    match evaluate() {
        Ok(true) => ExitCode::SUCCESS,
        Ok(false) => ExitCode::from(1),
        Err(message) => {
            eprintln!("advisory evaluation incomplete: {message}");
            ExitCode::from(2)
        }
    }
}
