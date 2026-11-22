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