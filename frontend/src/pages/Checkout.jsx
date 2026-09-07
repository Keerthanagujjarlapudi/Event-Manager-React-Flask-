import { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import api from "../api";
import { getUser } from "../auth";

export default function Checkout() {
  const { eventId } = useParams();
  const nav = useNavigate();
  const user = getUser();

  const [event, setEvent] = useState(null);
  const [msg, setMsg] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const amountInr = 199;

  // ==========================================================
  // LOAD EVENT
  // ==========================================================

  useEffect(() => {
    async function loadEvent() {
      try {
        const res = await api.get("/events");

        const ev = (res.data || []).find(
          (e) =>
            String(e.id) ===
            String(eventId)
        );

        setEvent(ev || null);

      } catch (error) {

        console.error(
          "Failed to load event:",
          error
        );

        setEvent(null);
      }
    }

    if (eventId) {
      loadEvent();
    }

  }, [eventId]);


  // ==========================================================
  // LOGIN
  // ==========================================================

  if (!user) {
    return (
      <div className="container">
        <div className="card card-pad">

          <h2 className="title">
            Login required
          </h2>

          <p className="subtitle">
            Please login to continue.
          </p>

          <Link
            to="/login"
            className="btn btn-primary"
          >
            Login
          </Link>

        </div>
      </div>
    );
  }


  // ==========================================================
  // PAY ONLINE
  // ==========================================================

  async function payOnline() {

    if (loading) return;

    setLoading(true);
    setStatus("");
    setMsg(
      "Creating Razorpay payment..."
    );

    try {

      const res = await api.post(
        "/payments/create-link",
        {
          event_id: eventId,
          amount_inr: amountInr
        }
      );


      console.log(
        "Razorpay create-link:",
        res.data
      );


      if (!res.data?.ok) {

        throw new Error(
          res.data?.error ||
          "Unable to create payment."
        );
      }


      // Save our MongoDB payment ID

      if (res.data?.payment_id) {

        localStorage.setItem(
          "last_payment_id",
          res.data.payment_id
        );
      }


      // Save Razorpay Payment Link ID

      if (res.data?.payment_link_id) {

        localStorage.setItem(
          "last_payment_link_id",
          res.data.payment_link_id
        );
      }


      if (!res.data?.redirect_url) {

        throw new Error(
          "Razorpay payment URL was not returned."
        );
      }


      setMsg(
        "Redirecting to Razorpay..."
      );


      // Redirect to Razorpay

      window.location.href =
        res.data.redirect_url;


    } catch (error) {

      console.error(
        "Pay Online error:",
        error
      );

      setLoading(false);
      setStatus("error");

      setMsg(
        error?.response?.data?.error ||
        error?.response?.data?.message ||
        error?.message ||
        "Payment initialization failed."
      );
    }
  }


  // ==========================================================
  // PAY ON ARRIVAL
  // ==========================================================

  async function payOnArrival() {

    if (loading) return;

    setLoading(true);
    setStatus("");
    setMsg(
      "Saving Pay on Arrival choice..."
    );

    try {

      const res = await api.post(
        "/payments/pay-at-event",
        {
          event_id: eventId,
          amount_inr: amountInr
        }
      );


      console.log(
        "Pay on Arrival:",
        res.data
      );


      if (!res.data?.ok) {

        throw new Error(
          res.data?.error ||
          "Unable to select Pay on Arrival."
        );
      }


      if (res.data?.payment_id) {

        localStorage.setItem(
          "last_cash_payment_id",
          res.data.payment_id
        );
      }


      if (res.data?.redirect_url) {

        window.location.href =
          res.data.redirect_url;

        return;
      }


      window.location.href =
        `/payment/success?eventId=${encodeURIComponent(
          eventId
        )}&provider=cash`;


    } catch (error) {

      console.error(
        "Pay on Arrival error:",
        error
      );

      setLoading(false);
      setStatus("error");

      setMsg(
        error?.response?.data?.error ||
        error?.response?.data?.message ||
        error?.message ||
        "Failed to select Pay on Arrival."
      );
    }
  }


  // ==========================================================
  // UI
  // ==========================================================

  const alertClass =
    status === "error"
      ? "alert alert-danger"
      : "alert";


  return (
    <div className="container">

      <div className="card card-pad">

        <h2 className="title">
          Checkout
        </h2>


        <p className="subtitle">
          {event?.title ||
            "Event payment"}
        </p>


        <p>
          Amount:
          {" "}
          <strong>
            ₹{amountInr}
          </strong>
        </p>


        {msg && (
          <div
            className={alertClass}
            style={{
              marginTop: 12
            }}
          >
            {msg}
          </div>
        )}


        <div
          className="row"
          style={{
            marginTop: 16,
            gap: 10
          }}
        >

          {/* ================================================= */}
          {/* PAY ONLINE */}
          {/* ================================================= */}

          <button
            type="button"
            className="btn btn-primary"
            onClick={payOnline}
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : `Pay Online ₹${amountInr}`}
          </button>


          {/* ================================================= */}
          {/* PAY ON ARRIVAL */}
          {/* ================================================= */}

          <button
            type="button"
            className="btn"
            onClick={payOnArrival}
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : "Pay on Arrival"}
          </button>


          {/* ================================================= */}
          {/* BACK */}
          {/* ================================================= */}

          <button
            type="button"
            className="btn"
            onClick={() => nav(-1)}
            disabled={loading}
          >
            Back
          </button>

        </div>


        <div
          className="mono"
          style={{
            marginTop: 15
          }}
        >
          Pay Online uses Razorpay.
          Pay on Arrival creates a pending
          cash payment that can be confirmed
          at the venue.
        </div>

      </div>

    </div>
  );
}
