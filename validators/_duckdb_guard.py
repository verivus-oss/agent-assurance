"""Cold import boundary for the maintained native DuckDB reference binding."""

from _postgres_guard import FORBIDDEN as COMMON_FORBIDDEN
from _postgres_guard import Boundary as CommonBoundary, BoundaryError
from _postgres_guard import expected_proof as common_proof, guarded_lane as common_lane


FORBIDDEN = COMMON_FORBIDDEN | frozenset({'duckdb', 'pytz', 'pandas', 'numpy'})
MODE = 'duckdb-native-import-boundary-v1'


class Boundary(CommonBoundary):
    def __init__(self):
        super().__init__(forbidden=FORBIDDEN, mode=MODE)


def expected_proof():
    return common_proof(forbidden=FORBIDDEN, mode=MODE)


def guarded_lane(operation):
    return common_lane(operation, forbidden=FORBIDDEN, mode=MODE)


__all__ = ['Boundary', 'BoundaryError', 'FORBIDDEN', 'MODE', 'expected_proof', 'guarded_lane']
