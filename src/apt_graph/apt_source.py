"""Download and read Ubuntu Packages metadata with the standard library."""

import bz2
import gzip
import lzma
import re
from io import BytesIO
from urllib.error import URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from apt_graph.deb822 import read_records
from apt_graph.errors import InputError
from apt_graph.records import Catalog

DEFAULT_INDEX = 'dists/noble/main/binary-amd64/Packages.xz'
INDEX_PATH = re.compile(r'/Packages(?:\.(?:gz|xz|bz2))?$')
ARCH_PATH = re.compile(r'/binary-([a-z0-9-]+)/')
NETWORK_TIMEOUT = 30
MAX_DOWNLOAD = 64 * 1024 * 1024
MAX_UNPACKED = 256 * 1024 * 1024


def index_url(source: str) -> str:
    """Use a direct index URL or append the documented default path."""
    parts = urlsplit(source)
    path = parts.path.rstrip('/')
    if not INDEX_PATH.search(path):
        path += '/' + DEFAULT_INDEX
    return urlunsplit(parts._replace(path=path))


def download_index(url: str) -> bytes:
    """Download at most MAX_DOWNLOAD bytes and report HTTP failures."""
    request = Request(url, headers={'User-Agent': 'apt-graph-variant-30/1'})
    try:
        with urlopen(request, timeout=NETWORK_TIMEOUT) as response:
            payload = response.read(MAX_DOWNLOAD + 1)
    except (OSError, URLError, ValueError) as error:
        message = f'repository: cannot download {url}: {error}'
        raise InputError(message) from error
    if len(payload) > MAX_DOWNLOAD:
        raise InputError('repository: compressed index exceeds 64 MiB')
    return payload


def decode_index(payload: bytes) -> str:
    """Detect gzip, xz, bzip2, or plain UTF-8 by the payload bytes."""
    formats = ((b'\x1f\x8b', gzip.open),
               (b'\xfd7zXZ\x00', lzma.LZMAFile), (b'BZh', bz2.BZ2File))
    try:
        for prefix, reader in formats:
            if payload.startswith(prefix):
                with reader(BytesIO(payload)) as stream:
                    payload = stream.read(MAX_UNPACKED + 1)
                break
        if len(payload) > MAX_UNPACKED:
            raise InputError('repository: unpacked index exceeds 256 MiB')
        return payload.decode('utf-8-sig')
    except (OSError, EOFError, UnicodeError, lzma.LZMAError) as error:
        raise InputError(f'repository: invalid Packages index: {error}') \
            from error


def load_apt(source: str) -> Catalog:
    """Build a catalog from one downloaded architecture index."""
    url = index_url(source)
    text = decode_index(download_index(url))
    arch_match = ARCH_PATH.search(urlsplit(url).path)
    arch = arch_match.group(1) if arch_match else ''
    return Catalog(read_records(text), arch)
