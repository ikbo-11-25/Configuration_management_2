"""Check dependency ordering for DAGs, depth limits, and cycles."""

import unittest

from apt_graph.order import dependency_order, describe_order
from test_graph import build_fixture


class OrderTests(unittest.TestCase):
    """Check the order and explain graph conditions that prevent it."""

    def test_dependency_before_parent(self):
        """The shared dependency comes first and occurs only once."""
        result = dependency_order(build_fixture('A', 3))
        self.assertEqual([node.name for node in result.packages], list('DBCA'))
        self.assertEqual(result.cycles, ())

    def test_depth_limited_order(self):
        """Packages beyond the chosen depth do not appear in the list."""
        result = dependency_order(build_fixture('A', 1))
        self.assertEqual([node.name for node in result.packages], list('BCA'))

    def test_cycle_report(self):
        """A cycle is visible and does not masquerade as a strict order."""
        graph = build_fixture('E', 4)
        result = dependency_order(graph)
        cycle = result.cycles[0]
        self.assertEqual([node.name for node in cycle], list('EFE'))
        self.assertIn('strict dependency order is impossible',
                      describe_order(graph))
