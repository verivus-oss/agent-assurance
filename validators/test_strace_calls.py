"""Accepted and rejected syscall trace records."""
from _test_require import require
from _strace_calls import parsed_calls

def test_selected_calls() -> None:
    trace = 'execve("/usr/bin/python3", ["python3"], 0x0) = 0\n[pid  123] openat(AT_FDCWD, "safe.toml", O_RDONLY) = 3\n456 connect(3, 0x0, 16) = -1\n+++ exited with 0 +++\n"execve(inside argument)"\n'
    calls = parsed_calls(trace)
    require([name for name, _ in calls] == ['execve', 'openat', 'connect'])
    require('safe.toml' in calls[1][1])

def test_malformed_prefix_is_not_a_call() -> None:
    require(parsed_calls('[pid nope] open(1)\n<... open resumed>\n') == [])
if __name__ == '__main__':
    test_selected_calls()
    test_malformed_prefix_is_not_a_call()
    print('syscall trace parser: 2 test groups passed')
