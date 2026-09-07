from flask import Blueprint, request, jsonify
from db import registrations, checkins, events
from utils.auth import auth_required
from bson import ObjectId

checkin_bp = Blueprint("checkins", __name__, url_prefix="/api/checkin")

@checkin_bp.post("")
@auth_required(roles=["organizer", "volunteer"])
def checkin():
    data = request.get_json() or {}
    payload = (data.get("qr_payload") or "").strip()

    # payload format: "eventId:userId"
    if not payload or ":" not in payload:
        return jsonify({"error": "Invalid QR data"}), 400

    event_id, user_id = payload.split(":", 1)

    # Verify registration exists
    reg = registrations.find_one({"event_id": event_id, "user_id": user_id})
    if not reg:
        return jsonify({
            "ok": False,
            "status": "not_registered",
            "message": "Participant is NOT registered for this event"
        }), 404

    # Optional: fetch event title (nice for UI)
    event_title = None
    try:
        ev = events.find_one({"_id": ObjectId(event_id)})
        if ev:
            event_title = ev.get("title")
    except Exception:
        # event_id may not be ObjectId or event not found, ignore
        pass

    # Prevent double check-in
    already = checkins.find_one({"event_id": event_id, "user_id": user_id})
    if already:
        return jsonify({
            "ok": True,
            "status": "already_checked_in",
            "message": "Already checked in",
            "participant": {
                "name": reg.get("name", ""),
                "email": reg.get("email", ""),
                "event_id": event_id,
                "event_title": event_title
            }
        }), 200

    # Mark check-in
    checkins.insert_one({
        "event_id": event_id,
        "user_id": user_id,
        "by": request.user["user_id"]
    })

    registrations.update_one(
        {"_id": reg["_id"]},
        {"$set": {"status": "checked_in"}}
    )

    return jsonify({
        "ok": True,
        "status": "checked_in",
        "message": f"Checked in: {reg.get('name','participant')}",
        "participant": {
            "name": reg.get("name", ""),
            "email": reg.get("email", ""),
            "event_id": event_id,
            "event_title": event_title
        }
    }), 200
