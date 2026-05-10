"""
scheduler.py

Isolated background scheduler for GPA Goes UP.
Run as a SEPARATE PROCESS alongside the Flask server:

    # Terminal 1 — Flask
    python app.py

    # Terminal 2 — Scheduler
    python scheduler.py

Why isolated (not inside Flask):
  Running APScheduler inside Flask causes the scheduler to fire once per
  worker when using multi-worker deployments (gunicorn -w N). An isolated
  process fires exactly once regardless of worker count, and holds no Flask
  memory overhead.

Two retrain triggers:
  1. Threshold (every 30 min): if new_students_since_last_retrain >= 3 → retrain
  2. Midnight  (daily 00:00) : if new_students_since_last_retrain > 0  → retrain

File safety:
  Both triggers acquire the shared FileLock from ml/csv_appender.py before
  reading the CSVs, ensuring Flask's append cannot interleave with a retrain
  read.

Timezone: Africa/Cairo (Egypt Standard / Summer Time).
"""

from __future__ import annotations

import logging
import os
import sys

# ── Make the project root importable ─────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron       import CronTrigger
from apscheduler.triggers.interval   import IntervalTrigger

from ml.csv_appender import (
    LOCK,
    get_new_student_count,
    reset_new_student_count,
)
from ml.train import train_and_save

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [scheduler] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TIMEZONE          = "Africa/Cairo"
RETRAIN_THRESHOLD = 3          # must match csv_appender.py intent
BASE_DIR          = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Retrain logic
# ---------------------------------------------------------------------------

def _run_retrain(reason: str) -> None:
    """Acquire the CSV lock, retrain all models, save the best, reset counter."""
    log.info(f"Retrain triggered — reason: {reason}")
    try:
        with LOCK:
            metrics = train_and_save(data_dir=BASE_DIR)

        reset_new_student_count()

        best = metrics.get("best_model", "unknown")
        rows = metrics.get("total_training_rows", 0)
        log.info(f"Retrain complete | best model: {best} | training rows: {rows}")

        for model_name, res in metrics.get("cv_results", {}).items():
            log.info(
                f"  {model_name:20s}  "
                f"mean_tolerance_accuracy = {res['mean_tolerance_accuracy']:.4f}  "
                f"± {res['std']:.4f}  "
                f"folds = {res['fold_scores']}"
            )

    except Exception as exc:
        log.error(f"Retrain failed: {exc}", exc_info=True)


# ---------------------------------------------------------------------------
# Scheduled jobs
# ---------------------------------------------------------------------------

def threshold_check() -> None:
    """
    Fires every 30 minutes.
    Retrains when the number of newly appended students reaches the threshold.
    """
    count = get_new_student_count()
    if count >= RETRAIN_THRESHOLD:
        _run_retrain(
            f"{count} new student(s) accumulated "
            f"(threshold = {RETRAIN_THRESHOLD})"
        )
    else:
        log.info(
            f"Threshold check — {count}/{RETRAIN_THRESHOLD} new students "
            f"accumulated, no retrain yet."
        )


def midnight_retrain() -> None:
    """
    Fires daily at midnight (Africa/Cairo).
    Retrains if any new data has accumulated since the last retrain,
    ensuring the model is never more than one day stale regardless of traffic.
    """
    count = get_new_student_count()
    if count > 0:
        _run_retrain(f"midnight sweep — {count} new student(s) pending")
    else:
        log.info("Midnight check — no new data, skipping retrain.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info("=" * 60)
    log.info("GPA Goes UP — background scheduler starting")
    log.info(f"  Timezone        : {TIMEZONE}")
    log.info(f"  Retrain threshold: every {RETRAIN_THRESHOLD} new students")
    log.info(f"  Midnight sweep  : daily at 00:00 {TIMEZONE}")
    log.info(f"  CSV base dir    : {BASE_DIR}")
    log.info("=" * 60)

    scheduler = BlockingScheduler(timezone=TIMEZONE)

    scheduler.add_job(
        threshold_check,
        trigger=IntervalTrigger(minutes=30),
        id="threshold_check",
        name="Threshold-based retrain check (every 30 min)",
        replace_existing=True,
        misfire_grace_time=120,
    )

    scheduler.add_job(
        midnight_retrain,
        trigger=CronTrigger(hour=0, minute=0, timezone=TIMEZONE),
        id="midnight_retrain",
        name="Daily midnight retrain sweep",
        replace_existing=True,
        misfire_grace_time=300,
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped cleanly.")
