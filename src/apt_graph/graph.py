"""Build a depth-limited graph with recursive depth-first search."""

from dataclasses import dataclass, field

from apt_graph.records import PackageId, Record
from apt_graph.relations import Relation
from apt_graph.resolve import Resolver

ROOT_DEPTH = 0


@dataclass(frozen=True)
class Edge:
    """The selected target and the relationship that requires it."""

    target: PackageId
    relation: Relation


@dataclass
class Graph:
    """Vertices, edges, and unsatisfied groups within the depth bound."""

    root: PackageId
    depths: dict[PackageId, int] = field(default_factory=dict)
    edges: dict[PackageId, tuple[Edge, ...]] = field(default_factory=dict)
    missing: dict[PackageId, tuple[Relation, ...]] = field(default_factory=dict)


class GraphBuilder:
    """Revisit a node only if a shorter path expands its depth budget."""

    def __init__(self, resolver: Resolver, limit: int) -> None:
        """Store resolution policy and maximum edge distance."""
        self.resolver = resolver
        self.limit = limit

    def build(self, root: Record) -> Graph:
        """Return a new graph with the root at depth zero."""
        graph = Graph(root.package)
        self.visit(graph, root, ROOT_DEPTH)
        return graph

    def visit(self, graph: Graph, record: Record, depth: int) -> None:
        """Perform recursive DFS while retaining edges that close cycles."""
        package = record.package
        if depth >= graph.depths.get(package, self.limit + 1):
            return
        graph.depths[package] = depth
        graph.edges.setdefault(package, ())
        if depth == self.limit:
            return
        edges = []
        missing = []
        for relation in record.relations():
            target = self.resolver.resolve(relation)
            if target is None:
                missing.append(relation)
            else:
                edges.append(Edge(target.package, relation))
                self.visit(graph, target, depth + 1)
        graph.edges[package] = tuple(edges)
        if missing:
            graph.missing[package] = tuple(missing)


def describe_graph(graph: Graph) -> str:
    """Print the adjacency list, depth, and unsatisfied groups."""
    lines = []
    for package, depth in sorted(graph.depths.items()):
        lines.append(f'{package.describe()} depth={depth}')
        for edge in graph.edges[package]:
            target = edge.target.describe()
            lines.append(f'  -> {target} ({edge.relation.field})')
        for relation in graph.missing.get(package, ()):
            lines.append(f'  ? {relation.describe()}')
    return '\n'.join(lines)
