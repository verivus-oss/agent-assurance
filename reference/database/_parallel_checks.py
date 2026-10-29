"""One or two owned worker threads for private database acceptance checks."""

import threading
import time


class _WorkerOutcome:
    """Transfer a worker's result or failure to its joining caller."""

    def __init__(self):
        self.value = None
        self.failure = None
        self.finished = False

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, traceback):
        self.failure = error
        self.finished = True
        # The joining caller raises this same failure after all workers finish.
        return error is not None


def run_calls(operation, arguments, *, timeout, abort=None):
    """Return input-ordered results or fail the lane after joining its workers.

    A deadline failure never yields partial results. Workers are daemons so a
    stuck native driver cannot keep a failed validation process alive. Native
    calls cannot be cancelled by Python; the caller must abandon its private
    lane on failure. An abort callback releases peers waiting at a barrier.
    """
    if not callable(operation) or abort is not None and not callable(abort):
        raise TypeError("parallel checks require callable operations")
    if (type(arguments) is not tuple or not 1 <= len(arguments) <= 2
            or any(type(values) is not tuple for values in arguments)):
        raise TypeError("parallel checks require one or two argument tuples")
    if type(timeout) not in (int, float) or not 0 < timeout <= threading.TIMEOUT_MAX:
        raise ValueError("parallel checks require a positive supported deadline")
    outcomes = [_WorkerOutcome() for _ in arguments]

    def invoke(index, values):
        with outcomes[index] as outcome:
            outcome.value = operation(*values)

    deadline = time.monotonic() + timeout
    workers = [threading.Thread(target=invoke, args=(index, values), daemon=True)
               for index, values in enumerate(arguments)]
    started = []
    try:
        for worker in workers:
            started.append(worker)
            worker.start()
        for worker in started:
            worker.join(max(0, deadline - time.monotonic()))
        if any(worker.is_alive() for worker in started):
            raise TimeoutError("parallel database check exceeded its deadline")
        if not all(outcome.finished for outcome in outcomes):
            raise RuntimeError("parallel database check ended without an outcome")
        for outcome in outcomes:
            if outcome.failure is not None:
                raise outcome.failure
        return [outcome.value for outcome in outcomes]
    except BaseException:
        try:
            if abort is not None:
                abort()
        finally:
            for worker in started:
                if worker.ident is not None:
                    worker.join(max(0, deadline - time.monotonic()))
        raise
