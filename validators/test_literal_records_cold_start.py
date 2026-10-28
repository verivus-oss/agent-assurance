"""Run every declared record component control without matcher imports."""

import sys


if __name__ == "__main__":
    if sys.implementation.name != "cpython" or not sys.flags.no_site:
        raise RuntimeError("record cold controls require CPython with -S")
    observed = set()
    attempted_imports = set()

    def audit(event, arguments):
        if event == "import" and arguments[0].split(".")[0] in ("re", "regex", "_sre", "dataclasses"):
            attempted_imports.add(arguments[0])
            raise RuntimeError("record component attempted a retired dependency import: " + arguments[0])

    def profile(frame, event, argument):
        if event == "c_call" and type(getattr(argument, "__self__", None)).__name__ == "Pattern":
            if getattr(argument, "__name__", "") in ("match", "search", "fullmatch", "findall", "finditer", "split", "sub", "subn"):
                observed.add((frame.f_code.co_name, argument.__name__))

    sys.addaudithook(audit)
    sys.setprofile(profile)
    import os
    from _test_require import require

    directory = os.path.dirname(os.path.abspath(__file__))
    names = {name[:-3] for name in os.listdir(directory)
             if name.startswith("test_literal_records") and name.endswith(".py")
             and name != os.path.basename(__file__)}
    require("test_literal_records" in names)
    executed = set()
    for name in sorted(names):
        module = __import__(name)
        tests = {symbol for symbol in vars(module) if symbol.startswith("test_") and callable(vars(module)[symbol])}
        require(tests, "record component module had no controls: " + name)
        visited = set()
        for symbol in sorted(tests):
            getattr(module, symbol)()
            visited.add(symbol)
        require(visited == tests, "record component controls did not execute completely")
        executed.add(name)
    sys.setprofile(None)
    require(executed == names, "record component population did not execute completely")
    require(not attempted_imports, "record component suppressed forbidden import attempts: " + repr(sorted(attempted_imports)))
    require(not observed, "record component called Python matchers: " + repr(sorted(observed)))
    require(not ({"re", "regex", "_sre", "dataclasses"} & set(sys.modules)), "record component imported retired dependency machinery")
    print("record cold control: complete component population executed without regex or dataclasses imports or Python matcher calls")
    print("scope: record carriers and controls; other reference-store imports and external dependencies were not instrumented")
