import os
import uuid
from datetime import datetime

import razorpay

from flask import Blueprint, request, jsonify

from utils.auth import auth_required
from db import events, payments

from bson import ObjectId
from bson.errors import InvalidId


# ============================================================
# BLUEPRINT
# ============================================================

payment_bp = Blueprint(
    "payments",
    __name__,
    url_prefix="/api/payments"
)


# ============================================================
# CONFIGURATION
# ============================================================

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
).rstrip("/")

RAZORPAY_KEY_ID = os.getenv(
    "RAZORPAY_KEY_ID"
)

RAZORPAY_KEY_SECRET = os.getenv(
    "RAZORPAY_KEY_SECRET"
)


# ============================================================
# RAZORPAY CLIENT
# ============================================================

razorpay_client = None

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(
        auth=(
            RAZORPAY_KEY_ID,
            RAZORPAY_KEY_SECRET
        )
    )


# ============================================================
# EVENT HELPER
# ============================================================

def _get_event_or_error(event_id: str):

    if not event_id:
        return None, (
            jsonify({
                "error": "event_id is required"
            }),
            400
        )

    try:
        event_oid = ObjectId(event_id)

    except InvalidId:
        return None, (
            jsonify({
                "error": "Invalid event_id"
            }),
            400
        )

    ev = events.find_one({
        "_id": event_oid
    })

    if not ev:
        return None, (
            jsonify({
                "error": "Event not found"
            }),
            404
        )

    if not ev.get("published", False):
        return None, (
            jsonify({
                "error": "Event is not published"
            }),
            400
        )

    return ev, None


# ============================================================
# AMOUNT HELPER
# ============================================================

def _parse_amount(data):

    try:

        amount_inr = int(
            data.get("amount_inr") or 199
        )

        if amount_inr <= 0:
            return None, (
                jsonify({
                    "error": "Invalid amount"
                }),
                400
            )

        return amount_inr, None

    except Exception:

        return None, (
            jsonify({
                "error": "Invalid amount"
            }),
            400
        )


# ============================================================
# PAY ONLINE
# CREATE RAZORPAY PAYMENT LINK
# ============================================================

@payment_bp.post("/create-link")
@auth_required(roles=["participant"])
def create_payment_link():

    # --------------------------------------------------------
    # Check configuration
    # --------------------------------------------------------

    if not RAZORPAY_KEY_ID:
        return jsonify({
            "error":
                "RAZORPAY_KEY_ID is not configured."
        }), 500

    if not RAZORPAY_KEY_SECRET:
        return jsonify({
            "error":
                "RAZORPAY_KEY_SECRET is not configured."
        }), 500

    if razorpay_client is None:
        return jsonify({
            "error":
                "Razorpay client is not initialized."
        }), 500


    # --------------------------------------------------------
    # Read request
    # --------------------------------------------------------

    data = request.get_json() or {}

    event_id = (
        data.get("event_id") or ""
    ).strip()


    # --------------------------------------------------------
    # Validate event
    # --------------------------------------------------------

    ev, err = _get_event_or_error(
        event_id
    )

    if err:
        return err


    # --------------------------------------------------------
    # Validate amount
    # --------------------------------------------------------

    amount_inr, err2 = _parse_amount(
        data
    )

    if err2:
        return err2


    # --------------------------------------------------------
    # Current participant
    # --------------------------------------------------------

    user_id = request.user["user_id"]

    user_name = request.user.get(
        "name",
        ""
    )

    user_email = request.user.get(
        "email",
        ""
    )


    # --------------------------------------------------------
    # Convert INR to paise
    #
    # ₹199 = 19900 paise
    # --------------------------------------------------------

    amount_paise = amount_inr * 100


    # --------------------------------------------------------
    # Unique reference ID
    # --------------------------------------------------------

    reference_id = (
        "EVT"
        + event_id[-8:]
        + "_"
        + uuid.uuid4().hex[:12]
    )

    reference_id = reference_id[:40]


    # --------------------------------------------------------
    # Callback URL
    # --------------------------------------------------------

    callback_url = (
        f"{FRONTEND_URL}"
        f"/payment/success"
        f"?eventId={event_id}"
        f"&provider=razorpay"
    )


    # --------------------------------------------------------
    # Razorpay Payment Link request
    # --------------------------------------------------------

    payment_link_data = {

        "amount": amount_paise,

        "currency": "INR",

        "accept_partial": False,

        "reference_id": reference_id,

        "description": (
            f"Payment for "
            f"{ev.get('title', 'Event')}"
        ),

        "callback_url": callback_url,

        "callback_method": "get",

        "customer": {
            "name": user_name,
            "email": user_email
        },

        "notes": {
            "event_id": event_id,
            "user_id": str(user_id)
        },

        "reminder_enable": False
    }


    # --------------------------------------------------------
    # Create Razorpay Payment Link
    # --------------------------------------------------------

    try:

        razorpay_link = (
            razorpay_client.payment_link.create(
                payment_link_data
            )
        )

    except Exception as e:

        print(
            "========== RAZORPAY CREATE ERROR =========="
        )

        print(repr(e))

        print(
            "============================================"
        )

        return jsonify({
            "error":
                "Razorpay payment link creation failed.",
            "details":
                str(e)
        }), 502


    # --------------------------------------------------------
    # Extract Razorpay response
    # --------------------------------------------------------

    payment_link_id = (
        razorpay_link.get("id")
    )

    payment_link_url = (
        razorpay_link.get("short_url")
    )


    if not payment_link_id:

        return jsonify({
            "error":
                "Razorpay did not return payment_link_id."
        }), 502


    if not payment_link_url:

        return jsonify({
            "error":
                "Razorpay did not return payment URL."
        }), 502


    # --------------------------------------------------------
    # Save payment in MongoDB
    # --------------------------------------------------------

    payment_document = {

        "provider": "razorpay",

        "event_id": event_id,

        "event_title": ev.get(
            "title",
            "Event"
        ),

        "user_id": user_id,

        "user_name": user_name,

        "user_email": user_email,

        "amount_inr": amount_inr,

        "amount_paise": amount_paise,

        "status": "created",

        "payment_link_id":
            payment_link_id,

        "reference_id":
            reference_id,

        "payment_link_url":
            payment_link_url,

        "created_at":
            datetime.utcnow()
    }


    try:

        result = payments.insert_one(
            payment_document
        )

    except Exception as e:

        print(
            "MongoDB payment save error:",
            repr(e)
        )

        return jsonify({
            "error":
                "Payment link was created but "
                "could not be saved."
        }), 500


    # --------------------------------------------------------
    # Return payment URL
    # --------------------------------------------------------

    return jsonify({

        "ok": True,

        "provider": "razorpay",

        "payment_id":
            str(result.inserted_id),

        "payment_link_id":
            payment_link_id,

        "reference_id":
            reference_id,

        "amount_inr":
            amount_inr,

        "status":
            "created",

        "redirect_url":
            payment_link_url

    }), 200


# ============================================================
# VERIFY RAZORPAY PAYMENT
# ============================================================

@payment_bp.get("/verify")
@auth_required(roles=["participant"])
def verify_razorpay_payment():

    # --------------------------------------------------------
    # Check Razorpay
    # --------------------------------------------------------

    if razorpay_client is None:

        return jsonify({
            "error":
                "Razorpay is not configured."
        }), 500


    # --------------------------------------------------------
    # Read query parameters
    # --------------------------------------------------------

    event_id = (
        request.args.get("eventId") or ""
    ).strip()

    payment_link_id = (
        request.args.get("razorpay_payment_link_id")
        or ""
    ).strip()


    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if not event_id:

        return jsonify({
            "error":
                "eventId is required."
        }), 400


    if not payment_link_id:

        return jsonify({
            "error":
                "razorpay_payment_link_id is required."
        }), 400


    # --------------------------------------------------------
    # Find our local payment
    # --------------------------------------------------------

    local_payment = payments.find_one({

        "provider": "razorpay",

        "event_id": event_id,

        "payment_link_id":
            payment_link_id,

        "user_id":
            request.user["user_id"]

    })


    if not local_payment:

        return jsonify({
            "error":
                "Payment record not found."
        }), 404


    # --------------------------------------------------------
    # Get payment link from Razorpay
    # --------------------------------------------------------

    try:

        razorpay_link = (
            razorpay_client.payment_link.fetch(
                payment_link_id
            )
        )

    except Exception as e:

        print(
            "Razorpay verification error:",
            repr(e)
        )

        return jsonify({
            "error":
                "Unable to verify payment with Razorpay.",
            "details":
                str(e)
        }), 502


    # --------------------------------------------------------
    # Razorpay status
    # --------------------------------------------------------

    razorpay_status = (
        razorpay_link.get("status")
    )

    razorpay_amount = (
        razorpay_link.get("amount")
    )

    local_amount_paise = (
        local_payment.get(
            "amount_paise",
            0
        )
    )


    # --------------------------------------------------------
    # Verify amount
    # --------------------------------------------------------

    if int(razorpay_amount or 0) != int(
        local_amount_paise
    ):

        return jsonify({

            "ok": False,

            "paid": False,

            "error":
                "Payment amount mismatch.",

            "razorpay_status":
                razorpay_status

        }), 400


    # --------------------------------------------------------
    # Determine paid status
    # --------------------------------------------------------

    paid = (
        razorpay_status == "paid"
    )


    # --------------------------------------------------------
    # Update MongoDB
    # --------------------------------------------------------

    if paid:

        payments.update_one(

            {
                "_id":
                    local_payment["_id"]
            },

            {
                "$set": {

                    "status":
                        "paid",

                    "paid_at":
                        datetime.utcnow(),

                    "razorpay_status":
                        razorpay_status

                }
            }

        )

        final_status = "paid"

    else:

        payments.update_one(

            {
                "_id":
                    local_payment["_id"]
            },

            {
                "$set": {

                    "razorpay_status":
                        razorpay_status

                }
            }

        )

        final_status = (
            local_payment.get(
                "status",
                "created"
            )
        )


    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({

        "ok": True,

        "paid": paid,

        "provider":
            "razorpay",

        "payment_id":
            str(
                local_payment["_id"]
            ),

        "payment_link_id":
            payment_link_id,

        "status":
            final_status,

        "razorpay_status":
            razorpay_status,

        "amount_inr":
            local_payment.get(
                "amount_inr",
                0
            )

    }), 200


# ============================================================
# PAY ON ARRIVAL
# ============================================================

@payment_bp.post("/pay-at-event")
@auth_required(roles=["participant"])
def pay_at_event():

    data = request.get_json() or {}

    event_id = (
        data.get("event_id") or ""
    ).strip()


    ev, err = _get_event_or_error(
        event_id
    )

    if err:
        return err


    amount_inr, err2 = _parse_amount(
        data
    )

    if err2:
        return err2


    user_id = request.user["user_id"]


    # --------------------------------------------------------
    # Prevent duplicates
    # --------------------------------------------------------

    existing = payments.find_one({

        "event_id": event_id,

        "user_id": user_id,

        "provider": "cash"

    })


    if existing:

        return jsonify({

            "ok": True,

            "provider": "cash",

            "payment_id":
                str(existing["_id"]),

            "status":
                existing.get(
                    "status",
                    "pending_cash"
                ),

            "amount_inr":
                existing.get(
                    "amount_inr",
                    amount_inr
                ),

            "redirect_url": (
                f"{FRONTEND_URL}"
                f"/payment/success"
                f"?eventId={event_id}"
                f"&provider=cash"
            )

        }), 200


    # --------------------------------------------------------
    # Create cash payment
    # --------------------------------------------------------

    result = payments.insert_one({

        "provider": "cash",

        "event_id": event_id,

        "event_title":
            ev.get(
                "title",
                "Event"
            ),

        "user_id": user_id,

        "user_name":
            request.user.get(
                "name",
                ""
            ),

        "user_email":
            request.user.get(
                "email",
                ""
            ),

        "amount_inr":
            amount_inr,

        "status":
            "pending_cash",

        "created_at":
            datetime.utcnow()

    })


    return jsonify({

        "ok": True,

        "provider": "cash",

        "payment_id":
            str(result.inserted_id),

        "status":
            "pending_cash",

        "amount_inr":
            amount_inr,

        "message":
            "Pay on arrival selected. "
            "Please pay at the venue.",

        "redirect_url": (
            f"{FRONTEND_URL}"
            f"/payment/success"
            f"?eventId={event_id}"
            f"&provider=cash"
        )

    }), 200


# ============================================================
# ORGANIZER MARKS CASH AS PAID
# ============================================================

@payment_bp.post("/mark-cash-paid")
@auth_required(
    roles=[
        "organizer",
        "volunteer"
    ]
)
def mark_cash_paid():

    data = request.get_json() or {}

    payment_id = (
        data.get("payment_id") or ""
    ).strip()


    if not payment_id:

        return jsonify({
            "error":
                "payment_id is required"
        }), 400


    try:

        pid = ObjectId(payment_id)

    except InvalidId:

        return jsonify({
            "error":
                "Invalid payment_id"
        }), 400


    pay = payments.find_one({

        "_id": pid,

        "provider": "cash"

    })


    if not pay:

        return jsonify({
            "error":
                "Cash payment record not found"
        }), 404


    payments.update_one(

        {
            "_id": pid
        },

        {
            "$set": {

                "status":
                    "paid_cash",

                "paid_at":
                    datetime.utcnow(),

                "verified_by":
                    request.user["user_id"]

            }
        }

    )


    return jsonify({

        "ok": True,

        "message":
            "Cash payment marked as PAID.",

        "status":
            "paid_cash"

    }), 200


# ============================================================
# PARTICIPANT PAYMENT STATUS
# ============================================================

@payment_bp.get("/my-status/<event_id>")
@auth_required(roles=["participant"])
def my_payment_status(event_id):

    event_id = (
        event_id or ""
    ).strip()


    if not event_id:

        return jsonify({
            "error":
                "event_id is required"
        }), 400


    pay = payments.find_one({

        "event_id": event_id,

        "user_id":
            request.user["user_id"],

        # Get any payment method
        "provider": {
            "$in": [
                "cash",
                "razorpay"
            ]
        }

    })


    if not pay:

        return jsonify({

            "ok": True,

            "status":
                "not_started"

        }), 200


    return jsonify({

        "ok": True,

        "provider":
            pay.get(
                "provider"
            ),

        "payment_id":
            str(pay["_id"]),

        "status":
            pay.get(
                "status",
                "created"
            ),

        "amount_inr":
            pay.get(
                "amount_inr",
                0
            )

    }), 200
