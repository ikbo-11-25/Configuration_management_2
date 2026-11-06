"""Check Debian version comparisons and deterministic alternatives."""

import unittest

from apt_graph.graph import GraphBuilder
from apt_graph.records import Catalog, PackageId, Record
from apt_graph.resolve import Resolver
from apt_graph.versions import compare_versions


class ResolutionTests(unittest.TestCase):
    """Exercise version operators and virtual packages."""

    def test_version_order(self):
        """Epochs, revisions, tilde, and digit runs compare correctly."""
        for older, newer in [('9.9', '1:1.0'), ('1.0~rc1', '1.0'),
                             ('1.0-2', '1.0-10'), ('1.9', '1.10'),
                             ('1.0+a', '1.0+b'), ('1.0a', '1.0+')]:
            with self.subTest(older=older, newer=newer):
                self.assertLess(compare_versions(older, newer), 0)
                self.assertGreater(compare_versions(newer, older), 0)
        self.assertEqual(compare_versions('1.01', '1.1-0'), 0)

    def test_alternatives_providers_and_missing(self):
        """Resolve the highest suitable version, provider, and missing edge."""
        deps = 'lib (>= 2) | fallback, virtual (>= 3), missing'
        root = Record(PackageId('app', '1'), depends=deps)
        records = [root, Record(PackageId('lib', '1')),
                   Record(PackageId('lib', '2')),
                   Record(PackageId('lib', '10')),
                   Record(PackageId('provider', '1'), provides='virtual (= 3)')]
        graph = GraphBuilder(Resolver(Catalog(records)), 1).build(root)
        targets = [edge.target for edge in graph.edges[root.package]]
        self.assertEqual(targets, [PackageId('lib', '10'),
                                   PackageId('provider', '1')])
        self.assertEqual(graph.missing[root.package][0].describe(),
                         'Depends: missing')

    def test_first_available_alternative(self):
        """Skip an absent package and accept the next alternative."""
        root = Record(PackageId('app', '1'), depends='absent | fallback')
        fallback = Record(PackageId('fallback', '2'))
        resolver = Resolver(Catalog([root, fallback]))
        self.assertEqual(resolver.resolve(root.relations()[0]), fallback)
