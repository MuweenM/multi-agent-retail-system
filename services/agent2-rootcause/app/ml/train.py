"""Train and compare the Lecture 6 Agent 2 text-classification workflows."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import joblib
from imblearn.over_sampling import RandomOverSampler, SMOTE
from imblearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import make_scorer, f1_score
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

from retail_common.taxonomy import ROOT_CAUSES

from app.ml.evaluate import classification_metrics, save_confusion_heatmap, save_json
from app.ml.features import load_records, make_dataset, split_dataset


SEED = 3041
MODELS_DIR = Path(__file__).parents[1] / "models"
MODEL_PATH = MODELS_DIR / "rootcause_model.joblib"
RESULTS_PATH = MODELS_DIR / "training_results.json"
HEATMAP_PATH = MODELS_DIR / "confusion_matrix_heatmap.png"


class BalancedMultinomialNB(BaseEstimator, ClassifierMixin):
    """MultinomialNB equivalent of class_weight='balanced' via sample weights."""

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha

    def fit(self, X, y):
        self.model_ = MultinomialNB(alpha=self.alpha)
        counts = {label: sum(value == label for value in y) for label in set(y)}
        weights = [len(y) / (len(counts) * counts[label]) for label in y]
        self.model_.fit(X, y, sample_weight=weights)
        self.classes_ = self.model_.classes_
        return self

    def predict(self, X):
        return self.model_.predict(X)


def _estimator(pipeline_name: str, strategy: str):
    class_weight = "balanced" if strategy == "class_weight=balanced" else None
    if pipeline_name == "BoW + MultinomialNB":
        vectorizer = CountVectorizer(ngram_range=(1, 2), min_df=1)
        classifier = BalancedMultinomialNB() if class_weight else MultinomialNB()
    elif pipeline_name == "TF-IDF + MultinomialNB":
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        classifier = BalancedMultinomialNB() if class_weight else MultinomialNB()
    elif pipeline_name == "TF-IDF + LogisticRegression":
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        classifier = LogisticRegression(max_iter=1000, class_weight=class_weight, random_state=SEED)
    elif pipeline_name == "TF-IDF + LinearSVC + calibration":
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        svc = LinearSVC(class_weight=class_weight, random_state=SEED)
        classifier = CalibratedClassifierCV(svc, method="sigmoid", cv=3)
    elif pipeline_name == "TF-IDF + RandomForest":
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        classifier = RandomForestClassifier(
            n_estimators=160, class_weight=class_weight, random_state=SEED, n_jobs=-1
        )
    else:
        raise ValueError(f"unknown pipeline: {pipeline_name}")

    steps = [("features", vectorizer)]
    if strategy == "random_oversampling":
        steps.append(("resample", RandomOverSampler(random_state=SEED)))
    elif strategy == "SMOTE":
        steps.append(("resample", SMOTE(random_state=SEED, k_neighbors=3)))
    steps.append(("classifier", classifier))
    return Pipeline(steps=steps)


def _run_experiment(name: str, strategy: str, X_train, y_train, X_test, y_test, cv) -> tuple[dict, object]:
    model = _estimator(name, strategy)
    scoring = make_scorer(f1_score, average="macro", zero_division=0)
    cv_result = cross_validate(
        model,
        X_train,
        y_train,
        cv=cv,
        scoring=scoring,
        return_train_score=True,
        n_jobs=1,
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    metrics = classification_metrics(y_test, predictions, list(ROOT_CAUSES))
    metrics.update({
        "pipeline": name,
        "imbalance_strategy": strategy,
        "cv_macro_f1_mean": float(cv_result["test_score"].mean()),
        "cv_macro_f1_std": float(cv_result["test_score"].std()),
        "cv_train_macro_f1_mean": float(cv_result["train_score"].mean()),
        "cv_validation_macro_f1_mean": float(cv_result["test_score"].mean()),
        "held_out_macro_f1": metrics["macro_f1"],
    })
    return metrics, model


def train() -> dict:
    records = load_records()
    texts, labels = make_dataset(records)
    X_train, X_test, y_train, y_test = split_dataset(texts, labels)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    experiments = []
    fitted_models = {}
    pipeline_names = [
        "BoW + MultinomialNB",
        "TF-IDF + MultinomialNB",
        "TF-IDF + LogisticRegression",
        "TF-IDF + LinearSVC + calibration",
        "TF-IDF + RandomForest",
    ]
    strategies = ["class_weight=balanced", "random_oversampling", "SMOTE"]
    for pipeline_name in pipeline_names:
        for strategy in strategies:
            print(f"Training {pipeline_name} / {strategy}")
            metrics, model = _run_experiment(pipeline_name, strategy, X_train, y_train, X_test, y_test, cv)
            experiments.append(metrics)
            fitted_models[(pipeline_name, strategy)] = model

    selected = max(experiments, key=lambda result: (result["held_out_macro_f1"], result["cv_macro_f1_mean"]))
    selected_key = (selected["pipeline"], selected["imbalance_strategy"])
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(fitted_models[selected_key], MODEL_PATH)
    selected_model = fitted_models[selected_key]
    selected_predictions = selected_model.predict(X_test)
    save_confusion_heatmap(y_test, selected_predictions, list(ROOT_CAUSES), HEATMAP_PATH,
                           f"Agent 2 confusion matrix: {selected['pipeline']} / {selected['imbalance_strategy']}")
    payload = {
        "training_date": date.today().isoformat(),
        "dataset": str(Path("data/returns/returns.csv")),
        "input_features": ["product_name", "issue_text"],
        "excluded_features": ["customer", "district", "gender", "channel", "protected_attributes"],
        "cv": "stratified 5-fold",
        "held_out_test_size": 0.2,
        "selection_metric": "held_out_macro_f1",
        "selected_model": selected,
        "experiments": experiments,
        "artifacts": {
            "model": str(MODEL_PATH),
            "confusion_heatmap": str(HEATMAP_PATH),
        },
    }
    save_json(payload, RESULTS_PATH)
    print("Experiment summary (selected by held-out macro-F1):")
    for result in experiments:
        print(
            f"{result['pipeline']} | {result['imbalance_strategy']} | "
            f"accuracy={result['accuracy']:.6f} | "
            f"error={result['misclassification_error']:.6f} | "
            f"macro_f1={result['held_out_macro_f1']:.6f} | "
            f"cv_train_f1={result['cv_train_macro_f1_mean']:.6f} | "
            f"cv_validation_f1={result['cv_validation_macro_f1_mean']:.6f}"
        )
    print("Selected per-class metrics:")
    for label, values in selected["per_class"].items():
        print(
            f"{label} | precision={values['precision']:.6f} | "
            f"recall={values['recall']:.6f} | f1={values['f1']:.6f}"
        )
    print(json.dumps({"selected_model": selected, "model_path": str(MODEL_PATH)}, indent=2))
    return payload


if __name__ == "__main__":
    train()