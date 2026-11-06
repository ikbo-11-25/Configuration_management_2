"""Test recursive DFS, shared vertices, depth bounds, and cycles."""

import unittest

from apt_graph.config import ROOT
from apt_graph.graph import GraphBuilder
from apt_graph.records import Catalog, PackageId, Record
from apt_graph.resolve import Resolver
from apt_graph.test_source import load_fixture


def build_fixture(name: str, limit: int, version: str = '1.0'):
    """Build one graph from the bundled test repository."""
    catalog = load_fixture(ROOT / 'examples' / 'repository.json')
    return GraphBuilder(Resolver(catalog), limit).build(
        catalog.exact(name, version),
    )


class GraphTests(unittest.TestCase):
    """Check graph structure rather than just command completion."""

    def test_diamond(self):
        """A shared dependency remains one vertex with two incoming edges."""
        graph = build_fixture('A', 3)
        self.assertEqual({node.name for node in graph.depths}, set('ABCD'))
        targets = [edge.target.name for edges in graph.edges.values()
                   for edge in edges]
        self.assertEqual(targets.count('D'), 2)

    def test_boundary(self):
        """A limit of one includes direct dependencies, but no children."""
        graph = build_fixture('A', 1)
        self.assertEqual({node.name for node in graph.depths}, set('ABC'))
        self.assertEqual(graph.edges[PackageId('B', '1.0')], ())
        self.assertEqual(set(build_fixture('A', 0).depths), {graph.root})

    def test_cycle(self):
        """The edge that closes a cycle is kept without recursing forever."""
        graph = build_fixture('E', 10)
        self.assertEqual(len(graph.depths), 2)
        self.assertEqual(graph.edges[PackageId('F', '1.0')][0].target,
                         graph.root)

    def test_shorter_path_reopens_node(self):
        """A later shorter path can expand a previously truncated node."""
        records = [Record(PackageId(name, '1'), depends=deps)
                   for name, deps in [('A', 'B, C'), ('B', 'C'),
                                      ('C', 'D'), ('D', '')]]
        catalog = Catalog(records)
        graph = GraphBuilder(Resolver(catalog), 2).build(catalog.exact('A', '1'))
        self.assertEqual(graph.depths[PackageId('C', '1')], 1)
        self.assertEqual(graph.depths[PackageId('D', '1')], 2)

    def test_root_version(self):
        """Changing the root version selects different dependencies."""
        graph = build_fixture('A', 1, '2.0')
        targets = [edge.target.name for edge in graph.edges[graph.root]]
        self.assertEqual(targets, ['E'])
