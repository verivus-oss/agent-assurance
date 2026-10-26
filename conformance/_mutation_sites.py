"""Shared mutation-site selection and stable diagnostic fingerprints."""

import ast
import re


class DisableSite(ast.NodeTransformer):
    """Replace the Nth errors/defects `.append(...)` statement with `pass`."""

    def __init__(self, target: int) -> None:
        self.target = target
        self.seen = 0
        self.line: int | None = None
        self.fingerprint: str = ""

    def visit_Expr(self, node: ast.Expr):
        call = node.value
        if (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "append"
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id in ("errors", "defects")
        ):
            index = self.seen
            self.seen += 1
            if index == self.target:
                self.line = node.lineno
                self.fingerprint = fingerprint(call)
                return ast.copy_location(ast.Pass(), node)
        return node


def fingerprint(call: ast.Call) -> str:
    """A stable identity for a check, derived from its message rather than its line.

    Line numbers move whenever anything above them is edited, so a baseline keyed
    on them would churn on unrelated changes and, worse, could be silently
    re-pointed at a different check. The message text is what actually identifies
    the rule.
    """
    parts: list[str] = []
    for node in ast.walk(call):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            parts.append(node.value)
    text = " ".join(parts)
    text = re.sub(r"\s+", " ", text).strip()
    # Strip AFTER truncating too. A 70-char cut can land mid-gap and leave a
    # trailing space, and every TOML writer and formatter strips trailing
    # whitespace on the way into the baseline file. The stored identity would
    # then never match the computed one, so the check reads as permanently
    # "newly unprotected" and the gate fails on a difference that is not real.
    return text[:70].strip() if text else "<no-literal>"
