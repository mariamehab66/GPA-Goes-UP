import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from upload import upload_bp

load_dotenv()

log = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)

    # ── Secret key ────────────────────────────────────────────────────────────
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        raise RuntimeError(
            "SECRET_KEY environment variable is not set. "
            "Add it to your .env file."
        )
    app.config["SECRET_KEY"] = secret

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Allows your frontend origin to call this API.
    # Set FRONTEND_ORIGIN in .env to your frontend URL.
    # Example: FRONTEND_ORIGIN=http://localhost:3000
    # In production: FRONTEND_ORIGIN=https://yoursite.com
    frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
    CORS(app, origins=[frontend_origin])

    # ── Upload config ─────────────────────────────────────────────────────────
    upload_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "uploads"
    )
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"]      = upload_folder
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

    # ── Logging ───────────────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    # ── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(upload_bp)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File too large. Maximum size is 16MB."}), 413

    @app.errorhandler(500)
    def server_error(e):
        log.exception("Unhandled server error")
        return jsonify({"error": "Internal server error."}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)