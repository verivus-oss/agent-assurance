"""Run the complete JSON component controls from a fresh CPython process."""

import sys


if __name__ == "__main__":
    if sys.implementation.name != "cpython" or not sys.flags.no_site:
        raise RuntimeError("JSON cold controls require CPython with -S")
    observed = set()

    def audit(event, arguments):
        if event == "import" and arguments[0].split(".")[0] in ("re", "regex", "_sre", "json"):
            raise RuntimeError("JSON component attempted a retired matcher import: " + arguments[0])

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
             if name.startswith("test_literal_json") and name.endswith(".py")
             and name != os.path.basename(__file__)}
    require("test_literal_json" in names)
    executed = set()
    for name in sorted(names):
        module = __import__(name)
        tests = {symbol for symbol in vars(module) if symbol.startswith("test_") and callable(vars(module)[symbol])}
        require(tests, "JSON component module had no controls: " + name)
        visited = set()
        for symbol in sorted(tests):
            getattr(module, symbol)()
            visited.add(symbol)
        require(visited == tests, "JSON component controls did not execute completely")
        executed.add(name)
    sys.setprofile(None)
    require(executed == names, "JSON component population did not execute completely")
    require(not observed, "JSON component called Python matchers: " + repr(sorted(observed)))
    require(not ({"re", "regex", "_sre", "json"} & set(sys.modules)), "JSON component imported retired matcher machinery")
    print("JSON cold control: complete declared component population executed without Python regex or standard JSON imports or matcher calls")
    print("scope: component imports and controls; native C internals, external hooks and other product entry points were not instrumented")
