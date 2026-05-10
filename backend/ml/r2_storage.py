"""
ml/r2_storage.py

Cloudflare R2 persistence layer for training CSVs and ML model artifacts.

On every container restart (Koyeb free tier uses ephemeral storage), call
sync_on_startup() to pull the latest files down from R2 before Flask serves
any requests.

After writing CSVs or the model locally, call upload_csvs() or upload_model()
to push the updated files back so they survive the next restart.

Falls back silently to local-only mode when R2 env vars are absent, so
local development works without any cloud credentials.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (from environment variables)
# ---------------------------------------------------------------------------

_ENDPOINT   = os.environ.get("R2_ENDPOINT_URL", "")      # https://<id>.r2.cloudflarestorage.com
_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY_ID", "")
_SECRET_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
BUCKET      = os.environ.get("R2_BUCKET_NAME", "gpa-goes-up")

# ---------------------------------------------------------------------------
# Local paths  ←→  R2 object keys
# ---------------------------------------------------------------------------

_BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TRAINING_DIR = os.path.join(_BASE_DIR, "data", "training")
_MODELS_DIR   = os.path.join(_BASE_DIR, "ml", "models")

_SYNC_MAP: dict[str, str] = {
    os.path.join(_TRAINING_DIR, "student.csv"):              "training/student.csv",
    os.path.join(_TRAINING_DIR, "enrollment.csv"):           "training/enrollment.csv",
    os.path.join(_MODELS_DIR,   "best_course_model.pkl"):    "models/best_course_model.pkl",
    os.path.join(_MODELS_DIR,   "training_state.json"):      "models/training_state.json",
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_configured() -> bool:
    return bool(_ENDPOINT and _ACCESS_KEY and _SECRET_KEY)


def _client():
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=_ENDPOINT,
        aws_access_key_id=_ACCESS_KEY,
        aws_secret_access_key=_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def download(remote_key: str, local_path: str) -> bool:
    """Download *remote_key* from R2 to *local_path*. Returns True on success."""
    if not _is_configured():
        return False
    try:
        from botocore.exceptions import ClientError

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        _client().download_file(BUCKET, remote_key, local_path)
        log.info("[r2] Downloaded %s → %s", remote_key, local_path)
        return True
    except Exception as exc:
        # ClientError 404 is normal on the very first run (file doesn't exist yet).
        code = getattr(getattr(exc, "response", {}), "get", lambda *_: None)("Error", {}).get("Code")
        if code == "404" or "NoSuchKey" in str(exc):
            log.debug("[r2] %s not in R2 yet (first run?)", remote_key)
        else:
            log.warning("[r2] download failed for %s: %s", remote_key, exc)
        return False


def upload(local_path: str, remote_key: str) -> bool:
    """Upload *local_path* to R2 as *remote_key*. Returns True on success."""
    if not _is_configured():
        return False
    if not os.path.exists(local_path):
        log.warning("[r2] upload skipped — local file not found: %s", local_path)
        return False
    try:
        _client().upload_file(local_path, BUCKET, remote_key)
        log.info("[r2] Uploaded %s → %s", local_path, remote_key)
        return True
    except Exception as exc:
        log.warning("[r2] upload failed %s → %s: %s", local_path, remote_key, exc)
        return False


def sync_on_startup() -> None:
    """
    Pull all persistent artifacts from R2 to the local filesystem.
    Safe to call when R2 is not configured (no-op with an info log).
    """
    if not _is_configured():
        log.info("[r2] R2 not configured — running in local-only mode.")
        return
    log.info("[r2] Syncing artifacts from R2 bucket '%s' ...", BUCKET)
    for local_path, remote_key in _SYNC_MAP.items():
        download(remote_key, local_path)
    log.info("[r2] Startup sync complete.")


def upload_csvs() -> None:
    """Re-upload both training CSVs to R2 after a new student is appended."""
    for local_path, remote_key in _SYNC_MAP.items():
        if remote_key.startswith("training/"):
            upload(local_path, remote_key)


def upload_model() -> None:
    """Re-upload the model artifact and state file to R2 after retraining."""
    for local_path, remote_key in _SYNC_MAP.items():
        if remote_key.startswith("models/"):
            upload(local_path, remote_key)
