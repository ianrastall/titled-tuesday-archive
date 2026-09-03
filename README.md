# titled-tuesday-archive
The files from Chesscom, renamed and sorted. The collection is published at
https://chessnerd.net/titled-tuesday-archive.html and is not complete.

## Data and naming

ZIPs live in year folders. Each contains one matching PGN, for example
`2024/titled-tuesday-2024-01-02a.zip` → `titled-tuesday-2024-01-02a.pgn`.
The suffix `a` means early and `b` means late. An absent suffix leaves the
session unspecified; it does not imply that early and late have been combined.

`tt_manifest.json` is the website's structured source. `tt_links.txt`,
`tt_events.txt`, and `tt_game_counts.txt` are generated compatibility exports.
All four come from the actual ZIP contents, with forward-slash download URLs.
Dates identify events, not the latest Date tag inside a downloaded game.
Counts include the game records in the PGN, including zero-move results.

## Add missing events later

Use Python 3.10 or newer. Preview selected new files first. For example, once a
September 8 PGN is available:

```powershell
python archive_metadata.py --import-pgn D:\chessnerd\tt\260908-titled-tuesday.pgn
```

Once that missing PGN is available, add `--write` to import it and regenerate
metadata. The importer preserves the source file and its PGN bytes, verifies the
ZIP, and refuses duplicate event dates/sessions. It supports these filename forms:

- `YYMMDD[a|b]-titled-tuesday.pgn`
- `titled-tuesday-YYYY-MM-DD[a|b].pgn`
- `YYYY-titled-tuesday-blitz-month-DD[-early|-late].pgn`

Multiple file paths can follow `--import-pgn`. To rebuild metadata without adding
PGNs, run `python archive_metadata.py --write`. Without `--write`, it only checks
and previews. `generate_tt_metadata.py` and `fix_tt_links.py` delegate to this
same workflow. Run tests with `python -m unittest test_archive_metadata`.

Publish the new ZIPs and metadata to this repository first. In Chess Nerd, run
`npm run sync:tt`, validate and commit the updated snapshot, then publish the site.
Each site deployment also refreshes the manifest automatically from this
repository's current commit.

## September 3, 2026 import

The 412 existing ZIPs were preserved. Added 32 event files for 2026: January 6
from `D:\chessnerd\tt`, 26 other files from
`D:\dev\proj\chessnerd\New folder`, and five July/August files from
`D:\dev\pgn\cc-events-new`. The duplicate January 6 export in the second folder
was not imported. Each added ZIP preserves its selected source PGN bytes.

The follow-up import added the newly supplied **July 14, July 21, and September 1,
2026** files from `D:\dev\pgn\cc-events-new` (6,259 games). The July 7 ZIP was
refreshed from that folder's newer export, preserving its 1,805 games while
updating source links and adding end timestamps. The supplied July 28 and four
August PGNs already matched their ZIPs byte for byte and were left as they were.

The archive now contains **447 events and 825,726 games**, including 35 event
files for 2026 through September 1. This describes the files present, not a claim
of complete game coverage.
