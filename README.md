# N.E.W. — concept visualization pipeline

Turns a paper into a legible, well-set dossier. It does not review the
paper, validate it, or improve its argument: every output carries a notice
saying so.

The pipeline exists to remove two failure modes that come from doing this by
hand: reading a paper partially, and drawing a figure that looks like the
paper's data without being computed from it.

## Install

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Papers whose equations are images (anything exported from Google Docs or Word)
also need the OCR extra, which pulls in torch:

```sh
.venv/bin/pip install -r requirements-ocr.txt
```

## Read a paper

```sh
.venv/bin/python -m newph extract paper.pdf -o build/paper
```

Writes `paper.md`, `paper.json` and `figures/`. The page count comes from the
document itself, so a partial read is visible rather than silent:

```
pages      32
words      15889
headers    14
equations  0
```

`equations 0` on a 32-page physics paper means the formulas are bitmaps. Isolate
and OCR them:

```python
from newph.formulas import extract_formula_images, ocr

images = extract_formula_images("paper.pdf", "build/paper/formulas")
images = ocr(images)          # fills .latex via pix2tex
```

## Draw a figure from the paper's own formula

A figure is computed from the LaTeX, and refused unless it first reproduces a
number the manuscript states:

```sh
.venv/bin/python -m newph plot '\frac{1}{N} \cdot m^{4}' \
  --var n --domain 1e100:1e140 --const m=1 \
  --check 1e123:1e-123 \
  --logx --logy --mark 1e123 --mark-label 'N_H ~ 10^123' \
  --xlabel 'horizon-volume events N_H' --ylabel 'rho_Lambda / m_P^4' \
  -o build/paper/figures/fig-dark-energy.png
```

`--check at:expected` is the guard. Give it a value the paper does not support
and nothing is drawn:

```
refused: \frac{1}{N} \cdot m^{4} at n=1e+123 gives 1e-123, manuscript states 1e-60
```

Symbol names are read off the parsed expression, never assumed:
`latex2sympy` lowercases them, so `N` arrives as `n`.

## Layout

`docs/STACK.md` lists the verified tools for each stage, including what runs
locally and what needs its own service.
