import pandas as pd

from pitstop_analyzer.analysis import (
    detect_outliers,
    driver_consistency,
    driver_summary,
    overall_summary,
)


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "vehicle_number": "1",
                "driver_name": "Driver A",
                "vehicle_manufacturer": "Ford",
                "leader_lap": 10,
                "pit_stop_type": "OTHER",
                "pit_stop_duration": 10.0,
                "total_duration": 65.0,
                "positions_gained_lost": 2,
                "completed_stop": True,
            },
            {
                "vehicle_number": "1",
                "driver_name": "Driver A",
                "vehicle_manufacturer": "Ford",
                "leader_lap": 20,
                "pit_stop_type": "TWO_WHEEL_CHANGE_RIGHT",
                "pit_stop_duration": 12.0,
                "total_duration": 67.0,
                "positions_gained_lost": -1,
                "completed_stop": True,
            },
            {
                "vehicle_number": "2",
                "driver_name": "Driver B",
                "vehicle_manufacturer": "Toyota",
                "leader_lap": 30,
                "pit_stop_type": "FOUR_WHEEL_CHANGE",
                "pit_stop_duration": 80.0,
                "total_duration": 130.0,
                "positions_gained_lost": -20,
                "completed_stop": True,
            },
        ]
    )


def test_overall_summary_finds_fastest_stop() -> None:
    summary = overall_summary(sample_frame())
    assert summary["fastest_pit_stop_seconds"] == 10.0
    assert summary["fastest_driver"] == "Driver A"


def test_driver_summary_aggregates_stops() -> None:
    result = driver_summary(sample_frame())
    driver_a = result.loc[result["driver_name"] == "Driver A"].iloc[0]
    assert driver_a["stops"] == 2
    assert driver_a["average_pit_stop"] == 11.0


def test_outlier_detector_returns_long_stop() -> None:
    result = detect_outliers(sample_frame(), multiplier=0.5)
    assert "Driver B" in result["driver_name"].tolist()



def test_driver_consistency_calculates_variation() -> None:
    result = driver_consistency(sample_frame(), minimum_stops=2)

    driver_a = result.loc[result["driver_name"] == "Driver A"].iloc[0]

    assert driver_a["stops"] == 2
    assert driver_a["pit_stop_std"] == 1.0
    assert driver_a["duration_range"] == 2.0
    assert driver_a["consistency_cv_percent"] == 9.091
