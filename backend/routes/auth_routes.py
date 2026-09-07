from flask import Blueprint, request, jsonify
from db import users
from utils.auth import hash_password, verify_password, create_token
from bson import ObjectId

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")
    role = data.get("role", "participant")  # organizer/volunteer/participant
    phone = data.get("phone", "").strip()

    if role not in ["organizer", "volunteer", "participant"]:
        return jsonify({"error": "Invalid role"}), 400
    if not name or not email or not password:
        return jsonify({"error": "name/email/password required"}), 400

    if users.find_one({"email": email}):
        return jsonify({"error": "Email already exists"}), 409

    hashed = hash_password(password)
    doc = {"name": name, "email": email, "password": hashed, "role": role, "phone": phone}
    res = users.insert_one(doc)

    token = create_token({"user_id": str(res.inserted_id), "email": email, "role": role, "name": name})
    return jsonify({"token": token, "user": {"id": str(res.inserted_id), "name": name, "email": email, "role": role}}), 201

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    user = users.find_one({"email": email})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not verify_password(password, user["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_token({
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
    })
    return jsonify({
        "token": token,
        "user": {"id": str(user["_id"]), "name": user["name"], "email": user["email"], "role": user["role"]}
    })
