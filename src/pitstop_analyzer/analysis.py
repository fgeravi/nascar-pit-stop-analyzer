from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "vehicle_number",
    "driver_name",
    "vehicle_manufacturer",
    "leader_lap",
    "lap_count",
    "total_duration",
    "pit_stop_duration",
    "in_travel_duration",
    "out_travel_duration",
    "pit_stop_type",
    "positions_gained_lost",
}


def load_data(path: str | Path) -> pd.DataFrame:
    """Load pit-stop records from a JSON array and validate the schema."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("The JSON root must be an array of pit-stop records.")

    frame = pd.DataFrame(records)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    numeric_columns = [
        "leader_lap",
        "lap_count",
        "total_duration",
        "pit_stop_duration",
        "in_travel_duration",
        "out_travel_duration",
        "pit_in_rank",
        "pit_out_rank",
        "positions_gained_lost",
    ]
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["driver_name"] = (
        frame["driver_name"]
        .astype(str)
        .str.replace("#", "", regex=False)
        .str.strip()
    )
    frame["vehicle_number"] = frame["vehicle_number"].astype(str)

    # A valid completed stop needs a positive total duration and pit-out time.
    if "pit_out_race_time" in frame.columns:
        frame["completed_stop"] = (
            frame["total_duration"].gt(0) & frame["pit_out_race_time"].gt(0)
        )
    else:
        frame["completed_stop"] = frame["total_duration"].gt(0)

    frame["tire_count_changed"] = sum(
        frame.get(column, False).astype(bool).astype(int)
        for column in [
            "left_front_tire_changed",
            "left_rear_tire_changed",
            "right_front_tire_changed",
            "right_rear_tire_changed",
        ]
    )

    return frame


def completed_stops(frame: pd.DataFrame) -> pd.DataFrame:
    """Return completed pit stops only."""
    return frame.loc[frame["completed_stop"]].copy()


def overall_summary(frame: pd.DataFrame) -> dict[str, object]:
    """Create headline metrics for the dataset."""
    valid = completed_stops(frame)
    if valid.empty:
        return {
            "records": len(frame),
            "completed_stops": 0,
            "drivers": frame["driver_name"].nunique(),
            "manufacturers": frame["vehicle_manufacturer"].nunique(),
            "average_pit_stop_seconds": None,
            "median_pit_stop_seconds": None,
            "fastest_pit_stop_seconds": None,
            "fastest_driver": None,
        }

    fastest_index = valid["pit_stop_duration"].idxmin()
    fastest = valid.loc[fastest_index]
    return {
        "records": int(len(frame)),
        "completed_stops": int(len(valid)),
        "drivers": int(frame["driver_name"].nunique()),
        "manufacturers": int(frame["vehicle_manufacturer"].nunique()),
        "average_pit_stop_seconds": round(float(valid["pit_stop_duration"].mean()), 3),
        "median_pit_stop_seconds": round(float(valid["pit_stop_duration"].median()), 3),
        "fastest_pit_stop_seconds": round(float(fastest["pit_stop_duration"]), 3),
        "fastest_driver": str(fastest["driver_name"]),
    }


def driver_summary(frame: pd.DataFrame, minimum_stops: int = 1) -> pd.DataFrame:
    """Aggregate pit-stop performance by driver."""
    valid = completed_stops(frame)
    grouped = (
        valid.groupby(
            ["vehicle_number", "driver_name", "vehicle_manufacturer"],
            as_index=False,
        )
        .agg(
            stops=("pit_stop_duration", "size"),
            average_pit_stop=("pit_stop_duration", "mean"),
            median_pit_stop=("pit_stop_duration", "median"),
            fastest_pit_stop=("pit_stop_duration", "min"),
            average_total_lane_time=("total_duration", "mean"),
            net_positions=("positions_gained_lost", "sum"),
        )
    )
    grouped = grouped.loc[grouped["stops"] >= minimum_stops].copy()
    numeric = [
        "average_pit_stop",
        "median_pit_stop",
        "fastest_pit_stop",
        "average_total_lane_time",
    ]
    grouped[numeric] = grouped[numeric].round(3)
    return grouped.sort_values(["average_pit_stop", "stops"], ascending=[True, False])


def stop_type_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Compare performance by pit-stop type."""
    valid = completed_stops(frame)
    summary = (
        valid.groupby("pit_stop_type", as_index=False)
        .agg(
            stops=("pit_stop_duration", "size"),
            average_pit_stop=("pit_stop_duration", "mean"),
            median_pit_stop=("pit_stop_duration", "median"),
            fastest_pit_stop=("pit_stop_duration", "min"),
            average_positions=("positions_gained_lost", "mean"),
        )
        .sort_values("average_pit_stop")
    )
    summary[["average_pit_stop", "median_pit_stop", "fastest_pit_stop", "average_positions"]] = (
        summary[["average_pit_stop", "median_pit_stop", "fastest_pit_stop", "average_positions"]].round(3)
    )
    return summary


def detect_outliers(frame: pd.DataFrame, multiplier: float = 1.5) -> pd.DataFrame:
    """Detect unusually long pit stops using the IQR rule."""
    valid = completed_stops(frame)
    if valid.empty:
        return valid

    q1 = valid["pit_stop_duration"].quantile(0.25)
    q3 = valid["pit_stop_duration"].quantile(0.75)
    threshold = q3 + multiplier * (q3 - q1)

    columns = [
        "vehicle_number",
        "driver_name",
        "leader_lap",
        "pit_stop_type",
        "pit_stop_duration",
        "total_duration",
        "positions_gained_lost",
    ]
    return (
        valid.loc[valid["pit_stop_duration"] > threshold, columns]
        .sort_values("pit_stop_duration", ascending=False)
        .reset_index(drop=True)
    )
