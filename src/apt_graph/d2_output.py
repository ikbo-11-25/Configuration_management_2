"""Serialize the resolved dependency graph to D2 source text."""

import json

from apt_graph.graph import Graph
from apt_graph.records import PackageId


def quote(text: str) -> str:
    """Escape a label so user data cannot be interpreted as D2 syntax."""
    return json.dumps(text, ensure_ascii=False)


def package_label(package: PackageId) -> str:
    """Put the package name and exact version on separate lines."""
    arch = f' · {package.arch}' if package.arch else ''
    return f'{package.name}\n{package.version}{arch}'


def unresolved_lines(graph: Graph, ids: dict):
    """Add separate warning nodes for each unresolved required group."""
    number = 0
    for package, groups in sorted(graph.missing.items()):
        for group in groups:
            node_id = f'u{number}'
            number += 1
            yield f'{node_id}: {quote(group.describe())}'
            yield f'{node_id}.style.fill: "#fef3c7"'
            yield f'{ids[package]} -> {node_id}: unresolved'


def to_d2(graph: Graph) -> str:
    """Emit deterministic D2 with explicit vertices, including isolates."""
    ids = {package: f'p{number}'
           for number, package in enumerate(sorted(graph.depths))}
    lines = ['# Ubuntu APT dependencies', 'direction: down', '']
    for package, node_id in ids.items():
        lines.append(f'{node_id}: {quote(package_label(package))}')
    lines.append(f'{ids[graph.root]}.style.fill: "#dbeafe"')
    lines.append(f'{ids[graph.root]}.style.stroke: "#1d4ed8"')
    lines.append('')
    for package in ids:
        for edge in graph.edges[package]:
            target = ids[edge.target]
            label = quote(edge.relation.field)
            lines.append(f'{ids[package]} -> {target}: {label}')
    lines.extend(unresolved_lines(graph, ids))
    return '\n'.join(lines).rstrip() + '\n'
