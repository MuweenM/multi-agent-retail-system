"""Metrics and plots for the Lecture 6 Agent 2 experiments."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


def classification_metrics(y_true, y_pred, labels: list[str]) -> dict:
    report = classification_report(
        y_true, y_pred, labels=labels, target_names=labels, output_dict=True, zero_division=0
    )
    accuracy = accuracy_score(y_true, y_pred)
    return {
        "accuracy": float(accuracy),
        "misclassification_error": float(1.0 - accuracy),
        "per_class": {
            label: {
                "precision": float(report[label]["precision"]),
                "recall": float(report[label]["recall"]),
                "f1": float(report[label]["f1-score"]),
            }
            for label in labels
        },
        "macro_f1": float(report["macro avg"]["f1-score"]),
    }


def save_confusion_heatmap(y_true, y_pred, labels: list[str], output_path: Path, title: str) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    figure, axis = plt.subplots(figsize=(12, 10))
    image = axis.imshow(matrix, interpolation="nearest", cmap="Blues")
    figure.colorbar(image, ax=axis)
    axis.set(
        xticks=np.arange(len(labels)), yticks=np.arange(len(labels)),
        xticklabels=labels, yticklabels=labels,
        ylabel="True label", xlabel="Predicted label", title=title,
    )
    plt.setp(axis.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    threshold = matrix.max() / 2.0 if matrix.size else 0
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            axis.text(column, row, int(matrix[row, column]), ha="center", va="center",
                      color="white" if matrix[row, column] > threshold else "black")
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def save_json(payload: dict, output_path: Path) -> None:
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")