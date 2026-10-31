"""Independent value, restoration and refusal controls for temporary attributes."""

from types import ModuleType

from _temporary_attribute import temporary_attribute, returning, raising, successive
from _test_require import require, expect_raises


def test_module_values_nested_restoration_and_failure_propagation():
    owner = ModuleType('temporary_attribute_control')
    owner.value = None
    first, second = object(), object()
    error = ValueError('independent temporary attribute failure')
    with temporary_attribute(owner, 'value', first) as selected:
        require(selected is first and owner.value is first)
        caught = None
        try:
            with temporary_attribute(owner, 'value', second):
                require(owner.value is second)
                raise error
        except ValueError as observed:
            caught = observed
            require(observed is error)
        require(caught is error, 'temporary scope suppressed its body failure')
        require(owner.value is first)
    require(owner.value is None and vars(owner)['value'] is None)


def test_inherited_attributes_and_raw_descriptors_restore_exactly():
    token = object()
    class Parent:
        value = token
    class Child(Parent):
        @staticmethod
        def callback():
            return token
    original = vars(Child)['callback']
    require('value' not in vars(Child))
    with temporary_attribute(Child, 'value', False):
        require(vars(Child)['value'] is False and Parent.value is token)
    require('value' not in vars(Child) and Child.value is token)
    with temporary_attribute(Child, 'callback', None):
        require(Child.callback is None)
    require(vars(Child)['callback'] is original and Child.callback() is token)


def test_missing_attributes_and_unsupported_owners_are_refused():
    owner = ModuleType('missing_attribute_control')
    class SuppliedName(str):
        def isidentifier(self):
            raise AssertionError('supplied identifier override was executed')
    expect_raises(AttributeError, lambda: temporary_attribute(owner, 'missing', 7).__enter__(),
                  'missing attribute was silently manufactured')
    require('missing' not in vars(owner))
    for candidate, name in ((object(), 'value'), (owner, ''), (owner, 'not-an-identifier'), (owner, 7),
                            (owner, SuppliedName('value'))):
        expect_raises(TypeError, lambda: temporary_attribute(candidate, name, 7).__enter__(),
                      'unsupported temporary attribute request passed')
    require(not {name for name in vars(owner) if not name.startswith('__')})


def test_failed_installation_never_enters_the_body():
    class Locked(type):
        def __setattr__(cls, name, value):
            if name == 'value':
                raise OSError('independent attribute write refusal')
            return super().__setattr__(name, value)
    class Owner(metaclass=Locked):
        value = 3
    entered = False
    caught = None
    try:
        with temporary_attribute(Owner, 'value', 7):
            entered = True
    except OSError as observed:
        caught = observed
        require(str(observed) == 'independent attribute write refusal')
    require(not entered and caught is not None, 'attribute installation failure was suppressed')
    require(Owner.value == 3)


def test_restoration_failure_retains_the_body_failure_and_can_be_repaired():
    original, replacement = object(), object()
    class RefuseRestoration(type):
        def __setattr__(cls, name, value):
            if name == 'value' and value is original and cls.refuse:
                raise OSError('independent restoration refusal')
            return super().__setattr__(name, value)
    class Owner(metaclass=RefuseRestoration):
        value = original
        refuse = False
    body_failure = ValueError('independent body failure')
    caught = None
    try:
        try:
            with temporary_attribute(Owner, 'value', replacement):
                Owner.refuse = True
                raise body_failure
        except OSError as observed:
            caught = observed
            require(str(observed) == 'independent restoration refusal' and observed.__context__ is body_failure)
            require(Owner.value is replacement)
        require(caught is not None, 'restoration failure was suppressed')
    finally:
        Owner.refuse = False
        Owner.value = original
    require(Owner.value is original)


def test_callbacks_preserve_values_failures_and_finite_reply_boundaries():
    token = object()
    constant = returning(token)
    require(constant() is token and constant(1, named=2) is token)
    error = OSError('independent callback failure')
    fault = raising(error)
    try:
        fault(1, named=2)
    except OSError as observed:
        require(observed is error)
    else:
        raise AssertionError('declared callback failure did not execute')
    expect_raises(TypeError, lambda: raising(ValueError), 'exception class was accepted as an instance')
    values = [None, False, token]
    callback = successive(values)
    values[:] = [7]
    require(callback() is None and callback(1) is False and callback(named=2) is token)
    for _ in range(2):
        try:
            callback()
        except AssertionError as observed:
            require(str(observed) == 'temporary replies exhausted')
        else:
            raise AssertionError('undeclared extra callback invocation succeeded')
    tuple_callback = successive((3, 4))
    require(tuple_callback() == 3 and tuple_callback() == 4)
    class SuppliedList(list):
        def __iter__(self):
            raise AssertionError('supplied reply iterator override was executed')
    for unsupported in ([], (), iter((1,)), 'data', {'value': 1}, SuppliedList([1])):
        expect_raises(TypeError, lambda: successive(unsupported), 'unsupported reply population passed')


if __name__ == '__main__':
    required = {name for name, value in tuple(globals().items()) if name.startswith('test_') and callable(value)}
    require(required, 'temporary attribute controls are absent')
    visited = set()
    for name in sorted(required):
        globals()[name]()
        visited.add(name)
    require(visited == required)
    print('temporary attributes: complete declared values, restoration, failure and refusal controls executed')
