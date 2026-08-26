#!/usr/bin/env python3

import argparse
from pathlib import Path


def find_duplicates(directory):
    """
    Find files ending with _1 before their extension.
    Examples:
        photo_1.jpg
        video_1.mp4
        document_1.pdf
    """
    for path in directory.rglob("*"):
        if not path.is_file():
            continue

        # Split filename into stem and extension
        # photo_1.jpg -> photo_1 + .jpg
        if path.stem.endswith("_1"):
            yield path


def main():
    parser = argparse.ArgumentParser(
        description="Find and optionally delete files ending with _1."
    )

    parser.add_argument(
        "directory",
        help="Directory/hard drive to search"
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete the files. Without this, only a preview is shown."
    )

    args = parser.parse_args()

    directory = Path(args.directory).expanduser().resolve()

    if not directory.exists():
        print(f"Error: directory does not exist: {directory}")
        return

    if not directory.is_dir():
        print(f"Error: not a directory: {directory}")
        return

    files = list(find_duplicates(directory))

    if not files:
        print("No files ending with _1 were found.")
        return

    print(f"Found {len(files)} files:\n")

    for file in files:
        print(f"  {file}")

    if not args.delete:
        print("\nDRY RUN — nothing was deleted.")
        print("If these are the files you want to remove, run:")
        print(f'  python3 {Path(__file__).name} "{directory}" --delete')
        return

    print("\nDeleting files...")

    deleted = 0
    failed = 0

    for file in files:
        try:
            file.unlink()
            print(f"Deleted: {file}")
            deleted += 1
        except Exception as e:
            print(f"FAILED: {file} ({e})")
            failed += 1

    print("\nDone.")
    print(f"Deleted: {deleted}")
    print(f"Failed:  {failed}")


if __name__ == "__main__":
    main()