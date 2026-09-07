import { useEffect, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import api from "../api";
import { getUser } from "../auth";

export default function CheckIn() {
  const user = getUser();

  const [cameraOn, setCameraOn] = useState(false);

  const [status, setStatus] = useState(""); 
  // checked_in | already_checked_in | not_registered | error | idle

  const [message, setMessage] = useState("");
  const [participant, setParticipant] = useState(null);

  const qrRef = useRef(null);
  const busyRef = useRef(false);

  if (!(user?.role === "organizer" || user?.role === "volunteer")) {
    return (
      <div className="container">
        <div className="card card-pad">
          <h2 className="title">Forbidden</h2>
          <p className="subtitle">Only organizers or volunteers can check people in.</p>
        </div>
      </div>
    );
  }

  useEffect(() => {
    // Create once
    qrRef.current = new Html5Qrcode("reader");

    // Cleanup
    return () => {
      stopCameraSafe();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function resetUI() {
    setStatus("idle");
    setMessage("");
    setParticipant(null);
  }

  async function stopCameraSafe() {
    const qr = qrRef.current;
    if (!qr) return;

    try {
      await qr.stop(); // works only if started
    } catch {}
    try {
      await qr.clear();
    } catch {}
    setCameraOn(false);
  }

  async function sendToBackend(qr_payload) {
    if (busyRef.current) return;
    busyRef.current = true;

    setStatus("idle");
    setMessage("Processing...");
    setParticipant(null);

    try {
      const res = await api.post("/checkin", { qr_payload });

      setStatus(res.data.status || "checked_in");
      setMessage(res.data.message || "Done");
      setParticipant(res.data.participant || null);
    } catch (e) {
      // If participant not registered, backend returns 404 with message
      const apiMsg = e?.response?.data?.message;
      const apiErr = e?.response?.data?.error;

      if (e?.response?.status === 404) {
        setStatus("not_registered");
        setMessage(apiMsg || "Participant is NOT registered for this event");
      } else {
        setStatus("error");
        setMessage(apiErr || apiMsg || "Check-in failed");
      }

      setParticipant(null);
    } finally {
      // Small cooldown so the same QR doesn't spam requests
      setTimeout(() => {
        busyRef.current = false;
      }, 1500);
    }
  }

  async function startCamera() {
    resetUI();
    const qr = qrRef.current;
    if (!qr) return;

    // If something was left running, stop first
    await stopCameraSafe();

    try {
      await qr.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        async (decodedText) => {
          await sendToBackend(decodedText);
        },
        () => {}
      );
      setCameraOn(true);
    } catch (e) {
      setStatus("error");
      setMessage("Camera start failed. Allow camera permission (mobile Chrome works best).");
      setCameraOn(false);
    }
  }

  async function stopCamera() {
    await stopCameraSafe();
  }

  async function handleUpload(e) {
    resetUI();

    const file = e.target.files?.[0];
    if (!file) return;

    // Stop camera so file scan doesn't conflict
    await stopCameraSafe();

    const qr = qrRef.current;
    if (!qr) return;

    try {
      // decode QR from image file
      const decodedText = await qr.scanFile(file, true);
      await sendToBackend(decodedText);
    } catch (err) {
      setStatus("error");
      setMessage("Could not read QR from uploaded image. Use a clearer screenshot/photo.");
      setParticipant(null);
    } finally {
      // allow uploading same file again
      e.target.value = "";
    }
  }

  const alertClass =
    status === "checked_in"
      ? "alert alert-success"
      : status === "already_checked_in"
      ? "alert"
      : status === "not_registered"
      ? "alert alert-danger"
      : status === "error"
      ? "alert alert-danger"
      : "alert";

  return (
    <div className="container">
      <h2 className="title">QR Check-in</h2>
      <p className="subtitle">Scan with camera OR upload QR image from phone gallery.</p>

      <div className="card card-pad">
        <div className="row" style={{ marginBottom: 12 }}>
          {!cameraOn ? (
            <button className="btn btn-primary" onClick={startCamera}>
              Start Camera
            </button>
          ) : (
            <button className="btn" onClick={stopCamera}>
              Stop Camera
            </button>
          )}

          <label className="btn" style={{ cursor: "pointer" }}>
            Upload QR Image
            <input
              type="file"
              accept="image/*"
              style={{ display: "none" }}
              onChange={handleUpload}
            />
          </label>

          <button className="btn" onClick={resetUI}>
            Clear
          </button>
        </div>

        <div id="reader" className="reader" />

        {message && (
          <div style={{ marginTop: 12 }} className={alertClass}>
            <b>Status:</b> {message}
          </div>
        )}

        {participant && (
          <div style={{ marginTop: 12 }} className="card card-pad">
            <div className="kv">
              <b>Name</b> <span>{participant.name || "-"}</span>
              <b>Email</b> <span className="mono">{participant.email || "-"}</span>
              <b>Event</b>{" "}
              <span className="mono">
                {participant.event_title ? participant.event_title : participant.event_id}
              </span>
            </div>
          </div>
        )}

        <div className="mono" style={{ marginTop: 10 }}>
          Tip: Some browsers require HTTPS for camera. If camera fails on desktop, scan on mobile.
        </div>
      </div>
    </div>
  );
}
