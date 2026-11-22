from concurrent.futures import ThreadPoolExecutor

def test_list_bookings_for_date(client):
    res = client.get("/bookings", params={"date": "2026-12-07"})
    assert res.status_code == 200
    bookings = res.json()
    assert len(bookings) == 8
    starts = [b["start"] for b in bookings]
    assert starts == sorted(starts)


def test_list_bookings_for_room(client):
    res = client.get("/bookings", params={"date": "2026-12-07", "room_id": 3})
    assert [b["title"] for b in res.json()] == ["Standup sync", "Retro"]


def test_create_booking(client):
    res = client.post(
        "/bookings",
        json={
            "room_id": 3,
            "creator_id": 2,
            "title": "Pairing",
            "attendee_ids": [2, 6],
            "start": "2026-12-07T15:00:00",
            "end": "2026-12-07T15:30:00",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["room"]["name"] == "Huddle"
    assert {a["name"] for a in body["attendees"]} == {"Ben", "Farah"}


def test_overlapping_booking_is_rejected(client):
    res = client.post(
        "/bookings",
        json={
            "room_id": 1,
            "creator_id": 1,
            "attendee_ids": [1],
            "start": "2026-12-07T10:30:00",
            "end": "2026-12-07T11:00:00",
        },
    )
    assert res.status_code == 409


def test_end_must_be_after_start(client):
    res = client.post(
        "/bookings",
        json={
            "room_id": 1,
            "creator_id": 1,
            "start": "2026-12-07T11:00:00",
            "end": "2026-12-07T10:00:00",
        },
    )
    assert res.status_code == 422


def test_unknown_room(client):
    res = client.post(
        "/bookings",
        json={
            "room_id": 99,
            "creator_id": 1,
            "start": "2026-12-07T10:00:00",
            "end": "2026-12-07T11:00:00",
        },
    )
    assert res.status_code == 404


def test_unknown_attendee(client):
    res = client.post(
        "/bookings",
        json={
            "room_id": 3,
            "creator_id": 1,
            "attendee_ids": [42],
            "start": "2026-12-07T15:00:00",
            "end": "2026-12-07T15:30:00",
        },
    )
    assert res.status_code == 400


def test_back_to_back_bookings_are_allowed(client):
    first = client.post(
        "/bookings",
        json={
            "room_id": 1,
            "creator_id": 1,
            "attendee_ids": [1],
            "start": "2026-12-10T10:00:00",
            "end": "2026-12-10T11:00:00",
        },
    )
    assert first.status_code == 201

    second = client.post(
        "/bookings",
        json={
            "room_id": 1,
            "creator_id": 2,
            "attendee_ids": [2],
            "start": "2026-12-10T11:00:00",
            "end": "2026-12-10T12:00:00",
        },
    )
    assert second.status_code == 201



def test_concurrent_bookings_only_one_succeeds(client):
    payload = {
        "room_id": 2,
        "creator_id": 1,
        "attendee_ids": [1],
        "title": "Concurrent meeting",
        "start": "2026-12-15T10:00:00",
        "end": "2026-12-15T11:00:00",
    }

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(client.post, "/bookings", json=payload)
            for _ in range(2)
        ]

        responses = [future.result(timeout=15) for future in futures]

    status_codes = sorted(response.status_code for response in responses)

    assert status_codes == [201, 409]
