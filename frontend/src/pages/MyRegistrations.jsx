import { useEffect, useState } from "react";
import api from "../api";
import { getUser } from "../auth";

export default function MyRegistrations() {
  const user = getUser();
  const [regs, setRegs] = useState([]);
  const [err, setErr] = useState("");

  if (user?.role !== "participant") {
    return (
      <div className="container">
        <div className="card card-pad">
          <h2 className="title">Forbidden</h2>
          <p className="subtitle">Only participants can view registrations.</p>
        </div>
      </div>
    );
  }

  useEffect(() => {
    api.get("/registrations/my")
      .then((res) => setRegs(res.data))
      .catch((e) => setErr(e?.response?.data?.error || "Failed to load"));
  }, []);

  return (
    <div className="container">
      <h2 className="title">My Registrations</h2>
      <p className="subtitle">Show this QR at the entry for check-in.</p>

      {err && <div className="alert alert-danger">{err}</div>}

      <div className="grid">
        {regs.map((r) => (
          <div key={r.id} className="card card-pad">
            <div className="kv">
              <b>Event ID</b><span className="mono">{r.event_id}</span>
              <b>Status</b><span className="badge">{r.status}</span>
            </div>

            {r.qr_image ? (
              <div style={{ marginTop: 12 }}>
                <img src={r.qr_image} alt="QR" className="qr" />
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
