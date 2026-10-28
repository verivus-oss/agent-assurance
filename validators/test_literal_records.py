"""Declared record fields, constructor boundaries and mutability controls."""

import _literal_records as records
from _literal_records import Projection, Specimen, Vocabulary, __all__
from _test_require import expect_raises, require


def cases():
    return {
        "Vocabulary": (Vocabulary, {"attribute": "mode", "values": ("one", "two"),
                                   "extensible": False, "source": "core/ontology.toml",
                                   "declaration": {"attribute": "mode"}}, True),
        "Projection": (Projection, {"source": b"captured bytes", "instance": {"instance": 1},
                                   "provenance": {"source": "upstream"},
                                   "fields": {"runtime_kind": "os-sandbox"},
                                   "unindexed_fields": (("meta", "optional"),)}, True),
        "Specimen": (Specimen, {"name": "sample", "kind": "adapter-contract", "accepted": True,
                               "owner": "dispatch", "doc": {"meta": {}}, "needle": "INV04",
                               "root_mode": "missing-core"}, False),
    }


def test_complete_named_constructor_population():
    required = cases()
    public = {name for name, value in vars(records).items()
              if not name.startswith("_") and isinstance(value, type) and value.__module__ == records.__name__}
    require(public == set(__all__), "record exports omit a public carrier")
    require(set(required) == set(__all__) and len(__all__) == len(required))
    visited = set()
    for name, (constructor, fields, _frozen) in required.items():
        positional = constructor(*fields.values())
        keyword = constructor(**fields)
        require(type(positional) is constructor and positional == keyword)
        require(positional.__match_args__ == tuple(fields))
        for field, value in fields.items():
            require(getattr(positional, field) is value, "record field or value identity changed: " + name + "." + field)
        expect_raises(TypeError, lambda: constructor(), "absent required record fields passed")
        expect_raises(TypeError, lambda: constructor(**fields, unexpected=True), "unknown record field passed")
        expect_raises(TypeError, lambda: constructor(*fields.values(), "extra"), "extra positional record field passed")
        require(positional.__eq__(tuple(fields.values())) is NotImplemented)
        visited.add(name)
    require(visited == set(required))


def test_frozen_fields_and_mutable_payloads():
    for name, (constructor, fields, frozen) in cases().items():
        if not frozen:
            continue
        record = constructor(**fields)
        for field in fields:
            expect_raises(AttributeError, lambda: setattr(record, field, None), "frozen assignment passed: " + name + "." + field)
            expect_raises(AttributeError, lambda: delattr(record, field), "frozen deletion passed: " + name + "." + field)
        expect_raises(AttributeError, lambda: setattr(record, "unexpected", None), "frozen extra field passed")
        payload_name = "declaration" if name == "Vocabulary" else "fields"
        payload = fields[payload_name]
        payload["additional"] = True
        require(getattr(record, payload_name) is payload and getattr(record, payload_name)["additional"] is True)
        expect_raises(TypeError, lambda: hash(record), "mutable payload became hashable")


def test_mutable_specimen_and_defaults():
    doc = {"meta": {"template_kind": "adapter-contract"}}
    record = Specimen("name", "adapter-contract", True, "dispatch", doc)
    require(record.needle == "" and record.root_mode == "" and record.doc is doc)
    rejected = Specimen("rejected", "adapter-contract", False, "dispatch", doc)
    require(rejected.accepted is False, "rejected specimen constructor changed acceptance")
    record.name = "changed"
    record.accepted = False
    record.needle = "INV02"
    require(record.name == "changed" and record.accepted is False and record.needle == "INV02")
    del record.needle
    expect_raises(AttributeError, lambda: record.needle, "deleted mutable field remained present")
    record.needle = "restored"
    expect_raises(TypeError, lambda: hash(record), "mutable specimen became hashable")


def test_equality_representations_and_recursion():
    declaration = {"attribute": "mode"}
    value = Vocabulary("mode", ("one",), False, "source", declaration)
    same = Vocabulary("mode", ("one",), False, "source", {"attribute": "mode"})
    changed = Vocabulary("other", ("one",), False, "source", {"attribute": "mode"})
    require(value == same and value != changed)
    require(repr(value) == "Vocabulary(attribute='mode', values=('one',), extensible=False, source='source', declaration={'attribute': 'mode'})")
    declaration["record"] = value
    require("'record': ..." in repr(value))
    require(repr(Projection(b"raw", {}, None, {}, ())) == "Projection(source=b'raw', instance={}, provenance=None, fields={}, unindexed_fields=())")
    require(repr(Specimen("name", "kind", True, "owner", {})) == "Specimen(name='name', kind='kind', accepted=True, owner='owner', doc={}, needle='', root_mode='')")


if __name__ == "__main__":
    tests = {name: value for name, value in globals().items() if name.startswith("test_") and callable(value)}
    require(tests)
    executed = set()
    for name, test in sorted(tests.items()):
        test()
        executed.add(name)
    require(executed == set(tests))
    print("literal records: complete constructor, value identity, mutability and representation controls executed")
