import { useEffect, useState } from "react";
import api from "../api";
import { getUser } from "../auth";

export default function MyRegistrations() {

  const user = getUser();

  const [regs, setRegs] = useState([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);


  useEffect(() => {

    if (user?.role !== "participant") {
      setLoading(false);
      return;
    }

    api
      .get("/registrations/my")

      .then((res) => {

        console.log(
          "MY REGISTRATIONS:",
          res.data
        );

        res.data.forEach((r) => {

          console.log(
            "Registration:",
            r.id
          );

          console.log(
            "QR available:",
            !!r.qr_image
          );

          console.log(
            "QR start:",
            r.qr_image?.substring(0, 80)
          );

        });

        setRegs(res.data);

        setErr("");

      })

      .catch((e) => {

        console.error(
          "Registration load error:",
          e
        );

        setErr(
          e?.response?.data?.error ||
          "Failed to load registrations"
        );

      })

      .finally(() => {

        setLoading(false);

      });

  }, [user?.role]);


  if (user?.role !== "participant") {

    return (

      <div className="container">

        <div className="card card-pad">

          <h2 className="title">
            Forbidden
          </h2>

          <p className="subtitle">
            Only participants can view
            registrations.
          </p>

        </div>

      </div>

    );
  }


  if (loading) {

    return (

      <div className="container">

        <h2 className="title">
          My Registrations
        </h2>

        <p className="subtitle">
          Loading your registrations...
        </p>

      </div>

    );
  }


  return (

    <div className="container">

      <h2 className="title">
        My Registrations
      </h2>

      <p className="subtitle">
        Show this QR at the entry
        for check-in.
      </p>


      {err && (

        <div className="alert alert-danger">
          {err}
        </div>

      )}


      {!err && regs.length === 0 && (

        <div className="card card-pad">

          <p className="subtitle">
            You have no registrations yet.
          </p>

        </div>

      )}


      <div className="grid">

        {regs.map((r) => (

          <div
            key={r.id}
            className="card card-pad"
          >

            <div className="kv">


              {r.event_title && (
                <>
                  <b>Event</b>

                  <span>
                    {r.event_title}
                  </span>
                </>
              )}


              <b>
                Event ID
              </b>

              <span className="mono">
                {r.event_id}
              </span>


              {r.event_date && (
                <>
                  <b>Date</b>

                  <span>
                    {r.event_date}
                  </span>
                </>
              )}


              <b>
                Status
              </b>

              <span className="badge">
                {r.status}
              </span>


              <b>
                Registration ID
              </b>

              <span className="mono">
                {r.id}
              </span>

            </div>


            {r.qr_image ? (

              <div
                style={{
                  marginTop: "20px",
                  textAlign: "center"
                }}
              >

                <p
                  style={{
                    marginBottom: "10px",
                    fontWeight: "600"
                  }}
                >
                  Check-in QR
                </p>


                <img

                  src={r.qr_image}

                  alt="Registration QR"

                  style={{
                    width: "220px",
                    height: "220px",
                    objectFit: "contain",
                    backgroundColor: "white",
                    padding: "10px",
                    borderRadius: "10px"
                  }}

                  onLoad={() => {

                    console.log(
                      "QR loaded successfully:",
                      r.id
                    );

                  }}

                  onError={(e) => {

                    console.error(
                      "QR IMAGE FAILED:",
                      r.id
                    );

                    console.error(
                      "QR value:",
                      r.qr_image?.substring(
                        0,
                        150
                      )
                    );

                  }}

                />

              </div>

            ) : (

              <div
                style={{
                  marginTop: "20px"
                }}
              >

                <p
                  style={{
                    color: "#ff6b6b"
                  }}
                >
                  QR code unavailable
                </p>

              </div>

            )}

          </div>

        ))}

      </div>

    </div>

  );
}
