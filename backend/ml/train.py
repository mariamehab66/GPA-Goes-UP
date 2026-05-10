"""
ml/train.py

Training pipeline for the GPA Goes UP ML recommender.

Models compared:
  1. Random Forest
  2. XGBoost
  3. Logistic Regression
  4. SoftVotingEnsemble (averages probabilities of the above three)

Evaluation: tolerance accuracy — within 1 bucket position of the truth.
Cross-validation: Leave-One-Student-Out (LOSO-CV).

Entry points:
  train_and_save(data_dir=None)
"""

from __future__ import annotations

import os
import pickle
import numpy as np
import pandas as pd

from sklearn.ensemble      import RandomForestClassifier
from sklearn.linear_model  import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.compose       import ColumnTransformer
from sklearn.pipeline      import Pipeline

from xgboost import XGBClassifier

from ml.data_loader import (
    BUCKET_ORDER,
    GPA_COUNTED,
    GRADE_POINTS,
    build_prerequisites_map,
    filter_training_rows,
    load_csvs,
)
from ml.features import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    build_training_features,
)
from ml import r2_storage

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODELS_DIR, "best_course_model.pkl")

# ---------------------------------------------------------------------------
# SoftVotingEnsemble
# ---------------------------------------------------------------------------

class SoftVotingEnsemble:
    """
    Averages predict_proba() across a list of fitted (preprocessor, classifier)
    pairs and exposes the same predict / predict_proba interface as a single
    sklearn Pipeline so predict.py can use it transparently.
    """

    def __init__(self, members: list[tuple]):
        # members: list of (fitted_preprocessor, fitted_classifier)
        self.members = members

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        probas = []
        for pre, clf in self.members:
            Xt = pre.transform(X)
            probas.append(clf.predict_proba(Xt))
        return np.mean(probas, axis=0)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)


# ---------------------------------------------------------------------------
# Metric
# ---------------------------------------------------------------------------

def tolerance_accuracy(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    tolerance: int = 1,
) -> float:
    return float(np.mean(np.abs(y_true.astype(int) - y_pred.astype(int)) <= tolerance))


# ---------------------------------------------------------------------------
# Preprocessor + classifier factories
# ---------------------------------------------------------------------------

def _make_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def _make_classifiers() -> dict[str, object]:
    return {
        "RandomForest": RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="mlogloss",
            random_state=42,
            verbosity=0,
        ),
        "LogisticRegression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            solver="lbfgs",
            random_state=42,
        ),
    }


# ---------------------------------------------------------------------------
# Enrichment stats (fold-safe)
# ---------------------------------------------------------------------------

def _compute_enrichment_stats(
    filtered_enrollment: pd.DataFrame,
    student_ids: list,
) -> dict[str, dict]:
    """
    Compute per-course historical stats from a subset of students only.
    Used inside LOSO-CV folds so the held-out student never contributes.
    """
    sub = filtered_enrollment[filtered_enrollment["Student_ID"].isin(student_ids)]
    if sub.empty:
        return {}

    stats: dict[str, dict] = {}
    for code, grp in sub.groupby("Course_Code"):
        grades = grp[grp["Grade"].isin(GPA_COUNTED)]["Grade"]
        if grades.empty:
            continue
        pts = grades.map(GRADE_POINTS).dropna()
        fail_mask = grp["Grade"].isin({"F", "Abs"})
        stats[str(code)] = {
            "avg_grade": float(pts.mean()) if not pts.empty else 0.0,
            "fail_rate": float(fail_mask.mean()),
        }
    return stats


# ---------------------------------------------------------------------------
# SMOTE (adaptive, applied to already-transformed data)
# ---------------------------------------------------------------------------

def _apply_smote(X_train: np.ndarray, y_train: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Apply SMOTE with adaptive k_neighbors.
    Falls back to no-op if imbalanced-learn is not installed or data is too small.
    """
    try:
        from imblearn.over_sampling import SMOTE
    except ImportError:
        return X_train, y_train

    classes, counts = np.unique(y_train, return_counts=True)
    min_count = int(counts.min())
    k = min(5, min_count - 1)
    if k < 1:
        return X_train, y_train

    try:
        sm = SMOTE(k_neighbors=k, random_state=42)
        return sm.fit_resample(X_train, y_train)
    except Exception:
        return X_train, y_train


# ---------------------------------------------------------------------------
# LOSO-CV
# ---------------------------------------------------------------------------

def run_loso_cv(
    feature_df: pd.DataFrame,
    filtered_enrollment: pd.DataFrame,
    label_encoder: LabelEncoder,
) -> dict[str, dict]:
    """
    Leave-One-Student-Out CV over all students.

    For each fold:
      1. Compute enrichment stats from training students only.
      2. Re-apply enrichment features to the training subset.
      3. Fit one preprocessor per fold; apply SMOTE only for LogisticRegression.
      4. Train all 3 base classifiers + Ensemble (RF+XGB+LR) + RF_XGB_Ensemble.
      5. Score on the held-out student.
    """
    student_ids = list(feature_df["student_id"].unique())
    y_all = label_encoder.transform(feature_df["grade_bucket"])

    model_names = ["RandomForest", "XGBoost", "LogisticRegression", "Ensemble", "RF_XGB_Ensemble"]
    results: dict[str, dict] = {n: {"fold_scores": []} for n in model_names}

    for held_out in student_ids:
        train_ids  = [s for s in student_ids if s != held_out]
        train_mask = feature_df["student_id"] != held_out
        test_mask  = feature_df["student_id"] == held_out

        X_train_raw = feature_df.loc[train_mask].copy()
        X_test_raw  = feature_df.loc[test_mask].copy()
        y_train = y_all[train_mask.values]
        y_test  = y_all[test_mask.values]

        if len(np.unique(y_train)) < 2 or len(X_test_raw) == 0:
            continue

        # -- Fold enrichment stats (training students only) -------------------
        fold_stats = _compute_enrichment_stats(filtered_enrollment, train_ids)
        for code, s in fold_stats.items():
            X_train_raw.loc[X_train_raw["course_code"] == code, "course_avg_grade"] = s["avg_grade"]
            X_train_raw.loc[X_train_raw["course_code"] == code, "course_fail_rate"] = s["fail_rate"]
            X_test_raw.loc[X_test_raw["course_code"]  == code, "course_avg_grade"] = s["avg_grade"]
            X_test_raw.loc[X_test_raw["course_code"]  == code, "course_fail_rate"] = s["fail_rate"]

        X_train_feat = X_train_raw[ALL_FEATURES]
        X_test_feat  = X_test_raw[ALL_FEATURES]

        # -- Fit preprocessor on training fold --------------------------------
        pre = _make_preprocessor()
        X_train_t = pre.fit_transform(X_train_feat)
        X_test_t  = pre.transform(X_test_feat)

        # SMOTE for LogisticRegression only.
        # RF and XGBoost already handle class imbalance via class_weight="balanced"
        # and are hurt by synthetic neighbors on small datasets.
        X_train_lr, y_train_lr = _apply_smote(X_train_t, y_train)

        # -- Train base classifiers -------------------------------------------
        classifiers = _make_classifiers()
        fitted_clfs: dict[str, object] = {}
        for name, clf in classifiers.items():
            X_tr = X_train_lr if name == "LogisticRegression" else X_train_t
            y_tr = y_train_lr if name == "LogisticRegression" else y_train
            clf.fit(X_tr, y_tr)
            fitted_clfs[name] = clf
            y_pred = clf.predict(X_test_t)
            results[name]["fold_scores"].append(tolerance_accuracy(y_test, y_pred))

        # -- Ensemble (RF + XGB + LR) -----------------------------------------
        ensemble = SoftVotingEnsemble(
            [(pre, fitted_clfs["RandomForest"]),
             (pre, fitted_clfs["XGBoost"]),
             (pre, fitted_clfs["LogisticRegression"])]
        )
        y_pred_ens = ensemble.predict(X_test_feat)
        results["Ensemble"]["fold_scores"].append(tolerance_accuracy(y_test, y_pred_ens))

        # -- RF_XGB_Ensemble (RF + XGB only, no LR) ---------------------------
        rf_xgb_ensemble = SoftVotingEnsemble(
            [(pre, fitted_clfs["RandomForest"]),
             (pre, fitted_clfs["XGBoost"])]
        )
        y_pred_rx = rf_xgb_ensemble.predict(X_test_feat)
        results["RF_XGB_Ensemble"]["fold_scores"].append(tolerance_accuracy(y_test, y_pred_rx))

    for name in results:
        scores = results[name]["fold_scores"]
        results[name]["mean"] = float(np.mean(scores)) if scores else 0.0
        results[name]["std"]  = float(np.std(scores))  if scores else 0.0

    return results


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def train_and_save(data_dir: str) -> dict:
    os.makedirs(MODELS_DIR, exist_ok=True)

    # ── 1. Load data ─────────────────────────────────────────────────────────
    enrollment, student, course, prerequisites = load_csvs(data_dir)

    filtered = filter_training_rows(enrollment)

    course_credits = (
        course[["Code", "Credit_Hours"]].rename(columns={"Code": "Course_Code"})
    )
    filtered = filtered.merge(course_credits, on="Course_Code", how="left")
    filtered["Credit_Hours"] = filtered["Credit_Hours"].fillna(3.0).astype(float)

    prereqs_map = build_prerequisites_map(prerequisites)

    # ── 2. Compute global enrichment stats (all students, for final model) ───
    all_student_ids = list(filtered["Student_ID"].unique())
    global_enrichment = _compute_enrichment_stats(filtered, all_student_ids)

    # ── 3. Build feature matrix with global enrichment placeholders ----------
    feature_df = build_training_features(
        filtered, course, prereqs_map,
        enrichment_stats=global_enrichment,
    )
    feature_df = feature_df.dropna(subset=["grade_bucket"]).reset_index(drop=True)

    if feature_df.empty:
        raise RuntimeError("No training rows produced. Check your data source.")

    # ── 4. Label encoder ─────────────────────────────────────────────────────
    le = LabelEncoder()
    le.fit(BUCKET_ORDER)

    valid_mask = feature_df["grade_bucket"].isin(set(BUCKET_ORDER))
    feature_df = feature_df[valid_mask].reset_index(drop=True)

    # ── 5. LOSO-CV (4 models) ────────────────────────────────────────────────
    cv_results = run_loso_cv(feature_df, filtered, le)

    # ── 6. Pick best model ────────────────────────────────────────────────────
    # Use mean − std as selection criterion to penalise high variance.
    # A consistent 0.61 is safer for academic advising than a swinging 0.62.
    best_name = max(cv_results, key=lambda k: cv_results[k]["mean"] - cv_results[k]["std"])

    # ── 7. Retrain best on ALL data ──────────────────────────────────────────
    X_full = feature_df[ALL_FEATURES]
    y_full = le.transform(feature_df["grade_bucket"])

    pre_full = _make_preprocessor()
    X_full_t = pre_full.fit_transform(X_full)

    # SMOTE for LogisticRegression only (same rule as in LOSO-CV).
    X_full_lr, y_full_lr = _apply_smote(X_full_t, y_full)

    classifiers = _make_classifiers()

    if best_name in ("Ensemble", "RF_XGB_Ensemble"):
        # Both ensemble variants need all base classifiers trained first.
        fitted_clfs = {}
        for name, clf in classifiers.items():
            X_tr = X_full_lr if name == "LogisticRegression" else X_full_t
            y_tr = y_full_lr if name == "LogisticRegression" else y_full
            clf.fit(X_tr, y_tr)
            fitted_clfs[name] = clf

        if best_name == "Ensemble":
            best_model = SoftVotingEnsemble(
                [(pre_full, fitted_clfs["RandomForest"]),
                 (pre_full, fitted_clfs["XGBoost"]),
                 (pre_full, fitted_clfs["LogisticRegression"])]
            )
        else:  # RF_XGB_Ensemble
            best_model = SoftVotingEnsemble(
                [(pre_full, fitted_clfs["RandomForest"]),
                 (pre_full, fitted_clfs["XGBoost"])]
            )
    else:
        X_tr = X_full_lr if best_name == "LogisticRegression" else X_full_t
        y_tr = y_full_lr if best_name == "LogisticRegression" else y_full
        clf = classifiers[best_name]
        clf.fit(X_tr, y_tr)
        # Wrap in SoftVotingEnsemble with a single member for a uniform interface.
        best_model = SoftVotingEnsemble([(pre_full, clf)])

    # ── 8. Persist artifact ───────────────────────────────────────────────────
    artifact = {
        "model":             best_model,
        "label_encoder":     le,
        "feature_columns":   ALL_FEATURES,
        "best_model_name":   best_name,
        "cv_results":        cv_results,
        "bucket_order":      BUCKET_ORDER,
        "enrichment_stats":  global_enrichment,
    }
    with open(MODEL_PATH, "wb") as fh:
        pickle.dump(artifact, fh)

    # Push the new model (and training state) to R2 so restarts load the
    # freshly trained artifact rather than the previous version.
    r2_storage.upload_model()

    return {
        "best_model": best_name,
        "total_training_rows": len(feature_df),
        "model_saved_to": MODEL_PATH,
        "cv_results": {
            name: {
                "mean_tolerance_accuracy": round(res["mean"], 4),
                "std":                     round(res["std"],  4),
                "fold_scores":             [round(s, 4) for s in res["fold_scores"]],
            }
            for name, res in cv_results.items()
        },
    }


# ---------------------------------------------------------------------------
# Run directly: python -m ml.train   (from the backend/ folder)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import importlib

    # Import this module under its real name (ml.train) so that
    # SoftVotingEnsemble is pickled as ml.train.SoftVotingEnsemble,
    # not __main__.SoftVotingEnsemble. Without this, Flask cannot
    # unpickle the saved model because __main__ is app.py at runtime.
    _mod = importlib.import_module("ml.train")

    _data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "training")

    print("=" * 60)
    print("GPA Goes UP — Manual Training")
    print(f"Data directory : {_data_dir}")
    print(f"Model output   : {MODEL_PATH}")
    print("=" * 60)

    try:
        metrics = _mod.train_and_save(data_dir=_data_dir)
    except Exception as exc:
        print(f"\nTraining failed: {exc}")
        sys.exit(1)

    print(f"\nTotal training rows : {metrics['total_training_rows']}")
    print(f"Model saved to      : {metrics['model_saved_to']}")
    print(f"\n{'Model':<22} {'Mean':>8} {'Std':>8} {'Mean-Std':>10}  Fold scores")
    print("-" * 80)
    for name, res in metrics["cv_results"].items():
        mean     = res["mean_tolerance_accuracy"]
        std      = res["std"]
        selected = " ← SELECTED" if name == metrics["best_model"] else ""
        print(
            f"{name:<22} {mean:>8.4f} {std:>8.4f} {mean - std:>10.4f}  "
            f"{res['fold_scores']}{selected}"
        )
    print("=" * 60)

