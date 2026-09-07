import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { getUser } from "../auth";

export default function Events() {
  const nav = useNavigate();
  const user = getUser();

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const [status, setStatus] = useState("");
  const [message, setMessage] = useState("");

  async function loadEvents() {
    setLoading(true);
    setStatus("");
    setMessage("");
    try {
      const res = await api.get("/events");
      setEvents(res.data || []);
    } catch (e) {
      setStatus("error");
      setMessage(e?.response?.data?.error || "Failed to load events");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEvents();
  }, []);

  const alertClass =
    status === "success"
      ? "alert alert-success"
      : status === "error"
      ? "alert alert-danger"
      : "alert";

  return (
    <div className="container">
      <div className="space-between">
        <div>
          <h2 className="title">Events</h2>
          <p className="subtitle">Browse events. Participants can register for published events.</p>
        </div>

        <button className="btn" onClick={loadEvents}>Refresh</button>
      </div>

      {message ? (
        <div style={{ marginBottom: 12 }} className={alertClass}>
          {message}
        </div>
      ) : null}

      {loading ? (
        <div className="card card-pad">Loading...</div>
      ) : events.length === 0 ? (
        <div className="card card-pad">No events yet.</div>
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {events.map((ev) => {
            const canRegister = user?.role === "participant" && ev.published;

            return (
              <div key={ev.id} className="card card-pad">
                <div className="space-between" style={{ alignItems: "flex-start" }}>
                  <div>
                    <h3 style={{ margin: 0 }}>{ev.title}</h3>
                    <div className="mono" style={{ marginTop: 6 }}>
                      {ev.date || "No date set"}
                    </div>
                  </div>

                  <span className="badge">Published: {String(ev.published)}</span>
                </div>

                {ev.description ? (
                  <p style={{ color: "var(--muted)", marginTop: 10 }}>{ev.description}</p>
                ) : null}

                {Array.isArray(ev.schedule) && ev.schedule.length > 0 ? (
                  <div style={{ marginTop: 12 }}>
                    <b>Schedule</b>
                    <ul style={{ margin: "8px 0 0 18px", color: "var(--muted)" }}>
                      {ev.schedule.map((s, idx) => (
                        <li key={idx}>{s.time} — {s.item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <div style={{ marginTop: 12 }} className="row">
                  {canRegister ? (
                    <button
                      className="btn btn-primary"
                      onClick={() => nav(`/checkout/${ev.id}`)}
                    >
                      Register
                    </button>
                  ) : (
                    <span className="mono">
                      {user?.role === "participant"
                        ? ev.published
                          ? "Ready to register"
                          : "Event not published"
                        : user
                        ? "Login as participant to register"
                        : "Login to register"}
                    </span>
                  )}

                  <span className="mono">Event ID: {ev.id}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
