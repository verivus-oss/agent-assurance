"""Explicit record carriers for vocabulary, projection and conformance data."""

from reprlib import recursive_repr


class _Record:
    __slots__ = ()
    _field_names = ()

    def _set_values(self, values):
        if len(values) != len(self._field_names):
            raise TypeError("record constructor does not match its declared fields")
        for name, value in zip(self._field_names, values, strict=True):
            object.__setattr__(self, name, value)

    def _values(self):
        return tuple(getattr(self, name) for name in self._field_names)

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return self._values() == other._values()

    @recursive_repr()
    def __repr__(self):
        fields = ", ".join(name + "=" + repr(getattr(self, name)) for name in self._field_names)
        return type(self).__qualname__ + "(" + fields + ")"


class _FrozenRecord(_Record):
    __slots__ = ()

    def __setattr__(self, name, _value):
        raise AttributeError("cannot assign immutable record field: " + name)

    def __delattr__(self, name):
        raise AttributeError("cannot delete immutable record field: " + name)

    def __hash__(self):
        return hash(self._values())


class Vocabulary(_FrozenRecord):
    __slots__ = ("attribute", "values", "extensible", "source", "declaration")
    _field_names = __match_args__ = __slots__

    def __init__(self, attribute, values, extensible, source, declaration):
        self._set_values((attribute, values, extensible, source, declaration))


class Projection(_FrozenRecord):
    __slots__ = ("source", "instance", "provenance", "fields", "unindexed_fields")
    _field_names = __match_args__ = __slots__

    def __init__(self, source, instance, provenance, fields, unindexed_fields):
        self._set_values((source, instance, provenance, fields, unindexed_fields))


class Specimen(_Record):
    __slots__ = ("name", "kind", "accepted", "owner", "doc", "needle", "root_mode")
    _field_names = __match_args__ = __slots__

    def __init__(self, name, kind, accepted, owner, doc, needle="", root_mode=""):
        self._set_values((name, kind, accepted, owner, doc, needle, root_mode))


__all__ = ["Vocabulary", "Projection", "Specimen"]
