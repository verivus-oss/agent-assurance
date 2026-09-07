//! SPEC structural checks for document-owned runtime declarations. No execution.

use super::*;

pub fn vocab(repo_root: &Path, attribute: &str) -> Option<(Vec<String>, bool)> {
    let mut paths = vec![repo_root.join("core/ontology.toml")];
    let profile_root = repo_root.join("profiles");
    for entry in std::fs::read_dir(profile_root).ok()? {
        let path = entry.ok()?.path().join("ontology.toml");
        if path.is_file() {
            paths.push(path);
        }
    }
    if !paths.contains(&repo_root.join("profiles/agent-assurance/ontology.toml")) {
        return None;
    }
    paths.sort();
    let mut seen = std::collections::BTreeSet::new();
    let mut result = None;
    for path in paths {
        let doc = load(&path).ok()?;
        let entries = doc.get("attribute_vocabularies")?.as_array()?;
        if entries.is_empty() {
            return None;
        }
        for entry in entries {
            let name = entry.get("attribute")?.as_str()?;
            if name.is_empty() || !seen.insert(name.to_owned()) {
                return None;
            }
            let extensible = entry.get("extensible")?.as_bool()?;
            let values = entry.get("values")?.as_array()?;
            let mut tokens = Vec::new();
            for value in values {
                let token = value.as_str()?.to_owned();
                if tokens.contains(&token) {
                    return None;
                }
                tokens.push(token);
            }
            if name == attribute {
                result = Some((tokens, extensible));
            }
        }
    }
    result
}

pub fn hex64(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

fn assertion_id(value: &str) -> bool {
    let Some(tail) = value.strip_prefix("A-") else {
        return false;
    };
    let mut bytes = tail.bytes();
    bytes.next().is_some_and(|b| b.is_ascii_alphanumeric())
        && bytes.all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
}

pub fn fields(doc: &Value, kind: &str, repo_root: &Path) -> Vec<String> {
    let mut errors = Vec::new();
    let meta = doc.get("meta");
    if meta
        .and_then(|m| m.get("template_kind"))
        .and_then(Value::as_str)
        != Some(kind)
    {
        errors.push(format!("RDMETA: meta.template_kind must equal {kind:?}"));
    }
    let profile = meta
        .and_then(|m| m.get("framework_profile"))
        .and_then(Value::as_str);
    if !matches!(profile, Some("agent-assurance" | "AGDF")) {
        errors.push("RDMETA: meta.framework_profile must identify agent-assurance".into());
    }
    let bindings = [
        (
            "adapter-contract",
            "adapter",
            "runtime_kind",
            "runtime_kind",
            true,
        ),
        (
            "adapter-contract",
            "adapter",
            "runtime_network_policy",
            "runtime_network_policy",
            true,
        ),
        (
            "adapter-contract",
            "adapter",
            "runtime_clock_policy",
            "runtime_clock_policy",
            true,
        ),
        (
            "adapter-contract",
            "adapter",
            "id_derivation",
            "adapter_id_derivation",
            false,
        ),
        (
            "adapter-registry-binding",
            "binding",
            "adapter_ref_syntax",
            "adapter_ref_syntax",
            true,
        ),
        (
            "gate-decision",
            "decision",
            "verdict",
            "gate_decision_verdict",
            true,
        ),
    ];
    for (owner, section, field, attribute, required) in bindings {
        if kind != owner {
            continue;
        }
        let Some(table) = doc.get(section).and_then(Value::as_table) else {
            errors.push(format!("RDVOCAB {attribute}: {section} must be a table"));
            continue;
        };
        if !required && !table.contains_key(field) {
            continue;
        }
        let Some((values, false)) = vocab(repo_root, attribute) else {
            errors.push(format!(
                "RDLOAD: missing/invalid closed vocabulary {attribute}"
            ));
            continue;
        };
        if values.is_empty()
            || !table
                .get(field)
                .and_then(Value::as_str)
                .is_some_and(|v| values.iter().any(|x| x == v))
        {
            errors.push(format!(
                "RDVOCAB {attribute}: {section}.{field} must be a declared string"
            ));
        }
    }
    errors
}

fn nonempty(
    table: &toml::map::Map<String, Value>,
    field: &str,
    location: &str,
    errors: &mut Vec<String>,
) {
    if !table
        .get(field)
        .and_then(Value::as_str)
        .is_some_and(|v| !v.trim().is_empty())
    {
        errors.push(format!(
            "RDSTRUCT: {location}.{field} must be a nonempty string"
        ));
    }
}

fn entries<'a>(
    table: &'a toml::map::Map<String, Value>,
    field: &str,
    location: &str,
    required: bool,
    errors: &mut Vec<String>,
) -> Vec<&'a toml::map::Map<String, Value>> {
    if !required && !table.contains_key(field) {
        return Vec::new();
    }
    let Some(values) = table.get(field).and_then(Value::as_array) else {
        errors.push(format!(
            "RDSTRUCT: {location}.{field} must be an array of tables"
        ));
        return Vec::new();
    };
    if required && values.is_empty() {
        errors.push(format!("RDSTRUCT: {location}.{field} must be nonempty"));
    }
    let mut result = Vec::new();
    for value in values {
        match value.as_table() {
            Some(entry) => result.push(entry),
            None => errors.push(format!(
                "RDSTRUCT: every {location}.{field} entry must be a table"
            )),
        }
    }
    result
}

pub fn validate(doc: &Value, repo_root: &Path, binding: bool) -> Vec<String> {
    let kind = if binding {
        "adapter-registry-binding"
    } else {
        "adapter-contract"
    };
    let section = if binding { "binding" } else { "adapter" };
    let mut errors = fields(doc, kind, repo_root);
    let Some(table) = doc.get(section).and_then(Value::as_table) else {
        return errors;
    };
    if binding {
        nonempty(table, "adapter_ref", section, &mut errors);
        nonempty(table, "registry_url", section, &mut errors);
        let scheme = table.get("registry_url_scheme").and_then(Value::as_str);
        match vocab(repo_root, "registry_scheme") {
            Some((values, _)) if scheme.is_some_and(|s| values.iter().any(|v| v == s)) => (),
            Some(_) => errors.push(
                "INV01: binding.registry_url_scheme must be declared in registry_scheme".into(),
            ),
            None => errors.push("RDLOAD: invalid registry_scheme declaration".into()),
        }
        let matches = scheme
            .zip(table.get("registry_url").and_then(Value::as_str))
            .is_some_and(|(s, url)| url.starts_with(&format!("{s}://")));
        if !matches {
            errors.push(
                "INV02: binding.registry_url must start with the declared scheme followed by ://"
                    .into(),
            );
        }
        for entry in entries(table, "trust_anchor_refs", section, false, &mut errors) {
            nonempty(
                entry,
                "anchor_id",
                "binding.trust_anchor_refs[]",
                &mut errors,
            );
        }
        for entry in entries(table, "policy_constraint_refs", section, false, &mut errors) {
            if !entry
                .get("constraint_id")
                .and_then(Value::as_str)
                .is_some_and(assertion_id)
            {
                errors.push("INV03: binding.policy_constraint_refs[].constraint_id must match the whole ASCII assertion-ID grammar".into());
            }
        }
    } else {
        nonempty(table, "input_source", section, &mut errors);
        let Some((values, extensible)) = vocab(repo_root, "input_hash_method") else {
            errors.push("RDLOAD: invalid input_hash_method declaration".into());
            return errors;
        };
        if let Some(value) = table.get("input_hash_method") {
            if !value
                .as_str()
                .is_some_and(|s| extensible || values.iter().any(|v| v == s))
            {
                errors.push("RDVOCAB input_hash_method: adapter.input_hash_method must satisfy its declared string vocabulary".into());
            }
        }
        let digest = match table.get("runtime_kind").and_then(Value::as_str) {
            Some("wasi-component") => Some("component_digest"),
            Some("oci-action") => Some("oci_image_digest"),
            Some("os-sandbox") => Some("profile_args_digest"),
            _ => None,
        };
        match table.get("runtime_artifact").and_then(Value::as_table) {
            None => errors.push("INV02: adapter.runtime_artifact must be a table".into()),
            Some(artifact) => {
                if let Some(field) = digest {
                    if !artifact
                        .get(field)
                        .and_then(Value::as_str)
                        .is_some_and(hex64)
                    {
                        errors.push(format!("INV02: adapter.runtime_artifact.{field} must be exactly 64 lowercase ASCII hex characters"));
                    }
                }
            }
        }
        for entry in entries(table, "emits", section, true, &mut errors) {
            if !matches!(
                entry.get("ijb_primitive").and_then(Value::as_str),
                Some("thing" | "scope" | "path" | "observed" | "constraint" | "time")
            ) {
                errors.push(
                    "INV03: adapter.emits[].ijb_primitive must be one of the six IJB primitives"
                        .into(),
                );
            }
        }
        for entry in entries(table, "conformance_fixtures", section, true, &mut errors) {
            for field in ["raw_input_ref", "expected_bundle_ref"] {
                nonempty(entry, field, "adapter.conformance_fixtures[]", &mut errors);
            }
        }
        for entry in entries(table, "declared_invariants", section, false, &mut errors) {
            for field in ["id", "description", "enforced_by"] {
                nonempty(entry, field, "adapter.declared_invariants[]", &mut errors);
            }
        }
        if let Some(env) = table.get("runtime_env_allowlist") {
            if !env
                .as_array()
                .is_some_and(|values| values.iter().all(Value::is_str))
            {
                errors.push(
                    "RDSTRUCT: adapter.runtime_env_allowlist must be an array of strings".into(),
                );
            }
        }
    }
    errors
}
