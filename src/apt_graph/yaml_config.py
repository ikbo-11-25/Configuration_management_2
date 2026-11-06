"""Read the flat YAML mapping used by the configuration file."""

import json
import re
from pathlib import Path

from apt_graph.errors import InputError

KEY = re.compile(r'([a-z_][a-z_0-9]*):\s*(.*)')
QUOTED = r'''"(?:[^"\\]|\\.)*"|'(?:[^']|'')*' '''.strip()
VALUE = re.compile(rf'''({QUOTED}|[^'"#\[\]{{}}&*!|>][^#]*?)\s*(?:#.*)?''')
INTEGER = re.compile(r'[+-]?[0-9]+')


def parse_scalar(source: str):
    """Read a plain or quoted string, decimal integer, or boolean."""
    matched = VALUE.fullmatch(source.strip())
    if not matched:
        raise InputError('expected a scalar YAML value')
    text = matched.group(1).strip()
    if text.startswith('"'):
        try:
            return json.loads(text)
        except ValueError as error:
            raise InputError('invalid double-quoted string') from error
    if text.startswith("'"):
        return text[1:-1].replace("''", "'")
    if text in ('true', 'false'):
        return text == 'true'
    if INTEGER.fullmatch(text):
        try:
            return int(text)
        except ValueError as error:
            raise InputError('integer is too large') from error
    return text


def parse_mapping(text: str) -> dict:
    """Read one unindented key/value per line and reject duplicate keys."""
    mapping = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = KEY.fullmatch(line)
        if not match:
            raise InputError(f'YAML line {number}: expected key: value')
        key, value = match.groups()
        if key in mapping:
            raise InputError(f'YAML line {number}: duplicate key {key}')
        try:
            mapping[key] = parse_scalar(value)
        except InputError as error:
            raise InputError(f'YAML line {number}, {key}: {error}') from error
    return mapping


def read_mapping(path: Path) -> dict:
    """Read a UTF-8 configuration, including files with a BOM."""
    try:
        text = path.read_text(encoding='utf-8-sig')
    except (OSError, UnicodeError) as error:
        message = f'cannot read configuration {path}: {error}'
        raise InputError(message) from error
    return parse_mapping(text)
