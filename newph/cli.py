from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .extract import extract, find_math
from .mathplot import VerificationError, plot


def _pair(text: str) -> tuple[str, float]:
    name, _, value = text.partition("=")
    return name.strip(), float(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="newph")
    sub = parser.add_subparsers(dest="command", required=True)

    ex = sub.add_parser("extract", help="PDF -> markdown + figures + metadata")
    ex.add_argument("pdf", type=Path)
    ex.add_argument("-o", "--out", type=Path, default=Path("build"))

    pl = sub.add_parser("plot", help="LaTeX formula -> verified computed figure")
    pl.add_argument("tex")
    pl.add_argument("--var", required=True)
    pl.add_argument("--domain", required=True, help="lo:hi")
    pl.add_argument("-o", "--out", type=Path, required=True)
    pl.add_argument("--const", action="append", default=[], help="name=value")
    pl.add_argument("--check", help="at:expected — the value the manuscript states")
    pl.add_argument("--xlabel", default="")
    pl.add_argument("--ylabel", default="")
    pl.add_argument("--logx", action="store_true")
    pl.add_argument("--logy", action="store_true")
    pl.add_argument("--mark", type=float)
    pl.add_argument("--mark-label", default="")

    args = parser.parse_args(argv)

    if args.command == "extract":
        paper, markdown = extract(args.pdf, args.out)
        equations = find_math(markdown)
        print(f"pages      {paper.pages}")
        print(f"words      {paper.words}")
        print(f"headers    {len(paper.headers)}")
        print(f"equations  {len(equations)}")
        print(f"written    {args.out / 'paper.md'}")
        return 0

    lo, _, hi = args.domain.partition(":")
    check = None
    if args.check:
        at, _, expected = args.check.partition(":")
        check = (float(at), float(expected))

    try:
        out = plot(
            args.tex,
            variable=args.var,
            domain=(float(lo), float(hi)),
            out=args.out,
            constants=dict(_pair(c) for c in args.const),
            check=check,
            xlabel=args.xlabel,
            ylabel=args.ylabel,
            logx=args.logx,
            logy=args.logy,
            mark=args.mark,
            mark_label=args.mark_label,
        )
    except VerificationError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1

    print(f"written    {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
