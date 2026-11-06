"""Verify D2 structure and CLI output, including isolated vertices."""

import unittest
from contextlib import redirect_stdout
from io import StringIO

from apt_graph.__main__ import main
from apt_graph.d2_output import to_d2
from test_graph import build_fixture


class D2Tests(unittest.TestCase):
    """Exercise both D2 export and the user-facing CLI."""

    def test_diamond(self):
        """A shared target is declared once and used by both connections."""
        result = to_d2(build_fixture('A', 3))
        self.assertIn('p3: "D\\n1.0"', result)
        self.assertIn('p1 -> p3: "Depends"', result)
        self.assertIn('p2 -> p3: "Depends"', result)
        self.assertEqual(result.count('p3: "D\\n1.0"'), 1)

    def test_isolated_root(self):
        """An empty adjacency list still draws the root package."""
        result = to_d2(build_fixture('G', 0))
        self.assertIn('p0: "G\\n1.0"', result)
        self.assertNotIn(' -> ', result)

    def test_cli_default(self):
        """The final entry point prints D2 without extra diagnostic lines."""
        output = StringIO()
        with redirect_stdout(output):
            result = main([])
        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue(), to_d2(build_fixture('A', 3)))
