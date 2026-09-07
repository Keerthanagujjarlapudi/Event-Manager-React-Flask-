from flask import Blueprint, request, jsonify
from bson import ObjectId
from bson.errors import InvalidId
from db import registrations, events
from utils.auth import auth_required
from utils.qr import make_qr_base64
from utils.emailer import send_email
from utils.sms import send_sms

reg_bp = Blueprint("registrations", __name__, url_prefix="/api/registrations")


@reg_bp.post("/register/<event_id>")
@auth_required(roles=["participant"])
def register_for_event(event_id):
    user = request.user

    # ✅ Safe ObjectId conversion
    try:
        ev = events.find_one({"_id": ObjectId(event_id)})
    except InvalidId:
        return jsonify({"error": "Invalid event id"}), 400

    if not ev:
        return jsonify({"error": "Event not found"}), 404
    if not ev.get("published", False):
        return jsonify({"error": "Event not published"}), 403

    existing = registrations.find_one({"event_id": event_id, "user_id": user["user_id"]})
    if existing:
        return jsonify({"error": "Already registered"}), 409

    # Registration token (encoded into QR)
    reg_payload = f"{event_id}:{user['user_id']}"
    qr_b64 = make_qr_base64(reg_payload)  # should return base64 without data prefix

    doc = {
        "event_id": event_id,
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "qr_payload": reg_payload,
        "qr_image": qr_b64,
        "status": "registered"
    }
    res = registrations.insert_one(doc)

    # ✅ EMAIL CONFIRMATION (HTML + QR)
    subject = f"Registration Confirmed: {ev.get('title', 'Event')}"
    plain_body = (
        f"Hi {user.get('name','')},\n\n"
        f"You are registered for: {ev.get('title','')}\n"
        f"Date: {ev.get('date','')}\n\n"
        f"Show your QR at entry. You can also find it in My Registrations.\n\n"
        f"Thanks!\nEvent Platform"
    )

    # Embed QR directly (base64)
    # make_qr_base64 should return only base64; we add the prefix for HTML
    qr_data_uri = f"data:image/png;base64,{qr_b64}"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #111;">
      <h2 style="margin: 0 0 10px;">Registration Confirmed ✅</h2>
      <p style="margin: 0 0 12px;">Hi <b>{user.get('name','Participant')}</b>,</p>

      <div style="padding: 12px; border: 1px solid #ddd; border-radius: 10px;">
        <p style="margin: 0 0 6px;"><b>Event:</b> {ev.get('title','')}</p>
        <p style="margin: 0;"><b>Date:</b> {ev.get('date','TBA')}</p>
      </div>

      <p style="margin: 16px 0 8px;"><b>Your Check-in QR:</b></p>
      <img src="{qr_data_uri}" alt="QR Code" style="width: 220px; height: 220px; border: 1px solid #ddd; border-radius: 10px; padding: 8px;" />

      <p style="margin: 14px 0 0;">
        Show this QR at entry. You can also open <b>My Registrations</b> in the app to display it.
      </p>

      <p style="margin: 18px 0 0; font-size: 12px; color: #666;">
        Event Platform
      </p>
    </div>
    """

    try:
        send_email(user["email"], subject, plain_body, html=html_body)
    except Exception as e:
        # Keep registration successful even if email fails
        print("Email failed:", e)

    # SMS (optional - keep mock unless you store phone)
    phone = None
    if phone:
        try:
            send_sms(phone, f"Registered for {ev.get('title','')} on {ev.get('date','')}")
        except Exception as e:
            print("SMS failed:", e)

    return jsonify({"registration_id": str(res.inserted_id), "qr_image": qr_b64}), 201


@reg_bp.get("/my")
@auth_required(roles=["participant"])
def my_regs():
    user = request.user
    out = []
    for r in registrations.find({"user_id": user["user_id"]}):
        out.append({
            "id": str(r["_id"]),
            "event_id": r["event_id"],
            "status": r.get("status", ""),
            "qr_image": r.get("qr_image", "")
        })
    return jsonify(out)
