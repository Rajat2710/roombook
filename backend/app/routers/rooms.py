from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Booking, Room, User
from ..scheduling import suggest_slots
from ..schemas import (
    RoomIn,
    RoomOut,
    SlotSuggestIn,
    SlotSuggestOut,
)

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    return db.scalars(select(Room).order_by(Room.id)).all()


@router.get("/{room_id}", response_model=RoomOut)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.get(Room, room_id)

    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    return room


@router.post("", response_model=RoomOut, status_code=201)
def create_room(payload: RoomIn, db: Session = Depends(get_db)):
    room = Room(name=payload.name, capacity=payload.capacity)
    db.add(room)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A room with that name already exists",
        )

    return room


@router.post("/{room_id}/suggest", response_model=SlotSuggestOut)
def suggest_room_slots(
    room_id: int,
    payload: SlotSuggestIn,
    db: Session = Depends(get_db),
):
    # 1. Validate the room.
    room = db.get(Room, room_id)

    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    # 2. Validate the requester.
    requester = db.get(User, payload.requester_id)

    if requester is None:
        raise HTTPException(status_code=404, detail="Requester not found")

    # 3. Include the requester in the list of participants.
    participant_ids = set(payload.attendee_ids)
    participant_ids.add(payload.requester_id)

    participants = db.scalars(
        select(User).where(User.id.in_(participant_ids))
    ).all()

    if len(participants) != len(participant_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more attendees do not exist",
        )

    # The Board Room restriction is based on the requester's role.
    is_intern = requester.role == "intern"
    is_board_room = room.name == "Board Room"

    # 4. Define the requested day's boundaries.
    day_start = datetime.combine(payload.date, time.min)
    day_end = day_start + timedelta(days=1)

    # 5. Fetch bookings already occupying this room on that date.
    room_bookings = db.scalars(
        select(Booking).where(
            Booking.room_id == room_id,
            Booking.start < day_end,
            Booking.end > day_start,
        )
    ).all()

    # 6. Fetch bookings where the requester or any attendee
    # is already involved, whether as creator or attendee.
    attendee_bookings = db.scalars(
        select(Booking).where(
            or_(
                Booking.creator_id.in_(participant_ids),
                Booking.attendees.any(User.id.in_(participant_ids)),
            ),
            Booking.start < day_end,
            Booking.end > day_start,
        )
    ).all()

    # 7. Generate the earliest valid slots.
    slots = suggest_slots(
        requested_date=payload.date,
        duration_minutes=payload.duration_minutes,
        room_bookings=room_bookings,
        attendee_bookings=attendee_bookings,
        is_intern=is_intern,
        is_board_room=is_board_room,
    )

    return {
        "slots": [
            {"start": start, "end": end}
            for start, end in slots
        ]
    }