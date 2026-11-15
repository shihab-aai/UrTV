#!/usr/bin/env python3
"""Install the pinned Noto fonts as local build inputs for UrTV."""

import argparse
import hashlib
import io
import os
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from fontTools.ttLib import TTFont

REPO = Path(__file__).resolve().parents[2]
URL = "https://github.com/notofonts/arabic/releases/download/NotoSansArabic-v2.013/NotoSansArabic-v2.013.zip"
SHA256 = "1301aceaea84c501cf2e6dcfb3182e2328c8eae5725817fcb239672bda7154f1"
# Existing asset names are part of the phone and screensaver page interfaces.
FACES = {
    "Light": "Thmanyah-Light",
    "Regular": "Thmanyah-Regular",
    "Medium": "Thmanyah-Medium",
    "Bold": "ThmanyahDisplay-Bold",
}


def write_asset(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        tmp.write(content)
        pending = Path(tmp.name)
    try:
        # Replace a legacy local alias without overwriting the font it points to.
        os.replace(pending, path)
    finally:
        pending.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", type=Path, nargs="*", help="checkout paths (default: this checkout)")
    args = parser.parse_args()
    roots = args.roots or [REPO]
    for root in roots:
        if not (root / "src/template.html").is_file():
            parser.error(f"{root} is not an UrTV checkout")

    with urllib.request.urlopen(URL, timeout=30) as response:
        archive = response.read(20_000_001)
    if hashlib.sha256(archive).hexdigest() != SHA256:
        raise SystemExit("Noto Sans Arabic archive failed its SHA-256 check.")
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        license_text = bundle.read("OFL.txt")
        for weight, alias in FACES.items():
            otf = bundle.read(f"NotoSansArabic/full/otf/NotoSansArabic-{weight}.otf")
            woff2 = io.BytesIO()
            with TTFont(io.BytesIO(otf), recalcTimestamp=False) as font:
                font.flavor = "woff2"
                font.save(woff2)
            for root in roots:
                write_asset(root / f"assets/fonts/{alias}.woff2", woff2.getvalue())
                write_asset(root / f"android/launcher/src/main/assets/fonts/{alias}.otf", otf)

    for root in roots:
        write_asset(root / "assets/fonts/NotoSansArabic-OFL.txt", license_text)
        # The screensaver merges both asset trees. Remove the old generated copy.
        (root / "android/launcher/src/main/assets/fonts/NotoSansArabic-OFL.txt").unlink(missing_ok=True)
    print(f"Installed Noto Sans Arabic v2.013 in {len(roots)} checkout(s).")


if __name__ == "__main__":
    main()
