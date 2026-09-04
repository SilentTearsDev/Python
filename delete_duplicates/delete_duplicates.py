#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path


def find_duplicates(directory):
    """Find files whose filename stem ends with '_1'."""
    for path in directory.rglob("*"):
        if path.is_file() and path.stem.endswith("_1"):
            yield path


def main():
    parser = argparse.ArgumentParser(
        prog="ddel",
        description="Find and delete files ending with _1 before their extension.",
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to search (default: current directory)",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List matching files without deleting anything",
    )
    mode.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Delete all matching files",
    )

    args = parser.parse_args()

    directory = Path(args.directory).expanduser().resolve()

    if not directory.exists():
        print(f"Error: directory does not exist: {directory}", file=sys.stderr)
        return 1

    if not directory.is_dir():
        print(f"Error: not a directory: {directory}", file=sys.stderr)
        return 1

    files = list(find_duplicates(directory))

    if not files:
        print("No files ending with _1 were found.")
        return 0

    if args.list:
        print(f"Found {len(files)} matching file(s):\n")
        for file in files:
            print(file)
        return 0

    # Force-delete mode
    print(f"About to delete {len(files)} file(s):")
    for file in files:
        print(f"  {file}")

    answer = input("\nContinue? [y/N] ").strip().lower()
    if answer not in {"y", "yes"}:
        print("Cancelled.")
        return 0

    deleted = 0
    failed = 0

    for file in files:
        try:
            file.unlink()
            print(f"Deleted: {file}")
            deleted += 1
        except OSError as exc:
            print(f"FAILED: {file} ({exc})", file=sys.stderr)
            failed += 1

    print("\nDone.")
    print(f"Deleted: {deleted}")
    print(f"Failed:  {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
