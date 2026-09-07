import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS

from routes.auth_routes import auth_bp
from routes.event_routes import event_bp
from routes.registration_routes import reg_bp
from routes.checkin_routes import checkin_bp
from routes.payment_routes import payment_bp

from utils.emailer import init_mail  # ✅ add this


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ----------------------------
    # EMAIL CONFIG (Flask-Mail)
    # ----------------------------
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "1") == "1"
    app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "0") == "1"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

    init_mail(app)  # ✅ initialize mail here

    # ----------------------------
    # ROUTES
    # ----------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(reg_bp)
    app.register_blueprint(checkin_bp)
    app.register_blueprint(payment_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
