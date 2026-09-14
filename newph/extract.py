"""PDF ingestion: one pass, full document, authoritative page count."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import pymupdf
import pymupdf4llm


@dataclass
class Paper:
    path: str
    pages: int
    title_meta: str
    chars: int
    words: int
    headers: list[str]

    def as_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


def page_count(pdf: Path) -> int:
    with pymupdf.open(pdf) as doc:
        return doc.page_count


def extract(pdf: Path, out_dir: Path) -> tuple[Paper, str]:
    pdf, out_dir = Path(pdf), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with pymupdf.open(pdf) as doc:
        pages = doc.page_count
        title_meta = (doc.metadata or {}).get("title", "") or ""

    markdown = pymupdf4llm.to_markdown(
        str(pdf),
        show_progress=False,
        write_images=True,
        image_path=str(out_dir / "figures"),
        image_format="png",
    )

    headers = [
        line.strip() for line in markdown.splitlines() if line.startswith("#")
    ]

    paper = Paper(
        path=str(pdf),
        pages=pages,
        title_meta=title_meta,
        chars=len(markdown),
        words=len(markdown.split()),
        headers=headers,
    )

    (out_dir / "paper.md").write_text(markdown, encoding="utf-8")
    (out_dir / "paper.json").write_text(paper.as_json(), encoding="utf-8")
    return paper, markdown


DISPLAY_MATH = re.compile(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]", re.DOTALL)


def find_math(markdown: str) -> list[str]:
    found = []
    for a, b in DISPLAY_MATH.findall(markdown):
        tex = (a or b).strip()
        if tex:
            found.append(tex)
    return found
