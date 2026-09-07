from flask import Blueprint, request, jsonify
from bson import ObjectId
from bson.errors import InvalidId

from db import registrations, events
from utils.auth import auth_required
from utils.qr import make_qr_base64
from utils.emailer import send_email
from utils.sms import send_sms


reg_bp = Blueprint(
    "registrations",
    __name__,
    url_prefix="/api/registrations"
)


# ============================================================
# REGISTER FOR EVENT
# ============================================================

@reg_bp.post("/register/<event_id>")
@auth_required(roles=["participant"])
def register_for_event(event_id):

    user = request.user

    # --------------------------------------------------------
    # Validate event id
    # --------------------------------------------------------

    try:
        event_object_id = ObjectId(event_id)

    except (InvalidId, TypeError):

        return jsonify({
            "error": "Invalid event id"
        }), 400

    # --------------------------------------------------------
    # Find event
    # --------------------------------------------------------

    ev = events.find_one({
        "_id": event_object_id
    })

    if not ev:

        return jsonify({
            "error": "Event not found"
        }), 404

    # --------------------------------------------------------
    # Check published
    # --------------------------------------------------------

    if not ev.get("published", False):

        return jsonify({
            "error": "Event not published"
        }), 403

    # --------------------------------------------------------
    # Prevent duplicate registration
    # --------------------------------------------------------

    existing = registrations.find_one({
        "event_id": event_id,
        "user_id": user["user_id"]
    })

    if existing:

        return jsonify({
            "error": "Already registered",
            "registration_id": str(existing["_id"])
        }), 409

    # --------------------------------------------------------
    # Create registration first
    # --------------------------------------------------------

    registration_doc = {

        "event_id": event_id,

        "user_id": user["user_id"],

        "email": user.get("email", ""),

        "name": user.get("name", ""),

        "status": "registered",

        "qr_payload": "",

        "qr_image": ""
    }

    result = registrations.insert_one(
        registration_doc
    )

    registration_id = str(
        result.inserted_id
    )

    # --------------------------------------------------------
    # Generate QR
    # --------------------------------------------------------

    try:

        qr_payload = registration_id

        qr_b64 = make_qr_base64(
            qr_payload
        )

        print("============================")
        print("QR GENERATED")
        print("Registration ID:", registration_id)
        print("Payload:", qr_payload)
        print("QR Type:", type(qr_b64))
        print("QR Length:", len(qr_b64))
        print("QR Start:", qr_b64[:40])
        print("============================")

    except Exception as e:

        print("QR generation failed:", e)

        registrations.delete_one({
            "_id": result.inserted_id
        })

        return jsonify({
            "error": "QR generation failed"
        }), 500

    # --------------------------------------------------------
    # Save RAW BASE64 into MongoDB
    # --------------------------------------------------------

    registrations.update_one(

        {
            "_id": result.inserted_id
        },

        {
            "$set": {

                "qr_payload": qr_payload,

                "qr_image": qr_b64

            }
        }
    )

    # --------------------------------------------------------
    # Full browser-ready QR
    # --------------------------------------------------------

    qr_data_uri = (
        f"data:image/png;base64,{qr_b64}"
    )

    # --------------------------------------------------------
    # Event information
    # --------------------------------------------------------

    event_title = ev.get(
        "title",
        "Event"
    )

    event_date = ev.get(
        "date",
        "TBA"
    )

    participant_name = user.get(
        "name",
        "Participant"
    )

    # --------------------------------------------------------
    # Email
    # --------------------------------------------------------

    subject = (
        f"Registration Confirmed: "
        f"{event_title}"
    )

    plain_body = (

        f"Hi {participant_name},\n\n"

        f"Your registration is confirmed.\n\n"

        f"Event: {event_title}\n"

        f"Date: {event_date}\n"

        f"Registration ID: "
        f"{registration_id}\n\n"

        f"Show your QR code at entry.\n\n"

        f"Thanks!\n"

        f"Event Platform"
    )

    html_body = f"""
    <div style="
        font-family: Arial, sans-serif;
        line-height: 1.6;
        color: #111;
        max-width: 600px;
    ">

        <h2>
            Registration Confirmed ✅
        </h2>

        <p>
            Hi <b>{participant_name}</b>,
        </p>

        <div style="
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 10px;
        ">

            <p>
                <b>Event:</b>
                {event_title}
            </p>

            <p>
                <b>Date:</b>
                {event_date}
            </p>

            <p>
                <b>Registration ID:</b>
                {registration_id}
            </p>

        </div>

        <p>
            <b>Your Check-in QR:</b>
        </p>

        <img
            src="{qr_data_uri}"
            alt="QR Code"
            style="
                width: 220px;
                height: 220px;
                padding: 8px;
                border: 1px solid #ddd;
            "
        />

        <p>
            Show this QR at event entry.
        </p>

        <p style="
            font-size: 12px;
            color: #666;
        ">
            Event Platform
        </p>

    </div>
    """

    email_address = user.get(
        "email"
    )

    if email_address:

        try:

            send_email(
                email_address,
                subject,
                plain_body,
                html=html_body
            )

            print(
                "Email sent:",
                email_address
            )

        except Exception as e:

            print(
                "Email failed:",
                e
            )

    # --------------------------------------------------------
    # Optional SMS
    # --------------------------------------------------------

    phone = user.get(
        "phone"
    )

    if phone:

        try:

            send_sms(
                phone,
                f"Registered for "
                f"{event_title} "
                f"on {event_date}"
            )

        except Exception as e:

            print(
                "SMS failed:",
                e
            )

    # --------------------------------------------------------
    # API response
    # --------------------------------------------------------

    return jsonify({

        "message":
            "Registration successful",

        "registration": {

            "registration_id":
                registration_id,

            "event_id":
                event_id,

            "event_title":
                event_title,

            "event_date":
                event_date,

            "status":
                "registered",

            "qr_payload":
                qr_payload,

            # IMPORTANT:
            # Full image format sent to frontend
            "qr_image":
                qr_data_uri
        }

    }), 201


# ============================================================
# MY REGISTRATIONS
# ============================================================

@reg_bp.get("/my")
@auth_required(roles=["participant"])
def my_regs():

    user = request.user

    out = []

    user_regs = registrations.find({
        "user_id": user["user_id"]
    })

    for r in user_regs:

        # ----------------------------------------------------
        # Read QR from MongoDB
        # ----------------------------------------------------

        qr_value = r.get(
            "qr_image",
            ""
        )

        qr_image = ""

        if qr_value:

            # Already has prefix
            if qr_value.startswith(
                "data:image"
            ):

                qr_image = qr_value

            # Raw Base64
            else:

                qr_image = (
                    "data:image/png;base64,"
                    + qr_value
                )

        # ----------------------------------------------------
        # Get event info
        # ----------------------------------------------------

        event_title = ""
        event_date = ""

        try:

            event_id = r.get(
                "event_id",
                ""
            )

            ev = events.find_one({
                "_id": ObjectId(event_id)
            })

            if ev:

                event_title = ev.get(
                    "title",
                    ""
                )

                event_date = ev.get(
                    "date",
                    ""
                )

        except (
            InvalidId,
            TypeError,
            Exception
        ) as e:

            print(
                "Event lookup failed:",
                e
            )

        # ----------------------------------------------------
        # Debug
        # ----------------------------------------------------

        print("============================")

        print(
            "Registration:",
            str(r["_id"])
        )

        print(
            "QR exists:",
            bool(qr_value)
        )

        if qr_value:

            print(
                "QR length:",
                len(qr_value)
            )

            print(
                "QR start:",
                qr_value[:40]
            )

        print("============================")

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        out.append({

            "id":
                str(r["_id"]),

            "event_id":
                r.get(
                    "event_id",
                    ""
                ),

            "event_title":
                event_title,

            "event_date":
                event_date,

            "status":
                r.get(
                    "status",
                    ""
                ),

            "qr_payload":
                r.get(
                    "qr_payload",
                    ""
                ),

            "qr_image":
                qr_image
        })

    return jsonify(out), 200
