import csv
import io
import json
import logging
import os

import boto3

s3 = boto3.client("s3")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def read_text(filename):
    result = s3.get_object(
        Bucket=os.environ["ANALYTICS_BUCKET"],
        Key=f"analytics/output/{filename}",
    )
    return result["Body"].read().decode("utf-8-sig")


def read_csv(filename):
    return list(csv.DictReader(io.StringIO(read_text(filename))))


def lambda_handler(event, context):
    try:
        summary = json.loads(read_text("summary_metrics.json"))

        rooms = [
            {
                "room_id": row["room_id"],
                "reservation_count": int(row["reservation_count"]),
                "reserved_hours": float(row["reserved_hours"]),
            }
            for row in read_csv("reservations_by_room.csv")
        ]

        weekdays = [
            {
                "weekday": row["weekday"],
                "reservation_count": int(row["reservation_count"]),
            }
            for row in read_csv("reservations_by_weekday.csv")
        ]

        hours = [
            {
                "start_hour": int(row["start_hour"]),
                "reservation_count": int(row["reservation_count"]),
            }
            for row in read_csv("reservations_by_start_hour.csv")
        ]

        weekday_order = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday",
        ]
        weekdays.sort(key=lambda row: weekday_order.index(row["weekday"]))
        hours.sort(key=lambda row: row["start_hour"])
        rooms.sort(key=lambda row: -row["reservation_count"])

        result = {
            "source": "Historical reservation dataset; separate from live bookings",
            "summary": summary,
            "by_room": rooms,
            "by_weekday": weekdays,
            "by_start_hour": hours,
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result),
        }

    except Exception:
        logger.exception("Unable to load historical analytics")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Analytics temporarily unavailable"}),
        }
