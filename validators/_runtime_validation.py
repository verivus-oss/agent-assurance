"""Validate one captured root document; referenced evidence resolves separately."""

import argparse
from pathlib import Path

import _toml11 as toml
from _runtime_document_vocab import KINDS, validate_adapter
from _vocabulary import canonical_profile
from _diagnostics import printable
import validate_closure_root as closure
import validate_gate_decision as gate
import validate_ijb_conformance as ijb
import validate_provenance as provenance
import validate_kind_descriptor as descriptors
import validate_abstraction_class as abstraction

CHECKS = ("meta-posture", "profile-identity", "provenance-binding", "IJB-instance",
          "source-hash-closure", "controlling-descriptor-and-capability-envelope",
          "runtime-document-fields-and-declared-invariants")


def validate_document(doc: dict, path: Path, repo_root: Path, kind: str) -> list[str]:
    if kind not in KINDS:
        return [f"unsupported-projection: {kind!r}"]
    meta = doc.get("meta")
    if not isinstance(meta, dict):
        return ["RDMETA: meta must be a table"]
    if meta.get("template_kind") != kind:
        return [f"RDMETA: meta.template_kind must equal {kind!r}"]
    if canonical_profile(meta.get("framework_profile")) != "agent-assurance":
        return ["RDMETA: framework_profile must identify agent-assurance"]
    errors = ijb.validate_meta_posture(doc, str(path), repo_root)
    version = meta.get("schema_version")
    if isinstance(version, str) and version.split(".")[0] != "0":
        errors.append("RDMETA: reference projection version 1 supports schema major 0")
    try:
        descriptor_path = repo_root / f"profiles/agent-assurance/{kind}-kind.toml"
        descriptor = toml.loads(descriptor_path.read_text(encoding="utf-8"))
        errors.extend(descriptors.validate(descriptor, allow_placeholders=False))
        errors.extend(ijb.validate_kind_descriptor(descriptor, str(descriptor_path)))
        declaration = descriptor["kind"]
        for section in ("abstraction_class", "capability_envelope"):
            if not isinstance(declaration.get(section), dict):
                errors.append(f"RDLOAD: controlling descriptor requires kind.{section}")
        if isinstance(declaration.get("abstraction_class"), dict):
            errors.extend(abstraction.validate_abstraction_class(declaration["abstraction_class"], descriptor_path))
        if isinstance(declaration.get("capability_envelope"), dict):
            errors.extend(abstraction.validate_capability_envelope(declaration["capability_envelope"], descriptor_path,
                                                                  abstraction._load_domains(repo_root)))
        ontologies = []
        for relative in ("core/ontology.toml", "profiles/agent-assurance/ontology.toml"):
            source = repo_root / relative
            declaration = toml.loads(source.read_text(encoding="utf-8"))
            errors.extend(ijb.validate_ontology(declaration, relative))
            ontologies.append((relative, declaration))
        errors.extend(ijb.validate_instance(doc, str(path), *ijb.build_resolver(ontologies)))
        errors.extend(provenance.validate_one(path, repo_root, doc=doc))
        # Referenced profile files are a separate trusted input population.
        # Parse each before calling legacy discovery, which otherwise skips a
        # malformed profile. Never let a skipped file remove a required pin.
        for profile in sorted(repo_root.glob("profiles/*/PROFILE.toml")):
            toml.loads(profile.read_text(encoding="utf-8"))
        duplicates = closure.duplicate_profile_names(repo_root)
        errors.extend(duplicates)
        errors.extend(closure.validate(path, closure.load_pinned_records(repo_root),
                                       closure._loaded_profile_names(repo_root), data=doc))
        if kind == "gate-decision":
            errors.extend(gate.validate_one(path, repo_root, doc=doc))
        else:
            errors.extend(validate_adapter(doc, repo_root, binding=kind == "adapter-registry-binding"))
    except (OSError, ValueError, KeyError, TypeError, SystemExit) as exc:
        errors.append(f"RDLOAD: required validation input failed: {exc}")
    return errors


def cli(kind: str) -> int:
    parser = argparse.ArgumentParser(description=f"Validate {kind} declarations without runtime execution")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    errors = []
    for path in args.paths:
        try:
            captured = path.read_bytes()
            doc = toml.loads(captured.decode("utf-8"))
            errors.extend(validate_document(doc, path, args.repo_root.resolve(), kind))
        except (OSError, ValueError) as exc:
            errors.append(f"{path}: TOML input failed: {exc}")
    for error in errors:
        print("FAIL: " + printable(error))
    if not errors:
        print(f"PASS: {len(args.paths)} {kind} documents; checks={','.join(CHECKS)}; runtime execution and trust evaluation excluded")
    return int(bool(errors))
