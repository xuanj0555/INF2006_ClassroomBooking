from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = PROJECT_ROOT / "data" / "reservations.csv"
CLEANED_FILE = PROJECT_ROOT / "data" / "reservations_cleaned_newversion.csv"

MIN_DURATION_MINUTES = 5
MAX_DURATION_MINUTES = 240
EXPECTED_FINAL_ROWS = 51_319


def main():
    # Read room identifiers as text so values such as "033" retain
    # their leading zeros.
    raw = pd.read_csv(
        RAW_FILE,
        dtype={"room_number": "string"},
    )

    initial_rows = len(raw)
    working = raw.copy()
    exclusion_counts = {}

    # Parse the source timestamps.
    working["_start_time"] = pd.to_datetime(
        working["start_date"],
        errors="coerce",
    )
    working["_end_time"] = pd.to_datetime(
        working["end_date"],
        errors="coerce",
    )

    invalid_timestamp = (
        working["_start_time"].isna()
        | working["_end_time"].isna()
    )
    exclusion_counts["Invalid timestamps"] = int(
        invalid_timestamp.sum()
    )
    working = working.loc[~invalid_timestamp].copy()

    missing_room = (
        working["room_number"].isna()
        | working["room_number"].str.strip().eq("")
    )
    exclusion_counts["Missing room identifiers"] = int(
        missing_room.sum()
    )
    working = working.loc[~missing_room].copy()

    duplicate_rows = working.duplicated(
        subset=[
            "start_date",
            "end_date",
            "friendly_date",
            "duration",
            "room_number",
        ]
    )
    exclusion_counts["Exact duplicate rows"] = int(
        duplicate_rows.sum()
    )
    working = working.loc[~duplicate_rows].copy()

    # Use the timestamps as the authoritative duration source.
    working["_actual_duration_minutes"] = (
        working["_end_time"] - working["_start_time"]
    ).dt.total_seconds() / 60

    too_short = (
        working["_actual_duration_minutes"]
        < MIN_DURATION_MINUTES
    )
    exclusion_counts["Duration below 5 minutes"] = int(
        too_short.sum()
    )
    working = working.loc[~too_short].copy()

    too_long = (
        working["_actual_duration_minutes"]
        > MAX_DURATION_MINUTES
    )
    exclusion_counts["Duration above 240 minutes"] = int(
        too_long.sum()
    )
    working = working.loc[~too_long].copy()

    cleaned = pd.DataFrame(
        {
            "start_time": working["_start_time"].dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "end_time": working["_end_time"].dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "duration_minutes": (
                working["_actual_duration_minutes"]
                .round()
                .astype(int)
            ),
            "room_id": working["room_number"].str.strip(),
            "reservation_date": working[
                "_start_time"
            ].dt.strftime("%Y-%m-%d"),
            "weekday": working["_start_time"].dt.day_name(),
            "start_hour": working["_start_time"].dt.hour,
            "month": working["_start_time"].dt.month,
            "is_weekend": (
                working["_start_time"].dt.dayofweek >= 5
            ),
        }
    )

    total_excluded = sum(exclusion_counts.values())

    print(f"Raw rows: {initial_rows:,}")
    for rule, count in exclusion_counts.items():
        print(f"{rule}: {count:,}")
    print(f"Total excluded: {total_excluded:,}")
    print(f"Cleaned rows: {len(cleaned):,}")

    if len(cleaned) != EXPECTED_FINAL_ROWS:
        raise ValueError(
            "Unexpected final row count: "
            f"expected {EXPECTED_FINAL_ROWS:,}, "
            f"received {len(cleaned):,}"
        )

    CLEANED_FILE.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(
        CLEANED_FILE,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    print(f"PASS: cleaned dataset written to {CLEANED_FILE}")


if __name__ == "__main__":
    main()