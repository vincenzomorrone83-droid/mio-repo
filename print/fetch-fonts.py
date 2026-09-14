"""Download the dossier's typefaces locally.

The headless browser that Paged.js drives cannot reach Google Fonts in every
environment, and Paged.js aborts the render on the missing stylesheet rather
than falling back. Fetching the faces once removes the network from the build.

Only the latin subsets are kept, and only the weights the stylesheet asks for:
requesting a weight that is not bundled makes the browser synthesise it, which
smears the glyphs.
"""

import re
import subprocess
import sys
from pathlib import Path

FAMILIES = (
    "PT+Serif:ital,wght@0,400;0,700;1,400"
    "&family=Spectral:ital,wght@0,300;0,600;1,300"
    "&family=IBM+Plex+Mono:wght@400;500"
)
URL = f"https://fonts.googleapis.com/css2?family={FAMILIES}&display=swap"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
SUBSETS = {"latin", "latin-ext"}


def main() -> None:
    here = Path(__file__).parent
    fonts = here / "fonts"
    fonts.mkdir(exist_ok=True)

    fetched = subprocess.run(
        ["curl", "-sS", "-A", UA, URL], capture_output=True, text=True, check=True
    ).stdout

    kept, subset = [], None
    for chunk in re.split(r"(/\*[^*]+\*/)", fetched):
        if chunk.startswith("/*"):
            subset = chunk.strip("/* ").strip()
        elif subset in SUBSETS and "@font-face" in chunk:
            kept.append(chunk)

    css = "\n".join(kept)
    urls = sorted(set(re.findall(r"https://fonts\.gstatic\.com/[^)]+\.woff2", css)))
    if not urls:
        sys.exit("no font files found in the stylesheet")

    for url in urls:
        name = url.rsplit("/", 1)[-1]
        target = fonts / name
        if not target.exists():
            subprocess.run(["curl", "-sS", "-o", str(target), url], check=True)
        css = css.replace(url, f"fonts/{name}")

    (here / "fonts.css").write_text(css)
    size = sum(f.stat().st_size for f in fonts.glob("*.woff2")) / 1024
    print(f"{css.count('@font-face')} faces, {len(urls)} files, {size:.0f} KB")


if __name__ == "__main__":
    main()
