"""Entry point for the configurable dependency explorer."""

import argparse
import sys
from pathlib import Path

from apt_graph.apt_source import load_apt
from apt_graph.config import DEFAULT_CONFIG, Config, load_config
from apt_graph.d2_output import to_d2
from apt_graph.errors import InputError
from apt_graph.graph import GraphBuilder, describe_graph
from apt_graph.order import describe_order
from apt_graph.resolve import Resolver
from apt_graph.test_source import load_fixture


def analyze(config: Config, mode: str) -> str:
    """Load the selected source and produce a report."""
    if mode == 'config':
        return config.dump()
    if config.test_mode:
        catalog = load_fixture(Path(config.repository))
    else:
        catalog = load_apt(config.repository)
    root = catalog.exact(config.package, config.version)
    if mode == 'direct':
        lines = [root.package.describe()]
        lines.extend(relation.describe() for relation in root.relations())
        return '\n'.join(lines)
    graph = GraphBuilder(Resolver(catalog), config.max_depth).build(root)
    if mode == 'order':
        return describe_order(graph)
    if mode == 'd2':
        return to_d2(graph)
    return describe_graph(graph)


def main(argv: list[str] | None = None) -> int:
    """Validate settings and display the requested report."""
    parser = argparse.ArgumentParser(description='Ubuntu APT graph explorer')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG,
                        help='path to the YAML configuration')
    modes = ('config', 'direct', 'graph', 'order', 'd2')
    parser.add_argument('--mode', choices=modes, default='d2',
                        help='requested output')
    parser.add_argument('--output', type=Path,
                        help='also save the output as a UTF-8 text file')
    args = parser.parse_args(argv)
    try:
        report = analyze(load_config(args.config), args.mode)
        if args.output is not None:
            args.output.write_text(report.rstrip() + '\n', encoding='utf-8')
        print(report.rstrip())
    except (InputError, OSError, UnicodeError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
