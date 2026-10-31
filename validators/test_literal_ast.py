"""Independent source, literal, visitor and mutation-helper controls."""

import hashlib
import builtins
import os
import sys

import _literal_ast as ast
from _test_require import expect_raises, require
from _temporary_attribute import temporary_attribute, returning


def shape(value):
    if isinstance(value, ast.AST):
        return (type(value).__name__, tuple((name, shape(child)) for name, child in ast.iter_fields(value)
                                          if name not in ('lineno', 'col_offset', 'end_lineno', 'end_col_offset')))
    if isinstance(value, list):
        return [shape(child) for child in value]
    return value


def test_sources_and_literal_goldens():
    module = ast.parse('value = 1')
    require(isinstance(module, ast.Module) and len(module.body) == 1)
    assignment = module.body[0]
    require(isinstance(assignment, ast.Assign) and assignment.targets[0].id == 'value' and assignment.value.value == 1)
    require(isinstance(ast.parse('1 + 2', mode='eval'), ast.Expression))
    require(isinstance(ast.parse('value = 1', mode='single'), ast.Interactive))
    require(ast.parse(b'name = "\xc3\xa9"').body[0].value.value == 'é')
    cases = {
        'None': None, 'True': True, 'False': False, '0': 0, '-2': -2, '+3': 3,
        '1.25': 1.25, '2j': 2j, '1+2j': 1 + 2j, '3-4j': 3 - 4j,
        "'é'": 'é', "b'\\x00\\xff'": b'\x00\xff', '...': Ellipsis,
        '[]': [], '()': (), '{}': {}, '{1,2}': {1, 2}, 'set()': set(),
        '[1, True, None]': [1, True, None], '(1, "x")': (1, 'x'),
        '{"one": 1, "one": 2}': {'one': 2}, '  \t[1, 2]': [1, 2],
    }
    visited = set()
    for source, expected in cases.items():
        result = ast.literal_eval(source)
        require(type(result) is type(expected) and result == expected, 'declared literal answer changed: ' + source)
        require(ast.literal_eval(ast.parse(source.lstrip(), mode='eval')) == expected)
        visited.add(source)
    require(visited == set(cases))
    for source in ('name', '1/0', "__import__('absent_literal_control_module')", 'set(1)', 'set(value=1)',
                   '[name]', '{[]:1}', '{1, []}', '1 + 2', '[x for x in ()]'):
        expect_raises((ValueError, TypeError), lambda: ast.literal_eval(source), 'general expression executed as a literal')
    for value in (None, 1, bytearray(b'a=1'), memoryview(b'a=1')):
        expect_raises(TypeError, lambda: ast.parse(value), 'unsupported source operand passed')
    retired_options = {'type_comments': True}
    expect_raises(TypeError, lambda: ast.parse('a=1', **retired_options), 'retired parse option passed')
    for mode in ('func_type', 'future', None):
        expect_raises(ValueError, lambda: ast.parse('a=1', mode=mode), 'unsupported parse mode passed')
    for retired in ('dump', 'get_docstring', 'get_source_segment', 'increment_lineno', 'main', 'Num', 'Str', 'Index', 'ExtSlice'):
        require(not hasattr(ast, retired), 'retired AST API remained: ' + retired)


def test_native_parser_requires_the_declared_root():
    native = builtins.compile
    wrong = (None, object(), native('value = 1', '<private-control>', 'exec'),
             ast.AST(), ast.parse('1', mode='eval'))
    for value in wrong:
        with temporary_attribute(builtins, 'compile', returning(value)):
            error = expect_raises(RuntimeError, lambda: ast.parse('value = 1'),
                                  'absent or unrelated native parser output was accepted')
        require(str(error) == 'native Python parser did not return its declared syntax root')
        require(builtins.compile is native)
    require(type(ast.parse('value = 1')) is ast.Module)
    require(type(ast.parse('1', mode='eval')) is ast.Expression)
    require(type(ast.parse('value = 1', mode='single')) is ast.Interactive)


def test_source_subclass_buffers_and_diagnostics():
    def forbidden(*_arguments, **_options):
        raise AssertionError('source subclass method was executed')

    class Text(str):
        __str__ = encode = lstrip = __getitem__ = forbidden

    class Bytes(bytes):
        __bytes__ = decode = __getitem__ = forbidden

    require(ast.parse(Text('a = 1')).body[0].value.value == 1)
    require(ast.parse(Bytes(b'a = 2')).body[0].value.value == 2)
    require(ast.literal_eval(Text('  [1, 2]')) == [1, 2])
    sources = (b'value = (', b'value = "\xff"', 'é = (', 'value = "\ud800"', 'value = "\x00"')
    for source in sources:
        raw = source if type(source) is bytes else source.encode('utf-8', 'surrogatepass')
        error = expect_raises(SyntaxError, lambda: ast.parse(source), 'invalid Python source passed')
        require(error.source_sha256 == hashlib.sha256(raw).hexdigest())
        require(error.byte_span == (0, len(raw)))
        require(all(getattr(error, name) is None for name in ('filename', 'lineno', 'offset', 'end_lineno', 'end_offset', 'text')))
        require(error.__context__ is None and error.__cause__ is None)
        require('line' not in str(error) and 'column' not in str(error))
    error = expect_raises(ValueError, lambda: ast.literal_eval('invalid_name'), 'nonliteral source passed')
    require('Name' in str(error) and 'line' not in str(error) and 'column' not in str(error))
    source = ' \t(é'
    error = expect_raises(SyntaxError, lambda: ast.literal_eval(source), 'invalid literal syntax passed')
    raw = source.encode('utf-8')
    require(error.source_sha256 == hashlib.sha256(raw).hexdigest() and error.byte_span == (0, len(raw)))
    require(error.__context__ is None and error.__cause__ is None)


def test_visitors_transformations_and_locations():
    tree = ast.parse('errors.append("FIRST")\nvalue = 2\nerrors.append("SECOND")\n')

    class Select(ast.NodeVisitor):
        def __init__(self):
            self.messages = []

        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'append':
                self.messages.append(node.args[0].value)
            self.generic_visit(node)

    selected = Select()
    selected.visit(tree)
    require(selected.messages == ['FIRST', 'SECOND'])

    class Remove(ast.NodeTransformer):
        def visit_Expr(self, node):
            if isinstance(node.value, ast.Call) and node.value.args[0].value == 'FIRST':
                return ast.copy_location(ast.Pass(), node)
            return node

    transformed = Remove().visit(tree)
    require(isinstance(transformed.body[0], ast.Pass))
    ast.fix_missing_locations(transformed)
    rendered = ast.unparse(transformed)
    require('FIRST' not in rendered and 'SECOND' in rendered and 'value = 2' in rendered)
    require(shape(ast.parse(rendered)) == shape(transformed))
    partial = ast.Name(id='value')
    if hasattr(partial, 'ctx'):
        del partial.ctx
    require(list(ast.iter_fields(partial)) == [('id', 'value')])
    require(list(ast.iter_child_nodes(ast.Constant(value=1))) == [])


def test_unparser_grammar_boundaries():
    sources = (
        '', 'value = []', 'value = (1,)', 'value = {"a": 1}',
        'def f(a, /, b=1, *, c=True, **kw):\n    return (a + b) * 2\n',
        'async def f(values):\n    return [value async for value in values]\n',
        'value = f"count={1 + 2!r:>4}"', 'value = "é\\nquote\\\""',
        'try:\n    value()\nexcept* ValueError:\n    pass\n',
        'match value:\n    case {"a": [first, *rest]} if first:\n        result = rest\n',
    )
    require(len(sources) == len(set(sources)))
    visited = set()
    for source in sources:
        tree = ast.parse(source)
        require(shape(ast.parse(ast.unparse(tree))) == shape(tree), 'declared grammar roundtrip changed')
        visited.add(source)
    require(visited == set(sources))
    require(ast.unparse(ast.parse('1 + 2', mode='eval')) == '1 + 2')
    expect_raises(ValueError, lambda: ast.unparse(ast.Name(id='value', ctx=ast.Load())), 'unsupported root passed')

    class FutureStatement(ast.stmt):
        _fields = ()

    future = ast.Module(body=[FutureStatement()], type_ignores=[])
    error = expect_raises(ValueError, lambda: ast.unparse(future), 'unknown syntax was silently emitted')
    require('FutureStatement' in str(error))
    generic = ast.parse('def f():\n    pass')
    generic.body[0].type_params = ['future parameter']
    error = expect_raises(ValueError, lambda: ast.unparse(generic), 'unsupported type parameters were silently omitted')
    require('type parameters' in str(error))


def test_current_mutation_selector_and_fingerprint():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'conformance'))
    from _mutation_sites import DisableSite

    source = ('errors.append("FIRST")\nother.append("UNRELATED")\n'
              'saved = errors.append("ASSIGNMENT")\ndefects.append("SECOND")\n')
    probe = DisableSite(-1)
    probe.visit(ast.parse(source))
    require(probe.seen == 2 and probe.fingerprint == '')
    for index, expected in enumerate(('FIRST', 'SECOND')):
        selector = DisableSite(index)
        tree = selector.visit(ast.parse(source))
        ast.fix_missing_locations(tree)
        require(selector.seen == 2 and selector.fingerprint == expected)
        require(isinstance(tree.body[(0, 3)[index]], ast.Pass))
        regenerated = ast.unparse(tree)
        require('UNRELATED' in regenerated and 'ASSIGNMENT' in regenerated)
        require(shape(ast.parse(regenerated)) == shape(tree))
    unknown = DisableSite(2)
    tree = unknown.visit(ast.parse(source))
    require(unknown.seen == 2 and unknown.fingerprint == '' and shape(tree) == shape(ast.parse(source)))


if __name__ == '__main__':
    tests = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(tests)
    visited = set()
    for name, test in sorted(tests.items()):
        test()
        visited.add(name)
    require(visited == set(tests))
    print('owned AST controls: complete source/literal, diagnostic, visitor/mutation and supported/unsupported grammar cases executed')
