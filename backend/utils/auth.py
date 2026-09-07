import jwt
import bcrypt
from functools import wraps
from flask import request, jsonify
from config import Config

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed)

def create_token(payload: dict) -> str:
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])

def auth_required(roles=None):
    roles = roles or []

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "Missing token"}), 401

            token = auth.split(" ", 1)[1]
            try:
                payload = decode_token(token)
            except Exception:
                return jsonify({"error": "Invalid token"}), 401

            request.user = payload

            if roles and payload.get("role") not in roles:
                return jsonify({"error": "Forbidden"}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
