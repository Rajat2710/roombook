
from datetime import datetime
from types import SimpleNamespace

from app.scheduling import suggest_slots


def test_returns_first_three_available_slots(client):
    response = client.post(
        "/rooms/1/suggest",
        json={
            "requester_id": 5,
            "attendee_ids": [],
            "duration_minutes": 30,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 200

    slots = response.json()["slots"]

    assert len(slots) == 3
    assert slots[0]["start"] == "2026-12-10T09:30:00+05:30"
    assert slots[0]["end"] == "2026-12-10T10:00:00+05:30"
    assert slots[1]["start"] == "2026-12-10T09:45:00+05:30"
    assert slots[2]["start"] == "2026-12-10T10:00:00+05:30"


def test_rejects_duration_not_multiple_of_15(client):
    response = client.post(
        "/rooms/1/suggest",
        json={
            "requester_id": 5,
            "attendee_ids": [],
            "duration_minutes": 40,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 422


def test_rejects_duration_outside_allowed_range(client):
    response = client.post(
        "/rooms/1/suggest",
        json={
            "requester_id": 5,
            "attendee_ids": [],
            "duration_minutes": 300,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 422


def test_returns_no_slots_on_weekend(client):
    response = client.post(
        "/rooms/1/suggest",
        json={
            "requester_id": 5,
            "attendee_ids": [],
            "duration_minutes": 30,
            "date": "2026-12-12",
        },
    )

    assert response.status_code == 200
    assert response.json()["slots"] == []


def test_intern_cannot_book_board_room(client):
    response = client.post(
        "/rooms/2/suggest",
        json={
            "requester_id": 4,
            "attendee_ids": [],
            "duration_minutes": 30,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 200
    assert response.json()["slots"] == []


def test_employee_can_get_board_room_suggestions(client):
    response = client.post(
        "/rooms/2/suggest",
        json={
            "requester_id": 5,
            "attendee_ids": [],
            "duration_minutes": 30,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 200
    assert len(response.json()["slots"]) == 3


def test_unknown_room_returns_404(client):
    response = client.post(
        "/rooms/99/suggest",
        json={
            "requester_id": 5,
            "attendee_ids": [],
            "duration_minutes": 30,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 404


def test_unknown_requester_returns_404(client):
    response = client.post(
        "/rooms/1/suggest",
        json={
            "requester_id": 99,
            "attendee_ids": [],
            "duration_minutes": 30,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 404


def test_unknown_attendee_returns_400(client):
    response = client.post(
        "/rooms/1/suggest",
        json={
            "requester_id": 5,
            "attendee_ids": [99],
            "duration_minutes": 30,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 400


def test_attendee_conflict_in_another_room_is_excluded(client):
    # User 1 is already booked in room 3 from 10:00 to 11:00.
    booking = client.post(
        "/bookings",
        json={
            "room_id": 3,
            "creator_id": 1,
            "attendee_ids": [1],
            "start": "2026-12-10T10:00:00",
            "end": "2026-12-10T11:00:00",
        },
    )
    assert booking.status_code == 201

    response = client.post(
        "/rooms/1/suggest",
        json={
            "requester_id": 5,
            "attendee_ids": [1],
            "duration_minutes": 30,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 200

    for slot in response.json()["slots"]:
        start = datetime.fromisoformat(slot["start"])
        end = datetime.fromisoformat(slot["end"])

        conflict_start = datetime.fromisoformat(
            "2026-12-10T10:00:00+05:30"
        )
        conflict_end = datetime.fromisoformat(
            "2026-12-10T11:00:00+05:30"
        )

        assert not (start < conflict_end and end > conflict_start)


def test_requester_creator_conflict_is_excluded(client):
    # User 1 created a booking in a different room.
    booking = client.post(
        "/bookings",
        json={
            "room_id": 3,
            "creator_id": 1,
            "attendee_ids": [],
            "start": "2026-12-10T10:00:00",
            "end": "2026-12-10T11:00:00",
        },
    )
    assert booking.status_code == 201

    # User 1 is the requester, even though they aren't in attendee_ids.
    response = client.post(
        "/rooms/1/suggest",
        json={
            "requester_id": 1,
            "attendee_ids": [],
            "duration_minutes": 30,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 200

    for slot in response.json()["slots"]:
        start = datetime.fromisoformat(slot["start"])
        end = datetime.fromisoformat(slot["end"])

        conflict_start = datetime.fromisoformat(
            "2026-12-10T10:00:00+05:30"
        )
        conflict_end = datetime.fromisoformat(
            "2026-12-10T11:00:00+05:30"
        )

        assert not (start < conflict_end and end > conflict_start)


def test_long_existing_booking_has_cleaning_buffer(client):
    # This booking ends at 11:15, but the room stays unavailable until 11:30.
    booking = client.post(
        "/bookings",
        json={
            "room_id": 1,
            "creator_id": 5,
            "attendee_ids": [5],
            "start": "2026-12-10T10:00:00",
            "end": "2026-12-10T11:15:00",
        },
    )
    assert booking.status_code == 201

    response = client.post(
        "/rooms/1/suggest",
        json={
            "requester_id": 2,
            "attendee_ids": [],
            "duration_minutes": 30,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 200

    slots = response.json()["slots"]
    slot_starts = [slot["start"] for slot in slots]

    assert "2026-12-10T11:30:00+05:30" in slot_starts

    blocked_start = datetime.fromisoformat(
        "2026-12-10T10:00:00+05:30"
    )
    blocked_end = datetime.fromisoformat(
        "2026-12-10T11:30:00+05:30"
    )

    for slot in slots:
        start = datetime.fromisoformat(slot["start"])
        end = datetime.fromisoformat(slot["end"])

        assert not (start < blocked_end and end > blocked_start)


def test_long_suggested_meeting_respects_its_own_cleaning_buffer(client):
    # Existing short booking starts at 10:45.
    booking = client.post(
        "/bookings",
        json={
            "room_id": 1,
            "creator_id": 5,
            "attendee_ids": [5],
            "start": "2026-12-10T10:45:00",
            "end": "2026-12-10T11:00:00",
        },
    )
    assert booking.status_code == 201

    response = client.post(
        "/rooms/1/suggest",
        json={
            "requester_id": 2,
            "attendee_ids": [],
            "duration_minutes": 75,
            "date": "2026-12-10",
        },
    )

    assert response.status_code == 200

    slots = response.json()["slots"]

    # 09:30–10:45 would need a buffer until 11:00,
    # which conflicts with the existing 10:45–11:00 booking.
    assert slots[0]["start"] == "2026-12-10T11:00:00+05:30"


def test_short_meeting_can_overlap_lunch_but_longer_one_cannot():
    requested_date = datetime.fromisoformat("2026-12-10").date()

    room_bookings = [
        SimpleNamespace(
            start=datetime(2026, 12, 10, 9, 30),
            end=datetime(2026, 12, 10, 12, 45),
        )
    ]

    short_slots = suggest_slots(
        requested_date=requested_date,
        duration_minutes=30,
        room_bookings=room_bookings,
        attendee_bookings=[],
        is_intern=False,
        is_board_room=False,
    )

    # A 30-minute meeting may start at 13:00, overlapping lunch.
    assert short_slots
    assert short_slots[0][0].time().isoformat() == "13:00:00"

    long_slots = suggest_slots(
        requested_date=requested_date,
        duration_minutes=45,
        room_bookings=room_bookings,
        attendee_bookings=[],
        is_intern=False,
        is_board_room=False,
    )

    # A 45-minute meeting cannot overlap lunch, so it starts at 14:00.
    assert long_slots
    assert long_slots[0][0].time().isoformat() == "14:00:00"
