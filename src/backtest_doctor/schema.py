"""Offline, declarative CSV column aliases; never executes user configuration."""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path

MAX_SCHEMA_BYTES = 16 * 1024
CANONICAL_FIELDS = {
    'ohlcv': frozenset(('timestamp', 'open', 'high', 'low', 'close', 'volume')),
    'ledger': frozenset(('signal_bar_close', 'entry_time', 'next_bar_open',
                         'stop_hit', 'target_hit')),
    'stability': frozenset(('exit_time', 'gross_return')),
}


def _no_duplicate_keys(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('duplicate JSON key')
        result[name] = value
    return result


def load_columns(path):
    """Read small trusted local JSON, rejecting duplicates and path symlinks."""
    path = Path(path)
    if path.is_symlink():
        raise ValueError('symlink configuration rejected')
    flags = os.O_RDONLY
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    with os.fdopen(fd, 'rb') as f:
        info = os.fstat(f.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_SCHEMA_BYTES:
            raise ValueError('invalid configuration file')
        data = f.read(MAX_SCHEMA_BYTES + 1)
        if len(data) > MAX_SCHEMA_BYTES:
            raise ValueError('oversized configuration file')
    document = json.loads(data.decode('utf-8-sig'), object_pairs_hook=_no_duplicate_keys)
    if not isinstance(document, dict) or not document:
        raise ValueError('invalid configuration structure')
    result = {}
    for mode, aliases in document.items():
        if mode not in CANONICAL_FIELDS or not isinstance(aliases, dict) or not aliases:
            raise ValueError('invalid configuration section')
        if not set(aliases).issubset(CANONICAL_FIELDS[mode]):
            raise ValueError('unknown canonical column')
        for value in aliases.values():
            if not isinstance(value, str) or not value.strip() or len(value) > 128:
                raise ValueError('invalid source column name')
        if len(set(aliases.values())) != len(aliases):
            raise ValueError('ambiguous source column mapping')
        result[mode] = aliases
    return result


def normalize_rows(rows, mode, columns):
    """Rename headers without changing input values; reject collisions."""
    aliases = columns.get(mode, {})
    if not aliases:
        return rows
    normalized = []
    for row in rows:
        for canonical, original in aliases.items():
            if original not in row or (canonical != original and canonical in row):
                raise ValueError('missing or ambiguous mapped source column')
        copy = dict(row)
        for canonical, original in aliases.items():
            copy[canonical] = copy[original]
        normalized.append(copy)
    return normalized
