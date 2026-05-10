"""
ml/predict.py

Inference pipeline and greedy schedule selector.

Public API:
    recommend(student_data, rule_engine_payload, course_df, prerequisites_map)
        → dict with top_recommended, alternative_courses, and metadata.
"""

from __future__ import annotations

import os
import pickle

import pandas as pd

from ml.data_loader import BUCKET_ORDER, BUCKET_TO_GRADES
from ml.features    import ALL_FEATURES, build_inference_features
from ml.train       import MODEL_PATH, SoftVotingEnsemble  # noqa: F401 — needed for pickle

# Bucket index used for ranking: lower index = better predicted grade.
_BUCKET_RANK: dict[str, int] = {b: i for i, b in enumerate(BUCKET_ORDER)}

# Keys added internally during ranking — stripped before the API response.
_INTERNAL_KEYS = frozenset({"_bucket_rank", "_weight", "_failed", "_past_gap"})


# ---------------------------------------------------------------------------
# Model loader
# ---------------------------------------------------------------------------

def load_model() -> dict:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"No trained model found at '{MODEL_PATH}'. "
            "Call POST /api/admin/retrain to train the model first."
        )
    with open(MODEL_PATH, "rb") as fh:
        return pickle.load(fh)


# ---------------------------------------------------------------------------
# Prediction + ranking
# ---------------------------------------------------------------------------

def predict_and_rank(
    student_data: dict,
    rule_engine_payload: dict,
    course_df: pd.DataFrame,
    prerequisites_map: dict[str, list[str]],
) -> list[dict]:
    """
    Score every eligible course and return them sorted best-predicted-grade first.

    Each returned dict is the original course dict enriched with:
        predicted_grade_bucket  str   e.g. "Good"
        predicted_grade_range   str   e.g. "B+, B"   (shows both bucket + grades, Q2)
        grade_probabilities     dict  {bucket: probability, …}
        _bucket_rank            int   (internal, stripped before API response)
    """
    artifact          = load_model()
    model             = artifact["model"]
    le                = artifact["label_encoder"]
    enrichment_stats  = artifact.get("enrichment_stats", {})

    eligible_courses = rule_engine_payload.get("engine_suggested_courses", [])
    if not eligible_courses:
        return []

    feat_df = build_inference_features(
        student_data, eligible_courses, course_df, prerequisites_map,
        enrichment_stats=enrichment_stats,
    )

    if feat_df.empty:
        return []

    X            = feat_df[ALL_FEATURES]
    pred_encoded = model.predict(X)
    pred_proba   = model.predict_proba(X)          # shape (n_courses, n_classes)
    pred_buckets = le.inverse_transform(pred_encoded)

    # Build class-probability dict using the label encoder's class order.
    class_names: list[str] = list(le.inverse_transform(range(len(le.classes_))))

    ranked: list[dict] = []
    for i, course in enumerate(eligible_courses):
        bucket = str(pred_buckets[i])
        ranked.append({
            **course,
            "predicted_grade_bucket": bucket,
            "predicted_grade_range":  BUCKET_TO_GRADES.get(bucket, ""),
            "grade_probabilities": {
                class_names[j]: round(float(pred_proba[i][j]), 4)
                for j in range(len(class_names))
            },
            "_bucket_rank": _BUCKET_RANK.get(bucket, len(BUCKET_ORDER)),
        })

    # Primary sort: best predicted grade first.
    # Tiebreaker: bottleneck_weight (higher = more important to take early).
    ranked.sort(key=lambda c: (c["_bucket_rank"], -int(c.get("bottleneck_weight", 0))))
    return ranked


# ---------------------------------------------------------------------------
# Greedy selector
# ---------------------------------------------------------------------------

def greedy_selector(
    ranked_courses: list[dict],
    max_allowed_hours: int,
) -> dict:
    """
    Split the ranked list into top_recommended and alternative_courses.

    Rules:
      1. Add courses to top_recommended until max_allowed_hours is reached.
      2. STRICT ELECTIVE RULE: exactly one elective per group may enter
         top_recommended, and it must be the group's highest-scoring course.
         Group key: (Level, Semester, Type) — consistent with the rule engine.
         Score: _bucket_rank ASC, then probability of predicted bucket DESC.
      3. All non-winner electives from a group go directly to alternative_courses.
      4. Everything that cannot fit in the hours budget goes to alternative_courses.

    Internal annotation keys are stripped from the returned dicts.
    """
    # ── Step 1: pre-select the best elective per group ────────────────────────
    # Score tuple: (bucket_rank, -prob) — lower is better on both dimensions.
    _best: dict[tuple, tuple] = {}   # group_key → (score_tuple, course_code)

    for c in ranked_courses:
        if not c.get("Is_elective"):
            continue
        group_key = (
            c.get("Level", 0),
            str(c.get("Semester", "")).lower(),
            str(c.get("Type", "")),
        )
        bucket = c.get("predicted_grade_bucket", "")
        score  = (
            c.get("_bucket_rank", len(BUCKET_ORDER)),
            -c.get("grade_probabilities", {}).get(bucket, 0.0),
        )
        if group_key not in _best or score < _best[group_key][0]:
            _best[group_key] = (score, c.get("Code", ""))

    elective_winners:       set[str]   = {entry[1] for entry in _best.values()}
    placed_elective_groups: set[tuple] = set()   # groups already in top_recommended

    # ── Step 2: greedy fill ───────────────────────────────────────────────────
    top_recommended:     list[dict] = []
    alternative_courses: list[dict] = []
    hours_used: float = 0.0

    for course in ranked_courses:
        credit_hours = float(course.get("Credit_Hours", 3))
        is_elective  = bool(course.get("Is_elective", False))
        clean        = {k: v for k, v in course.items() if k not in _INTERNAL_KEYS}

        if is_elective:
            group_key = (
                course.get("Level", 0),
                str(course.get("Semester", "")).lower(),
                str(course.get("Type", "")),
            )
            # Non-winner → always alternative, no budget check needed.
            if course.get("Code", "") not in elective_winners:
                alternative_courses.append(clean)
                continue
            # Winner but group already placed (safety guard).
            if group_key in placed_elective_groups:
                alternative_courses.append(clean)
                continue

        # Hours budget check.
        if hours_used + credit_hours <= max_allowed_hours:
            top_recommended.append(clean)
            hours_used += credit_hours
            if is_elective:
                placed_elective_groups.add(group_key)
        else:
            alternative_courses.append(clean)

    return {
        "top_recommended":         top_recommended,
        "alternative_courses":     alternative_courses,
        "total_recommended_hours": hours_used,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def recommend(
    student_data: dict,
    rule_engine_payload: dict,
    course_df: pd.DataFrame,
    prerequisites_map: dict[str, list[str]],
) -> dict:
    """
    Full pipeline: predict grades → rank → greedy selector → return split lists.

    Return shape:
    {
        student_id, target_semester, academic_status, max_allowed_hours,
        warnings, total_recommended_hours,
        top_recommended:     [ {course fields + prediction fields}, … ],
        alternative_courses: [ {course fields + prediction fields}, … ],
    }
    """
    max_hours = int(rule_engine_payload.get("max_allowed_hours", 18))

    ranked    = predict_and_rank(student_data, rule_engine_payload, course_df, prerequisites_map)
    selection = greedy_selector(ranked, max_hours)

    return {
        "student_id":        rule_engine_payload.get("student_id"),
        "target_semester":   rule_engine_payload.get("target_semester"),
        "academic_status":   rule_engine_payload.get("academic_status"),
        "max_allowed_hours": max_hours,
        "warnings":          rule_engine_payload.get("warnings", []),
        **selection,
    }
