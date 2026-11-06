"""Produce dependency-first order and report why a strict order can fail."""

from dataclasses import dataclass

from apt_graph.graph import Graph
from apt_graph.records import PackageId

ORDER_START = 1


@dataclass(frozen=True)
class Ordering:
    """A dependency-first traversal and the cycles it encountered."""

    packages: tuple[PackageId, ...]
    cycles: tuple[tuple[PackageId, ...], ...]


def dependency_order(graph: Graph) -> Ordering:
    """Append each vertex after its children, noting DFS back edges."""
    root = graph.root
    frames = [(root, iter(graph.edges[root]))]
    active = {root: 0}
    visited = {root}
    order = []
    cycles = []
    while frames:
        package, children = frames[-1]
        edge = next(children, None)
        if edge is None:
            frames.pop()
            del active[package]
            order.append(package)
            continue
        target = edge.target
        if target in active:
            chain = tuple(node for node, _ in frames[active[target]:])
            cycles.append(chain + (target,))
        elif target not in visited:
            active[target] = len(frames)
            visited.add(target)
            frames.append((target, iter(graph.edges[target])))
    return Ordering(tuple(order), tuple(dict.fromkeys(cycles)))


def describe_order(graph: Graph) -> str:
    """Display the order with explicit cycle and resolution notices."""
    ordering = dependency_order(graph)
    lines = ['Dependency order within the configured depth:']
    if ordering.cycles:
        lines.append('Cycles found; a strict dependency order is impossible.')
        for cycle in ordering.cycles:
            lines.append('  ' + ' -> '.join(node.describe() for node in cycle))
        lines.append('The list below is DFS order after breaking back edges.')
    if graph.missing:
        lines.append('Unresolved dependencies are omitted from this list:')
        for package, relations in sorted(graph.missing.items()):
            for relation in relations:
                lines.append(f'  {package.describe()}: {relation.describe()}')
    for number, package in enumerate(ordering.packages, start=ORDER_START):
        lines.append(f'{number}. {package.describe()}')
    return '\n'.join(lines)
