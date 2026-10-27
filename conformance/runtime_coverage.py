"""Mapping-derived diagnostic and wrapper mutations, without new exemptions."""

import ast
import _json_decode as json
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
                             "accepted": not errors, "errors": errors, "needle": case.needle,
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


def mutation_result(baseline, observed):
    population = [(row["specimen"], row["expected"], row["needle"]) for row in baseline]
    if population != [(row["specimen"], row["expected"], row["needle"]) for row in observed]:
        raise RuntimeError("mutation changed the executed specimen population")
    witnesses = []
    diagnostic_changes = []
    for before, after in zip(baseline, observed, strict=True):
        failures = []
        if after["accepted"] != after["expected"]:
            failures.append("expected acceptance or rejection")
        if after["needle"] and not any(after["needle"].lower() in error.lower() for error in after["errors"]):
            failures.append("required diagnostic token")
        if not before["passed"] or after["passed"] != (not failures):
            raise RuntimeError("runtime specimen property result is inconsistent")
        if failures:
            witnesses.append({"specimen": after["specimen"], "failing_properties": failures,
                              "expected": after["expected"], "accepted": after["accepted"],
                              "required_diagnostic": after["needle"],
                              "before": before["errors"], "after": after["errors"]})
        elif before["errors"] != after["errors"]:
            diagnostic_changes.append({"specimen": after["specimen"],
                                       "before": before["errors"], "after": after["errors"]})
    status = "killed" if witnesses else "diagnostic-only" if diagnostic_changes else "unprotected"
    return {"status": status, "witnesses": witnesses, "diagnostic_changes": diagnostic_changes}


def diagnostic_only_control(root, baseline):
    path = root / "validators/validate_gate_decision.py"
    original = path.read_text()
    target = "decision.failed_constraint_refs must be an array"
    if original.count(target) != 1:
        raise RuntimeError("diagnostic-only control did not select exactly one message")
    path.write_text(original.replace(target, "control: " + target, 1))
    try:
        observed = execute(root)
    finally:
        path.write_text(original)
    result = mutation_result(baseline, observed)
    if result["status"] != "diagnostic-only" or not result["diagnostic_changes"] or result["witnesses"]:
        raise AssertionError("diagnostic-only control must change messages without failing a specimen property")
    return {"mutation": "diagnostic-text-prefix", **result}


def audit(root, report):
    baseline = execute(root)
    if not all(row["passed"] for row in baseline):
        report.write_text(json.dumps({"status": "baseline-failed", "failures": [row for row in baseline if not row["passed"]]}, indent=2))
        raise RuntimeError("independent runtime specimens failed before any mutation")
    control = diagnostic_only_control(root, baseline)
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
            results.append({"owner": owner, "mutation": label, **mutation_result(baseline, observed)})
    report.write_text(json.dumps({"status": "passed" if results and all(row["status"] == "killed" for row in results) else "failed",
                                 "control": control, "mutations": results, "skipped": []}, ensure_ascii=True, indent=2) + "\n")
    unprotected = [row for row in results if row["status"] != "killed"]
    if not results or unprotected:
        raise AssertionError("new runtime checks lack removal witnesses: " + json.dumps(unprotected))
    killed = sum(row["status"] == "killed" for row in results)
    if killed != len(results) or control["status"] != "diagnostic-only":
        raise AssertionError("runtime mutation report counts do not match verdicts")
    print(f"Runtime coverage: {killed}/{len(results)} isolated mutations have failing-property witnesses; diagnostic-only control=1; skipped=[]")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "--worker":
        raise SystemExit("use coverage_audit.py, or --worker REPO_ROOT")
    worker(Path(sys.argv[2]).resolve())
