
import { useState } from "react";
import DateNav from "./components/DateNav.jsx";
import RoomList from "./components/RoomList.jsx";
import BookingList from "./components/BookingList.jsx";
import FindSlot from "./components/FindSlot.jsx";

const FIRST_SEEDED_DAY = "2026-12-07";

export default function App() {
  const [date, setDate] = useState(FIRST_SEEDED_DAY);
  const [refreshKey, setRefreshKey] = useState(0);

  function handleBooked() {
    setRefreshKey((current) => current + 1);
  }

  return (
    <main>
      <header>
        <h1>RoomBook</h1>

        <DateNav date={date} onChange={setDate} />
      </header>

      <FindSlot date={date} onBooked={handleBooked} />

      <div className="layout">
        <RoomList />

        <BookingList
          date={date}
          refreshKey={refreshKey}
        />
      </div>
    </main>
  );
}
