import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { setAuth } from "../auth";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const nav = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setErr("");
    try {
      const res = await api.post("/auth/login", { email, password });
      setAuth(res.data);
      nav("/");
    } catch (e2) {
      setErr(e2?.response?.data?.error || "Login failed");
    }
  }

  return (
    <div className="container">
      <div className="card card-pad" style={{ maxWidth: 520, margin: "0 auto" }}>
        <h2 className="title">Login</h2>
        <p className="subtitle">Organizer/Volunteer must login to use Check-in.</p>

        <form onSubmit={submit} className="row" style={{ flexDirection: "column", alignItems: "stretch" }}>
          <input className="btn" style={{ textAlign: "left" }} placeholder="Email" value={email} onChange={(e)=>setEmail(e.target.value)} />
          <input className="btn" style={{ textAlign: "left" }} type="password" placeholder="Password" value={password} onChange={(e)=>setPassword(e.target.value)} />
          <button className="btn btn-primary" type="submit">Login</button>
          {err && <div className="alert alert-danger">{err}</div>}
        </form>
      </div>
    </div>
  );
}
