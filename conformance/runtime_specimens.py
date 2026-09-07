"""Independent descriptor-derived expectations for the three runtime document kinds.

The fixed answers below do not import the new vocabulary validator or storage
mapping. The gate separately compares this field population with that mapping.
"""


from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "validators"))
import _toml11 as toml  # noqa: E402
from _instrument import require

FIELDS = (
    ("adapter-contract", "adapter", "runtime_kind", ("wasi-component", "oci-action", "os-sandbox"), True),
    ("adapter-contract", "adapter", "runtime_network_policy", ("denied", "loopback-only", "allowlist", "open"), True),
    ("adapter-contract", "adapter", "runtime_clock_policy", ("injected", "source-date-epoch", "monotonic-from-zero", "host-wall-clock"), True),
    ("adapter-contract", "adapter", "id_derivation", ("content-hash", "nonce", "external"), False),
    ("adapter-registry-binding", "binding", "adapter_ref_syntax", ("content-hash", "name-version-pin"), True),
    ("gate-decision", "decision", "verdict", ("pass", "fail"), True),
)
DIGEST_FIELDS = {"wasi-component": "component_digest", "oci-action": "oci_image_digest", "os-sandbox": "profile_args_digest"}


def encode(value):
    if isinstance(value, dict):
        return "{ " + ", ".join(json.dumps(key) + " = " + encode(item) for key, item in value.items()) + " }"
    if isinstance(value, list):
        return "[" + ", ".join(encode(item) for item in value) + "]"
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def dump(doc):
    return ("\n".join(json.dumps(key) + " = " + encode(value) for key, value in doc.items()) + "\n").encode()


@dataclass
class Specimen:
    name: str
    kind: str
    accepted: bool
    owner: str
    doc: dict
    needle: str = ""
    root_mode: str = ""


def specimens(root: Path) -> list[Specimen]:
    kinds = ("adapter-contract", "adapter-registry-binding", "gate-decision")
    base = {kind: toml.loads((root / f"examples/minimal-{kind}.toml").read_text()) for kind in kinds}
    result = []

    def add(kind, name, accepted, owner, edit=lambda doc: None, needle="", root_mode=""):
        doc = deepcopy(base[kind])
        edit(doc)
        result.append(Specimen(kind + "/" + name, kind, accepted, owner, doc, needle, root_mode))

    for kind in kinds:
        add(kind, "canonical", True, "dispatch")
        add(kind, "profile-alias", True, "profile-identity", lambda doc: doc["meta"].update(framework_profile="AGDF"))
        add(kind, "unrelated-profile", False, "profile-identity", lambda doc: doc["meta"].update(framework_profile="other"), "framework_profile")
        add(kind, "custom-license", True, "extensibility", lambda doc: doc["meta"].update(license="LicenseRef-private-choice"))
        section = {"adapter-contract": "adapter", "adapter-registry-binding": "binding", "gate-decision": "decision"}[kind]
        add(kind, "section/not-table", False, "required-section", lambda doc: doc.update({section: []}))
        add(kind, "repository/missing-core", False, "required-input", root_mode="missing-core")
    malformed = [("unknown", "__undeclared__"), ("empty", ""), ("integer", 17), ("boolean", True),
                 ("array", ["denied"]), ("table", {"value": "denied"})]
    for kind, section, field, tokens, required in FIELDS:
        for token in tokens:
            def edit(doc):
                doc[section][field] = token
                if field == "runtime_kind":
                    doc[section]["runtime_artifact"] = {DIGEST_FIELDS[token]: "a" * 64}
                if field == "verdict" and token == "pass":  # nosec B105 # noqa: S105
                    doc[section].pop("failed_constraint_refs")
            add(kind, field + "/accept/" + token, True, "field:" + field, edit)
        for label, value in malformed:
            add(kind, field + "/reject/" + label, False, "field:" + field,
                lambda doc: doc[section].update({field: value}), "RDVOCAB")
        add(kind, field + "/absent", not required, "field:" + field, lambda doc: doc[section].pop(field))
        for label, value in (("uppercase", tokens[0].upper()), ("space", tokens[0] + " "), ("newline", tokens[0] + "\n")):
            require(value not in tokens)
            add(kind, field + "/reject/" + label, False, "field:" + field, lambda doc: doc[section].update({field: value}), "RDVOCAB")

    adapter = "adapter-contract"
    for runtime, field in DIGEST_FIELDS.items():
        add(adapter, "digest/" + runtime + "/valid", True, "INV02",
            lambda doc: doc["adapter"].update(runtime_kind=runtime, runtime_artifact={field: "a" * 64}))
        for label, value in (("uppercase", "A" * 64), ("newline", "a" * 64 + "\n"), ("unicode", "\u0430" * 64),
                             ("short", "a" * 63), ("wrong-type", 5)):
            add(adapter, "digest/" + runtime + "/" + label, False, "INV02",
                lambda doc: doc["adapter"].update(runtime_kind=runtime, runtime_artifact={field: value}), "INV02")
        add(adapter, "digest/" + runtime + "/wrong-family", False, "INV02",
            lambda doc: doc["adapter"].update(runtime_kind=runtime, runtime_artifact={"unrelated_digest": "a" * 64}), "INV02")
    for primitive in ("thing", "scope", "path", "observed", "constraint", "time"):
        add(adapter, "emits/" + primitive, True, "INV03", lambda doc: doc["adapter"].update(emits=[{"ijb_primitive": primitive}]))
    add(adapter, "emits/undeclared", False, "INV03", lambda doc: doc["adapter"].update(emits=[{"ijb_primitive": "unknown"}]), "INV03")
    add(adapter, "artifact/not-table", False, "INV02", lambda doc: doc["adapter"].update(runtime_artifact=[]), "INV02")
    for field in ("emits", "conformance_fixtures"):
        for label, value in (("empty", []), ("not-array", {}), ("not-table-entry", [3])):
            add(adapter, field + "/" + label, False, "required-section:" + field,
                lambda doc: doc["adapter"].update({field: value}), field)
    add(adapter, "input-source/empty", False, "required-field:input_source", lambda doc: doc["adapter"].update(input_source=""), "input_source")
    add(adapter, "hash-method/extension", True, "extensibility", lambda doc: doc["adapter"].update(input_hash_method="private-canonicalizer"))
    add(adapter, "hash-method/wrong-type", False, "extensibility", lambda doc: doc["adapter"].update(input_hash_method=1), "input_hash_method")
    add(adapter, "fixture/missing-expected", False, "required-section:conformance_fixtures",
        lambda doc: doc["adapter"].update(conformance_fixtures=[{"raw_input_ref": "inert"}]), "expected_bundle_ref")
    for field in ("id", "description", "enforced_by"):
        add(adapter, "declared-invariant/missing-" + field, False, "optional-structure",
            lambda doc: doc["adapter"]["declared_invariants"][0].pop(field), field)
    add(adapter, "environment/wrong-entry", False, "optional-structure", lambda doc: doc["adapter"].update(runtime_env_allowlist=[1]), "runtime_env_allowlist")

    binding = "adapter-registry-binding"
    for scheme in ("file", "https", "oci", "ipfs"):
        add(binding, "scheme/" + scheme, True, "INV01", lambda doc: doc["binding"].update(registry_url_scheme=scheme, registry_url=scheme + "://inert"))
    add(binding, "scheme/undeclared", False, "INV01", lambda doc: doc["binding"].update(registry_url_scheme="undeclared", registry_url="undeclared://inert"), "INV01")
    add(binding, "scheme/declared-extension", True, "INV01",
        lambda doc: doc["binding"].update(registry_url_scheme="private-registry", registry_url="private-registry://inert"),
        root_mode="registry-extension")
    add(adapter, "repository/closed-vocabulary-extensible", False, "required-input", root_mode="closed-extensible")
    add(binding, "url/mismatched-prefix", False, "INV02", lambda doc: doc["binding"].update(registry_url="http://inert"), "INV02")
    add(binding, "url/matching-prefix", True, "INV02")
    add(binding, "citations/absent", True, "optional-structure", lambda doc: (doc["binding"].pop("trust_anchor_refs"), doc["binding"].pop("policy_constraint_refs")))
    for field in ("trust_anchor_refs", "policy_constraint_refs"):
        add(binding, field + "/not-array", False, "optional-structure", lambda doc: doc["binding"].update({field: {}}), field)
        add(binding, field + "/bad-entry", False, "optional-structure", lambda doc: doc["binding"].update({field: [1]}), field)
    add(binding, "trust-anchor/missing-id", False, "optional-structure", lambda doc: doc["binding"].update(trust_anchor_refs=[{}]), "anchor_id")
    for field in ("adapter_ref", "registry_url"):
        add(binding, field + "/empty", False, "required-field:" + field, lambda doc: doc["binding"].update({field: ""}), field)
    gate = "gate-decision"
    for label, value, accepted in (("ascii-uppercase", "A-AbC_09-x", True), ("newline", "A-ok\n", False),
                                    ("unicode", "A-\u0430", False), ("empty-slug", "A-", False), ("wrong-type", 2, False)):
        add(binding, "assertion-id/" + label, accepted, "INV03",
            lambda doc: doc["binding"].update(policy_constraint_refs=[{"constraint_id": value}]), "" if accepted else "INV03")
        add(gate, "assertion-id/" + label, accepted, "INV02",
            lambda doc: doc["decision"].update(failed_constraint_refs=[{"constraint_id": value}]), "" if accepted else "INV02")
    for label, value in (("uppercase", "A" * 64), ("newline", "a" * 64 + "\n"), ("unicode", "\u0430" * 64)):
        add(gate, "digest/" + label, False, "INV04", lambda doc: doc["decision"].update(evidence_root=value), "INV04")
    add(gate, "unknown-verdict/no-failures", False, "field:verdict",
        lambda doc: (doc["decision"].update(verdict="unknown"), doc["decision"].pop("failed_constraint_refs")), "RDVOCAB")
    add(gate, "pass-with-failures", False, "INV01", lambda doc: doc["decision"].update(verdict="pass"), "INV01")
    add(gate, "fail-without-failures", False, "INV01", lambda doc: doc["decision"].pop("failed_constraint_refs"), "INV01")
    for field in ("failed_constraint_refs", "override_refs"):
        for label, value in (("table", {}), ("boolean", False), ("integer", 0)):
            add(gate, field + "/wrong-type/" + label, False, "optional-structure", lambda doc: doc["decision"].update({field: value}), field)
        add(gate, field + "/wrong-entry", False, "optional-structure", lambda doc: doc["decision"].update({field: [1]}), field)
    add(gate, "override/malformed-observed", False, "INV03",
        lambda doc: doc["decision"].update(override_refs=[{"observation_line": "A-wrong = thing()"}]), "INV03")
    attribution = {"subject_class": "self-modification", "proposing_provider_id": "openai", "proposing_model_family_id": "gpt",
                   "deciding_provider_id": "anthropic", "deciding_model_family_id": "claude"}
    add(gate, "self-modification/independent", True, "INV06", lambda doc: doc["decision"].update(attribution))
    add(gate, "self-modification/missing-attribution", False, "INV06", lambda doc: doc["decision"].update(subject_class="self-modification"), "INV06")
    add(gate, "subject/undeclared", False, "INV06", lambda doc: doc["decision"].update(subject_class="unknown-subject"), "INV06")
    add(gate, "subject/wrong-type", False, "INV06", lambda doc: doc["decision"].update(subject_class=[]), "INV06")
    for name, changed in (("same-provider", {"deciding_provider_id": "openai"}),
                          ("same-family", {"deciding_model_family_id": "gpt"}),
                          ("unknown-provider", {"deciding_provider_id": "not-declared"}),
                          ("unknown-family", {"deciding_model_family_id": "not-declared"})):
        add(gate, "self-modification/" + name, False, "INV06", lambda doc: doc["decision"].update({**attribution, **changed}), "INV06")
    add(gate, "repository/missing-subject-catalog", False, "required-input",
        lambda doc: doc["decision"].update(subject_class="downstream-change"), root_mode="malformed-ontology")
    add(gate, "repository/missing-provider-catalog", False, "required-input",
        lambda doc: doc["decision"].update(attribution), root_mode="malformed-ontology")
    if len({case.name for case in result}) != len(result) or not result:
        raise AssertionError("specimen identities are missing or duplicated")
    return result


def prepare_roots(root, work):
    """Trusted-input variants, separate from untrusted document mutations."""
    sys.path.insert(0, str(root / "reference/database"))
    from _contract import bundle_entries
    entries = bundle_entries(root)
    roots = {"": root}
    for mode in {case.root_mode for case in specimens(root)} - {""}:
        candidate = work / mode
        candidate.mkdir(parents=True, exist_ok=True)
        for relative in entries:
            target = candidate / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((root / relative).read_bytes())
        ontology = candidate / "profiles/agent-assurance/ontology.toml"
        text = ontology.read_text()
        if mode == "registry-extension":
            old = '["file", "https", "oci", "ipfs"]'
            require(text.count(old) == 1)
            ontology.write_text(text.replace(old, '["file", "https", "oci", "ipfs", "private-registry"]'))
        elif mode == "closed-extensible":
            start = text.index('attribute   = "runtime_kind"')
            prefix, tail = text[:start], text[start:]
            require('extensible  = false' in tail.split('[[attribute_vocabularies]]')[0])
            ontology.write_text(prefix + tail.replace('extensible  = false', 'extensible  = true', 1))
        elif mode == "missing-core":
            (candidate / "core/ontology.toml").unlink()
        else:
            require(mode == "malformed-ontology")
            ontology.write_text("malformed ontology = [")
        roots[mode] = candidate
    return roots
