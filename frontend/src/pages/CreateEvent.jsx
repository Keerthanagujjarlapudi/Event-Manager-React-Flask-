import { useState } from "react";
import api from "../api";
import { getUser } from "../auth";

export default function CreateEvent() {
  const user = getUser();
  const [msg, setMsg] = useState("");
  const [status, setStatus] = useState(""); // success | error | idle

  const [form, setForm] = useState({
    title: "",
    description: "",
    date: "",
    published: false,
    schedule: [{ time: "10:00", item: "Opening" }],
  });

  if (user?.role !== "organizer") {
    return (
      <div className="container">
        <div className="card card-pad">
          <h2 className="title">Forbidden</h2>
          <p className="subtitle">Only organizers can create events.</p>
        </div>
      </div>
    );
  }

  function updateSchedule(index, key, value) {
    const copy = [...form.schedule];
    copy[index] = { ...copy[index], [key]: value };
    setForm({ ...form, schedule: copy });
  }

  async function submit(e) {
    e.preventDefault();
    setMsg("");
    setStatus("");

    try {
      await api.post("/events", form);
      setStatus("success");
      setMsg("Event created successfully");

      // Reset form
      setForm({
        title: "",
        description: "",
        date: "",
        published: false,
        schedule: [{ time: "10:00", item: "Opening" }],
      });
    } catch (e2) {
      setStatus("error");
      setMsg(e2?.response?.data?.error || "Failed to create event");
    }
  }

  const alertClass =
    status === "success"
      ? "alert alert-success"
      : status === "error"
      ? "alert alert-danger"
      : "alert";

  return (
    <div className="container">
      <div className="card card-pad" style={{ maxWidth: 900, margin: "0 auto" }}>
        <h2 className="title">Create Event</h2>
        <p className="subtitle">
          Organizers can create and publish events here.
        </p>

        <form onSubmit={submit} style={{ display: "grid", gap: 14 }}>
          <div className="row">
            <div style={{ flex: 1 }}>
              <div className="label">Event Title</div>
              <input
                className="input"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Tech Conference 2025"
              />
            </div>

            <div style={{ width: 220 }}>
              <div className="label">Date</div>
              <input
                className="input"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
                placeholder="YYYY-MM-DD"
              />
            </div>
          </div>

          <div>
            <div className="label">Description</div>
            <textarea
              className="textarea"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Describe the event..."
            />
          </div>

          <label className="row" style={{ color: "var(--muted)" }}>
            <input
              type="checkbox"
              checked={form.published}
              onChange={(e) =>
                setForm({ ...form, published: e.target.checked })
              }
            />
            Published (visible to participants)
          </label>

          <div className="card card-pad" style={{ background: "rgba(255,255,255,0.02)" }}>
            <div className="space-between">
              <b>Schedule</b>
              <button
                type="button"
                className="btn"
                onClick={() =>
                  setForm({
                    ...form,
                    schedule: [...form.schedule, { time: "", item: "" }],
                  })
                }
              >
                Add Item
              </button>
            </div>

            <div style={{ display: "grid", gap: 10, marginTop: 10 }}>
              {form.schedule.map((s, i) => (
                <div key={i} className="row">
                  <input
                    className="input"
                    style={{ width: 140 }}
                    value={s.time}
                    onChange={(e) =>
                      updateSchedule(i, "time", e.target.value)
                    }
                    placeholder="10:00"
                  />
                  <input
                    className="input"
                    style={{ flex: 1 }}
                    value={s.item}
                    onChange={(e) =>
                      updateSchedule(i, "item", e.target.value)
                    }
                    placeholder="Opening keynote"
                  />
                  <button
                    type="button"
                    className="btn btn-danger"
                    onClick={() =>
                      setForm({
                        ...form,
                        schedule: form.schedule.filter((_, idx) => idx !== i),
                      })
                    }
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>

          <button className="btn btn-primary" type="submit">
            Create Event
          </button>

          {msg && <div className={alertClass}>{msg}</div>}
        </form>
      </div>
    </div>
  );
}
