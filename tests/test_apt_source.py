"""Verify APT transport, control parsing, versions, and relations."""

import bz2
import gzip
import lzma
import unittest
from unittest.mock import patch

from apt_graph.apt_source import decode_index, index_url, load_apt
from apt_graph.errors import InputError

SAMPLE = '''Package: demo
Version: 1.0
Architecture: amd64
Pre-Depends: early
Depends: lib:any (>= 1.2) | other,
 helper
Recommends: optional

Package: demo
Version: 2.0
Architecture: amd64
Depends: new-lib
'''


class AptSourceTests(unittest.TestCase):
    """Exercise metadata loading without external network in unit tests."""

    def test_compression_formats(self):
        """Equivalent bytes decode in each supported index format."""
        data = SAMPLE.encode()
        for payload in (data, gzip.compress(data), lzma.compress(data),
                        bz2.compress(data)):
            self.assertEqual(decode_index(payload), SAMPLE)

    def test_urls(self):
        """Expand mirror roots and preserve explicit index URLs."""
        mirror = 'https://example.test/ubuntu'
        self.assertIn('/dists/noble/main/binary-amd64/', index_url(mirror))
        explicit = f'{mirror}/dists/jammy/main/binary-arm64/Packages.gz'
        self.assertEqual(index_url(explicit), explicit)

    def test_extract_exact_version_and_groups(self):
        """Only the requested record contributes mandatory relationships."""
        with patch('apt_graph.apt_source.download_index',
                   return_value=gzip.compress(SAMPLE.encode())):
            catalog = load_apt('https://example.test/ubuntu')
        root = catalog.exact('demo', '1.0')
        self.assertEqual(root.package.arch, 'amd64')
        self.assertEqual([group.describe() for group in root.relations()], [
            'Pre-Depends: early', 'Depends: lib:any (>= 1.2) | other',
            'Depends: helper',
        ])
        with self.assertRaisesRegex(InputError, 'version:'):
            catalog.exact('demo', '3.0')

    def test_invalid_metadata(self):
        """Malformed index text fails with a repository error."""
        with patch('apt_graph.apt_source.download_index',
                   return_value=b'<html>not an index</html>'):
            with self.assertRaisesRegex(InputError, 'repository:'):
                load_apt('https://example.test/ubuntu')
