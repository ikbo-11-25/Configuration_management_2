"""Entry point for the configurable dependency explorer."""

import argparse
import sys
from pathlib import Path

from apt_graph.config import DEFAULT_CONFIG, load_config
from apt_graph.errors import InputError


def main(argv: list[str] | None = None) -> int:
    """Validate YAML settings and display them for the first stage."""
    parser = argparse.ArgumentParser(description='Ubuntu APT graph explorer')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG,
                        help='path to the YAML configuration')
    args = parser.parse_args(argv)
    try:
        print(load_config(args.config).dump())
    except InputError as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
