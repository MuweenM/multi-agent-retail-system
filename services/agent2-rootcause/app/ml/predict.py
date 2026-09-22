"""Inference helper for the selected Agent 2 classifier."""

from __future__ import annotations

from pathlib import Path

import joblib

from app.ml.features import analyze_text


MODEL_PATH = Path(__file__).parents[1] / "models" / "rootcause_model.joblib"


def load_model(model_path: Path = MODEL_PATH):
    return joblib.load(model_path)


def predict_root_cause(product_name: str, issue_text: str, model_path: Path = MODEL_PATH) -> str:
    model = load_model(model_path)
    return str(model.predict([analyze_text(f"{product_name} {issue_text}")])[0])