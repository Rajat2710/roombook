Decisions and Trade-offs

Task 1: Back-to-Back Booking Fix

Assumption

Booking time intervals are treated as half-open intervals [start, end). The start time is inclusive, while the end time is exclusive.

Implementation

Updated the overlaps() function in backend/app/scheduling.py to use strict comparisons:

Two bookings that end and start at the same time are allowed.

Bookings with an actual time intersection are rejected.

Added a regression test in backend/tests/test_bookings.py to verify that consecutive bookings in the same room are accepted.

Trade-offs

Half-open intervals provide a natural way to support consecutive bookings without requiring an artificial gap between meetings.

Other Issues Identified

The booking creation endpoint checks room availability but does not check whether attendees have conflicting bookings in other rooms.

The availability check and database insert are separate operations. Concurrent requests could both pass the availability check before either booking is inserted.

The current schema validation removes timezone information rather than converting timestamps to the configured timezone.

Future Improvements

Add database-level protection against concurrent overlapping room bookings.

Validate attendee availability across all rooms.

Normalize and validate timestamps consistently using the Asia/Kolkata timezone.

AI Usage

AI assistance was used to understand the existing overlap logic, identify the boundary-condition bug, and develop a regression test. The implementation and test results were reviewed locally.




## Task 2: Find a slot API

### Assumptions
- The requester is included in the participant conflict checks, even if they are not included in `attendee_ids`.
- The intern restriction applies to the requester booking the Board Room. An intern attending a meeting booked by someone else does not independently prevent the booking.
- Cleaning buffers apply to room availability, not attendee availability.
- The 15-minute cleaning buffer is added after meetings longer than 60 minutes.

### Implementation and trade-offs
- Candidate slots are generated at 15-minute intervals, in chronological order, and the first three valid slots are returned.
- Existing room bookings and participant bookings are queried for the requested date.
- Participant conflicts include both booking creators and attendees.
- Timezone-aware IST datetimes are returned by the suggestion API.
- The implementation uses application-level availability checks. These checks alone do not prevent simultaneous booking requests; Task 3 will address that separately.

### Testing
- Added tests for duration validation, weekends, Board Room restrictions, lunch-hour rules, participant conflicts across rooms, and cleaning buffers.
- Verified the existing Task 1 back-to-back booking regression test still passes.
