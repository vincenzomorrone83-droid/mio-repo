"""Turn the screen dossier into a print document for Paged.js.

Two things differ from the screen version. Source order: on screen a grid
places the margin notes, so they may sit anywhere in the markup; in a paginated
flow a float lands on whatever page its source position falls on, so each note
has to follow the paragraph that cites it. And resources: the headless browser
cannot reach Google Fonts here, and Paged.js aborts on the missing stylesheet,
so the faces are served from ./fonts.
"""

import re
import sys
from pathlib import Path

SOURCE = Path(
    "/tmp/claude-0/-home-user-mio-repo/4ff87785-14c6-550d-a142-552415bf70e2/scratchpad/minamoto-dossier.html"
)
ASIDE = re.compile(
    r'\s*<aside class="sidenote"><span class="n">(\d+)</span>.*?</aside>', re.DOTALL
)


def move_notes_to_their_references(html: str) -> tuple[str, int]:
    notes = {number: block for block, number in ((m.group(0), m.group(1)) for m in ASIDE.finditer(html))}
    if not notes:
        return html, 0

    html = ASIDE.sub("", html)

    moved = 0
    for number, block in notes.items():
        ref = f'<span class="sidenote-ref">{number}</span>'
        position = html.find(ref)
        if position == -1:
            print(f"  nota {number}: nessun riferimento trovato, lasciata fuori", file=sys.stderr)
            continue
        close = html.find("</p>", position)
        if close == -1:
            print(f"  nota {number}: paragrafo non chiuso", file=sys.stderr)
            continue
        cut = close + len("</p>")
        html = html[:cut] + "\n" + block.strip() + html[cut:]
        moved += 1
    return html, moved


def local_fonts(html: str) -> str:
    html = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", html)
    html = re.sub(
        r'<link href="https://fonts\.googleapis\.com[^"]*" rel="stylesheet">',
        '<link rel="stylesheet" href="fonts.css">',
        html,
    )
    if "fonts.googleapis.com" in html:
        raise SystemExit("a remote font reference survived; Paged.js would abort")
    return html


def main() -> None:
    src = SOURCE.read_text()
    src, moved = move_notes_to_their_references(src)
    print(f"note spostate accanto al loro riferimento: {moved}")
    src = local_fonts(src)

    head_end = src.index("</style>") + len("</style>")
    head, body = src[:head_end], src[head_end:]

    Path("print.html").write_text(
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        f"{head}\n<link rel=\"stylesheet\" href=\"print.css\">\n"
        "<style>*{box-sizing:border-box}body{margin:0}img{max-width:100%}</style>\n"
        f"</head>\n<body>\n{body}\n</body>\n</html>\n"
    )
    print("print.html scritto")


if __name__ == "__main__":
    main()
