import csv
import io
import json
import logging
import os

import boto3

s3 = None
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def read_text(filename):
    global s3
    if s3 is None:
        s3 = boto3.client("s3")
    result = s3.get_object(
        Bucket=os.environ["ANALYTICS_BUCKET"],
        Key=f"analytics/output/{filename}",
    )
    return result["Body"].read().decode("utf-8-sig")


def read_csv(filename):
    return list(csv.DictReader(io.StringIO(read_text(filename))))


def lambda_handler(event, context):
    try:
        denied = check_admin(event)
        if denied:
            return denied
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


def deny(status, code, message):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps({"code": code, "message": message}),
    }


def check_admin(event):
    # Trust only claims inserted by the API Gateway JWT authorizer.
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    issuer, subject = claims.get("iss"), claims.get("sub")
    if not issuer or not subject:
        return deny(401, "not_signed_in", "Verified authentication required.")
    expected = os.environ.get("AUTH_ISSUER")
    table_name = os.environ.get("USERS_TABLE")
    if not expected or not table_name:
        return deny(503, "auth_not_configured", "Analytics authorisation is not configured.")
    if issuer != expected:
        return deny(401, "wrong_issuer", "Invalid authentication issuer.")
    table = boto3.resource("dynamodb").Table(table_name)
    matches, options = [], {"ConsistentRead": True}
    while True:
        page = table.scan(**options)
        matches.extend(u for u in page.get("Items", [])
                       if u.get("auth_issuer") == issuer and u.get("auth_sub") == subject)
        if not page.get("LastEvaluatedKey"):
            break
        options["ExclusiveStartKey"] = page["LastEvaluatedKey"]
    if len(matches) != 1:
        return deny(403, "identity_unmapped", "Identity is not mapped to one account.")
    user = matches[0]
    if user.get("is_active") is not True:
        return deny(403, "account_inactive", "Your account is not active.")
    if user.get("is_admin") is not True:
        return deny(403, "not_allowed", "Administrator access required.")
    return None
