"""Bound the local credential import graph and reject dependency cycles."""

import _literal_ast as ast
from _literal_path import Path
from _test_require import expect_raises, require


def require_acyclic(graph):
    active, finished = set(), set()

    def visit(name):
        if name in active:
            raise ValueError("credential import cycle: " + name)
        if name in finished:
            return
        active.add(name)
        for dependency in sorted(graph[name]):
            visit(dependency)
        active.remove(name)
        finished.add(name)

    for name in sorted(graph):
        visit(name)
    require(finished == set(graph), "credential dependency population was not traversed")


def test_credential_import_graph():
    directory = Path(__file__).resolve().parent
    sources = {path.stem: path for path in directory.iterdir()
               if path.is_file() and path.name.startswith("_credential_") and path.suffix == ".py"}
    require({"_credential_detection", "_credential_primitives", "_credential_formats", "_credential_structures"} <= set(sources))
    graph = {}
    for name, path in sources.items():
        dependencies = set()
        for node in ast.walk(ast.parse(path.read_bytes())):
            if isinstance(node, ast.Import):
                dependencies.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                dependencies.add(node.module.split(".")[0])
        graph[name] = dependencies & set(sources)
    require_acyclic(graph)
    require(not graph["_credential_primitives"], "shared predicates depend on their consumers")
    # Prove a cycle in any governed module is rejected, including lazy imports.
    visited = set()
    for name in graph:
        mutated = {key: value | ({key} if key == name else set()) for key, value in graph.items()}
        error = expect_raises(ValueError, lambda: require_acyclic(mutated), "self import cycle passed")
        require(str(error) == "credential import cycle: " + name)
        visited.add(name)
    require(visited == set(sources), "cycle rejection controls omitted a credential module")
    require_acyclic({"first": {"second"}, "second": set()})
    expect_raises(ValueError, lambda: require_acyclic({"first": {"second"}, "second": {"first"}}),
                  "mutual import cycle passed")


if __name__ == "__main__":
    test_credential_import_graph()
    print("credential dependency controls: derived source graph accepted; self and mutual cycles rejected")
