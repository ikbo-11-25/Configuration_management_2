"""Package records and exact lookup by name and version."""

from dataclasses import dataclass

from apt_graph.errors import InputError
from apt_graph.relations import Relation, parse_relations


@dataclass(frozen=True, order=True)
class PackageId:
    """Identify a package version without conflating architectures."""

    name: str
    version: str
    arch: str = ''

    def describe(self) -> str:
        """Show the name, version, and optional architecture."""
        suffix = f' [{self.arch}]' if self.arch else ''
        return f'{self.name}={self.version}{suffix}'


@dataclass(frozen=True)
class Record:
    """Raw relationship fields from one paragraph of an APT index."""

    package: PackageId
    pre_depends: str = ''
    depends: str = ''
    provides: str = ''
    multi_arch: str = ''

    def relations(self) -> tuple[Relation, ...]:
        """Read mandatory dependencies; omit Recommends and Suggests."""
        return (parse_relations(self.pre_depends, 'Pre-Depends')
                + parse_relations(self.depends, 'Depends'))


class Catalog:
    """Index package records from one source."""

    def __init__(self, records, arch: str = '') -> None:
        """Build package and name indexes once."""
        self.records = {record.package: record for record in records}
        if not self.records:
            raise InputError('repository: no package records')
        self.arch = arch
        self.by_name = {}
        for record in self.records.values():
            self.by_name.setdefault(record.package.name, []).append(record)

    def exact(self, name: str, version: str) -> Record:
        """Find the requested exact version; never silently use latest."""
        candidates = self.by_name.get(name, [])
        for record in candidates:
            if record.package.version == version:
                return record
        if not candidates:
            raise InputError(f'package: {name!r} not found in repository')
        available = sorted({row.package.version for row in candidates})
        versions = ', '.join(available)
        message = f'version: {name}={version} not found; have {versions}'
        raise InputError(message)
