"""Mapping-derived diagnostic and wrapper mutations, without new exemptions."""

import ast
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "validators"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference/database"))
from _contract import load_mapping  # noqa: E402
from _mutation_sites import DisableSite  # noqa: E402


def worker(root):
    from runtime_specimens import specimens, prepare_roots
    import validate_gate_decision
    import validate_adapter_contract
    import validate_adapter_registry_binding
    roots = prepare_roots(root, root / ".local/runtime-coverage-inputs")
    validators = {"gate-decision": lambda doc, trusted: validate_gate_decision.validate_one(root / "inert.toml", trusted, doc=doc),
                  "adapter-contract": lambda doc, trusted: validate_adapter_contract.validate(doc, trusted),
                  "adapter-registry-binding": lambda doc, trusted: validate_adapter_registry_binding.validate(doc, trusted)}
    observations = []
    for case in specimens(root):
        errors = validators[case.kind](case.doc, roots[case.root_mode])
        observations.append({"specimen": case.name, "expected": case.accepted,
                             "accepted": not errors, "errors": errors,
                             "passed": (not errors) == case.accepted and (not case.needle or any(case.needle.lower() in error.lower() for error in errors))})
    print(json.dumps(observations, ensure_ascii=True))


def audited_owners(root):
    owners = {owner for row in load_mapping(root) if row["representation"] == "document-column"
              for owner in row["validator_owners"]}
    if not owners:
        raise ValueError("mapping declares no validator owners")
    return owners


def execute(root):
    process = subprocess.run([sys.executable, str(root / "conformance/runtime_coverage.py"), "--worker", str(root)],  # nosec B603 # noqa: S603
                             cwd=root, capture_output=True, text=True, timeout=120)  # nosec B603 # noqa: S603
    if process.returncode != 0:
        raise RuntimeError("runtime mutation suite did not run: " + process.stdout + process.stderr)
    observed = json.loads(process.stdout)
    if not observed or not any(row["expected"] for row in observed) or all(row["expected"] for row in observed):
        raise RuntimeError("runtime mutation suite has no positive/negative population")
    return observed


def audit(root, report):
    baseline = execute(root)
    if not all(row["passed"] for row in baseline):
        report.write_text(json.dumps({"status": "baseline-failed", "failures": [row for row in baseline if not row["passed"]]}, indent=2))
        raise RuntimeError("independent runtime specimens failed before any mutation")
    results = []
    for owner in sorted(audited_owners(root)):
        path = root / owner
        original = path.read_text()
        probe = DisableSite(-1)
        probe.visit(ast.parse(original))
        mutations = []
        for index in range(probe.seen):
            transform = DisableSite(index)
            tree = transform.visit(ast.parse(original))
            ast.fix_missing_locations(tree)
            mutations.append(("diagnostic/" + transform.fingerprint, ast.unparse(tree)))
        if not mutations:
            if owner.endswith("validate_adapter_contract.py"):
                changed = original.replace("validate = validate_adapter", "validate = lambda *args, **kwargs: []")
            elif owner.endswith("validate_adapter_registry_binding.py"):
                changed = original.replace("return validate_adapter(doc, repo_root, binding=True)", "return []")
            else:
                raise ValueError("owner has no discoverable checks or tested call boundary: " + owner)
            if changed == original:
                raise ValueError("wrapper boundary mutation did not select its subject")
            mutations.append(("public-validation-call-boundary", changed))
        for label, changed in mutations:
            path.write_text(changed)
            try:
                observed = execute(root)
            finally:
                path.write_text(original)
            if len(observed) != len(baseline):
                raise RuntimeError("mutation changed the executed specimen population")
            witnesses = [{"specimen": after["specimen"], "before": before["errors"], "after": after["errors"]}
                         for before, after in zip(baseline, observed, strict=True)
                         if before["errors"] != after["errors"]]
            results.append({"owner": owner, "mutation": label, "status": "killed" if witnesses else "unprotected",
                            "property": "expected rejection or diagnostic removed", "witnesses": witnesses})
    report.write_text(json.dumps({"status": "passed" if all(row["status"] == "killed" for row in results) else "failed",
                                 "mutations": results, "skipped": []}, ensure_ascii=True, indent=2) + "\n")
    unprotected = [row for row in results if row["status"] != "killed"]
    if not results or unprotected:
        raise AssertionError("new runtime checks lack removal witnesses: " + json.dumps(unprotected))
    print(f"Runtime coverage: {len(results)} isolated mutations have failing-property witnesses; new exemptions=0; skipped=[]")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "--worker":
        raise SystemExit("use coverage_audit.py, or --worker REPO_ROOT")
    worker(Path(sys.argv[2]).resolve())
