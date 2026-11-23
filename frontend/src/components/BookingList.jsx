
import { useEffect, useState } from "react";
import { getBookings } from "../api.js";
import { formatTime } from "../dates.js";

export default function BookingList({ date, refreshKey }) {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    setLoading(true);
    setError(null);

    getBookings(date)
      .then((data) => {
        if (active) {
          setBookings(data);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [date, refreshKey]);

  return (
    <section className="card">
      <h2>Bookings for {date}</h2>

      {loading && <p className="muted">Loading...</p>}

      {error && <p className="error">{error}</p>}

      {!loading && !error && bookings.length === 0 && (
        <p className="muted">No bookings.</p>
      )}

      {!loading && !error && bookings.length > 0 && (
        <table>
          <tbody>
            {bookings.map((booking) => (
              <tr key={booking.id}>
                <td className="time">
                  {formatTime(booking.start)}–
                  {formatTime(booking.end)}
                </td>

                <td>{booking.room.name}</td>

                <td>{booking.title}</td>

                <td className="muted">
                  {booking.attendees
                    .map((attendee) => attendee.name)
                    .join(", ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
