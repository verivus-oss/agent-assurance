"""The reference PostgreSQL interface and its native session contract."""

from _postgres_client import (DatabaseError, DivisionByZero, NativeConnection, OperationalError,
                              ParameterEncodingError, PROTOCOL, ProgrammingError, TransactionStatus, connect, identifier)

__all__ = ['DatabaseError', 'DivisionByZero', 'NativeConnection', 'OperationalError', 'ParameterEncodingError', 'PROTOCOL',
           'ProgrammingError', 'TransactionStatus', 'connect', 'identifier', 'native_connection']


def native_connection(connection):
    # Failure-injection wrappers delegate this marker to their owned session.
    if getattr(connection, 'reference_protocol', None) != PROTOCOL:
        raise TypeError('PostgreSQL reference store requires its owned native session')
    return connection
