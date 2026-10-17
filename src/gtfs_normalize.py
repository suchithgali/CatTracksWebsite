from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

from src.gtfs_loader import OFFICIAL_GTFS_DIR

NORMALIZED_DIR = OFFICIAL_GTFS_DIR.parent / "gtfs"
MIN_TRAVEL_TIME_SECONDS = 60
TWELVE_HOURS = 12 * 60 * 60
MAX_SEGMENT_SECONDS = 2 * 60 * 60


def time_to_seconds(value: str) -> int:
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def seconds_to_time(value: int) -> str:
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def normalize_trip(rows: pd.DataFrame, report: list[dict[str, str]]) -> pd.DataFrame:
    rows = rows.sort_values("stop_sequence").copy()
    previous_departure: int | None = None

    for index, row in rows.iterrows():
        arrival = time_to_seconds(row["arrival_time"])
        departure = time_to_seconds(row["departure_time"])
        if departure < arrival:
            departure = arrival

        if previous_departure is not None and arrival < previous_departure:
            original_arrival = arrival
            while arrival < previous_departure:
                arrival += TWELVE_HOURS
            if arrival - previous_departure > MAX_SEGMENT_SECONDS:
                arrival = previous_departure + MIN_TRAVEL_TIME_SECONDS
                correction = "monotonic_clamp"
            else:
                correction = "12_hour_rollover"
            departure = max(departure, arrival)
            report.append(
                {
                    "trip_id": str(row["trip_id"]),
                    "stop_id": str(row["stop_id"]),
                    "original_arrival": str(row["arrival_time"]),
                    "normalized_arrival": seconds_to_time(arrival),
                    "correction": correction,
                    "original_seconds": str(original_arrival),
                }
            )

        if departure < arrival:
            departure = arrival
        rows.at[index, "arrival_time"] = seconds_to_time(arrival)
        rows.at[index, "departure_time"] = seconds_to_time(departure)
        previous_departure = departure

    return rows


def normalize_feed(
    source_dir: Path = OFFICIAL_GTFS_DIR,
    output_dir: Path = NORMALIZED_DIR,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for source in source_dir.glob("*.txt"):
        shutil.copy2(source, output_dir / source.name)

    stop_times_path = source_dir / "stop_times.txt"
    stop_times = pd.read_csv(stop_times_path, dtype=str)
    corrections: list[dict[str, str]] = []
    normalized_groups = [
        normalize_trip(rows, corrections)
        for _, rows in stop_times.groupby("trip_id", sort=False)
    ]
    normalized = pd.concat(normalized_groups, ignore_index=True)
    normalized = normalized.sort_values(["trip_id", "stop_sequence"])
    normalized.to_csv(output_dir / "stop_times.txt", index=False)

    report = {
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "trips_processed": int(stop_times["trip_id"].nunique()),
        "segments_normalized": len(corrections),
        "corrections": corrections,
    }
    (output_dir / "validation_report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    result = normalize_feed()
    print(json.dumps({key: value for key, value in result.items() if key != "corrections"}, indent=2))
