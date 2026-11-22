
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

WORK_START = time(9, 30)
WORK_END = time(18, 30)
LUNCH_START = time(13, 0)
LUNCH_END = time(14, 0)

SLOT_INTERVAL_MINUTES = 15
CLEANING_BUFFER_MINUTES = 15


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """True if two half-open time ranges overlap."""
    return a_start < b_end and b_start < a_end


def suggest_slots(
    requested_date: date,
    duration_minutes: int,
    room_bookings: list,
    attendee_bookings: list,
    is_intern: bool,
    is_board_room: bool,
) -> list[tuple[datetime, datetime]]:
    """Return the earliest three valid meeting slots for a room and participants."""

    # No meetings are suggested on weekends.
    if requested_date.weekday() >= 5:
        return []

    if is_intern and is_board_room:
        return []

    work_start = datetime.combine(requested_date, WORK_START)
    work_end = datetime.combine(requested_date, WORK_END)

    meeting_duration = timedelta(minutes=duration_minutes)
    cleaning_buffer = timedelta(minutes=CLEANING_BUFFER_MINUTES)

    suggestions = []
    candidate_start = work_start

    while candidate_start + meeting_duration <= work_end:
        candidate_end = candidate_start + meeting_duration

        # Meetings longer than 30 minutes cannot overlap lunch.
        if duration_minutes > 30:
            lunch_start = datetime.combine(requested_date, LUNCH_START)
            lunch_end = datetime.combine(requested_date, LUNCH_END)

            if overlaps(candidate_start, candidate_end, lunch_start, lunch_end):
                candidate_start += timedelta(minutes=SLOT_INTERVAL_MINUTES)
                continue

        # Room availability includes cleaning buffers after long meetings.
        candidate_blocked_end = candidate_end
        if duration_minutes > 60:
            candidate_blocked_end += cleaning_buffer

        room_conflict = False
        for booking in room_bookings:
            existing_blocked_end = booking.end

            if (booking.end - booking.start) > timedelta(minutes=60):
                existing_blocked_end += cleaning_buffer

            if overlaps(
                candidate_start,
                candidate_blocked_end,
                booking.start,
                existing_blocked_end,
            ):
                room_conflict = True
                break

        if room_conflict:
            candidate_start += timedelta(minutes=SLOT_INTERVAL_MINUTES)
            continue

        # Attendees are blocked only during the actual meeting, not cleaning.
        attendee_conflict = any(
            overlaps(candidate_start, candidate_end, booking.start, booking.end)
            for booking in attendee_bookings
        )

        if not attendee_conflict:
            suggestions.append(
                (
                    candidate_start.replace(tzinfo=IST),
                    candidate_end.replace(tzinfo=IST),
                )
            )

            if len(suggestions) == 3:
                break

        candidate_start += timedelta(minutes=SLOT_INTERVAL_MINUTES)

    return suggestions

