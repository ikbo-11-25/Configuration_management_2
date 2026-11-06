"""Load a local JSON graph whose package identifiers are A through Z."""

import json
from pathlib import Path

from apt_graph.config import TEST_NAME, VERSION
from apt_graph.errors import InputError
from apt_graph.records import Catalog, PackageId, Record


def unique_object(items: list) -> dict:
    """Reject duplicate JSON names rather than overwriting package data."""
    result = {}
    for key, value in items:
        if key in result:
            raise InputError(f'test repository: duplicate key {key!r}')
        result[key] = value
    return result


def fixture_records(data):
    """Validate package, version, and dependency lists in the fixture."""
    if not isinstance(data, dict):
        raise InputError('test repository: expected an object of packages')
    for name, versions in data.items():
        if not TEST_NAME.fullmatch(name) or not isinstance(versions, dict):
            raise InputError(f'test repository: invalid package {name!r}')
        yield from fixture_versions(name, versions)


def fixture_versions(name: str, versions: dict):
    """Read the versioned dependency lists for one test package."""
    for version, dependencies in versions.items():
        if not VERSION.fullmatch(version):
            raise InputError(f'test repository: bad version {version!r}')
        if not isinstance(dependencies, list):
            raise InputError(f'test repository: {name} needs a list')
        if any(not isinstance(dep, str) or not TEST_NAME.fullmatch(dep)
               for dep in dependencies):
            raise InputError(f'test repository: bad dependency of {name}')
        depends = ', '.join(dependencies)
        yield Record(PackageId(name, version), depends=depends)


def load_fixture(path: Path) -> Catalog:
    """Read the fixture without network access."""
    try:
        text = path.read_text(encoding='utf-8-sig')
        data = json.loads(text, object_pairs_hook=unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InputError(f'test repository: {error}') from error
    return Catalog(fixture_records(data))
