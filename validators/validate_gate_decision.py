#!/usr/bin/env python3
"""Validate a gate-decision instance against
profiles/agent-assurance/gate-decision-kind.toml's hard invariants
INV01..INV06.

This is the SPEC-layer validator referenced by every INV0n's
`enforced_by` field. It does NOT do the RUNTIME-SPEC work named in
INV05 (resolving constraint IDs against bundle contents, verifying
the evidence-root hash, evaluating overrides cryptographically); it
enforces structural shape and the conditional-required-and-inequality
predicate of INV06 against the declared vocabularies in
profiles/agent-assurance/ontology.toml.

Usage:
    python3 validators/validate_gate_decision.py --repo-root . FILE ...

Exit code 0 on full agreement, 1 on any defect.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py


EVIDENCE_ROOT_RX = re.compile(r"^[0-9a-f]{64}$")
ASSERTION_ID_RX = re.compile(r"^A-[A-Za-z0-9][A-Za-z0-9_-]*$")
OBSERVED_LINE_RX = re.compile(
    # Loose check against the canonical-grammar `observed(...)` shape from
    # foundations/ijb/canonical-assertion-grammar.md lines 46-68. SPEC-layer
    # validation accepts any `<assertion-id> = observed(<arg-list>)` where
    # arg-list is comma-separated `key=value` pairs. Full ABNF validation
    # is RUNTIME-SPEC; this regex catches obvious shape defects.
    r"^A-[A-Za-z0-9][A-Za-z0-9_-]*\s*=\s*observed\([^)]+\)\s*$"
)


def load_vocab(ontology_path: pathlib.Path, attribute: str) -> set[str]:
    """Load an attribute_vocabulary's `values` set from the agent-assurance
    ontology. Raises FileNotFoundError if the ontology is missing; raises
    KeyError if the attribute is not declared."""
    doc = tomllib.loads(ontology_path.read_text())
    for entry in doc.get("attribute_vocabularies", []):
        if entry.get("attribute") == attribute:
            return set(entry.get("values", []))
    raise KeyError(f"attribute_vocabulary {attribute!r} not declared in {ontology_path}")


def validate_one(path: pathlib.Path, repo_root: pathlib.Path) -> list[str]:
    """Return a list of defect strings (empty list = PASS)."""
    defects: list[str] = []
    try:
        doc = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as e:
        return [f"{path}: TOML parse failed: {e}"]

    meta = doc.get("meta", {})
    if meta.get("template_kind") != "gate-decision":
        return [
            f"{path}: meta.template_kind = {meta.get('template_kind')!r} "
            "(expected 'gate-decision'); not a gate-decision instance"
        ]
    if meta.get("framework_profile") != "agent-assurance":
        defects.append(
            f"{path}: meta.framework_profile = "
            f"{meta.get('framework_profile')!r} (expected 'agent-assurance' "
            "per gate-decision-kind.toml required_fields)"
        )

    decision = doc.get("decision") or {}
    if not isinstance(decision, dict):
        defects.append(f"{path}: missing or non-table [decision]")
        return defects

    verdict = decision.get("verdict")
    failed_refs = decision.get("failed_constraint_refs") or []
    if not isinstance(failed_refs, list):
        defects.append(
            f"{path}: decision.failed_constraint_refs must be an array; "
            f"got {type(failed_refs).__name__}"
        )
        failed_refs = []

    # ------------------------------------------------------------------
    # INV01: verdict == "pass" iff failed_constraint_refs is empty.
    # ------------------------------------------------------------------
    is_pass = verdict == "pass"
    is_empty = len(failed_refs) == 0
    if is_pass != is_empty:
        defects.append(
            f"{path}: INV01 violated: decision.verdict = {verdict!r} but "
            f"failed_constraint_refs has {len(failed_refs)} entr"
            f"{'y' if len(failed_refs) == 1 else 'ies'}. Verdict 'pass' "
            "requires empty/absent failed_constraint_refs; verdict 'fail' "
            "requires at least one entry."
        )

    # ------------------------------------------------------------------
    # INV02: every failed_constraint_refs[].constraint_id matches assertion-id syntax.
    # ------------------------------------------------------------------
    for i, ref in enumerate(failed_refs):
        if not isinstance(ref, dict):
            defects.append(
                f"{path}: INV02 violated: failed_constraint_refs[{i}] is "
                f"not a table; got {type(ref).__name__}"
            )
            continue
        cid = ref.get("constraint_id")
        if not isinstance(cid, str) or not ASSERTION_ID_RX.match(cid):
            defects.append(
                f"{path}: INV02 violated: failed_constraint_refs[{i}]."
                f"constraint_id = {cid!r} does not match assertion-id "
                f"regex {ASSERTION_ID_RX.pattern}"
            )

    # ------------------------------------------------------------------
    # INV03: every override_refs[].observation_line parses as observed(...).
    # ------------------------------------------------------------------
    overrides = decision.get("override_refs") or []
    if not isinstance(overrides, list):
        defects.append(
            f"{path}: decision.override_refs must be an array; "
            f"got {type(overrides).__name__}"
        )
        overrides = []
    for i, ovr in enumerate(overrides):
        if not isinstance(ovr, dict):
            defects.append(
                f"{path}: INV03 violated: override_refs[{i}] is "
                f"not a table; got {type(ovr).__name__}"
            )
            continue
        line = ovr.get("observation_line")
        if not isinstance(line, str) or not OBSERVED_LINE_RX.match(line):
            defects.append(
                f"{path}: INV03 violated: override_refs[{i}]."
                f"observation_line does not match canonical observed(...) "
                f"shape: {line!r}"
            )

    # ------------------------------------------------------------------
    # INV04: evidence_root matches 64 hex chars.
    # ------------------------------------------------------------------
    er = decision.get("evidence_root")
    if not isinstance(er, str) or not EVIDENCE_ROOT_RX.match(er):
        defects.append(
            f"{path}: INV04 violated: decision.evidence_root = {er!r} "
            f"does not match {EVIDENCE_ROOT_RX.pattern}"
        )

    # ------------------------------------------------------------------
    # INV06: self-modification cross-provider AND predicate.
    # ------------------------------------------------------------------
    subject_class = decision.get("subject_class")
    if subject_class is not None:
        # subject_class is OPTIONAL but when present MUST be drawn from vocab.
        try:
            subject_class_vocab = load_vocab(
                repo_root / "profiles" / "agent-assurance" / "ontology.toml",
                "subject_class",
            )
        except (FileNotFoundError, KeyError) as e:
            defects.append(
                f"{path}: INV06 vocab load failed (subject_class): {e}"
            )
            subject_class_vocab = None
        if subject_class_vocab is not None and subject_class not in subject_class_vocab:
            defects.append(
                f"{path}: INV06 violated: decision.subject_class = "
                f"{subject_class!r} not in subject_class vocabulary "
                f"{sorted(subject_class_vocab)}"
            )

    if subject_class == "self-modification":
        # All four attribution fields REQUIRED.
        required_keys = [
            "proposing_provider_id",
            "proposing_model_family_id",
            "deciding_provider_id",
            "deciding_model_family_id",
        ]
        missing = [k for k in required_keys
                   if not isinstance(decision.get(k), str)
                   or not decision.get(k)]
        if missing:
            defects.append(
                f"{path}: INV06 violated: subject_class = 'self-modification' "
                f"requires all four of {required_keys}; missing or empty: "
                f"{missing}"
            )

        # Vocabulary membership.
        try:
            provider_vocab = load_vocab(
                repo_root / "profiles" / "agent-assurance" / "ontology.toml",
                "provider_id",
            )
            family_vocab = load_vocab(
                repo_root / "profiles" / "agent-assurance" / "ontology.toml",
                "model_family_id",
            )
        except (FileNotFoundError, KeyError) as e:
            defects.append(
                f"{path}: INV06 vocab load failed: {e}"
            )
            return defects

        prop_p = decision.get("proposing_provider_id")
        prop_f = decision.get("proposing_model_family_id")
        dec_p = decision.get("deciding_provider_id")
        dec_f = decision.get("deciding_model_family_id")

        for label, value, vocab in (
            ("proposing_provider_id", prop_p, provider_vocab),
            ("deciding_provider_id", dec_p, provider_vocab),
            ("proposing_model_family_id", prop_f, family_vocab),
            ("deciding_model_family_id", dec_f, family_vocab),
        ):
            if isinstance(value, str) and value and value not in vocab:
                defects.append(
                    f"{path}: INV06 violated: decision.{label} = {value!r} "
                    f"not in vocabulary {sorted(vocab)}"
                )

        # The load-bearing AND predicate: BOTH inequalities must hold.
        if (isinstance(prop_p, str) and isinstance(dec_p, str)
                and isinstance(prop_f, str) and isinstance(dec_f, str)
                and prop_p and dec_p and prop_f and dec_f):
            same_provider = dec_p == prop_p
            same_family = dec_f == prop_f
            if same_provider or same_family:
                problem = []
                if same_provider:
                    problem.append(
                        f"deciding_provider_id ({dec_p!r}) == "
                        f"proposing_provider_id ({prop_p!r})"
                    )
                if same_family:
                    problem.append(
                        f"deciding_model_family_id ({dec_f!r}) == "
                        f"proposing_model_family_id ({prop_f!r})"
                    )
                defects.append(
                    f"{path}: INV06 violated (conjunctive AND): "
                    f"{' AND '.join(problem)}. INV06 requires BOTH "
                    f"deciding_provider_id != proposing_provider_id AND "
                    f"deciding_model_family_id != proposing_model_family_id. "
                    f"Same-provider/different-family and different-provider/"
                    f"same-family BOTH fail INV06."
                )

    return defects


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a gate-decision instance against the hard "
            "invariants INV01..INV06 declared in "
            "profiles/agent-assurance/gate-decision-kind.toml. "
            "INV01: verdict-failed_refs bijection. INV02: assertion-id "
            "regex on failed_constraint_refs[]. INV03: canonical "
            "observed(...) shape on override_refs[]. INV04: 64-hex "
            "evidence_root. INV05: scope declaration only (no validator "
            "action; RUNTIME-SPEC handles bundle/hash/override checks). "
            "INV06: self-modification cross-provider AND predicate "
            "(deciding provider_id AND model_family_id MUST both differ "
            "from proposing)."
        ),
    )
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path("."),
                        help="Repository root (used to locate the agent-assurance ontology).")
    parser.add_argument("paths", nargs="+", type=pathlib.Path,
                        help="Gate-decision TOML file(s) to validate.")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    all_defects: list[str] = []
    pass_count = 0
    for p in args.paths:
        defects = validate_one(p.resolve(), repo_root)
        if defects:
            all_defects.extend(defects)
        else:
            pass_count += 1

    if all_defects:
        for d in all_defects:
            print(f"FAIL: {d}")
        print(f"\nGATE-DECISION VALIDATION FAILED ({len(all_defects)} "
              f"defect{'s' if len(all_defects) != 1 else ''}; "
              f"{pass_count} file{'s' if pass_count != 1 else ''} passed).")
        return 1

    print(f"GATE-DECISION VALIDATION PASSED "
          f"({len(args.paths)} file{'s' if len(args.paths) != 1 else ''} checked; "
          f"INV01..INV06 enforced).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
