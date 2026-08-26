# Delete Duplicates

A simple Python tool that recursively finds files ending in `_1` before the file extension and optionally deletes them.

### Usage

First, run it without `--delete` to preview what will be removed:

```bash
./delete_duplicates.py "/path/to/drive" "./delete _duplicates.py /run/media/user/drive_name"
```

If everything looks correct, delete the files with:

```bash
./delete_duplicates.py "/path/to/drive" --delete   "./delete _duplicates.py /run/media/user/drive_name --delete"
```

### Examples

Files like these will be detected:

```text
photo_1.jpg
video_1.mp4
document_1.pdf
```

The tool searches through all subdirectories.

**Important:** Always run the tool without `--delete` first and check the results before deleting anything.
