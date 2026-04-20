#!/usr/bin/env python3
"""
migrate_ohm_names.py
--------------------
Renames directories and files inside an OHM-data folder so they match the
new naming convention introduced in the No-Individuals branch:

  OLD pattern:  <basename> - dg_<epoch>/
  NEW pattern:  <sanitized-basename>--dg_<epoch>/

Files *inside* each output directory are also passed through sanitize_filename
so any non-conforming filenames are fixed too.

Usage
-----
  # Preview all renames (safe, no changes made):
  python3 migrate_ohm_names.py

  # Preview a specific OHM-data path:
  python3 migrate_ohm_names.py /Volumes/Acasis1TB/OHM-data

  # Apply all renames:
  python3 migrate_ohm_names.py --apply

  # Apply to a specific path:
  python3 migrate_ohm_names.py --apply /Volumes/Acasis1TB/OHM-data
"""

import sys
import re
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Import sanitize_filename from the sibling common-DG-utilities repo
# ---------------------------------------------------------------------------
_cdu_path = Path(__file__).resolve().parent.parent / "common-DG-utilities"
if str(_cdu_path) not in sys.path:
    sys.path.insert(0, str(_cdu_path))

try:
    from common_dg_utilities.dg_utils import sanitize_filename
except ImportError as exc:
    sys.exit(
        f"ERROR: Could not import sanitize_filename from {_cdu_path}\n"
        f"  {exc}\n"
        "  Make sure the common-DG-utilities repo is checked out as a sibling of OHM."
    )

# ---------------------------------------------------------------------------
# Regex matching the OLD separator pattern:  <anything> - dg_<digits>
# ---------------------------------------------------------------------------
OLD_DIR_RE = re.compile(r"^(.*?) - (dg_\d+)$")
NEW_DIR_RE = re.compile(r"^(.+)--(dg_\d+)$")

# Files that follow the epoch-based scheme; confirming they are already clean.
KNOWN_EPOCH_FILE_RE = re.compile(r"^dg_\d+")


def candidate_ohm_data_paths() -> list[Path]:
    """Return a list of plausible OHM-data locations to check when none is given."""
    candidates = [
        Path.home() / "OHM-data",
    ]
    # Also check any mounted external volumes on macOS
    volumes = Path("/Volumes")
    if volumes.exists():
        for vol in volumes.iterdir():
            candidates.append(vol / "OHM-data")
    return [p for p in candidates if p.is_dir()]


def new_dir_name(old_name: str) -> str | None:
    """
    Given a directory name, return the corrected name, or None if already correct.

    Handles three cases (applied in sequence):
      1. Old-style separator  '<basename> - dg_<epoch>'  → sanitized + '--dg_<epoch>'
      2. Already-migrated but still has trailing '_' before '--':  'Foo_merged_--dg_<epoch>' → 'Foo_merged--dg_<epoch>'
      3. Lowercase '_merged' anywhere in the name  →  uppercase '_MERGED'
    """
    result = old_name

    # Case 1: old-style ' - dg_' separator
    m = OLD_DIR_RE.match(result)
    if m:
        basename_part, dg_part = m.group(1), m.group(2)
        result = f"{sanitize_filename(basename_part).rstrip('_')}--{dg_part}"
    else:
        # Case 2: already on new scheme but basename still ends in '_' before '--'
        m = NEW_DIR_RE.match(result)
        if m:
            basename_part, dg_part = m.group(1), m.group(2)
            result = f"{basename_part.rstrip('_')}--{dg_part}"

    # Case 3: lowercase _merged → uppercase _MERGED
    result = re.sub(r'_merged', r'_MERGED', result, flags=re.IGNORECASE)

    return result if result != old_name else None


def collect_renames(ohm_data: Path) -> list[tuple[Path, Path]]:
    """
    Walk ohm_data and return a list of (old_path, new_path) pairs for every
    item (directory or file) that needs renaming.

    Order matters: files inside a directory are listed before the directory
    rename so that when --apply is run we don't rename the parent first and
    lose the file paths.
    """
    renames: list[tuple[Path, Path]] = []

    for child in sorted(ohm_data.iterdir()):
        if not child.is_dir():
            continue

        proposed_dir_name = new_dir_name(child.name)
        if proposed_dir_name is None:
            # Not an old-style output directory — skip (logfiles, etc.)
            continue

        # ---------- files inside the output directory ----------
        for file in sorted(child.iterdir()):
            if not file.is_file():
                continue
            sanitized = sanitize_filename(file.name)
            sanitized = re.sub(r'_merged', r'_MERGED', sanitized, flags=re.IGNORECASE)
            if sanitized != file.name:
                renames.append((file, child / sanitized))

        # ---------- the directory itself ----------
        if proposed_dir_name != child.name:
            new_dir = ohm_data / proposed_dir_name
            renames.append((child, new_dir))

    return renames


def print_plan(renames: list[tuple[Path, Path]], ohm_data: Path):
    if not renames:
        print("  (nothing to rename — all names are already up to date)")
        return

    dirs = [(o, n) for o, n in renames if o.is_dir()]
    files = [(o, n) for o, n in renames if o.is_file()]

    if dirs:
        print(f"\n  Directories ({len(dirs)}):")
        for old, new in dirs:
            print(f"    {old.name}")
            print(f"    => {new.name}")
    if files:
        print(f"\n  Files ({len(files)}):")
        for old, new in files:
            print(f"    {old.relative_to(ohm_data)}")
            print(f"    => {new.relative_to(ohm_data)}")


def apply_renames(renames: list[tuple[Path, Path]]) -> tuple[int, int]:
    ok = 0
    errors = 0
    for old, new in renames:
        # On case-insensitive filesystems (macOS APFS default) a case-only
        # rename reports the target as already existing.  Detect this by
        # comparing lower-cased names and use a two-step rename via a temp
        # name to work around the limitation.
        case_only = new.exists() and old.name.lower() == new.name.lower()
        if new.exists() and not case_only:
            print(f"  SKIP (target already exists): {old.name} => {new.name}")
            errors += 1
            continue
        try:
            if case_only:
                tmp = old.parent / (old.name + "__dg_tmp")
                old.rename(tmp)
                tmp.rename(new)
            else:
                old.rename(new)
            print(f"  ✅ {old.name}")
            print(f"     => {new.name}")
            ok += 1
        except Exception as exc:
            print(f"  ❌ {old.name}: {exc}")
            errors += 1
    return ok, errors


def main():
    parser = argparse.ArgumentParser(
        description="Migrate OHM-data directory/file names to the sanitized naming scheme."
    )
    parser.add_argument(
        "ohm_data",
        nargs="?",
        help="Path to the OHM-data directory (auto-detected if omitted)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually perform the renames (default is dry-run / preview only)",
    )
    args = parser.parse_args()

    # ---- Resolve OHM-data path ----
    if args.ohm_data:
        targets = [Path(args.ohm_data)]
        if not targets[0].is_dir():
            sys.exit(f"ERROR: '{targets[0]}' is not a directory.")
    else:
        targets = candidate_ohm_data_paths()
        if not targets:
            sys.exit(
                "ERROR: Could not auto-detect an OHM-data directory.\n"
                "Pass the path explicitly:  python3 migrate_ohm_names.py /path/to/OHM-data"
            )

    mode = "APPLY" if args.apply else "DRY-RUN (preview only — use --apply to rename)"
    print(f"\n{'='*60}")
    print(f"  OHM name migration  [{mode}]")
    print(f"{'='*60}")

    total_ok = total_errors = 0

    for ohm_data in targets:
        print(f"\nOHM-data: {ohm_data}")
        renames = collect_renames(ohm_data)

        if not args.apply:
            print_plan(renames, ohm_data)
            if renames:
                print(f"\n  → {len(renames)} rename(s) pending. Run with --apply to execute.")
        else:
            if not renames:
                print("  (nothing to rename)")
            else:
                ok, errors = apply_renames(renames)
                total_ok += ok
                total_errors += errors

    if args.apply:
        print(f"\n{'='*60}")
        print(f"  Done: {total_ok} renamed, {total_errors} error(s)/skipped")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print("  Dry-run complete. No changes were made.")
        print("  Run with --apply to perform the renames.")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
