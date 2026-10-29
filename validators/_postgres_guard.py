"""Cold import and matching boundary for the actual PostgreSQL lane."""

import sys
import threading


FORBIDDEN = frozenset({'re', 'regex', '_sre', 'pathlib', 'fnmatch', 'glob', 'urllib', 'dataclasses', 'json',
                       'uuid', 'platform', 'typing', 'subprocess', 'shutil', 'psycopg', 'psycopg_binary',
                       'psycopg_c', 'unittest', 'concurrent', 'logging'})
MODE = 'postgres-native-import-boundary-v1'


class BoundaryError(RuntimeError):
    pass


class Boundary:
    def __init__(self):
        if sys.implementation.name != 'cpython' or not sys.flags.no_site:
            raise BoundaryError('PostgreSQL guarded lane requires CPython with site disabled')
        if FORBIDDEN & set(sys.modules):
            raise BoundaryError('PostgreSQL guard found a preloaded forbidden module')
        self.attempted = set()
        self.patterns = set()
        self.active = False
        self.previous_main = sys.getprofile()
        self.previous_worker = threading.getprofile()

        def audit(event, arguments):
            if self.active and event == 'import' and arguments[0].split('.')[0] in FORBIDDEN:
                self.attempted.add(arguments[0])
                raise BoundaryError('PostgreSQL guard blocked a forbidden import')

        def profile(frame, event, value):
            if (self.active and event == 'c_call' and type(getattr(value, '__self__', None)).__name__ == 'Pattern'
                    and getattr(value, '__name__', '') in {'match', 'search', 'fullmatch', 'findall', 'finditer', 'split', 'sub', 'subn'}):
                self.patterns.add(value.__name__)
                raise BoundaryError('PostgreSQL guard blocked a pattern matching attempt')
            if self.previous_main is not None or self.previous_worker is not None:
                previous = self.previous_main if threading.current_thread() is threading.main_thread() else self.previous_worker
                if previous is not None:
                    previous(frame, event, value)

        self.audit = audit
        self.profile = profile

    def __enter__(self):
        self.active = True
        try:
            sys.addaudithook(self.audit)
            sys.setprofile(self.profile)
            threading.setprofile(self.profile)
            if sys.getprofile() is not self.profile or threading.getprofile() is not self.profile:
                raise BoundaryError('PostgreSQL guard profile installation failed')
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def proof(self):
        if (not self.active or self.attempted or self.patterns or FORBIDDEN & set(sys.modules)
                or sys.getprofile() is not self.profile or threading.getprofile() is not self.profile):
            raise BoundaryError('PostgreSQL guarded lane suppressed a boundary violation or lost its guard')
        return {'mode': MODE, 'status': 'passed', 'implementation': 'cpython', 'site_disabled': True,
                'forbidden_roots': sorted(FORBIDDEN), 'import_attempts': [], 'pattern_attempts': [],
                'profiles': 'main-and-new-worker-threads'}

    def __exit__(self, *_error):
        self.active = False
        sys.setprofile(self.previous_main)
        threading.setprofile(self.previous_worker)
        return False


def expected_proof():
    return {'mode': MODE, 'status': 'passed', 'implementation': 'cpython', 'site_disabled': True,
            'forbidden_roots': sorted(FORBIDDEN), 'import_attempts': [], 'pattern_attempts': [],
            'profiles': 'main-and-new-worker-threads'}


def guarded_lane(operation):
    with Boundary() as boundary:
        receipt = operation()
        receipt['execution_guard'] = boundary.proof()
        return receipt
