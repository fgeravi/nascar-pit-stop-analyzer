from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import (
    detect_outliers,
    driver_consistency,
    driver_summary,
    load_data,
    overall_summary,
    stop_type_summary,
)
from .fetch import DEFAULT_FEED_URL, fetch_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze NASCAR pit-stop timing and position-change data."
    )
    parser.add_argument(
        "--data",
        default="data/pit_stops.json",
        help="Path to the source JSON array.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch", help="Download the NASCAR live pit-data feed.")
    fetch.add_argument("--url", default=DEFAULT_FEED_URL)
    fetch.add_argument("--output", default="data/live_pit_stops.json")
    subparsers.add_parser("summary", help="Print headline dataset metrics.")

    drivers = subparsers.add_parser("drivers", help="Rank drivers by pit-stop performance.")
    drivers.add_argument("--min-stops", type=int, default=2)
    drivers.add_argument("--top", type=int, default=15)

    subparsers.add_parser("types", help="Compare pit-stop types.")

    consistency = subparsers.add_parser(
        "consistency",
        help="Rank drivers by pit-stop consistency.",
    )
    consistency.add_argument("--min-stops", type=int, default=2)
    consistency.add_argument("--top", type=int, default=15)

    outliers = subparsers.add_parser("outliers", help="List unusually long stops.")
    outliers.add_argument("--multiplier", type=float, default=1.5)
    outliers.add_argument("--top", type=int, default=20)

    export = subparsers.add_parser("export", help="Write CSV reports and PNG charts.")
    export.add_argument("--output", default="outputs")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "fetch":
        path = fetch_json(args.url, args.output)
        print(f"Downloaded feed to {path}")
        return

    frame = load_data(args.data)

    if args.command == "summary":
        print(json.dumps(overall_summary(frame), indent=2))
        return

    if args.command == "drivers":
        result = driver_summary(frame, minimum_stops=args.min_stops).head(args.top)
        print(result.to_string(index=False))
        return

    if args.command == "types":
        print(stop_type_summary(frame).to_string(index=False))
        return

    if args.command == "consistency":
        result = driver_consistency(
            frame,
            minimum_stops=args.min_stops,
        ).head(args.top)
        print(result.to_string(index=False))
        return

    if args.command == "outliers":
        result = detect_outliers(frame, multiplier=args.multiplier).head(args.top)
        print(result.to_string(index=False))
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    drivers_path = output_dir / "driver_summary.csv"
    types_path = output_dir / "stop_type_summary.csv"
    outliers_path = output_dir / "pit_stop_outliers.csv"
    consistency_path = output_dir / "driver_consistency.csv"
    summary_path = output_dir / "summary.json"

    driver_summary(frame).to_csv(drivers_path, index=False)
    stop_type_summary(frame).to_csv(types_path, index=False)
    detect_outliers(frame).to_csv(outliers_path, index=False)
    driver_consistency(frame).to_csv(consistency_path, index=False)
    summary_path.write_text(
        json.dumps(overall_summary(frame), indent=2), encoding="utf-8"
    )
    from .charts import create_charts

    chart_paths = create_charts(frame, output_dir)

    print(f"Created {drivers_path}")
    print(f"Created {types_path}")
    print(f"Created {outliers_path}")
    print(f"Created {consistency_path}")
    print(f"Created {summary_path}")
    for path in chart_paths:
        print(f"Created {path}")


if __name__ == "__main__":
    main()
