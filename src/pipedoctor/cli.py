"""PipeDoctor command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from pipedoctor import diagnose


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pipedoctor")
    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser("demo", help="run a small Pandas demo")
    demo_parser.add_argument("--format", choices=["text", "json", "markdown", "html"], default="text")
    demo_parser.add_argument("--output")

    csv_parser = subparsers.add_parser("csv", help="diagnose a CSV file with Pandas")
    csv_parser.add_argument("path")
    csv_parser.add_argument("--previous")
    csv_parser.add_argument("--key", action="append", default=[])
    csv_parser.add_argument("--critical", action="append", default=[])
    csv_parser.add_argument("--cdc-order-column")
    csv_parser.add_argument("--format", choices=["text", "json", "markdown", "html"], default="text")
    csv_parser.add_argument("--output")

    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "demo":
        report = _demo(show=args.format == "text")
        _emit(report, args.format, args.output)
        return 0
    if args.command == "csv":
        report = _csv(args)
        _emit(report, args.format, args.output)
        return 0
    parser.print_help()
    return 1


def _csv(args: argparse.Namespace):
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit("Install pandas support with: pip install 'pipedoctor[pandas]'") from exc

    df = pd.read_csv(args.path)
    previous = pd.read_csv(args.previous) if args.previous else None
    return diagnose(
        df,
        name=Path(args.path).name,
        previous=previous,
        key_columns=args.key,
        critical_columns=args.critical,
        cdc_order_column=args.cdc_order_column,
        show=args.format == "text",
    )


def _demo(show: bool):
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit("Install pandas support with: pip install 'pipedoctor[pandas]'") from exc

    df = pd.DataFrame(
        {
            "customer_id": [1, 1, 2, None, None, None, 4, 5],
            "country": ["US", "US", "US", "US", "US", "IN", "UK", "US"],
            "amount": [10, 10, 20, 9999, 18, 17, 16, 15],
            "event_time": pd.to_datetime(
                [
                    "2026-05-01 10:00",
                    "2026-05-01 10:00",
                    "2026-05-01 10:01",
                    "2026-05-01 09:58",
                    "2026-05-01 10:04",
                    "2026-05-01 10:05",
                    "2026-05-01 10:06",
                    "2026-05-01 10:07",
                ]
            ),
        }
    )
    return diagnose(
        df,
        name="demo_orders",
        key_columns=["customer_id"],
        critical_columns=["customer_id"],
        cdc_order_column="event_time",
        show=show,
    )


def _emit(report, fmt: str, output: str | None) -> None:
    if fmt == "text":
        if output:
            report.to_markdown(output)
        return
    if fmt == "json":
        text = report.to_json(output)
    elif fmt == "markdown":
        text = report.to_markdown(output)
    else:
        text = report.to_html(output)
    if not output:
        print(text)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
