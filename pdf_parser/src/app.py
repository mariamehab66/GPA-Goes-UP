"""
app.py — Flask application factory.

Wires together: upload blueprint, session teardown hook, and logging.
Usage:
    from src.app import create_app
    app = create_app()
    app.run()
"""
import logging
import os

from flask import Flask, g

from .api.upload import upload_bp
from .session.session_store import register_teardown


def create_app(config: dict | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config: Optional dict of Flask config overrides (useful for testing).
    """
    app = Flask(__name__)

    # Basic config
    app.config["JSON_SORT_KEYS"] = False
    if config:
        app.config.update(config)

    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    # Register blueprints
    app.register_blueprint(upload_bp)

    # T033: Register session teardown hook
    # The DB session is stored in g.db_session by the caller before each request.
    register_teardown(app, lambda: g.get("db_session"))

    return app
