from src.gtfs_normalize import normalize_feed


def test_normalized_feed_has_monotonic_trip_times(tmp_path):
    report = normalize_feed(output_dir=tmp_path)
    assert report["trips_processed"] == 242
    assert report["segments_normalized"] > 0

    import pandas as pd

    stop_times = pd.read_csv(tmp_path / "stop_times.txt", dtype=str)
    for _, rows in stop_times.groupby("trip_id"):
        times = [
            int(hour) * 3600 + int(minute) * 60 + int(second)
            for hour, minute, second in rows.sort_values("stop_sequence")[
                "departure_time"
            ].str.split(":")
        ]
        assert times == sorted(times)
