"""Artifact-bound access to the maintained native reference binding."""

from _decimal import Decimal
from datetime import date, datetime, time, timedelta
import hashlib
import os
import stat
import sys
import threading

from _path_scan import Path
from _json_decode import loads


PROTOCOL = 'dagtoml-duckdb-native-v2'
VERSIONS = frozenset({'1.5.0', '1.5.3'})
_LOCK = threading.RLock()
_MODULE = None
_BOUND = None


class ArtifactError(RuntimeError):
    pass


def _sha(value):
    return type(value) is str and len(value) == 64 and all(character in '0123456789abcdef' for character in value)


def _path(value):
    return (type(value) is str and bool(value) and '\\' not in value and not value.startswith('/')
            and all(part not in ('', '.', '..') for part in value.split('/'))
            and not any(ord(character) < 32 or ord(character) == 127 for character in value))


def _roster(values):
    if not isinstance(values, list) or not values:
        raise ArtifactError('native DuckDB source population is absent')
    result = {}
    for value in values:
        if (type(value) is not dict or set(value) != {'path', 'sha256'} or not _path(value['path'])
                or not _sha(value['sha256']) or value['path'] in result):
            raise ArtifactError('native DuckDB file identity is invalid or repeated')
        result[value['path']] = value['sha256']
    return [{'path': name, 'sha256': digest} for name, digest in sorted(result.items())]


def _metadata(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _parents(root, relative):
    if not _path(relative):
        raise ArtifactError('native DuckDB retained path is invalid')
    current = root
    for part in relative.split('/')[:-1]:
        current = current / part
        if not stat.S_ISDIR(os.stat(current, follow_symlinks=False).st_mode):
            raise ArtifactError('native DuckDB retained path has a linked or non-directory parent')


def _recipe(root, relative='tools/dagtoml-duckdb-native-go'):
    _parents(root, relative)
    source = root / relative
    if not stat.S_ISDIR(os.stat(source, follow_symlinks=False).st_mode):
        raise ArtifactError('native DuckDB recipe root is not a regular directory')
    def unreadable(_error):
        raise ArtifactError('native DuckDB recipe population is unreadable')
    records = []
    for directory, directories, names in os.walk(source, followlinks=False, onerror=unreadable):
        if any(os.path.islink(os.path.join(directory, name)) for name in directories):
            raise ArtifactError('native DuckDB recipe has a linked directory')
        for name in names:
            path = os.path.join(directory, name)
            before = os.stat(path, follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode):
                raise ArtifactError('native DuckDB recipe has a nonregular file')
            with open(path, 'rb') as stream:
                data = stream.read()
                after = os.fstat(stream.fileno())
            if _metadata(before) != _metadata(after):
                raise ArtifactError('native DuckDB recipe moved during capture')
            records.append({'path': os.path.relpath(path, source).replace(os.sep, '/'),
                            'sha256': hashlib.sha256(data).hexdigest()})
    return _roster(records)


def inventory(domain, *populations):
    digest = hashlib.sha256(domain.encode('ascii') + b'\0')
    for population in populations:
        if not isinstance(population, list) or type(population) is not list:
            raise ArtifactError('native DuckDB identity population requires a plain list')
        digest.update(len(population).to_bytes(8, 'big'))
        for entry in population:
            for value in (entry['path'], entry['sha256']):
                encoded = value.encode('utf-8')
                digest.update(len(encoded).to_bytes(8, 'big'))
                digest.update(encoded)
    return digest.hexdigest()


def selected_version():
    value = os.environ.get('DAGTOML_DUCKDB_VERSION', '1.5.3')
    if type(value) is not str or value not in VERSIONS:
        raise ArtifactError('native DuckDB version is unsupported')
    return value


def _file(root, relative):
    _parents(root, relative)
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise ArtifactError('native DuckDB artifact requires a regular retained file')
    before = os.stat(path)
    data = path.read_bytes()
    if _metadata(before) != _metadata(os.stat(path)):
        raise ArtifactError('native DuckDB artifact moved during capture')
    return data


def build_identity(root, version=None):
    root = Path(root).resolve()
    version = selected_version() if version is None else version
    abi = sys.implementation.cache_tag
    if version not in VERSIONS or sys.implementation.name != 'cpython' or abi not in {'cpython-311', 'cpython-312', 'cpython-313'}:
        raise ArtifactError('native DuckDB version or Python ABI is unsupported')
    prefix = '.local/database-ci/duckdb-driver/' + version + '/' + abi
    try:
        record = loads(_file(root, prefix + '/binding-build.json'))
        if (type(record) is not dict or type(record.get('schema_version')) is not int or record['schema_version'] != 1
                or record.get('protocol') != PROTOCOL or record.get('version') != version
                or record.get('go_version') != 'go1.26.10' or record['python']['abi'] != abi
                or not _sha(record['compiler_sha256'])):
            raise ArtifactError('native DuckDB build declaration is invalid')
        own, prepared, pybind, python, core, native_sources = (_roster(record[name]) for name in
            ('owned_sources', 'prepared_sources', 'pybind_headers', 'python_headers', 'core_files', 'native_core_sources'))
        if own != _recipe(root):
            raise ArtifactError('native DuckDB recipe differs from its retained build')
        targets = [entry['path'] for entry in prepared
                   if entry['path'].startswith('src/duckdb_py/') and entry['path'].endswith('.cpp')]
        if not targets or record.get('compiled_sources') != targets:
            raise ArtifactError('native DuckDB compiled target population is incomplete')
        native_targets = sorted(['core/' + entry['path'] for entry in native_sources if entry['path'].endswith('.cpp')] +
                                [entry['path'] for entry in prepared if entry['path'].startswith(
                                    ('external/duckdb/extension/core_functions/', 'external/duckdb/extension/json/'))
                                 and entry['path'].endswith('.cpp')])
        if ({entry['path'] for entry in native_sources} != {'NOTICE', 'prepared.cpp', 'static_extensions.cpp'}
                or not any(path.startswith('external/duckdb/extension/core_functions/') for path in native_targets)
                or not any(path.startswith('external/duckdb/extension/json/') for path in native_targets)
                or record.get('native_core_targets') != native_targets):
            raise ArtifactError('native DuckDB core compiled source population is incomplete')
        if _recipe(root, prefix + '/core-sources') != native_sources:
            raise ArtifactError('native DuckDB core prepared source differs from its captured identity')
        compiler = [{'path': 'compiler', 'sha256': record['compiler_sha256']},
                    {'path': 'python-abi', 'sha256': hashlib.sha256(abi.encode('ascii')).hexdigest()}]
        marker = inventory('dagtoml-duckdb-binding-v2', own, prepared, pybind, python, core, native_sources, compiler)
        if marker != record.get('binding_identity'):
            raise ArtifactError('native DuckDB prepared input inventory differs from its binding identity')
        spec = loads((root / 'tools/dagtoml-duckdb-native-go/data/inputs.json').read_bytes())
        selected = spec['versions'][version]
        if (record.get('sdk_archive_sha256') != selected['sdk_sha256']
                or record.get('core_archive_sha256') != selected['core_sha256']
                or record.get('pybind_archive_sha256') != spec['pybind']['sha256']):
            raise ArtifactError('native DuckDB archive origins differ from the current declarations')
        binary = prefix + '/_duckdb.so'
        native_core = prefix + '/libduckdb.so'
        binary_sha = hashlib.sha256(_file(root, binary)).hexdigest()
        core_sha = hashlib.sha256(_file(root, native_core)).hexdigest()
        if (binary_sha != record.get('binary_sha256') or core_sha != record.get('core_sha256')
                or core != [{'path': 'libduckdb.so', 'sha256': core_sha}]):
            raise ArtifactError('native DuckDB executable or core differs from its retained identity')
        for item in prepared:
            name = item['path'].rsplit('/', 1)[-1]
            if name in {'LICENSE', 'NOTICE'} or name.startswith(('LICENSE.', 'NOTICE.')):
                notice = prefix + '/licenses/sdk/' + item['path']
                if hashlib.sha256(_file(root, notice)).hexdigest() != item['sha256']:
                    raise ArtifactError('native DuckDB supplier notice differs from its captured source')
        pybind_notice = next((item['sha256'] for item in pybind if item['path'] == 'LICENSE'), None)
        if not pybind_notice or hashlib.sha256(_file(root, prefix + '/licenses/pybind11/LICENSE')).hexdigest() != pybind_notice:
            raise ArtifactError('native DuckDB header supplier notice is missing or stale')
        return {'protocol': PROTOCOL, 'version': version, 'python_abi': abi,
                'binding_identity': marker, 'source_sha256': inventory('dagtoml-duckdb-recipe-v1', own),
                'prepared_core_sha256': inventory('dagtoml-duckdb-core-source-v1', native_sources),
                'binary_sha256': binary_sha, 'core_sha256': core_sha, 'binary': binary, 'core_binary': native_core}
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise ArtifactError('native DuckDB retained proof is malformed or unavailable') from exc


def _kernel_path(value):
    result = []
    position = 0
    while position < len(value):
        if value[position] == '\\' and len(value[position + 1:position + 4]) == 3 and all(
                digit in '01234567' for digit in value[position + 1:position + 4]):
            result.append(chr(int(value[position + 1:position + 4], 8)))
            position += 4
        else:
            result.append(value[position])
            position += 1
    return ''.join(result)


def _mapped(name):
    result = set()
    with open('/proc/self/maps', encoding='utf-8') as stream:
        for row in stream:
            fields = row.rstrip('\n').split(maxsplit=5)
            if len(fields) == 6:
                path = _kernel_path(fields[5])
                if path.rsplit('/', 1)[-1].removesuffix(' (deleted)') == name:
                    result.add(path)
    return result


def _module(root, proof):
    global _MODULE, _BOUND
    with _LOCK:
        if _MODULE is not None:
            if _BOUND != proof:
                raise ArtifactError('native DuckDB cannot switch a loaded version or artifact identity')
            return _MODULE
        expected = str(root / proof['core_binary'])
        if _mapped('libduckdb.so') - {expected}:
            raise ArtifactError('process already maps a different native DuckDB core')
        before = {name: _metadata(os.stat(root / proof[name])) for name in ('binary', 'core_binary')}
        directory = str((root / proof['binary']).parent)
        sys.path.insert(0, directory)
        try:
            import _duckdb as module
        finally:
            sys.path.remove(directory)
        if (Path(module.__file__).resolve() != (root / proof['binary']).resolve()
                or getattr(module, '__dagtoml_binding_identity__', None) != proof['binding_identity']
                or module.__version__ != proof['version']
                or any(_metadata(os.stat(root / proof[name])) != metadata for name, metadata in before.items())
                or _mapped('libduckdb.so') != {expected}
                or _mapped('_duckdb.so') != {str(root / proof['binary'])}):
            raise ArtifactError('loaded native DuckDB module or core differs from its retained identity')
        _MODULE, _BOUND = module, dict(proof)
        return module


def parameter(value):
    if value is None or type(value) in (bool, int, float, Decimal, date, datetime, time, timedelta):
        return value
    if isinstance(value, str):
        return str.__str__(value)
    if type(value) in (bytes, bytearray, memoryview):
        return bytes(value)
    if isinstance(value, (tuple, list)) and type(value) in (tuple, list):
        return [parameter(item) for item in value]
    if type(value) is dict:
        if any(not isinstance(key, str) for key in value):
            raise TypeError('native DuckDB reference structure keys must be text')
        return {str.__str__(key): parameter(item) for key, item in value.items()}
    raise TypeError('unsupported native DuckDB reference parameter type')


class _Rows:
    def __init__(self, rows):
        self.rows, self.position = rows, 0

    def fetchone(self):
        if self.position == len(self.rows):
            return None
        row = self.rows[self.position]
        self.position += 1
        return row

    def fetchall(self):
        rows = self.rows[self.position:]
        self.position = len(self.rows)
        return rows


class NativeConnection:
    reference_protocol = PROTOCOL

    def __init__(self, destination):
        self._root = Path(__file__).resolve().parents[2]
        self._proof = build_identity(self._root)
        self._module = _module(self._root, self._proof)
        prefix = self._proof['binary'].rsplit('/', 1)[0]
        paths = [self._proof[name] for name in ('binary', 'core_binary')]
        paths += [prefix + '/core-sources/' + name for name in ('NOTICE', 'prepared.cpp', 'static_extensions.cpp')]
        self._fingerprints = {path: _metadata(os.stat(self._root / path)) for path in paths}
        self._lock = threading.RLock()
        self._connection = self._module.connect(destination)
        self.closed = False

    @property
    def driver_identity(self):
        return dict(self._proof)

    def _current(self):
        if self.closed:
            raise ArtifactError('native DuckDB connection is closed')
        try:
            current = (inventory('dagtoml-duckdb-recipe-v1', _recipe(self._root)) == self._proof['source_sha256']
                       and all(_metadata(os.stat(self._root / path, follow_symlinks=False)) == metadata
                               for path, metadata in self._fingerprints.items()))
            for path in self._fingerprints:
                _parents(self._root, path)
        except (OSError, ArtifactError):
            self.close()
            raise
        if not current:
            self.close()
            raise ArtifactError('native DuckDB recipe or artifacts moved during the session')

    def execute(self, sql, parameters=()):
        if not isinstance(sql, str) or type(parameters) not in (tuple, list):
            raise TypeError('native DuckDB execution requires SQL text and a parameter sequence')
        sql = str.__str__(sql)
        if '\0' in sql:
            raise TypeError('native DuckDB SQL must not contain NUL bytes')
        values = [parameter(value) for value in parameters]
        with self._lock:
            self._current()
            cursor = self._connection.execute(sql, values)
            return _Rows(cursor.fetchall() if cursor.description is not None else [])

    def close(self):
        with self._lock:
            if not self.closed:
                self._connection.close()
                self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_error):
        self.close()
        return False


def connect(destination):
    return NativeConnection(destination)


def native_connection(connection):
    # Failure-injection wrappers delegate this marker to their owned connection.
    if getattr(connection, 'reference_protocol', None) != PROTOCOL:
        raise TypeError('DuckDB reference store requires its bound native connection')
    return connection


def connection_error(error):
    return _MODULE is not None and isinstance(error, _MODULE.IOException)
