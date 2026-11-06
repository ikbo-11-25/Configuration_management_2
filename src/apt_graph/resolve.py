"""Choose dependency records from one index without an install solver."""

from functools import cmp_to_key

from apt_graph.records import Catalog, Record
from apt_graph.relations import Dependency, Relation, parse_relations
from apt_graph.versions import compare_versions, satisfies


def compare_records(left: Record, right: Record) -> int:
    """Compare the versions of two candidate records."""
    return compare_versions(left.package.version, right.package.version)


class Resolver:
    """Resolve required groups with a deterministic local policy."""

    def __init__(self, catalog: Catalog) -> None:
        """Keep the catalog and build a virtual package index."""
        self.catalog = catalog
        self.providers = {}
        for record in catalog.records.values():
            for group in parse_relations(record.provides, 'Provides'):
                for item in group.alternatives:
                    entries = self.providers.setdefault(item.name, [])
                    entries.append((record, item.version or ''))

    def architecture_ok(self, record: Record, dependency: Dependency) -> bool:
        """Handle native, explicit, and :any qualifiers for this index."""
        if dependency.arch == 'any':
            return record.multi_arch == 'allowed'
        requested = dependency.arch
        if requested in (None, 'native'):
            requested = self.catalog.arch
        return not requested or record.package.arch in (requested, 'all', '')

    def candidate(self, dependency: Dependency) -> Record | None:
        """Prefer a real package, then a provider of a virtual package."""
        direct = self.catalog.by_name.get(dependency.name, [])
        direct = [(record, record.package.version) for record in direct]
        match = self.select(direct, dependency)
        if match is not None:
            return match
        return self.select(self.providers.get(dependency.name, []), dependency)

    def select(self, candidates: list, dependency: Dependency) -> Record | None:
        """Keep matching records, then prefer name and highest version."""
        matches = [record for record, version in candidates
                   if self.architecture_ok(record, dependency)
                   and satisfies(version, dependency.operator,
                                 dependency.version)]
        if not matches:
            return None
        name = min(record.package.name for record in matches)
        pool = (record for record in matches if record.package.name == name)
        return max(pool, key=cmp_to_key(compare_records))

    def resolve(self, relation: Relation) -> Record | None:
        """Use the first alternative that has a compatible candidate."""
        for dependency in relation.alternatives:
            record = self.candidate(dependency)
            if record is not None:
                return record
        return None
