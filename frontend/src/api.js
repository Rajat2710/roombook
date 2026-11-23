
const BASE = "/api";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, options) {
  const res = await fetch(BASE + path, options);

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : null;

    throw new ApiError(
      detail || `Request failed (${res.status})`,
      res.status
    );
  }

  return res.json();
}

export const getRooms = () => request("/rooms");

export const getUsers = () => request("/users");

export const getBookings = (date) =>
  request(`/bookings?date=${encodeURIComponent(date)}`);

export const createBooking = (booking) =>
  request("/bookings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(booking),
  });

export const suggestSlots = (roomId, data) =>
  request(`/rooms/${roomId}/suggest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
