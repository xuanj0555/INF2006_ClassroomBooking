# Roomly Data Dictionary

## 1. Project scope

Roomly provides campus room booking and reservation-demand analytics.

The project uses two separate categories of data:
- Live application records: users, rooms, bookings and participants.
- Historical reservation data: the cleaned Kaggle dataset used for analytics.

Historical reservations do not establish actual attendance or occupancy.
The project does not perform no-show prediction.

The tables below describe the proposed logical data model.
Their physical database implementation will be documented separately.

## 2. Users

Stores student and faculty accounts.

| Field | Type | Required | Description |
|---|---|---|---|
| user_id | Text | Yes | Primary key. Unique internal account identifier. |
| school_id | Text | Yes | School-issued identifier. Must be unique across accounts. |
| name | Text | Yes | User's display name. |
| role | Text | Yes | Allowed values: student, faculty. |
| is_active | Boolean | Yes | Whether the account may use the service. |

Notes:
- Confirm that school IDs are unique across students and faculty.
- Store school_id as text to preserve leading zeros and letters.
- Account status is maintained by an authorised administrator or
  school integration; alumni status is not automatically inferred.
- Being faculty does not automatically grant administrator permissions.
- Passwords are not stored in this table.
- Development and submitted samples use fictional identities.

## 3. Rooms

Stores rooms offered by Roomly.

| Field | Type | Required | Description |
|---|---|---|---|
| room_id | Text | Yes | Primary key. Unique room identifier. |
| name | Text | Yes | Room display name. |
| location | Text | Yes | Building, floor or location description. |
| capacity | Integer | Yes | Maximum participants, including the organiser. Must be greater than zero. |
| is_active | Boolean | Yes | Whether the room accepts new bookings. |

Room capacities and locations must come from a documented source
or be clearly labelled as fictional demonstration values.

Historical room identifiers do not automatically represent rooms
at our own campus.

## 4. Bookings

Stores reservations created through Roomly.

| Field | Type | Required | Description |
|---|---|---|---|
| booking_id | Text | Yes | Primary key. Unique reservation identifier. |
| organiser_id | Text | Yes | References Users.user_id. |
| room_id | Text | Yes | References Rooms.room_id. |
| start_time | Timestamp | Yes | Start of the reserved slot. |
| end_time | Timestamp | Yes | End of the reserved slot. |
| status | Text | Yes | Allowed values: confirmed, cancelled. |
| created_at | Timestamp | Yes | Time the application created the booking. |

Time convention:
- Application timestamps include a timezone offset or are stored in UTC.
- The interface displays booking times in Asia/Singapore.
- Each new application booking lasts one hour.
- Historical reservations retain their original durations.

## 5. BookingParticipants

Links every participant, including the organiser, to a booking.

| Field | Type | Required | Description |
|---|---|---|---|
| booking_id | Text | Yes | References Bookings.booking_id. Part of the composite primary key. |
| user_id | Text | Yes | References Users.user_id. Part of the composite primary key. |
| joined_at | Timestamp | Yes | Time the participant was added. |

The combination of booking_id and user_id must be unique.

The organiser must appear in this table for their booking.
Participant capacity and scheduling restrictions are documented
in src/booking_rules.md.

## 6. Historical reservation dataset

File: data/processed/reservations_cleaned.csv

Source:
https://www.kaggle.com/datasets/aceeedev/university-library-room-reservations

Inspected file:
- 51,319 reservation records.
- 46 distinct room identifiers.
- Reservation start dates from 6 January to 31 December 2024.

| Field | Type | Description |
|---|---|---|
| start_time | Date/time | Historical reservation start. Source timezone is not confirmed. |
| end_time | Date/time | Historical reservation end. |
| duration_minutes | Integer | Reservation duration in whole minutes. |
| room_id | Text | Historical room identifier. Preserve leading zeros and letters. |
| booking_date | Date | Date derived from start_time. This is the reservation date, not the booking creation date. |
| weekday | Text | Day of the week derived from start_time. |
| start_hour | Integer | Hour of start_time, from 0 to 23. |
| month | Integer | Month of start_time, from 1 to 12. |
| is_weekend | Boolean | True for Saturday or Sunday; otherwise false. |

The dictionary currently matches the supplied CSV.
If booking_date is renamed to reservation_date, update this document
and all scripts that read that column.

Known limitations:
- No user identities, participant lists or attendance outcomes.
- No booking creation timestamp or cancellation status.
- Nine dates within the covered interval have no reservation starts.
  Their meaning must be documented before filling daily counts with zero.
- Two records overlap earlier reservations for the same room identifier
  and require review.
- Some whole-minute durations differ from timestamp calculations by
  up to 30 seconds, consistent with rounding.
- Historical reservation durations range from 5 to 240 minutes.
- The source timezone and dataset licence must be documented.

## 7. Analytics definitions

- Reservation count: number of historical reservation records starting
  within the selected period.
- Reserved hours: sum of duration_minutes divided by 60, for records
  starting within the selected period.
- Average reservation duration: mean duration_minutes for the
  selected records.
- Peak reservation periods: hours or weekdays with the most
  reservation starts.

Reserved hours are summed reservation durations, not verified occupied
hours. Overlapping records may inflate totals and must be reviewed.

These metrics describe recorded reservations, not actual attendance,
physical occupancy or unsuccessful booking attempts.

Any forecasting extension must be evaluated on later dates excluded
from training and compared with a simple baseline.
