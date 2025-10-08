#!/usr/bin/env python3
"""
Batch convert files from ./input -> ./output preserving folder structure.
Uses Pillow for common image formats and can fall back to ffmpeg for other formats.

Example:
  python convert_to_webp.py                # uses ./input and ./output
  python convert_to_webp.py --input data/images --output out --width 800 --quality 85
  python convert_to_webp.py --input file.jpg --output out/file.webp
"""

import argparse
import subprocess
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import sys

# Defaults (you can change)
DEFAULT_INPUT = Path.cwd() / "input"
DEFAULT_OUTPUT = Path.cwd() / "output"
PIL_SUPPORTED = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

def ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def convert_with_pillow(src: Path, dst: Path, width: int | None, height: int | None, quality: int):
    try:
        with Image.open(src) as img:
            orig_w, orig_h = img.size
            # Auto-orient using EXIF if present
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            # Resize keeping aspect ratio if only one dimension supplied
            if width and height:
                new_size = (width, height)
                img = img.resize(new_size, Image.LANCZOS)
            elif width:
                new_h = int((width / orig_w) * orig_h)
                img = img.resize((width, new_h), Image.LANCZOS)
            elif height:
                new_w = int((height / orig_h) * orig_w)
                img = img.resize((new_w, height), Image.LANCZOS)

            # Handle animation (GIF)
            save_kwargs = {"format": "WEBP", "quality": quality}
            if getattr(img, "is_animated", False):
                # Preserve animation frames
                frames = []
                try:
                    for frame in ImageSequence.Iterator(img):
                        frames.append(frame.copy())
                    frames[0].save(dst, save_all=True, append_images=frames[1:], loop=0,
                                   duration=img.info.get("duration", 100), **save_kwargs)
                except Exception as e:
                    # fallback: save first frame only
                    frames[0].save(dst, **save_kwargs)
            else:
                img.save(dst, **save_kwargs)
        return True, None
    except UnidentifiedImageError:
        return False, "UnidentifiedImageError"
    except Exception as e:
        return False, str(e)

def convert_with_ffmpeg(src: Path, dst: Path, width: int | None, height: int | None, quality: int):
    if not ffmpeg_available():
        return False, "ffmpeg-not-found"
    cmd = ["ffmpeg", "-y", "-i", str(src)]
    # qscale for ffmpeg: lower is better quality for some encoders, but for libwebp use -q:v
    # We'll try with libwebp
    vf = None
    if width and height:
        vf = f"scale={width}:{height}"
    elif width:
        vf = f"scale={width}:-1"
    elif height:
        vf = f"scale=-1:{height}"
    if vf:
        cmd += ["-vf", vf]
    # Use libwebp encoder if available; fallback to generic
    cmd += ["-quality", str(quality), str(dst)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, None
    except subprocess.CalledProcessError as e:
        return False, str(e)

def ensure_parent(dst: Path):
    if not dst.parent.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)

def process_file(src: Path, dst: Path, width: int | None, height: int | None,
                 quality: int, skip_existing: bool, ffmpeg_fallback: bool):
    # Ensure dst extension is .webp
    dst = dst.with_suffix(".webp")
    ensure_parent(dst)

    if skip_existing and dst.exists():
        print(f"[skip] {dst} (exists)")
        return

    ext = src.suffix.lower()
    # If source is already webp and you want to copy or re-encode, we re-encode by default
    if ext in PIL_SUPPORTED:
        # use Pillow
        success, error = convert_with_pillow(src, dst, width, height, quality)
        if success:
            print(f"[pillow] {src} -> {dst}")
            return
        else:
            print(f"[pillow-fail] {src}: {error}")
            # fall through to ffmpeg if enabled
    # If not supported by Pillow or pillow failed, try ffmpeg fallback
    if ffmpeg_fallback:
        success, error = convert_with_ffmpeg(src, dst, width, height, quality)
        if success:
            print(f"[ffmpeg] {src} -> {dst}")
            return
        else:
            print(f"[ffmpeg-fail] {src}: {error}")
            return
    else:
        print(f"[skip] {src}: unsupported format and ffmpeg fallback disabled.")

def collect_sources(path: Path):
    if path.is_file():
        return [path]
    files = []
    for p in path.rglob("*"):
        if p.is_file():
            files.append(p)
    return files

def main():
    parser = argparse.ArgumentParser(description="Convert images to WebP preserving folder structure.")
    parser.add_argument("--input", "-i", type=Path, default=DEFAULT_INPUT,
                        help="Input file or folder (default: ./input)")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT,
                        help="Output folder (default: ./output)")
    parser.add_argument("--width", type=int, default=None, help="Target width (pixels)")
    parser.add_argument("--height", type=int, default=None, help="Target height (pixels)")
    parser.add_argument("--quality", type=int, default=60, help="Quality 0-100 (default: 90)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip files that already exist in output")
    parser.add_argument("--ffmpeg-fallback", action="store_true", help="Use ffmpeg when Pillow cannot handle the file")
    args = parser.parse_args()

    src_path: Path = args.input
    out_root: Path = args.output
    width = args.width
    height = args.height
    quality = args.quality
    skip_existing = args.skip_existing
    ffmpeg_fallback = args.ffmpeg_fallback

    # Validate
    if not src_path.exists():
        print(f"Input path does not exist: {src_path}", file=sys.stderr)
        sys.exit(2)

    # Create output root if missing
    out_root.mkdir(parents=True, exist_ok=True)

    sources = collect_sources(src_path)
    if not sources:
        print("No files found to process.")
        return

    for src in sources:
        # Compute relative path from input root; if single file input, use its name
        if src_path.is_dir():
            rel = src.relative_to(src_path)
        else:
            rel = src.name
        dst = out_root / rel
        process_file(src, dst, width, height, quality, skip_existing, ffmpeg_fallback)

if __name__ == "__main__":
    # Lazy imports used in functions
    from PIL import ImageSequence, ImageOps  # imported here to avoid top-level complexity
    main()
