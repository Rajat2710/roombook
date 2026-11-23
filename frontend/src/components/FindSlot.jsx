
import { useEffect, useState } from "react";
import {
  ApiError,
  createBooking,
  getRooms,
  getUsers,
  suggestSlots,
} from "../api.js";
import { formatTime } from "../dates.js";

export default function FindSlot({ date, onBooked }) {
  const [rooms, setRooms] = useState([]);
  const [users, setUsers] = useState([]);

  const [roomId, setRoomId] = useState("");
  const [requesterId, setRequesterId] = useState("");
  const [attendeeIds, setAttendeeIds] = useState([]);
  const [duration, setDuration] = useState("60");
  const [title, setTitle] = useState("");

  const [slots, setSlots] = useState([]);

  const [loadingData, setLoadingData] = useState(true);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [bookingSlot, setBookingSlot] = useState(null);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  // Load rooms and users when the component mounts.
  useEffect(() => {
    let active = true;

    async function loadFormData() {
      setLoadingData(true);
      setError("");

      try {
        const [roomData, userData] = await Promise.all([
          getRooms(),
          getUsers(),
        ]);

        if (!active) return;

        setRooms(roomData);
        setUsers(userData);

        if (roomData.length > 0) {
          setRoomId(String(roomData[0].id));
        }

        if (userData.length > 0) {
          setRequesterId(String(userData[0].id));
        }
      } catch (err) {
        if (active) {
          setError(err.message);
        }
      } finally {
        if (active) {
          setLoadingData(false);
        }
      }
    }

    loadFormData();

    return () => {
      active = false;
    };
  }, []);

  // Suggestions become stale whenever any search input changes.
  useEffect(() => {
    setSlots([]);
    setError("");
    setMessage("");
  }, [date, roomId, requesterId, attendeeIds, duration]);

  function toggleAttendee(userId) {
    setAttendeeIds((current) =>
      current.includes(userId)
        ? current.filter((id) => id !== userId)
        : [...current, userId]
    );
  }

  async function handleFindSlots(event) {
    event.preventDefault();

    setLoadingSlots(true);
    setSlots([]);
    setError("");
    setMessage("");

    try {
      const result = await suggestSlots(roomId, {
        requester_id: Number(requesterId),
        attendee_ids: attendeeIds,
        duration_minutes: Number(duration),
        date,
      });

      setSlots(result.slots);

      if (result.slots.length === 0) {
        setMessage("No available slots found for this date.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingSlots(false);
    }
  }

  async function handleBook(slot) {
    setBookingSlot(slot.start);
    setError("");
    setMessage("");

    try {
      await createBooking({
        room_id: Number(roomId),
        creator_id: Number(requesterId),
        attendee_ids: attendeeIds,
        title: title.trim() || "Room booking",
        start: slot.start,
        end: slot.end,
      });

      setSlots((current) =>
        current.filter((item) => item.start !== slot.start)
      );

      setMessage("Booking successful!");
      onBooked();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        // The slot was taken after suggestions were generated.
        setSlots([]);
        setError(
          "This slot was just booked by someone else. Please find slots again."
        );
      } else {
        setError(err.message);
      }
    } finally {
      setBookingSlot(null);
    }
  }

  if (loadingData) {
    return (
      <section className="card find-slot">
        <h2>Find a slot</h2>
        <p className="muted">Loading rooms and users...</p>
      </section>
    );
  }

  return (
    <section className="card find-slot">
      <h2>Find a slot</h2>

      <form onSubmit={handleFindSlots}>
        <label>
          Room
          <select
            value={roomId}
            onChange={(event) => setRoomId(event.target.value)}
            required
          >
            {rooms.map((room) => (
              <option key={room.id} value={room.id}>
                {room.name} ({room.capacity} seats)
              </option>
            ))}
          </select>
        </label>

        <label>
          Requester
          <select
            value={requesterId}
            onChange={(event) => setRequesterId(event.target.value)}
            required
          >
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.name} ({user.role})
              </option>
            ))}
          </select>
        </label>

        <label>
          Meeting title
          <input
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="e.g. Project discussion"
            maxLength={200}
          />
        </label>

        <label>
          Duration
          <select
            value={duration}
            onChange={(event) => setDuration(event.target.value)}
            required
          >
            {[15, 30, 45, 60, 75, 90, 120, 150, 180, 240].map(
              (minutes) => (
                <option key={minutes} value={minutes}>
                  {minutes} minutes
                </option>
              )
            )}
          </select>
        </label>

        <fieldset>
          <legend>Attendees</legend>

          {users
            .filter((user) => String(user.id) !== requesterId)
            .map((user) => (
              <label className="attendee-option" key={user.id}>
                <input
                  type="checkbox"
                  checked={attendeeIds.includes(user.id)}
                  onChange={() => toggleAttendee(user.id)}
                />
                {user.name}
              </label>
            ))}

          {users.length <= 1 && (
            <p className="muted">No additional attendees available.</p>
          )}
        </fieldset>

        <div className="selected-date">
          <strong>Selected date:</strong> {date}
        </div>

        <button
          type="submit"
          disabled={
            loadingSlots ||
            !roomId ||
            !requesterId ||
            rooms.length === 0 ||
            users.length === 0
          }
        >
          {loadingSlots ? "Finding slots..." : "Find available slots"}
        </button>
      </form>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {message && (
        <p className="success" role="status">
          {message}
        </p>
      )}

      {slots.length > 0 && (
        <div className="suggested-slots">
          <h3>Available slots</h3>

          <p className="muted">
            Showing the earliest available suggestions.
          </p>

          {slots.map((slot) => (
            <div className="slot" key={slot.start}>
              <span>
                {formatTime(slot.start)} – {formatTime(slot.end)}
              </span>

              <button
                type="button"
                disabled={bookingSlot !== null}
                onClick={() => handleBook(slot)}
              >
                {bookingSlot === slot.start ? "Booking..." : "Book"}
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
