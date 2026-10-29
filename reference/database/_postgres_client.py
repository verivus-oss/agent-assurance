"""Buffered reference-store operations through the owned native session."""

from datetime import date, datetime
from _decimal import Decimal
import hashlib
import os
import stat
import threading

from _path_scan import Path
from _json_decode import dumps, loads
from _owned_session import Session, SessionError


PROTOCOL = 'dagtoml-postgres-v1'


class DatabaseError(RuntimeError):
    def __init__(self, message, *, sqlstate=None):
        self.sqlstate = sqlstate
        super().__init__(message)


class OperationalError(DatabaseError):
    pass


class DivisionByZero(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    pass


class ParameterEncodingError(DatabaseError):
    """A text parameter was refused before PostgreSQL execution."""


class TransactionStatus:
    IDLE = 'I'
    INTRANS = 'T'
    INERROR = 'E'


def source_identity(root):
    """Frame the complete regular source population used by the native build."""
    if not stat.S_ISDIR(os.stat(root, follow_symlinks=False).st_mode):
        raise OperationalError('PostgreSQL driver source root is not a regular directory')
    def unreadable(_error):
        raise OperationalError('PostgreSQL driver source population is unreadable')
    files = {}
    for directory, directories, names in os.walk(root, followlinks=False, onerror=unreadable):
        if any(os.path.islink(os.path.join(directory, name)) for name in directories):
            raise OperationalError('PostgreSQL driver source has linked directories')
        for name in names:
            path = os.path.join(directory, name)
            before = os.stat(path, follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode):
                raise OperationalError('PostgreSQL driver source has a nonregular entry')
            with open(path, 'rb') as stream:
                data = stream.read()
                after = os.fstat(stream.fileno())
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise OperationalError('PostgreSQL driver source changed during capture')
            files[os.path.relpath(path, root).replace(os.sep, '/')] = data
    if not files:
        raise OperationalError('PostgreSQL driver source population is absent')
    digest = hashlib.sha256(b'dagtoml-postgres-source-v1\0')
    for name, data in sorted(files.items()):
        for value in (name.encode('utf-8'), data):
            digest.update(len(value).to_bytes(8, 'big'))
            digest.update(value)
    return digest.hexdigest(), {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}


def identifier(value):
    if type(value) is not str or '\0' in value:
        raise TypeError('PostgreSQL identifier must be NUL-free text')
    return '"' + value.replace('"', '""') + '"'


def parameter(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = str.__str__(value)
        if '\0' in value:
            raise ParameterEncodingError('PostgreSQL text parameters cannot contain NUL bytes')
        return value
    if type(value) is bool:
        return 'true' if value else 'false'
    if type(value) in (int, float, Decimal):
        return str(value)
    if type(value) is bytes:
        return '\\x' + value.hex()
    if type(value) in (date, datetime):
        return value.isoformat()
    if type(value) in (tuple, list):
        parts = []
        for item in value:
            if type(item) in (tuple, list):
                parts.append(parameter(item))
            elif item is None:
                parts.append('NULL')
            else:
                text = parameter(item)
                parts.append('"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"')
        return '{' + ','.join(parts) + '}'
    raise TypeError('unsupported PostgreSQL reference parameter type')


def array_value(text, scalar):
    position = 0

    def parse():
        nonlocal position
        if position >= len(text) or text[position] != '{':
            raise ProgrammingError('unsupported PostgreSQL array framing')
        position += 1
        values = []
        if position < len(text) and text[position] == '}':
            position += 1
            return values
        while position < len(text):
            if text[position] == '{':
                values.append(parse())
            else:
                quoted = text[position] == '"'
                if quoted:
                    position += 1
                value = []
                ended = not quoted
                while position < len(text):
                    character = text[position]
                    if character == '\\':
                        position += 1
                        if position >= len(text):
                            raise ProgrammingError('truncated PostgreSQL array escape')
                        value.append(text[position])
                        position += 1
                    elif quoted and character == '"':
                        position += 1
                        ended = True
                        break
                    elif not quoted and character in ',}':
                        break
                    else:
                        value.append(character)
                        position += 1
                if not ended:
                    raise ProgrammingError('unterminated PostgreSQL array value')
                item = ''.join(value)
                values.append(None if not quoted and item == 'NULL' else scalar(item))
            if position >= len(text):
                break
            character = text[position]
            position += 1
            if character == '}':
                return values
            if character != ',':
                raise ProgrammingError('invalid PostgreSQL array delimiter')
        raise ProgrammingError('unterminated PostgreSQL array')

    result = parse()
    if position != len(text):
        raise ProgrammingError('trailing PostgreSQL array bytes')
    return result


def bytea_value(text):
    if text.startswith('\\x'):
        try:
            return bytes.fromhex(text[2:])
        except ValueError as exc:
            raise ProgrammingError('invalid PostgreSQL binary hex text') from exc
    data = bytearray()
    position = 0
    while position < len(text):
        character = text[position]
        position += 1
        if character == '\\':
            if text[position:position + 1] == '\\':
                position += 1
                data.append(92)
            else:
                octal = text[position:position + 3]
                if len(octal) != 3 or any(value not in '01234567' for value in octal):
                    raise ProgrammingError('invalid PostgreSQL binary escape text')
                number = int(octal, 8)
                if number > 255:
                    raise ProgrammingError('PostgreSQL binary escape exceeds one byte')
                data.append(number)
                position += 3
        elif ord(character) <= 127:
            data.append(ord(character))
        else:
            raise ProgrammingError('unsupported PostgreSQL binary escape character')
    return bytes(data)


def result_value(oid, text):
    if text is None:
        return None
    if type(text) is not str:
        raise ProgrammingError('PostgreSQL native result is not text')
    if oid == 16:
        if text not in ('t', 'f'):
            raise ProgrammingError('invalid PostgreSQL boolean text')
        return text == 't'
    if oid in (20, 21, 23, 26, 28, 29):
        return int(text)
    if oid in (700, 701):
        return float(text)
    if oid == 1700:
        return Decimal(text)
    if oid in (114, 3802):
        return loads(text)
    if oid == 17:
        return bytea_value(text)
    if oid == 1082:
        return date.fromisoformat(text)
    if oid in (1114, 1184):
        return datetime.fromisoformat(text)
    arrays = {1000: 16, 1001: 17, 1005: 21, 1007: 23, 1009: 25, 1015: 1043, 1016: 20,
              1021: 700, 1022: 701, 1182: 1082, 1115: 1114, 1185: 1184, 1231: 1700, 199: 114, 3807: 3802}
    if oid in arrays:
        return array_value(text, lambda value: result_value(arrays[oid], value))
    return text


class _Rows:
    def __init__(self, response):
        self._rows = [tuple(result_value(oid, item) for oid, item in zip(response['types'], row, strict=True))
                      for row in response['rows']]
        self._has_rows = response['has_rows']
        self._position = 0

    def fetchone(self):
        if not self._has_rows:
            raise ProgrammingError('PostgreSQL command did not return rows')
        if self._position == len(self._rows):
            return None
        row = self._rows[self._position]
        self._position += 1
        return row

    def fetchall(self):
        if not self._has_rows:
            raise ProgrammingError('PostgreSQL command did not return rows')
        rows = self._rows[self._position:]
        self._position = len(self._rows)
        return rows


def dependency_inventory(records):
    if type(records) is not list or not records:
        raise OperationalError('PostgreSQL native prepared dependency inventory is absent')
    files = {}
    for item in records:
        if type(item) is not dict or set(item) != {'path', 'sha256'}:
            raise OperationalError('PostgreSQL native prepared dependency record is malformed')
        name, digest = item['path'], item['sha256']
        if (type(name) is not str or not name or '\\' in name or name.startswith('/')
                or any(part in ('', '.', '..') for part in name.split('/'))
                or any(ord(character) < 32 or ord(character) == 127 for character in name)
                or name in files or type(digest) is not str or len(digest) != 64
                or any(character not in '0123456789abcdef' for character in digest)):
            raise OperationalError('PostgreSQL native prepared dependency identity is malformed or repeated')
        files[name] = digest
    result = hashlib.sha256(b'dagtoml-postgres-dependencies-v1\0')
    for name, digest in sorted(files.items()):
        for value in (name.encode('utf-8'), digest.encode('ascii')):
            result.update(len(value).to_bytes(8, 'big'))
            result.update(value)
    return result.hexdigest()


def build_identity(root):
    root = Path(root).resolve()
    source_sha256, files = source_identity(root / 'tools/dagtoml-postgres-go')
    relative = '.local/database-ci/postgres-driver/dagtoml-postgres-go'
    binary = root / relative
    if binary.is_symlink() or not binary.is_file() or (root / (relative + '.build.json')).is_symlink():
        raise OperationalError('PostgreSQL native driver requires regular retained build artifacts')
    record = loads((root / (relative + '.build.json')).read_bytes())
    packages = record['compiled_packages']
    if type(packages) is not dict or not packages or any(type(name) is not str or value is not True
                                                       for name, value in packages.items()):
        raise OperationalError('PostgreSQL native driver compiled package population is malformed')
    graph_digest = hashlib.sha256(b'dagtoml-postgres-graph-v1\0')
    for name in sorted(packages):
        encoded = name.encode('utf-8')
        graph_digest.update(len(encoded).to_bytes(8, 'big'))
        graph_digest.update(encoded)
    if (record['source_sha256'] != source_sha256 or record['go_version'] != 'go1.26.10'
            or {item['path']: item['sha256'] for item in record['sources']} != files
            or record['dependencies_sha256'] != dependency_inventory(record['prepared_dependencies'])
            or len(record['sources']) != len(files) or record['compiled_graph_sha256'] != graph_digest.hexdigest()
            or any(name == 'regexp' or name.startswith('regexp/') for name in record['compiled_packages'])):
        raise OperationalError('PostgreSQL native driver build identity is stale or incomplete')
    binary_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()
    if binary_sha256 != record['binary_sha256']:
        raise OperationalError('PostgreSQL native driver binary differs from its build identity')
    return {'protocol': PROTOCOL, 'go_version': record['go_version'], 'source_sha256': source_sha256,
            'binary_sha256': binary_sha256, 'dependencies_sha256': record['dependencies_sha256'],
            'compiled_graph_sha256': graph_digest.hexdigest(),
            'binary': relative}


class NativeConnection:
    reference_protocol = PROTOCOL

    def __init__(self, destination, *, dbname=None):
        self._session = None
        self._sequence = 0
        self._closed = True
        self.transaction_status = ''
        self.lock = threading.RLock()
        root = Path(__file__).resolve().parents[2]
        self._source_root = root / 'tools/dagtoml-postgres-go'
        self._driver_identity = build_identity(root)
        self.source_sha256 = self._driver_identity['source_sha256']
        self.binary_sha256 = self._driver_identity['binary_sha256']
        self.dependencies_sha256 = self._driver_identity['dependencies_sha256']
        self._binary = str(root / self._driver_identity['binary'])
        metadata = os.stat(self._binary)
        self._binary_identity = (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns)
        try:
            self._session = Session([self._binary])
            welcome = loads(self._session.frame())
            if (type(welcome) is not dict or welcome.get('protocol') != PROTOCOL
                    or type(welcome.get('request_id')) is not int or welcome['request_id'] != 0
                    or welcome.get('success') is not True
                    or welcome.get('source_sha256') != self.source_sha256
                    or welcome.get('dependencies_sha256') != self.dependencies_sha256
                    or welcome.get('compiled_graph_sha256') != self._driver_identity['compiled_graph_sha256']
                    or welcome.get('go_version') != 'go1.26.10'):
                raise OperationalError('PostgreSQL native driver handshake differs from its build identity')
            self._request({'operation': 'connect', 'destination': destination, 'database': dbname})
        except BaseException:
            if self._session is not None:
                self._session.close()
            raise

    @property
    def closed(self):
        return self._closed

    @property
    def driver_identity(self):
        return dict(self._driver_identity)

    @property
    def info(self):
        return self

    @property
    def autocommit(self):
        return True

    @autocommit.setter
    def autocommit(self, value):
        if value is not True:
            raise ProgrammingError('native PostgreSQL reference sessions use explicit transactions')

    def _request(self, request):
        try:
            if source_identity(self._source_root)[0] != self.source_sha256:
                raise OperationalError('PostgreSQL native driver source moved during its session')
            metadata = os.stat(self._binary)
            if (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns) != self._binary_identity:
                raise OperationalError('PostgreSQL native driver binary moved during its session')
        except (OSError, OperationalError):
            self._closed = True
            self._session.close()
            raise
        self._sequence += 1
        request['request_id'] = self._sequence
        try:
            response = loads(self._session.frame(dumps(request).encode('utf-8')))
        except (SessionError, OSError, ValueError) as exc:
            self._closed = True
            raise OperationalError('PostgreSQL native session could not complete its protocol') from exc
        if (type(response) is not dict or response.get('protocol') != PROTOCOL
                or type(response.get('request_id')) is not int or response.get('request_id') != self._sequence
                or type(response.get('success')) is not bool or type(response.get('closed')) is not bool
                or response.get('transaction') not in ('', 'I', 'T', 'E')
                or type(response.get('has_rows')) is not bool or type(response.get('rows')) is not list
                or type(response.get('types')) is not list
                or any(type(oid) is not int or not 0 < oid <= 4294967295 for oid in response['types'])
                or not response['closed'] and response['transaction'] == ''
                or not response['has_rows'] and bool(response['rows'])
                or response.get('sqlstate') is not None and (type(response['sqlstate']) is not str
                    or len(response['sqlstate']) != 5 or any(character not in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                                           for character in response['sqlstate']))
                or 'message' in response and type(response['message']) is not str
                or any(type(row) is not list or len(row) != len(response['types'])
                       or any(item is not None and type(item) is not str for item in row) for row in response['rows'])):
            self._session.close()
            self._closed = True
            raise OperationalError('PostgreSQL native reply has an invalid shape or identity')
        self._closed = response['closed']
        self.transaction_status = response['transaction']
        if not response['success']:
            state = response.get('sqlstate')
            error = OperationalError if self._closed else DivisionByZero if state == '22012' else DatabaseError
            raise error(response.get('message', 'PostgreSQL operation failed'), sqlstate=state)
        return response

    def execute(self, sql, parameters=()):
        if parameters is None:
            parameters = ()
        if type(sql) is not str or '\0' in sql or type(parameters) not in (tuple, list):
            raise TypeError('native PostgreSQL execution requires NUL-free SQL and a parameter sequence')
        with self.lock:
            return _Rows(self._request({'operation': 'execute', 'sql': sql,
                                        'parameters': [parameter(value) for value in parameters or ()]}))

    def close(self):
        with self.lock:
            try:
                if self._session is not None and not self._closed:
                    self._request({'operation': 'close'})
            finally:
                self._closed = True
                if self._session is not None:
                    self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_error):
        self.close()
        return False


def connect(destination, *, dbname=None):
    if not isinstance(destination, str) or dbname is not None and not isinstance(dbname, str):
        raise TypeError('PostgreSQL connection parameters must be text')
    destination = str.__str__(destination)
    dbname = None if dbname is None else str.__str__(dbname)
    if '\0' in destination or dbname is not None and '\0' in dbname:
        raise ValueError('PostgreSQL connection parameters must not contain NUL bytes')
    return NativeConnection(destination, dbname=dbname)
