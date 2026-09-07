import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { setAuth } from "../auth";

export default function Register() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "participant",
    phone: ""
  });
  const [err, setErr] = useState("");
  const nav = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setErr("");
    try {
      const res = await api.post("/auth/register", form);
      setAuth(res.data);
      nav("/");
    } catch (e2) {
      setErr(e2?.response?.data?.error || "Register failed");
    }
  }

  return (
    <div className="container">
      <div className="card card-pad" style={{ maxWidth: 640, margin: "0 auto" }}>
        <h2 className="title">Register</h2>

        <form onSubmit={submit} className="row" style={{ flexDirection: "column", alignItems: "stretch" }}>
          <input className="btn" style={{ textAlign: "left" }} placeholder="Name" value={form.name} onChange={(e)=>setForm({...form, name:e.target.value})} />
          <input className="btn" style={{ textAlign: "left" }} placeholder="Email" value={form.email} onChange={(e)=>setForm({...form, email:e.target.value})} />
          <input className="btn" style={{ textAlign: "left" }} placeholder="Phone (optional)" value={form.phone} onChange={(e)=>setForm({...form, phone:e.target.value})} />
          <input className="btn" style={{ textAlign: "left" }} type="password" placeholder="Password" value={form.password} onChange={(e)=>setForm({...form, password:e.target.value})} />

          <select className="btn" value={form.role} onChange={(e)=>setForm({...form, role:e.target.value})}>
            <option value="participant">participant</option>
            <option value="volunteer">volunteer</option>
            <option value="organizer">organizer</option>
          </select>

          <button className="btn btn-primary" type="submit">Create Account</button>
          {err && <div className="alert alert-danger">{err}</div>}
        </form>
      </div>
    </div>
  );
}
