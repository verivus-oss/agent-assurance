# Internal record carriers

The three authored dataclass sites at project commit
`1691549990e81ac801fbbc611d1f7e31a36b5719` move to explicit carriers in
`_literal_records.py`. Their current consumers are vocabulary discovery,
captured document projection and the active runtime conformance specimens.
The existing modules re-export the same class names.

`Vocabulary` and `Projection` reject ordinary assignment and deletion.
Their nested dictionaries keep the previous shallow mutability and value
identities. `Specimen` keeps mutable named fields and the empty `needle` and
`root_mode` defaults. Constructors retain their argument order and keyword
names, exact-type equality, field representations and literal structure-match
metadata. Representations handle recursive payloads. Mutable payloads remain
unhashable.

The carriers have explicit slots and constructors. They do not implement the
dataclass framework's field factories, reflection, replacement or serialization
APIs. The current tracked Python consumer search found no authored use of
those APIs. No template kind, database column or normative field rule changes.

The component controls derive the public carrier population, compare it with
independent field mappings, and exercise accepted/default construction, extra
or absent operands, mutable updates, frozen failures, equality boundaries and
representations. Fresh normal and optimized controls reject regex/dataclasses
imports and observe Python matcher calls. The direct-import source boundary
checks every tracked Python file for retired dependencies.

This component does not complete the reference-store cold audit. Pathlib and
external driver/dependency consumers remain inside that work. The component
instrument does not claim their imports or native internals were exercised.
