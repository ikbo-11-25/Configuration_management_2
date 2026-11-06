"""Entry point for the configurable dependency explorer."""

import argparse
import sys
from pathlib import Path

from apt_graph.apt_source import load_apt
from apt_graph.config import DEFAULT_CONFIG, load_config
from apt_graph.errors import InputError


def main(argv: list[str] | None = None) -> int:
    """Validate settings and show the selected package's direct relations."""
    parser = argparse.ArgumentParser(description='Ubuntu APT graph explorer')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG,
                        help='path to the YAML configuration')
    parser.add_argument('--mode', choices=('config', 'direct'),
                        default='direct', help='requested output')
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.mode == 'config':
            print(config.dump())
        elif config.test_mode:
            raise InputError('use examples/ubuntu/hello.yaml for this stage')
        else:
            catalog = load_apt(config.repository)
            root = catalog.exact(config.package, config.version)
            print(root.package.describe())
            for relation in root.relations():
                print(relation.describe())
    except InputError as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
