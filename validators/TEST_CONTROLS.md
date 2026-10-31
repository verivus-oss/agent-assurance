# Temporary verification attributes

At source `6266e2fee491223a715595ef8ba59662aa3c9ba4`, the complete
Git-index-derived Python syntax-tree import population contains nine
`unittest.mock` consumers. The protocol harness's module import reaches
Python's matcher machinery on both supported interpreter versions. Its
fault injection remains necessary for buffered reads, bundle changes,
connection acknowledgement, cleanup diagnostics and source-discovery tests.

`_temporary_attribute.py` provides existing module/class attribute replacement,
constant callbacks, explicit exception callbacks and captured finite replies.
Consumers pass the actual owner object and attribute name. An operation records
the raw local definition, installs the replacement, yields to its body, and
restores that exact definition on success or failure. An inherited attribute
is restored by removing the temporary local definition. Nested scopes restore
their immediately enclosing value. Installation errors propagate before body
execution. Body and restoration errors remain visible.

Owner objects and callbacks come from trusted verification code. Missing
attributes, unsupported owners, invalid names, exception classes and empty or
unbounded reply sources are refused. Reply lists are captured before calls,
and extra invocations fail. These operations mutate process state and belong
inside the verification scope that owns the affected module or class.

Dotted-name import resolution, generated mock objects, automatic attribute
creation, signature introspection, async mocks and framework discovery are
retired from these consumers. The current property checks assert actual
outcomes directly. Independent controls exercise falsy values, descriptor
identity, inherited and nested restoration, installation/body failures,
callback identity, input refusal and reply exhaustion. Cold controls also
import the actual protocol harness while rejecting framework and matcher
imports. Persistent driver lanes separately exercise the property witnesses.

The direct-import gate derives every tracked Python source and every supported
workflow literal before checking retired imports. Cold guards retain swallowed
import attempts. These controls cover the declared attribute helper and its
consumers; concurrent execution and other driver/scanner dependency audits
remain separate work.
