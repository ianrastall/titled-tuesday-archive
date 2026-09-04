#!/usr/bin/env python3
"""Build Titled Tuesday metadata from ZIPs and optionally import selected PGNs."""
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
NAME = re.compile(r'^cc_titled-tuesday_(\d{2})(\d{2})(\d{2})([ab]?)\.(?:pgn|zip)$')
LEGACY_NAME = re.compile(r'^titled-tuesday-(\d{4}-\d{2}-\d{2})([ab]?)\.(?:pgn|zip)$')
SHORT_NAME = re.compile(r'^(\d{2})(\d{2})(\d{2})([ab]?)-titled-tuesday\.pgn$')
EXPORT_NAME = re.compile(r'^(\d{4})-titled-tuesday-blitz-([a-z]+)-(\d{1,2})(?:-(early|late))?\.pgn$', re.I)
EVENT = re.compile(rb'^\[Event "(.*)"\]\s*$', re.M)
SESSION = {'': '', 'a': 'early', 'b': 'late'}


def archive_identity(filename: str) -> tuple[str, str]:
    match = NAME.fullmatch(filename)
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
        months = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}
        return date(int(match[1]), months[match[2].lower()], int(match[3])).isoformat(), {'early': 'a', 'late': 'b', None: ''}[match[4].lower() if match[4] else None]
    raise ValueError(f'Unrecognized Titled Tuesday filename: {filename}')


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--import-pgn', type=Path, nargs='+', default=[], help='Selected new PGNs; their names determine event dates and sessions.')
    parser.add_argument('--write', action='store_true', help='Create new ZIPs and write metadata. Otherwise preview only.')
    args = parser.parse_args()
    entries = [read_zip(path) for path in sorted(ROOT.glob('20[0-9][0-9]/*.zip'))]
    known = {entry['zip'] for entry in entries}
    pending = []
    for source in args.import_pgn:
        event_date, suffix = archive_identity(source.name)
        filename = f'cc_titled-tuesday_{event_date[2:4]}{event_date[5:7]}{event_date[8:10]}{suffix}.zip'
        if filename in known:
            raise ValueError(f'Archive already exists or was selected twice: {filename}')
        content = source.read_bytes()
        event, games = pgn_metadata(content, strict=True)
        if 'titled' not in event.lower() or 'tuesday' not in event.lower():
            raise ValueError(f'Not a Titled Tuesday event: {source}')
        known.add(filename)
        pending.append((source, filename, event, games, hashlib.sha256(content).hexdigest()))
        print(f'{source.name} -> {filename}: {games:,} games', flush=True)
    if args.write:
        for source, filename, event, games, digest in pending:
            content = source.read_bytes()
            if hashlib.sha256(content).hexdigest() != digest:
                raise ValueError(f'Source changed during import: {source}')
            event_date, _ = archive_identity(filename)
            destination = ROOT / event_date[:4] / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix('.zip.tmp')
            pgn = filename.removesuffix('.zip') + '.pgn'
            with zipfile.ZipFile(temporary, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                archive.writestr(pgn, content)
            with zipfile.ZipFile(temporary) as archive:
                if archive.read(pgn) != content:
                    raise ValueError(f'ZIP verification failed: {destination}')
            temporary.rename(destination)
            entries.append(entry_metadata(filename, pgn, event, games, hashlib.sha256(destination.read_bytes()).hexdigest()))
        for name, content in render_metadata(entries).items():
            target = ROOT / name
            if target.exists() and target.read_text(encoding='utf-8-sig') == content:
                continue
            temporary = target.with_suffix(target.suffix + '.tmp')
            temporary.write_text(content, encoding='utf-8', newline='\n')
            temporary.replace(target)
        print(f'Wrote {len(entries)} events and {sum(entry["games"] for entry in entries):,} games.')
    else:
        print(f'Validated {len(entries)} existing ZIPs and {len(pending)} new PGNs. Add --write to save.')


if __name__ == '__main__':
    main()
