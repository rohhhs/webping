#!/usr/bin/env python3
"""
list_output.py

List files under a directory (default: ./output), produce a JSON array of file paths,
and save to ./output_list.json (or another path you pass).

Usage examples:
  python list_output.py
  python list_output.py --root ./output --out ./output_list.json
  python list_output.py --root ./output --recursive False --include-dirs True
"""

from pathlib import Path
import json
import argparse
from typing import List


def list_files(
    root: Path,
    recursive: bool = True,
    include_dirs: bool = False,
    follow_symlinks: bool = False,
    return_relative: bool = True
) -> List[str]:
    """
    Return a list of file (and optionally directory) paths under `root`.

    Paths are returned as POSIX-style strings (forward slashes).
    If `return_relative` is True, returned paths are relative to `root`.
    """
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"Root path does not exist: {root}")

    results: List[str] = []
    if recursive:
        for p in root.rglob('*'):
            # Skip the root itself
            if p == root:
                continue
            try:
                is_dir = p.is_dir()
            except OSError:
                # If cannot stat the file for some reason, skip it
                continue

            if is_dir:
                if include_dirs:
                    path_str = p.relative_to(root).as_posix() if return_relative else p.resolve().as_posix()
                    results.append(path_str)
            else:
                # it's a file
                path_str = p.relative_to(root).as_posix() if return_relative else p.resolve().as_posix()
                results.append(path_str)
    else:
        # non-recursive: list only immediate children
        for p in sorted(root.iterdir()):
            try:
                is_dir = p.is_dir()
            except OSError:
                continue

            if is_dir:
                if include_dirs:
                    path_str = p.relative_to(root).as_posix() if return_relative else p.resolve().as_posix()
                    results.append(path_str)
            else:
                path_str = p.relative_to(root).as_posix() if return_relative else p.resolve().as_posix()
                results.append(path_str)

    return results


def save_json_list(items: List[str], out_path: Path, indent: int = 2):
    """
    Save list of strings to JSON file (overwrites if exists).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=indent)


def parse_bool(val: str) -> bool:
    v = val.lower()
    if v in ("1", "true", "t", "yes", "y", "on"):
        return True
    if v in ("0", "false", "f", "no", "n", "off"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


def main():
    parser = argparse.ArgumentParser(description="List files under a folder and write the list to JSON.")
    parser.add_argument("--root", "-r", type=Path, default=Path.cwd() / "output",
                        help="Root folder to list (default: ./output)")
    parser.add_argument("--out", "-o", type=Path, default=Path.cwd() / "output_list.json",
                        help="Output JSON file path (default: ./output_list.json)")
    parser.add_argument("--recursive", "-R", type=parse_bool, default=True,
                        help="Whether to walk recursively (True/False). Default: True")
    parser.add_argument("--include-dirs", "-d", action="store_true",
                        help="Include directories in the list (default: files only)")
    parser.add_argument("--absolute", "-a", action="store_true",
                        help="Return absolute paths instead of relative paths")
    parser.add_argument("--indent", type=int, default=2,
                        help="JSON indent level (default: 2)")

    args = parser.parse_args()

    try:
        items = list_files(
            root=args.root,
            recursive=args.recursive,
            include_dirs=args.include_dirs,
            follow_symlinks=False,
            return_relative=not args.absolute
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    save_json_list(items, args.out, indent=args.indent)
    print(f"Wrote {len(items)} entries to {args.out}")


if __name__ == "__main__":
    main()
