"""Check the YAML configuration and every invalid parameter."""

import unittest
from unittest.mock import patch

from apt_graph.config import DEFAULT_CONFIG, load_config
from apt_graph.errors import InputError
from apt_graph.yaml_config import parse_mapping


class ConfigTests(unittest.TestCase):
    """Verify required configuration fields and formats."""

    def test_valid_settings(self):
        """The bundled configuration resolves its source beside the YAML."""
        settings = load_config(DEFAULT_CONFIG)
        self.assertEqual(settings.package, 'A')
        self.assertEqual(settings.version, '1.0')
        self.assertIn('test_mode=true', settings.dump())
        self.assertTrue(settings.repository.endswith('repository.json'))

    def test_invalid_fields(self):
        """All five malformed settings fail with a named error."""
        good = {'package': 'A', 'repository': 'examples/repository.json',
                'test_mode': True, 'version': '1.0', 'max_depth': 3}
        bad = {'package': 'aa', 'repository': 'does-not-exist.json',
               'test_mode': 'true', 'version': 'wrong', 'max_depth': -1}
        for key, value in bad.items():
            with self.subTest(key=key):
                mapping = {**good, key: value}
                target = 'apt_graph.config.read_mapping'
                with patch(target, return_value=mapping):
                    with self.assertRaisesRegex(InputError, key):
                        load_config(DEFAULT_CONFIG)

    def test_duplicate_keys(self):
        """Duplicate fields cannot silently overwrite the configuration."""
        with self.assertRaisesRegex(InputError, 'duplicate key'):
            parse_mapping('package: A\npackage: B')

    def test_yaml_quoted_values(self):
        """Quoted hash marks and doubled single quotes are retained."""
        values = parse_mapping('path: "a # b" # comment\nvalue: \'a\'\'b\'')
        self.assertEqual(values, {'path': 'a # b', 'value': "a'b"})


if __name__ == '__main__':
    unittest.main()
