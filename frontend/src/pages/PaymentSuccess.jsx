import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api from "../api";

export default function PaymentSuccess() {
  const [searchParams] = useSearchParams();

  const eventId =
    searchParams.get("eventId");

  const provider =
    searchParams.get("provider");

  const razorpayPaymentLinkId =
    searchParams.get(
      "razorpay_payment_link_id"
    );

  const [loading, setLoading] =
    useState(true);

  const [success, setSuccess] =
    useState(false);

  const [message, setMessage] =
    useState("Checking payment...");

  useEffect(() => {

    async function checkPayment() {

      // =====================================================
      // CASH
      // =====================================================

      if (provider === "cash") {

        setSuccess(true);

        setMessage(
          "Pay on Arrival selected successfully. " +
          "Please pay at the venue."
        );

        setLoading(false);

        return;
      }


      // =====================================================
      // RAZORPAY
      // =====================================================

      if (
        provider === "razorpay" &&
        eventId &&
        razorpayPaymentLinkId
      ) {

        try {

          const res = await api.get(
            "/payments/verify",
            {
              params: {
                eventId:
                  eventId,

                razorpay_payment_link_id:
                  razorpayPaymentLinkId
              }
            }
          );


          console.log(
            "Payment verification:",
            res.data
          );


          if (res.data?.paid) {

            setSuccess(true);

            setMessage(
              "Payment successful!"
            );

          } else {

            setSuccess(false);

            setMessage(
              "Payment has not been confirmed yet."
            );
          }

        } catch (error) {

          console.error(
            "Payment verification error:",
            error
          );

          setSuccess(false);

          setMessage(
            error?.response?.data?.error ||
            "Unable to verify payment."
          );
        }

        setLoading(false);

        return;
      }


      // =====================================================
      // INVALID CALLBACK
      // =====================================================

      setSuccess(false);

      setMessage(
        "Invalid payment information."
      );

      setLoading(false);
    }


    checkPayment();

  }, [
    eventId,
    provider,
    razorpayPaymentLinkId
  ]);


  // =========================================================
  // UI
  // =========================================================

  if (loading) {

    return (
      <div className="container">

        <div className="card card-pad">

          <h2 className="title">
            Checking Payment
          </h2>

          <p className="subtitle">
            {message}
          </p>

        </div>

      </div>
    );
  }


  return (
    <div className="container">

      <div className="card card-pad">

        <h2 className="title">

          {success
            ? "Payment Successful"
            : "Payment Status"}

        </h2>


        <p className="subtitle">
          {message}
        </p>


        {success && (
          <div
            className="alert"
            style={{
              marginTop: 15
            }}
          >

            {provider === "cash"
              ? "Your Pay on Arrival request is recorded as pending cash payment."
              : "Your Razorpay payment has been confirmed."}

          </div>
        )}


        {!success && (
          <div
            className="alert alert-danger"
            style={{
              marginTop: 15
            }}
          >
            Your payment could not be confirmed.
          </div>
        )}


        <div
          style={{
            marginTop: 20
          }}
        >

          <Link
            to="/"
            className="btn btn-primary"
          >
            Go Home
          </Link>

        </div>

      </div>

    </div>
  );
}
