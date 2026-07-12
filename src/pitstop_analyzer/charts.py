from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .analysis import completed_stops, driver_summary


def create_charts(frame: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    """Create two portfolio-ready PNG charts and return their paths."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    valid = completed_stops(frame)

    driver_data = (
        driver_summary(frame, minimum_stops=2)
        .head(12)
        .sort_values("average_pit_stop", ascending=False)
    )
    if not driver_data.empty:
        plt.figure(figsize=(11, 7))
        plt.barh(driver_data["driver_name"], driver_data["average_pit_stop"])
        plt.xlabel("Average stationary stop duration (seconds)")
        plt.ylabel("Driver")
        plt.title("Fastest Average Pit Stops — Drivers with 2+ Completed Stops")
        plt.tight_layout()
        path = destination / "driver_average_pit_stops.png"
        plt.savefig(path, dpi=180, bbox_inches="tight")
        plt.close()
        files.append(path)

    if not valid.empty:
        plot_data = valid.loc[
            valid["pit_stop_duration"].between(0, valid["pit_stop_duration"].quantile(0.95))
        ]
        plt.figure(figsize=(10, 7))
        plt.scatter(
            plot_data["pit_stop_duration"],
            plot_data["positions_gained_lost"],
            alpha=0.65,
        )
        plt.axhline(0, linewidth=1)
        plt.xlabel("Stationary stop duration (seconds)")
        plt.ylabel("Positions gained/lost")
        plt.title("Pit-Stop Duration vs. Position Change (Extreme 5% Excluded)")
        plt.tight_layout()
        path = destination / "duration_vs_positions.png"
        plt.savefig(path, dpi=180, bbox_inches="tight")
        plt.close()
        files.append(path)

    return files
