"""Parse Ubuntu binary dependency expressions without APT or dpkg."""

import re
from dataclasses import dataclass

from apt_graph.errors import InputError

ATOM = re.compile(
    r'(?P<name>[a-zA-Z0-9][a-zA-Z0-9+.-]*)'
    r'(?::(?P<arch>[a-z0-9-]+))?'
    r'(?:\s*\(\s*(?P<operator><<|<=|=|>=|>>)\s*'
    r'(?P<version>[^\s()]+)\s*\))?'
)


@dataclass(frozen=True)
class Dependency:
    """One real or virtual package, optionally constrained by version."""

    name: str
    arch: str | None = None
    operator: str | None = None
    version: str | None = None

    def describe(self) -> str:
        """Restore the relationship text for direct-dependency output."""
        qualified = f'{self.name}:{self.arch}' if self.arch else self.name
        if self.operator:
            return f'{qualified} ({self.operator} {self.version})'
        return qualified


@dataclass(frozen=True)
class Relation:
    """One required group; satisfying any alternative suffices."""

    field: str
    alternatives: tuple[Dependency, ...]

    def describe(self) -> str:
        """Return the APT field type and all alternatives."""
        return f'{self.field}: ' + ' | '.join(
            dependency.describe() for dependency in self.alternatives
        )


def parse_dependency(text: str) -> Dependency:
    """Parse package[:architecture] with an optional version constraint."""
    match = ATOM.fullmatch(text.strip())
    if not match:
        raise InputError(f'invalid binary dependency: {text!r}')
    return Dependency(**match.groupdict())


def parse_relations(text: str, field: str) -> tuple[Relation, ...]:
    """Split comma-separated groups and pipe-separated alternatives."""
    if not text.strip():
        return ()
    return tuple(
        Relation(field, tuple(parse_dependency(part)
                              for part in group.split('|')))
        for group in text.split(',')
    )
