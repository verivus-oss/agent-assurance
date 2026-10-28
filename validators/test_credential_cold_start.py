"""Run the credential controls from a fresh CPython process without site hooks."""

import sys


if __name__ == "__main__":
    if sys.implementation.name != "cpython" or not sys.flags.no_site:
        raise RuntimeError("credential cold control requires CPython with -S")
    observed = set()
    attempted_imports = set()

    def audit(event, arguments):
        if event == "import" and arguments[0].split(".")[0] in ("re", "regex", "_sre"):
            attempted_imports.add(arguments[0])
            raise RuntimeError("credential component attempted a retired matcher import: " + arguments[0])

    def profile(frame, event, argument):
        if event == "c_call" and type(getattr(argument, "__self__", None)).__name__ == "Pattern":
            if getattr(argument, "__name__", "") in ("match", "search", "fullmatch", "findall", "finditer", "split", "sub", "subn"):
                observed.add((frame.f_code.co_filename, frame.f_code.co_name, argument.__name__))

    sys.addaudithook(audit)
    sys.setprofile(profile)
    import os
    from _test_require import require
    from _credential_report import encode_report

    directory = os.path.dirname(os.path.abspath(__file__))
    names = {name[:-3] for name in os.listdir(directory)
             if name.startswith("test_credential_") and name.endswith(".py")
             and name != os.path.basename(__file__)}
    names.add("test_secret_scan_filter")
    require({"test_credential_detection", "test_credential_history", "test_secret_scan_filter"} <= names)
    executed = set()
    for name in sorted(names):
        module = __import__(name)
        tests = [symbol for symbol in vars(module) if symbol.startswith("test_") and callable(vars(module)[symbol])]
        require(tests, "credential control module had no executed tests: " + name)
        for symbol in sorted(tests):
            getattr(module, symbol)()
        executed.add(name)
    sys.setprofile(None)
    require(executed == names, "credential control population did not execute completely")
    require(not attempted_imports, "credential component suppressed forbidden import attempts: " + repr(sorted(attempted_imports)))
    require(not observed, "credential path called Python matchers: " + encode_report([list(item) for item in sorted(observed)]))
    require(not ({"re", "regex", "_sre"} & set(sys.modules)), "credential path imported regex machinery")
    print("credential cold control: all selected component, policy and Git fixture controls executed without Python regex imports or matcher calls")
    print("scope: fresh Python imports and fixture execution; native Git internals and other product entry points were not instrumented")
