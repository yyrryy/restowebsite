#!/usr/bin/env python3
"""
Download product images from le-gout-knt-menu.json and save them
named after the product (slugified).

Usage:
    python3 download_images.py [path_to_json] [output_dir]

Defaults:
    path_to_json = le-gout-knt-menu.json (same folder as this script)
    output_dir   = images/
"""

import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Install it with:\n    pip install requests --break-system-packages")


def slugify(text: str) -> str:
    """Turn a product name into a safe, readable filename slug."""
    # Normalize accents (é -> e, œ -> oe handled manually, etc.)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "product"


def guess_extension(url: str, content_type: str = "") -> str:
    """Figure out a file extension from the URL path or the response content-type."""
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        return ext
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    if "gif" in content_type:
        return ".gif"
    return ".jpg"  # sensible default for this menu (most images are jpg)


def load_products(json_path: Path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    products = []
    for category in data.get("categories", []):
        cat_name = category.get("category", "uncategorized")
        for product in category.get("products", []):
            name = product.get("name", "unnamed")
            image = product.get("image")
            if image:
                products.append({"category": cat_name, "name": name, "image": image})
    return products


def download_images(json_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    products = load_products(json_path)

    print(f"Found {len(products)} products with images. Downloading to '{out_dir}'...\n")

    seen_names = {}  # dedupe filenames if two products share a slug
    ok, failed = 0, 0

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (image-downloader-script)"})

    for i, product in enumerate(products, 1):
        name = product["name"]
        url = product["image"]
        slug = slugify(name)

        # Avoid overwriting files when two products slugify to the same name
        count = seen_names.get(slug, 0)
        seen_names[slug] = count + 1
        suffix = f"-{count+1}" if count else ""

        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            ext = guess_extension(url, resp.headers.get("Content-Type", ""))
            filename = f"{slug}{suffix}{ext}"
            filepath = out_dir / filename

            with open(filepath, "wb") as f:
                f.write(resp.content)

            print(f"[{i}/{len(products)}] OK   {name!r} -> {filename}")
            ok += 1
        except Exception as e:
            print(f"[{i}/{len(products)}] FAIL {name!r} ({url}): {e}")
            failed += 1

    print(f"\nDone. {ok} downloaded, {failed} failed.")


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent

    json_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else script_dir / "le-gout-knt-menu.json"
    out_arg = Path(sys.argv[2]) if len(sys.argv) > 2 else script_dir / "images"

    if not json_arg.exists():
        sys.exit(f"JSON file not found: {json_arg}")

    download_images(json_arg, out_arg)