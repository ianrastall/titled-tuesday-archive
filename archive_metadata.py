#!/usr/bin/env python3
"""Build Titled Tuesday metadata, import new PGNs, and migrate legacy names.

Canonical filenames are ``titled-tuesday_YYYY-MM-DD[a|b].(zip|pgn)``: the ISO
date plus an optional session suffix (``a`` = early, ``b`` = late; omitted for
single-session events). Each ZIP holds one identically named PGN whose game
content is never modified. The importer also recognizes the older
``cc_titled-tuesday_YYMMDD[a|b]`` names and the raw export names so both new
imports and a one-time ``--migrate`` re-pack can read them.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import re
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CANONICAL_NAME = re.compile(r'^titled-tuesday_(\d{4})-(\d{2})-(\d{2})([ab]?)\.(?:pgn|zip)$')
OLD_CANONICAL_NAME = re.compile(r'^cc_titled-tuesday_(\d{2})(\d{2})(\d{2})([ab]?)\.(?:pgn|zip)$')
LEGACY_NAME = re.compile(r'^titled-tuesday-(\d{4}-\d{2}-\d{2})([ab]?)\.(?:pgn|zip)$')
SHORT_NAME = re.compile(r'^(\d{2})(\d{2})(\d{2})([ab]?)-titled-tuesday\.pgn$')
EXPORT_NAME = re.compile(r'^(\d{4})-titled-tuesday-blitz-([a-z]+)-(\d{1,2})(?:-(early|late))?\.pgn$', re.I)
EVENT = re.compile(rb'^\[Event "(.*)"\]\s*$', re.M)
SESSION = {'': '', 'a': 'early', 'b': 'late'}

_MONTHS = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}


def archive_identity(filename: str) -> tuple[str, str]:
    match = CANONICAL_NAME.fullmatch(filename)
    if match:
        return date(int(match[1]), int(match[2]), int(match[3])).isoformat(), match[4]
    match = OLD_CANONICAL_NAME.fullmatch(filename)
    if match:
        return date(2000 + int(match[1]), int(match[2]), int(match[3])).isoformat(), match[4]
    match = LEGACY_NAME.fullmatch(filename)
    if match:
        return date.fromisoformat(match[1]).isoformat(), match[2]
    match = SHORT_NAME.fullmatch(filename)
    if match:
        return date(2000 + int(match[1]), int(match[2]), int(match[3])).isoformat(), match[4]
    match = EXPORT_NAME.fullmatch(filename)
    if match:
        session = {'early': 'a', 'late': 'b', None: ''}[match[4].lower() if match[4] else None]
        return date(int(match[1]), _MONTHS[match[2].lower()], int(match[3])).isoformat(), session
    raise ValueError(f'Unrecognized Titled Tuesday filename: {filename}')


def canonical_filename(iso_date: str, suffix: str) -> str:
    return f'titled-tuesday_{iso_date}{suffix}.zip'


def pgn_metadata(content: bytes, strict: bool = False) -> tuple[str, int]:
    events = EVENT.findall(content.removeprefix(b'\xef\xbb\xbf'))
    if not events:
        raise ValueError('PGN has no Event headers.')
    if strict:
        for tag in (b'White', b'Black', b'Result'):
            if len(re.findall(rb'^\[' + tag + rb' "[^"\r\n]+"\]\s*$', content, re.M)) != len(events):
                raise ValueError(f'PGN has missing or duplicate {tag.decode()} headers.')
    return events[0].decode('utf-8').strip(), len(events)


def entry_metadata(filename: str, pgn: str, event: str, games: int, sha256: str) -> dict:
    event_date, suffix = archive_identity(filename)
    year = int(event_date[:4])
    return dict(pgn=pgn, zip=filename, year=year, date=event_date, session=SESSION[suffix],
                event=event, games=games,
                url=f'https://github.com/ianrastall/titled-tuesday-archive/raw/main/{year}/{filename}',
                sha256=sha256)


def write_zip(destination: Path, pgn_name: str, content: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(pgn_name, content)
    with zipfile.ZipFile(temporary) as archive:
        if archive.namelist() != [pgn_name] or archive.read(pgn_name) != content:
            raise ValueError(f'ZIP verification failed: {destination}')
    temporary.replace(destination)


def read_inner_pgn(path: Path) -> bytes:
    with zipfile.ZipFile(path) as archive:
        names = [item.filename for item in archive.infolist() if not item.is_dir()]
        if len(names) != 1:
            raise ValueError(f'Expected one PGN in {path}: {names}')
        return archive.read(names[0])


def read_zip(path: Path) -> dict:
    event_date, _ = archive_identity(path.name)
    if path.parent.name != event_date[:4]:
        raise ValueError(f'Wrong year folder: {path}')
    with zipfile.ZipFile(path) as archive:
        names = [item.filename for item in archive.infolist() if not item.is_dir()]
        expected = path.with_suffix('.pgn').name
        if names != [expected]:
            raise ValueError(f'Expected one canonical PGN in {path}: {names}')
        event, games = pgn_metadata(archive.read(expected))
    return entry_metadata(path.name, expected, event, games, hashlib.sha256(path.read_bytes()).hexdigest())


def render_metadata(entries: list[dict]) -> dict[str, str]:
    entries = sorted(entries, key=lambda entry: entry['zip'])
    return {
        'tt_manifest.json': json.dumps(entries, ensure_ascii=False, indent=2) + '\n',
        'tt_links.txt': ''.join(f"{entry['url']}\n" for entry in entries),
        'tt_events.txt': ''.join(f"{entry['pgn']}: {entry['event']}\n" for entry in entries),
        'tt_game_counts.txt': ''.join(f"{entry['pgn']}: {entry['games']}\n" for entry in entries),
    }


def migrate(write: bool) -> int:
    """Re-pack legacy ``cc_titled-tuesday_YYMMDD[a|b]`` ZIPs under the canonical name."""
    renames = 0
    for path in sorted(ROOT.glob('20[0-9][0-9]/*.zip')):
        if CANONICAL_NAME.fullmatch(path.name):
            continue
        if not OLD_CANONICAL_NAME.fullmatch(path.name):
            raise ValueError(f'Unexpected archive name during migrate: {path}')
        event_date, suffix = archive_identity(path.name)
        new_zip = canonical_filename(event_date, suffix)
        new_pgn = new_zip.removesuffix('.zip') + '.pgn'
        destination = path.parent / new_zip
        if destination.exists():
            raise ValueError(f'Target already exists: {destination}')
        print(f'{path.name} -> {new_zip}', flush=True)
        renames += 1
        if write:
            write_zip(destination, new_pgn, read_inner_pgn(path))
            path.unlink()
    return renames


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--import-pgn', type=Path, nargs='+', default=[],
                        help='Selected new PGNs; their names determine event dates and sessions.')
    parser.add_argument('--migrate', action='store_true',
                        help='Re-pack any legacy cc_titled-tuesday_YYMMDD[a|b] ZIPs to the canonical name.')
    parser.add_argument('--write', action='store_true', help='Apply changes. Otherwise preview only.')
    args = parser.parse_args()

    if args.migrate:
        count = migrate(args.write)
        print(f'{"Migrated" if args.write else "Would migrate"} {count} legacy ZIPs.')

    entries = [read_zip(path) for path in sorted(ROOT.glob('20[0-9][0-9]/*.zip'))]
    known = {entry['zip'] for entry in entries}
    pending = []
    for source in args.import_pgn:
        event_date, suffix = archive_identity(source.name)
        filename = canonical_filename(event_date, suffix)
        if filename in known:
            raise ValueError(f'Archive already exists or was selected twice: {filename}')
        content = source.read_bytes()
        event, games = pgn_metadata(content, strict=True)
        if 'titled' not in event.lower() or 'tuesday' not in event.lower():
            raise ValueError(f'Not a Titled Tuesday event: {source}')
        known.add(filename)
        pending.append((source, filename, event, games, hashlib.sha256(content).hexdigest()))
        print(f'{source.name} -> {filename}: {games:,} games', flush=True)

    if not args.write:
        if args.import_pgn or not args.migrate:
            print(f'Validated {len(entries)} existing ZIPs and {len(pending)} new PGNs. Add --write to save.')
        return

    for source, filename, event, games, digest in pending:
        content = source.read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError(f'Source changed during import: {source}')
        event_date, _ = archive_identity(filename)
        destination = ROOT / event_date[:4] / filename
        pgn = filename.removesuffix('.zip') + '.pgn'
        write_zip(destination, pgn, content)
        entries.append(entry_metadata(filename, pgn, event, games, hashlib.sha256(destination.read_bytes()).hexdigest()))

    for name, content in render_metadata(entries).items():
        target = ROOT / name
        if target.exists() and target.read_text(encoding='utf-8-sig') == content:
            continue
        temporary = target.with_suffix(target.suffix + '.tmp')
        temporary.write_text(content, encoding='utf-8', newline='\n')
        temporary.replace(target)
    print(f'Wrote {len(entries)} events and {sum(entry["games"] for entry in entries):,} games.')


if __name__ == '__main__':
    main()
