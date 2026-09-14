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


def callable_of2(
    expression: Expression,
    variables: tuple[str, str],
    constants: dict[str, float] | None = None,
):
    expr = expression.expr
    for name, value in (constants or {}).items():
        expr = expr.subs(expression.symbol(name), value)

    first, second = (expression.symbol(name) for name in variables)
    remaining = expr.free_symbols - {first, second}
    if remaining:
        raise VerificationError(
            f"unbound symbols {[str(s) for s in remaining]}; "
            "a surface with free symbols would be decorative, not computed"
        )
    return sp.lambdify((first, second), expr, "numpy")


def _locus(tex: str, value: float, solve_for: str, given: str):
    """Solve tex == value for one variable, as a callable of the other."""
    expression = parse(tex)
    target, free = expression.symbol(solve_for), expression.symbol(given)
    roots = sp.solve(sp.Eq(expression.expr, value), target)
    if not roots:
        raise VerificationError(f"cannot solve {tex} = {value:g} for {solve_for}")
    return sp.lambdify(free, roots[0], "numpy")


def surface(
    tex: str,
    variables: tuple[str, str],
    domains: tuple[tuple[float, float], tuple[float, float]],
    out: Path,
    constants: dict[str, float] | None = None,
    check: tuple[float, float, float] | None = None,
    labels: tuple[str, str, str] = ("", "", ""),
    mask: tuple[str, float] | None = None,
    ridge: tuple[str, float, str] | None = None,
    slices: int | None = None,
    samples: int = 220,
    view: tuple[float, float] = (26.0, -56.0),
    low: str = "#cfe0da",
    high: str = "#0f4038",
    accent: str = "#b8862b",
) -> Path:
    from matplotlib.colors import LinearSegmentedColormap

    expression = parse(tex)
    f = callable_of2(expression, variables, constants)

    if check is not None:
        at_x, at_y, expected = check
        got = float(f(at_x, at_y))
        if abs(got - expected) / abs(expected) > 1e-6:
            raise VerificationError(
                f"{tex} at ({variables[0]}={at_x:g}, {variables[1]}={at_y:g}) "
                f"gives {got:g}, manuscript implies {expected:g}"
            )

    (x_lo, x_hi), (y_lo, y_hi) = domains
    x = np.linspace(x_lo, x_hi, samples)
    y = np.linspace(y_lo, y_hi, samples)
    grid_x, grid_y = np.meshgrid(x, y)

    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.asarray(f(grid_x, grid_y), dtype=float)
    z[~np.isfinite(z)] = np.nan

    # Cut the surface on the algebraic condition, not on the value of z: a
    # threshold on z alone leaves a ragged edge of half-sampled cells.
    if mask is not None:
        mask_tex, mask_max = mask
        g = callable_of2(parse(mask_tex), variables, constants)
        with np.errstate(divide="ignore", invalid="ignore"):
            blocked = np.asarray(g(grid_x, grid_y), dtype=float) >= mask_max
        z[blocked] = np.nan

    cmap = LinearSegmentedColormap.from_list("newph", [low, high])
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with plt.style.context(["science", "no-latex"]):
        fig = plt.figure(figsize=(6.3, 4.1))
        ax = fig.add_subplot(projection="3d", computed_zorder=False)

        if slices:
            # One exact curve per value of the second variable. A filled mesh
            # rasterises a divergence into visible stripes; discrete curves do
            # not, and each one is the solution for a stated parameter value.
            levels = np.linspace(y_lo, y_hi, slices)
            for index, level in enumerate(levels):
                with np.errstate(divide="ignore", invalid="ignore"):
                    curve = np.asarray(f(x, np.full_like(x, level)), dtype=float)
                if mask is not None:
                    blocked_row = (
                        np.asarray(g(x, np.full_like(x, level)), dtype=float) >= mask[1]
                    )
                    curve[blocked_row] = np.nan
                curve[~np.isfinite(curve)] = np.nan
                shade = cmap(0.25 + 0.75 * index / max(1, slices - 1))
                ax.plot(
                    x, np.full_like(x, level), curve,
                    color=shade, linewidth=1.5, zorder=3 + index,
                )
        else:
            ax.plot_surface(
                grid_x, grid_y, z,
                cmap=cmap, linewidth=0, antialiased=True,
                rcount=samples, ccount=samples,
                vmin=1.0, vmax=np.nanpercentile(z, 99),
            )

        if ridge is not None:
            ridge_tex, ridge_value, ridge_label = ridge
            along = _locus(ridge_tex, ridge_value, variables[0], variables[1])
            ys = np.linspace(y_lo, y_hi, 200)
            xs = np.asarray(along(ys), dtype=float)
            inside = (xs >= x_lo) & (xs <= x_hi)
            floor = float(np.nanmin(z))
            ax.plot(xs[inside], ys[inside], np.full(inside.sum(), floor),
                    color=accent, linewidth=1.7, zorder=8)
            if inside.any():
                mid = inside.nonzero()[0][inside.sum() // 2]
                ax.text(float(xs[mid]), float(ys[mid]), floor, f"  {ridge_label}",
                        color=accent, fontsize=8.5, zorder=9)

        ax.set_xlabel(labels[0], fontsize=9, labelpad=4)
        ax.set_ylabel(labels[1], fontsize=9, labelpad=2)
        ax.set_zlabel(labels[2], fontsize=9, labelpad=2)
        ax.tick_params(labelsize=8, pad=1)
        ax.view_init(elev=view[0], azim=view[1])
        ax.set_box_aspect((1.45, 1.0, 0.8))
        ax.locator_params(axis="y", nbins=5)
        ax.locator_params(axis="z", nbins=5)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.pane.set_alpha(0.0)
            axis._axinfo["grid"].update(color="#b4b1a4", linewidth=0.35, linestyle="-")
            axis._axinfo["tick"]["inward_factor"] = 0.0
            axis._axinfo["tick"]["outward_factor"] = 0.15
        fig.savefig(out, dpi=230, bbox_inches="tight", transparent=True)
        plt.close(fig)

    return out


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
