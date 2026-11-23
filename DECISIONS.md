# Decisions and Trade-offs

## Task 1: Back-to-Back Booking Fix

- **Assumption:** Booking intervals are half-open `[start, end)`, so a booking can start exactly when another ends.
- **Implementation:** Updated the `overlaps()` function to use strict comparisons and added a regression test.
- **Other issues identified:**
  - Attendee conflicts across different rooms were not checked. (High)
  - Concurrent requests could create double bookings. (High)
  - Datetime validation removed timezone information instead of consistently handling IST. (Medium)
- **AI usage:** Used ChatGPT to understand the overlap logic and develop the fix and test. Reviewed the implementation locally.

## Task 2: Find a Slot API

- **Assumptions:**
  - The requester is included in participant availability checks, even if not listed in `attendee_ids`.
  - The intern restriction applies to the requester booking the Board Room.
  - Cleaning buffers apply to room availability, not attendee availability.
- **Implementation:** Added `POST /rooms/{room_id}/suggest`. It checks room and participant availability, generates candidates at 15-minute intervals and returns the earliest three valid slots.
- **Trade-off:** Availability is calculated by querying existing bookings rather than maintaining a separate availability calendar.
- **Testing:** Added tests for lunch restrictions, cleaning buffers, participant conflicts, intern restrictions, weekends and invalid durations.
- **AI usage:** Used ChatGPT for implementation guidance and test-case development. Verified the behavior with pytest.

## Task 3: Prevent Concurrent Double Booking

- **Implementation:** Used PostgreSQL row-level locking (`SELECT FOR UPDATE`) on the room before checking availability and inserting a booking.
- **Trade-off:** Requests for the same room are serialized, even when their time slots do not overlap. This relies on PostgreSQL locking and does not provide equivalent protection with SQLite.
- **Limitation:** Concurrent attendee conflicts across different rooms are not fully prevented.
- **Testing:** Added a concurrency test verifying that one request succeeds and the other receives `409 Conflict`.
- **AI usage:** Used ChatGPT to understand and implement the locking approach, then verified it with PostgreSQL tests.

## Task 4: React UI

- **Implementation:** Added a form to select a room, requester, attendees, date and duration; display suggested slots; and book a slot with one click.
- Added loading, success and error states, and handling for slots taken by another user (`409 Conflict`).
- Previous suggestions are cleared when availability-related inputs change.
- The bookings calendar displays all bookings for the selected date, including creators and additional attendees.
- **Trade-off:** Used React component state and existing API endpoints instead of introducing a global state-management library or additional backend endpoints.
- **Testing:** Manually tested slot suggestions, booking, business rules, stale suggestions and concurrent booking attempts. Verified the frontend production build.

## Future Improvements

- Add automated frontend tests.
- Handle in-flight suggestion requests when search criteria change.
- Add attendee-level concurrency protection across different rooms.
- Add booking cancellation and editing.

## AI Usage

Used ChatGPT throughout the assignment for code understanding, implementation guidance, debugging and test planning. AI initially suggested using GET for the slot suggestion endpoint, but the assignment specifies POST. I corrected this after checking the requirements.
