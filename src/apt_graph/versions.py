"""Compare Debian versions by epoch, upstream version, and revision."""

import re
from itertools import zip_longest

RUNS = re.compile(r'([^0-9]*)([0-9]*)')
OTHER_OFFSET = 256
EQUAL = 0


def compare_values(left, right) -> int:
    """Return the sign of the comparison."""
    return (left > right) - (left < right)


def split_version(text: str) -> tuple[str, str, str]:
    """Supply zero for an absent epoch and an absent Debian revision."""
    epoch, separator, body = text.partition(':')
    if not separator:
        epoch, body = '0', text
    upstream, separator, revision = body.rpartition('-')
    if not separator:
        upstream, revision = body, '0'
    return epoch, upstream, revision


def digit_key(text: str) -> tuple[int, str]:
    """Compare arbitrary-length numbers without converting them to ints."""
    trimmed = text.lstrip('0')
    return len(trimmed), trimmed


def letter_rank(char: str) -> int:
    """Place tilde before end, then ASCII letters, then other characters."""
    if char == '~':
        return -1
    if not char:
        return EQUAL
    return ord(char) if char.isalpha() else ord(char) + OTHER_OFFSET


def compare_letters(left: str, right: str) -> int:
    """Compare a non-numeric run according to Debian's ordering."""
    for first, second in zip_longest(left, right, fillvalue=''):
        difference = compare_values(letter_rank(first), letter_rank(second))
        if difference:
            return difference
    return EQUAL


def compare_parts(left: str, right: str) -> int:
    """Compare alternating runs of non-digits and digits."""
    first_runs, second_runs = RUNS.findall(left), RUNS.findall(right)
    for first, second in zip_longest(first_runs, second_runs,
                                     fillvalue=('', '')):
        difference = compare_letters(first[0], second[0])
        if not difference:
            keys = digit_key(first[1]), digit_key(second[1])
            difference = compare_values(*keys)
        if difference:
            return difference
    return EQUAL


def compare_versions(left: str, right: str) -> int:
    """Return a negative, zero, or positive Debian version comparison."""
    epoch_a, upstream_a, revision_a = split_version(left)
    epoch_b, upstream_b, revision_b = split_version(right)
    return (compare_values(digit_key(epoch_a), digit_key(epoch_b))
            or compare_parts(upstream_a, upstream_b)
            or compare_parts(revision_a, revision_b))


def satisfies(actual: str, operator: str | None, wanted: str | None) -> bool:
    """Check one version constraint against a record or virtual version."""
    if operator is None:
        return True
    if not actual or wanted is None:
        return False
    order = compare_versions(actual, wanted)
    return {'<<': order < EQUAL, '<=': order <= EQUAL,
            '=': order == EQUAL, '>=': order >= EQUAL,
            '>>': order > EQUAL}[operator]
