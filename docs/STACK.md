# Stack

Every tool below was checked against its repository, not recalled from memory.
Notes marked **misurato** come from running it in this repo on a real 32-page
paper (`2505.0090v1`, exported from Google Docs).

## Stage 1 — Ingestion

| Tool | Role | Notes |
|---|---|---|
| [pymupdf4llm](https://github.com/pymupdf/pymupdf4llm) | PDF → Markdown for LLM reading | **misurato**: 8 s, ~105 k chars, all 14 headings found, no GPU. Installed here. |
| [PyMuPDF](https://github.com/pymupdf/pymupdf) | page count, embedded images | Page count read from the document itself — never from a preview or a caller's claim. |
| [pymupdf4llm-mcp](https://github.com/pymupdf/pymupdf4llm-mcp) | same, as an MCP server | Attach it and an assistant reads clean Markdown instead of page screenshots. |
| [MinerU](https://github.com/opendatalab/mineru) | heavy alternative, VLM+OCR, 109 languages | Formula recognition built in. Use when pymupdf4llm is not enough. |
| [Docling](https://github.com/docling-project/docling) | IBM Research converter, PDF/DOCX/PPTX → JSON/Markdown | Managed service also available. |
| [marker](https://github.com/VikParuchuri/marker) | PDF → Markdown + JSON, 38.9k stars | Tuned for books and scientific papers. |
| [GROBID](https://github.com/kermitt2/grobid) | title, **authors**, affiliations, references → XML/TEI | ~10.6 PDF/s. Runs as a Docker service; fixes the "author unknown" gap. |

## Stage 2 — Mathematics

A word-processor PDF stores each equation as a bitmap. **misurato**: this paper
holds **186 formula images and zero machine-readable equations**, so text
extraction returns `[?][?]` for every formula. OCR is mandatory, not optional.

| Tool | Role | Notes |
|---|---|---|
| [surya](https://github.com/datalab-to/surya) | full-page OCR with inline math | Surya 2 returns equations in `<math>` tags as KaTeX-compatible LaTeX. Supersedes [texify](https://github.com/VikParuchuri/texify), which is **deprecated**. |
| [LaTeX-OCR / pix2tex](https://github.com/lukas-blecher/LaTeX-OCR) | single formula image → LaTeX | MIT, ViT, runs on CPU. Used by `newph.formulas.ocr`. |
| [UniMERNet](https://github.com/opendatalab/UniMERNet) | formula recognition specialist | Ships the **CDM** metric: renders predicted and ground-truth LaTeX and matches them character by character — an automatic check, not trust. |
| [latex2sympy2_extended](https://github.com/huggingface/latex2sympy2_extended) | LaTeX → SymPy | ANTLR-based, more robust than SymPy's own parser. **Beware**: it lowercases symbol names (`N` → `n`), so read symbols off the parsed expression. |
| [SymPy](https://docs.sympy.org/latest/modules/parsing.html) | symbolic → numeric callable | `lambdify` turns the manuscript's own formula into a function. |

## Stage 3 — Figures

| Tool | Role |
|---|---|
| [SciencePlots](https://github.com/garrettj403/SciencePlots) | matplotlib styles that read as journal figures |
| [pgfplots](https://github.com/pgf-tikz/pgfplots) | `\addplot {expr}` — TeX samples the function itself at compile time |

## Stage 4 — Layout and output

| Tool | Role |
|---|---|
| [tufte-css](https://github.com/edwardtufte/tufte-css) | sidenotes, et-book, narrow measure |
| [gemini](https://github.com/anishathalye/gemini) | modern beamerposter theme, MIT |
| [Quarto](https://github.com/quarto-dev/quarto-cli) | one Markdown source → PDF, RevealJS slides, HTML |
| [Paged.js](https://github.com/pagedjs/pagedjs) + [pagedjs-cli](https://github.com/pagedjs/pagedjs-cli) | CSS Paged Media → print-ready PDF from HTML |

## What runs where

Installed and exercised in this repo: pymupdf4llm, PyMuPDF, SymPy,
latex2sympy2_extended, matplotlib, SciencePlots, pix2tex.

Needs its own service or a heavier host: GROBID (Docker + Java), surya and
MinerU (large models; CPU works via llama.cpp but slowly), Quarto and LaTeX
(system packages).
