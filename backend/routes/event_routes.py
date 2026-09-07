from flask import Blueprint, request, jsonify
from db import events
from utils.auth import auth_required
from datetime import datetime
from bson import ObjectId

event_bp = Blueprint("events", __name__, url_prefix="/api/events")

# Create event (organizer only)
@event_bp.post("")
@auth_required(roles=["organizer"])
def create_event():
    data = request.get_json() or {}

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    date = data.get("date", "").strip()
    published = bool(data.get("published", False))
    schedule = data.get("schedule", [])

    if not title:
        return jsonify({"error": "Event title is required"}), 400

    # Validate schedule format
    clean_schedule = []
    for item in schedule:
        if not isinstance(item, dict):
            continue
        time = item.get("time", "").strip()
        label = item.get("item", "").strip()
        if time and label:
            clean_schedule.append({"time": time, "item": label})

    doc = {
        "title": title,
        "description": description,
        "date": date,
        "published": published,
        "schedule": clean_schedule,
        "created_by": request.user["user_id"],
        "created_at": datetime.utcnow(),
    }

    res = events.insert_one(doc)

    return jsonify({
        "id": str(res.inserted_id),
        "message": "Event created successfully"
    }), 201


# List events (public)
@event_bp.get("")
def list_events():
    out = []
    for e in events.find().sort("created_at", -1):
        out.append({
            "id": str(e["_id"]),
            "title": e["title"],
            "description": e.get("description", ""),
            "date": e.get("date", ""),
            "published": e.get("published", False),
            "schedule": e.get("schedule", [])
        })
    return jsonify(out)
