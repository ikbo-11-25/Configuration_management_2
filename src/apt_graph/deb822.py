"""Read Debian control paragraphs from a Packages index."""

from apt_graph.errors import InputError
from apt_graph.records import PackageId, Record

REQUIRED = ('package', 'version', 'architecture')


def parse_paragraphs(text: str):
    """Yield dictionaries with unfolded continuation lines."""
    fields = {}
    key = None
    for line in text.splitlines():
        if not line.strip():
            if fields:
                yield fields
            fields = {}
            key = None
        elif line.startswith((' ', '\t')):
            if key is None:
                raise InputError('repository: continuation without a field')
            fields[key] += ' ' + line.strip()
        else:
            name, separator, value = line.partition(':')
            key = name.lower()
            if not separator or not name or key in fields:
                raise InputError(f'repository: invalid field {name!r}')
            fields[key] = value.strip()
    if fields:
        yield fields


def read_records(text: str):
    """Convert package paragraphs to compact relationship records."""
    for fields in parse_paragraphs(text):
        if any(not fields.get(key) for key in REQUIRED):
            raise InputError('repository: missing Package/Version/Architecture')
        package = PackageId(*(fields[key] for key in REQUIRED))
        yield Record(package, fields.get('pre-depends', ''),
                     fields.get('depends', ''), fields.get('provides', ''),
                     fields.get('multi-arch', ''))
