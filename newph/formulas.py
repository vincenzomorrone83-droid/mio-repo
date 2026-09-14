"""Pull formula images out of a PDF so a math-OCR model can read them.

Papers written in word processors render every equation as a bitmap. Text
extractors return nothing usable for those, so the images have to be isolated
and OCR'd separately.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import pymupdf


@dataclass
class FormulaImage:
    page: int
    index: int
    width: int
    height: int
    file: str
    latex: str | None = None


def extract_formula_images(
    pdf: Path,
    out_dir: Path,
    min_width: int = 40,
    min_height: int = 12,
    max_aspect: float = 40.0,
    dpi: int = 200,
) -> list[FormulaImage]:
    pdf, out_dir = Path(pdf), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    found: list[FormulaImage] = []
    with pymupdf.open(pdf) as doc:
        for page_number, page in enumerate(doc, start=1):
            for index, info in enumerate(page.get_images(full=True)):
                xref = info[0]
                rects = page.get_image_rects(xref)
                if not rects:
                    continue

                # Equations are stored as stencil masks whose glyphs live in the
                # alpha channel; pulling the xref alone yields an all-black
                # bitmap. Rendering the page region composites over the page.
                pix = page.get_pixmap(clip=rects[0], dpi=dpi)
                if pix.width < min_width or pix.height < min_height:
                    continue
                if pix.height and pix.width / pix.height > max_aspect:
                    continue

                name = f"p{page_number:03d}-{index:02d}.png"
                pix.save(out_dir / name)
                found.append(
                    FormulaImage(
                        page=page_number,
                        index=index,
                        width=pix.width,
                        height=pix.height,
                        file=str(out_dir / name),
                    )
                )

    (out_dir / "formulas.json").write_text(
        json.dumps([asdict(f) for f in found], indent=2), encoding="utf-8"
    )
    return found


def ocr(images: list[FormulaImage]) -> list[FormulaImage]:
    """Fill in .latex using pix2tex. Requires the optional 'ocr' extra."""
    from PIL import Image
    from pix2tex.cli import LatexOCR

    model = LatexOCR()
    for item in images:
        item.latex = model(Image.open(item.file))
    return images
