"""Run every owned path component control without matcher imports."""

import sys


if __name__ == '__main__':
    if sys.implementation.name != 'cpython' or not sys.flags.no_site:
        raise RuntimeError('path cold controls require CPython with -S')
    retired = {'re', 'regex', '_sre', 'pathlib', 'fnmatch', 'glob', 'urllib'}
    observed = set()

    def audit(event, arguments):
        if event == 'import' and arguments[0].split('.')[0] in retired:
            raise RuntimeError('owned path component attempted a retired import: ' + arguments[0])

    def profile(frame, event, argument):
        if event == 'c_call' and type(getattr(argument, '__self__', None)).__name__ == 'Pattern':
            if getattr(argument, '__name__', '') in ('match', 'search', 'fullmatch', 'findall', 'finditer', 'split', 'sub', 'subn'):
                observed.add((frame.f_code.co_name, argument.__name__))

    sys.addaudithook(audit)
    sys.setprofile(profile)
    import os
    from _test_require import require

    directory = os.path.dirname(os.path.abspath(__file__))
    names = {name[:-3] for name in os.listdir(directory) if name.startswith('test_path_primitives')
             and name.endswith('.py') and name != os.path.basename(__file__)}
    require('test_path_primitives' in names)
    executed = set()
    for name in sorted(names):
        module = __import__(name)
        tests = {symbol for symbol, value in vars(module).items() if symbol.startswith('test_') and callable(value)}
        require(tests, 'path component controls are absent: ' + name)
        visited = set()
        for symbol in sorted(tests):
            getattr(module, symbol)()
            visited.add(symbol)
        require(visited == tests)
        executed.add(name)
    sys.setprofile(None)
    require(executed == names and not observed and not (retired & set(sys.modules)))
    print('path cold control: complete declared component population executed without retired imports or Python matcher calls')
    print('scope: owned lexical/native primitives and explicit discovery; native Windows execution, native OS internals and other dependencies were not instrumented')
    if os.name != 'posix' or os.geteuid() == 0:
        print('skipped: owner permission denial requires a non-root POSIX process')
