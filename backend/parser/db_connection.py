import os
import logging
import mysql.connector
from mysql.connector import Error, pooling

log = logging.getLogger(__name__)

# ── Connection pool (created once at module load) ─────────────────────────────
# All config from environment variables — no credentials in source code.
_DB_CONFIG = {
    "host":      os.environ.get("DB_HOST",     "localhost"),
    "port":      int(os.environ.get("DB_PORT", "3306")),
    "user":      os.environ.get("DB_USER",     "gpa_app"),   # NOT root
    "password":  os.environ.get("DB_PASSWORD", ""),
    "database":  os.environ.get("DB_NAME",     "gpa_goes_database"),
    "charset":   "utf8mb4",          # required for Arabic text
    "autocommit": False,             # explicit — callers manage transactions
    "connection_timeout": 10,        # fail fast if DB unreachable
}

try:
    _pool = pooling.MySQLConnectionPool(
        pool_name="gpa_pool",
        pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
        **_DB_CONFIG,
    )
    log.info("MySQL connection pool initialised (size=%s)", _DB_CONFIG)
except Error as e:
    log.critical("Failed to create DB connection pool: %s", e)
    _pool = None


class DBConnectionError(Exception):
    """Raised when a database connection cannot be obtained."""


def get_connection() -> mysql.connector.MySQLConnection:
    """
    Obtain a connection from the pool.

    Returns:
        An active MySQLConnection with autocommit=False.

    Raises:
        DBConnectionError: If the pool is unavailable or connection fails.
    """
    if _pool is None:
        raise DBConnectionError(
            "Connection pool was not initialised. "
            "Check DB credentials and server availability."
        )

    try:
        conn = _pool.get_connection()
        if not conn.is_connected():
            conn.reconnect(attempts=2, delay=1)
        if not conn.is_connected():
            raise DBConnectionError("Connection obtained from pool is not active.")
        log.debug("DB connection obtained from pool")
        return conn

    except Error as e:
        log.error("Failed to get DB connection from pool: %s", e)
        raise DBConnectionError(f"Could not connect to database: {e}") from e