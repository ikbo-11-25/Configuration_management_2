"""Validate the five settings from the YAML configuration file."""

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from apt_graph.errors import InputError
from apt_graph.yaml_config import read_mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / 'config.yaml'
FIELDS = ('package', 'repository', 'test_mode', 'version', 'max_depth')
APT_NAME = re.compile(r'[a-z0-9][a-z0-9+.-]+')
TEST_NAME = re.compile(r'[A-Z]')
VERSION = re.compile(r'(?:[0-9]+:)?[0-9][A-Za-z0-9.+~:-]*')
MIN_DEPTH = 0
MAX_DEPTH = 256
MIN_PORT = 1


@dataclass(frozen=True)
class Config:
    """Settings after validation; local paths are already absolute."""

    package: str
    repository: str
    test_mode: bool
    version: str
    max_depth: int

    def dump(self) -> str:
        """Display exactly the five configurable fields."""
        values = vars(self).copy()
        values['test_mode'] = str(self.test_mode).lower()
        return '\n'.join(f'{key}={values[key]}' for key in FIELDS)


def check_fields(mapping: dict) -> None:
    """Reject a missing or unknown setting."""
    missing = set(FIELDS) - mapping.keys()
    unknown = mapping.keys() - set(FIELDS)
    if missing:
        raise InputError(f'missing settings: {", ".join(sorted(missing))}')
    if unknown:
        raise InputError(f'unknown settings: {", ".join(sorted(unknown))}')


def require_string(mapping: dict, key: str) -> str:
    """Read a nonempty text setting without control characters."""
    value = mapping[key]
    if not isinstance(value, str) or not value.strip():
        raise InputError(f'{key}: expected a nonempty string')
    if any(ord(char) < ord(' ') for char in value):
        raise InputError(f'{key}: control characters are not allowed')
    return value


def validate_url(value: str) -> str:
    """Allow an HTTP(S) index URL or archive base URL."""
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError as error:
        raise InputError('repository: invalid URL') from error
    if parts.scheme not in ('http', 'https') or not parts.hostname:
        raise InputError('repository: expected an HTTP or HTTPS URL')
    if parts.username or parts.password or parts.fragment:
        raise InputError('repository: credentials and fragments are forbidden')
    if any(char.isspace() for char in value) or port == MIN_PORT - 1:
        raise InputError('repository: invalid port or whitespace')
    return value


def validate_source(value: str, base: Path, test_mode: bool) -> str:
    """Return the remote URL or the resolved path to an existing fixture."""
    if not test_mode:
        return validate_url(value)
    try:
        path = (base / value).resolve()
        if path.is_file():
            return str(path)
    except (OSError, RuntimeError, ValueError) as error:
        raise InputError(f'repository: {error}') from error
    raise InputError(f'repository: file not found: {path}')


def load_config(path: Path) -> Config:
    """Read YAML and validate package, source, mode, version, and depth."""
    mapping = read_mapping(path)
    check_fields(mapping)
    test_mode = mapping['test_mode']
    if type(test_mode) is not bool:
        raise InputError('test_mode: expected true or false')
    package = require_string(mapping, 'package')
    name_pattern = TEST_NAME if test_mode else APT_NAME
    if not name_pattern.fullmatch(package):
        raise InputError('package: invalid name for the selected mode')
    version = require_string(mapping, 'version')
    if not VERSION.fullmatch(version):
        raise InputError('version: expected a quoted Debian version')
    depth = mapping['max_depth']
    if type(depth) is not int or not MIN_DEPTH <= depth <= MAX_DEPTH:
        raise InputError(f'max_depth: expected integer {MIN_DEPTH}..{MAX_DEPTH}')
    source = require_string(mapping, 'repository')
    source = validate_source(source, path.resolve().parent, test_mode)
    return Config(package, source, test_mode, version, depth)
