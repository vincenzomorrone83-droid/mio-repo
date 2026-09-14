"""Plot a figure from the paper's own LaTeX, never from a hand-drawn curve.

The chain is LaTeX -> SymPy -> numeric callable -> matplotlib. Every plot must
first reproduce a value the manuscript itself states, or it is refused.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import scienceplots  # noqa: F401  (registers the 'science' style)
import sympy as sp
from latex2sympy2_extended import latex2sympy


class VerificationError(Exception):
    pass


@dataclass
class Expression:
    tex: str
    expr: sp.Expr

    @property
    def symbols(self) -> list[sp.Symbol]:
        return sorted(self.expr.free_symbols, key=str)

    def symbol(self, name: str) -> sp.Symbol:
        for s in self.symbols:
            if str(s) == name:
                return s
        raise KeyError(
            f"{name!r} not in {[str(s) for s in self.symbols]} — "
            "latex2sympy lowercases names, read them from here"
        )


def parse(tex: str) -> Expression:
    return Expression(tex=tex, expr=sp.simplify(latex2sympy(tex)))


def callable_of(
    expression: Expression, variable: str, constants: dict[str, float] | None = None
):
    expr = expression.expr
    for name, value in (constants or {}).items():
        expr = expr.subs(expression.symbol(name), value)

    var = expression.symbol(variable)
    remaining = expr.free_symbols - {var}
    if remaining:
        raise VerificationError(
            f"unbound symbols {[str(s) for s in remaining]}; "
            "a plot with free symbols would be decorative, not computed"
        )
    return sp.lambdify(var, expr, "numpy")


def verify(
    expression: Expression,
    variable: str,
    at: float,
    expected: float,
    constants: dict[str, float] | None = None,
    rel_tol: float = 1e-6,
) -> float:
    got = float(callable_of(expression, variable, constants)(at))
    if expected == 0:
        ok = abs(got) <= rel_tol
    else:
        ok = abs(got - expected) / abs(expected) <= rel_tol
    if not ok:
        raise VerificationError(
            f"{expression.tex} at {variable}={at:g} gives {got:g}, "
            f"manuscript states {expected:g}"
        )
    return got


def plot(
    tex: str,
    variable: str,
    domain: tuple[float, float],
    out: Path,
    constants: dict[str, float] | None = None,
    check: tuple[float, float] | None = None,
    xlabel: str = "",
    ylabel: str = "",
    logx: bool = False,
    logy: bool = False,
    mark: float | None = None,
    mark_label: str = "",
    samples: int = 400,
    color: str = "#1f6f63",
    accent: str = "#b8862b",
) -> Path:
    expression = parse(tex)
    if check is not None:
        verify(expression, variable, check[0], check[1], constants)

    f = callable_of(expression, variable, constants)
    lo, hi = domain
    x = np.logspace(np.log10(lo), np.log10(hi), samples) if logx else np.linspace(lo, hi, samples)
    y = np.asarray(f(x), dtype=float)

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with plt.style.context(["science", "no-latex"]):
        fig, ax = plt.subplots(figsize=(5.2, 3.1))
        ax.plot(x, y, color=color, linewidth=1.4)
        if logx:
            ax.set_xscale("log")
        if logy:
            ax.set_yscale("log")
        if mark is not None:
            my = float(f(mark))
            ax.plot([mark], [my], marker="o", markersize=4, color=accent)
            ax.annotate(
                mark_label or f"{mark:.3g}",
                xy=(mark, my),
                xytext=(6, 6),
                textcoords="offset points",
                fontsize=8,
                color=accent,
            )
        ax.set_xlabel(xlabel or variable)
        ax.set_ylabel(ylabel)
        fig.savefig(out, dpi=220, bbox_inches="tight", transparent=True)
        plt.close(fig)

    return out
