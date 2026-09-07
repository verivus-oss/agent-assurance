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
from _runtime_document_vocab import validate_fields
from _vocabulary import load_catalog
from _diagnostics import printable, value_summary
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py


EVIDENCE_ROOT_RX = re.compile(r"^[0-9a-f]{64}$")
ASSERTION_ID_RX = re.compile(r"^A-[A-Za-z0-9][A-Za-z0-9_-]*$")
OBSERVED_LINE_RX = re.compile(
    # Loose check against the canonical-grammar `observed(...)` shape from
    # foundations/ijb/canonical-assertion-grammar.md, observed production. SPEC-layer
    # validation accepts any `<assertion-id> = observed(<arg-list>)` where
    # arg-list is comma-separated `key=value` pairs. Full ABNF validation
    # is RUNTIME-SPEC; this regex catches obvious shape defects.
    r"^A-[A-Za-z0-9][A-Za-z0-9_-]*\s*=\s*observed\([^)]+\)\s*$"
)


def load_vocab(ontology_path: pathlib.Path, attribute: str) -> set[str]:
    """Load an attribute_vocabulary's `values` set from the agent-assurance
    ontology. Raises FileNotFoundError if the ontology is missing; raises
    KeyError if the attribute is not declared."""
    return set(load_catalog(ontology_path.parents[2])[attribute].values)


def validate_one(path: pathlib.Path, repo_root: pathlib.Path, *, doc: dict | None = None) -> list[str]:
    """Return a list of defect strings (empty list = PASS)."""
    defects: list[str] = []
    if doc is None:
        try:
            doc = tomllib.loads(path.read_text())
        except (OSError, tomllib.TOMLDecodeError) as e:
            return [f"{path}: TOML parse failed: {e}"]

    defects.extend(f"{path}: {error}" for error in validate_fields(doc, "gate-decision", repo_root))
    decision = doc.get("decision")
    if not isinstance(decision, dict):
        return [*defects, f"{path}: missing or non-table [decision]"]

    verdict = decision.get("verdict")
    failed_refs = decision.get("failed_constraint_refs", [])
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
            f"{path}: INV01 violated: decision.verdict = {value_summary(verdict)} but "
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
        if not isinstance(cid, str) or not ASSERTION_ID_RX.fullmatch(cid):
            defects.append(
                f"{path}: INV02 violated: failed_constraint_refs[{i}]."
                f"constraint_id = {value_summary(cid)} does not match assertion-id "
                f"regex {ASSERTION_ID_RX.pattern}"
            )

    # ------------------------------------------------------------------
    # INV03: every override_refs[].observation_line parses as observed(...).
    # ------------------------------------------------------------------
    overrides = decision.get("override_refs", [])
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
                f"shape: {value_summary(line)}"
            )

    # ------------------------------------------------------------------
    # INV04: evidence_root matches 64 hex chars.
    # ------------------------------------------------------------------
    er = decision.get("evidence_root")
    if not isinstance(er, str) or not EVIDENCE_ROOT_RX.fullmatch(er):
        defects.append(
            f"{path}: INV04 violated: decision.evidence_root = {value_summary(er)} "
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
        except (OSError, ValueError, KeyError) as e:
            defects.append(
                f"{path}: INV06 vocab load failed (subject_class): {e}"
            )
            subject_class_vocab = None
        if subject_class_vocab is not None and (not isinstance(subject_class, str) or subject_class not in subject_class_vocab):
            defects.append(
                f"{path}: INV06 violated: decision.subject_class = "
                f"{value_summary(subject_class)} not in subject_class vocabulary "
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
        except (OSError, ValueError, KeyError) as e:
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
                    f"{path}: INV06 violated: decision.{label} = {value_summary(value)} "
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
            print("FAIL: " + printable(d))
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
