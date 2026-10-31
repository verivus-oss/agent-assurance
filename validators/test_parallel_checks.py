"""Exercise actual worker overlap, ordered outcomes and fatal worker failures."""

import sys
import threading

from _literal_path import Path
from _temporary_attribute import temporary_attribute
from _test_require import expect_raises, require

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reference/database'))
import _parallel_checks as parallel  # noqa: E402


def test_workers_overlap_and_retain_input_order():
    barrier = threading.Barrier(2)
    identities = set()
    lock = threading.Lock()

    def operation(value):
        with lock:
            identities.add(threading.get_ident())
        barrier.wait(timeout=2)
        return value

    require(parallel.run_calls(operation, (('first',), ('second',)), timeout=3, abort=barrier.abort)
            == ['first', 'second'], 'parallel results lost input order')
    require(len(identities) == 2 and threading.get_ident() not in identities,
            'parallel checks did not execute both workers concurrently')
    require(parallel.run_calls(lambda: None, ((),), timeout=2) == [None])


def test_worker_exceptions_are_raised_and_workers_finish():
    class WorkerAbort(BaseException):
        pass

    for failure in (ValueError('worker failed'), KeyboardInterrupt('worker interrupted'),
                    SystemExit('worker exited'), GeneratorExit('worker closed'), WorkerAbort('worker aborted')):
        done = threading.Event()
        aborted = []

        def operation(value):
            if value == 'fail':
                raise failure
            done.set()
            return 'peer completed'

        actual = expect_raises(type(failure),
                               lambda: parallel.run_calls(operation, (('fail',), ('peer',)),
                                                          timeout=2, abort=lambda: aborted.append(True)),
                               'worker failure yielded a successful result')
        require(actual is failure and done.is_set() and aborted == [True],
                'parallel checks lost the failure, peer completion or abort notification')


def test_start_failure_releases_and_joins_started_peer():
    barrier = threading.Barrier(2)
    workers, ended = [], threading.Event()
    original = threading.Thread
    failure = OSError('injected thread start failure')

    class RefuseStart:
        ident = None

        def start(self):
            raise failure

    def factory(*arguments, **options):
        if workers:
            return RefuseStart()
        worker = original(*arguments, **options)
        workers.append(worker)
        return worker

    def operation():
        try:
            barrier.wait(timeout=2)
        finally:
            ended.set()

    with temporary_attribute(parallel.threading, 'Thread', factory):
        actual = expect_raises(OSError,
                               lambda: parallel.run_calls(operation, ((), ()), timeout=3, abort=barrier.abort),
                               'thread startup failure yielded a result')
    require(actual is failure and len(workers) == 1 and ended.is_set() and not workers[0].is_alive(),
            'thread startup failure lost its cause or leaked the started peer')


def test_failure_after_thread_launch_still_joins_every_peer():
    barrier = threading.Barrier(2)
    workers, joined = [], set()
    original = threading.Thread
    failure = OSError('injected failure after thread launch')

    class Worker(original):
        def start(self):
            super().start()
            if self is workers[-1]:
                raise failure

        def join(self, timeout=None):
            super().join(timeout)
            joined.add(self)

    def factory(*arguments, **options):
        worker = Worker(*arguments, **options)
        workers.append(worker)
        return worker

    with temporary_attribute(parallel.threading, 'Thread', factory):
        actual = expect_raises(OSError,
                               lambda: parallel.run_calls(lambda: barrier.wait(timeout=2), ((), ()),
                                                          timeout=3, abort=barrier.abort),
                               'failure after native thread launch produced a result')
    require(actual is failure and len(workers) == 2 and joined == set(workers)
            and all(not worker.is_alive() for worker in workers), 'launched worker escaped failure cleanup')


def test_timeout_refuses_partial_results_and_notifies_abort():
    started, release, ended = threading.Event(), threading.Event(), threading.Event()
    workers, aborted = [], []
    original = threading.Thread

    def factory(*arguments, **options):
        worker = original(*arguments, **options)
        workers.append(worker)
        return worker

    def operation():
        started.set()
        try:
            release.wait(timeout=3)
            return 'too late'
        finally:
            ended.set()

    def abort():
        aborted.append(True)
        release.set()

    try:
        with temporary_attribute(parallel.threading, 'Thread', factory):
            error = expect_raises(TimeoutError,
                                  lambda: parallel.run_calls(operation, ((),), timeout=0.02, abort=abort),
                                  'expired worker produced partial results')
        require(str(error) == 'parallel database check exceeded its deadline' and aborted == [True])
    finally:
        release.set()
        for worker in workers:
            worker.join(timeout=3)
    require(len(workers) == 1 and workers[0].daemon and not workers[0].is_alive()
            and started.is_set() and ended.is_set(), 'timeout control did not release its actual worker')


def test_invalid_worker_contracts_fail_before_execution():
    invoked = []

    def operation(*values):
        invoked.append(values)

    for arguments in (None, [], (), ((), (), ()), ('value',), ([],)):
        expect_raises(TypeError, lambda: parallel.run_calls(operation, arguments, timeout=1),
                      'unsupported worker arguments passed')
    for timeout in (None, False, True, 0, -1, float('inf'), float('nan'), threading.TIMEOUT_MAX * 2, '1'):
        expect_raises(ValueError, lambda: parallel.run_calls(operation, ((),), timeout=timeout),
                      'invalid worker deadline passed')
    expect_raises(TypeError, lambda: parallel.run_calls(None, ((),), timeout=1), 'noncallable worker passed')
    expect_raises(TypeError, lambda: parallel.run_calls(operation, ((),), timeout=1, abort=False),
                  'noncallable abort callback passed')
    require(not invoked, 'invalid worker contract executed an operation')


if __name__ == '__main__':
    controls = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(controls)
    executed = set()
    for name, control in sorted(controls.items()):
        control()
        executed.add(name)
    require(executed == set(controls))
    print('parallel checks: actual overlap, ordered results, worker/start failure, timeout and argument refusal; skipped=[]')
