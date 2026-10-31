# Syntax-tree inspection and mutation

The declaration, citation and conformance consumers use `_literal_ast` through
the validator directory or the conformance `_syntax_tree` bridge. The native
CPython parser compiles source into a tree only. These helpers never execute
the inspected source. Literal evaluation accepts the declared Python literal
forms, including the empty-set spelling, and rejects general expressions.

The retained traversal, visitor, transformer and source regeneration helpers
are adapted from the supplier recorded in
`vendor-provenance/python-ast.toml`. The original license is retained in
`validators/licenses/CPython-LICENSE.txt`.

This is an internal current-source interface. Debug dumping, source-segment
extraction, documentation cleanup, the CLI, deprecated node aliases and
legacy constant visitor callbacks are retired. Parse accepts immutable text
or bytes and the current execution, expression and interactive modes. Extra
standard-library parse options are unsupported. Regeneration accepts module,
expression or interactive roots; unknown node handlers and nonempty generic
type parameters fail before emission. A newer grammar must be implemented
and exercised before a consumer can regenerate it.

Native parser positions stay transient inside inspection and mutation.
Malformed source raises a syntax error with the original byte digest and a
whole-buffer byte span. Native source coordinates and the original compiler
exception are not retained in that error. Malformed literals identify the
node type without embedding coordinates or the node representation.

`test_literal_ast_cold_start.py` derives and executes the component controls
with forbidden-import and matcher-call instrumentation. Both normal and
optimized Python modes are required. The guard integrity suite independently
injects swallowed forbidden imports into every tracked cold runner. These
controls cover the owned helper and its declared components, not native
compiler internals or unrelated dependency paths.
