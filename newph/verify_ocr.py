"""Triage OCR'd LaTeX before anyone reads it as if it were the paper's formula.

Math OCR gets symbols wrong often enough that its output cannot be published
unread: on the test paper, all four sampled formulas carried at least one error
(``\\frac{1}{2}`` read as ``\\frac{1}{\\mathcal{L}}``, ``=`` read as
``\\rightarrow``, a Dirac slash read as ``\\stackrel{\\cdot}{y}\\wedge``).

What this module does is cheap and reliable: reject LaTeX that is malformed or
that a renderer refuses. What it deliberately does not do is claim a formula is
*correct*. A pixel-overlap comparison between the rendered prediction and the
original crop was tried and dropped: it scored a hand-corrected Einstein
equation (0.062) no better than the wrong OCR of the same crop (0.063), because
glyph metrics and stroke weight dominate the measure. Deciding that two
formulas say the same thing needs character-level detection matching — the CDM
metric in https://github.com/opendatalab/UniMERNet/tree/main/cdm — or a human.
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


@dataclass
class Check:
    latex: str
    status: str  # "renderable" | "malformed" | "unrenderable"
    detail: str = ""

    @property
    def usable(self) -> bool:
        return self.status == "renderable"


def brace_balance(latex: str) -> tuple[bool, str]:
    depth = 0
    for i, ch in enumerate(latex):
        escaped = i > 0 and latex[i - 1] == "\\"
        if ch == "{" and not escaped:
            depth += 1
        elif ch == "}" and not escaped:
            depth -= 1
            if depth < 0:
                return False, f"closing brace without opener at char {i}"
    if depth:
        return False, f"{depth} unclosed brace(s)"
    for opener, closer in (("(", ")"), ("[", "]")):
        if latex.count(opener) != latex.count(closer):
            return False, f"unbalanced {opener}{closer}"
    return True, ""


def _reason(exc: Exception) -> str:
    # mathtext's ValueError starts with an empty line; the parse error follows.
    lines = [line.strip() for line in str(exc).splitlines() if line.strip()]
    for line in lines:
        if any(token in line for token in ("Exception", "Unknown", "Expected")):
            return line[:110]
    return f"{type(exc).__name__}: {lines[0][:100] if lines else 'no detail'}"


def check(latex: str) -> Check:
    balanced, why = brace_balance(latex)
    if not balanced:
        return Check(latex, "malformed", why)

    try:
        fig = plt.figure()
        fig.text(0, 0, f"${latex}$")
        fig.canvas.draw()
        plt.close(fig)
    except Exception as exc:
        plt.close("all")
        return Check(latex, "unrenderable", _reason(exc))

    return Check(latex, "renderable")


def triage(items) -> dict[str, list[Check]]:
    """Group formulas by whether they are fit to put in front of a reader."""
    groups: dict[str, list[Check]] = {
        "renderable": [],
        "malformed": [],
        "unrenderable": [],
    }
    for item in items:
        latex = item.latex if hasattr(item, "latex") else str(item)
        if not latex:
            continue
        result = check(latex)
        groups[result.status].append(result)
    return groups


def report(groups: dict[str, list[Check]]) -> str:
    lines = [
        f"renderable    {len(groups['renderable'])}",
        f"malformed     {len(groups['malformed'])}",
        f"unrenderable  {len(groups['unrenderable'])}",
        "",
        "Renderable means syntactically sound, not correct: every formula still",
        "needs CDM or a human before it is presented as the paper's own.",
    ]
    for status in ("malformed", "unrenderable"):
        for item in groups[status]:
            lines.append(f"  [{status}] {item.detail}")
            lines.append(f"            {item.latex[:80]}")
    return "\n".join(lines)
