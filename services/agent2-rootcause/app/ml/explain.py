"""
Explanation module for the Agent 2 root-cause classifier.

The production model is TF-IDF + LinearSVC wrapped in CalibratedClassifierCV.
CalibratedClassifierCV does not expose .coef_ directly, but each calibrated
classifier in .calibrated_classifiers_ holds an .estimator with .coef_.

Strategy:
- Take calibrated_classifiers_[0].estimator.coef_ (shape: n_classes × n_features)
- Retrieve the TF-IDF feature vector for the input text
- For each candidate class: importance_i = coef_[class_idx] * tfidf_vector
- Return top-N feature names by importance value

This approach is correct for LinearSVC wrapped in CalibratedClassifierCV, and
avoids fabricating values: every returned term corresponds to a real non-zero
TF-IDF weight multiplied by a real learned coefficient.
"""

from __future__ import annotations

import numpy as np


def explain_candidates(
    pipeline,
    text: str,
    candidate_labels: list[str],
    top_n: int = 5,
) -> dict[str, list[str]]:
    """Return top-N supporting terms for each candidate label.

    Args:
        pipeline: The fitted imblearn/sklearn Pipeline (TF-IDF + CalibratedClassifierCV).
        text:     Pre-processed input text (already passed through analyze_text).
        candidate_labels: List of label strings to explain (in order).
        top_n:    Number of top terms to return per label.

    Returns:
        dict mapping label → list[str] of top supporting feature names.
        Returns empty lists if explanation is not possible for any label.
    """
    result: dict[str, list[str]] = {label: [] for label in candidate_labels}

    try:
        # Step 1: Get the TF-IDF vectorizer from the pipeline
        tfidf = pipeline.named_steps.get("features")
        if tfidf is None:
            return result

        # Step 2: Transform the input text into a TF-IDF vector
        tfidf_matrix = tfidf.transform([text])  # shape (1, n_features)
        tfidf_vector = np.asarray(tfidf_matrix.todense())[0]  # shape (n_features,)

        feature_names = np.array(tfidf.get_feature_names_out())

        # Step 3: Access LinearSVC coefficients through CalibratedClassifierCV
        calibrated_clf = pipeline.named_steps.get("classifier")
        if calibrated_clf is None:
            return result

        # CalibratedClassifierCV stores a list of calibrated sub-classifiers.
        # Each sub-classifier has .estimator (the LinearSVC) and .classes_.
        calibrated_classifiers = getattr(calibrated_clf, "calibrated_classifiers_", None)
        if not calibrated_classifiers:
            return result

        # Use the first calibrated fold's LinearSVC for coefficient lookup.
        # All folds are trained on the same feature space.
        inner_estimator = calibrated_classifiers[0].estimator
        coef = getattr(inner_estimator, "coef_", None)  # shape (n_classes, n_features)
        classes = getattr(inner_estimator, "classes_", None)

        if coef is None or classes is None:
            return result

        class_list = list(classes)

        for label in candidate_labels:
            if label not in class_list:
                result[label] = []
                continue

            class_idx = class_list.index(label)
            if class_idx >= coef.shape[0]:
                result[label] = []
                continue

            # Importance = coefficient × TF-IDF value (element-wise)
            # Only consider features with non-zero TF-IDF weight in this text.
            importance = coef[class_idx] * tfidf_vector  # shape (n_features,)

            # Select only features that appear in this text (non-zero TF-IDF)
            nonzero_mask = tfidf_vector > 0
            if not np.any(nonzero_mask):
                result[label] = []
                continue

            nonzero_importance = importance[nonzero_mask]
            nonzero_names = feature_names[nonzero_mask]

            # Rank by importance descending; take top_n
            n = min(top_n, len(nonzero_importance))
            top_indices = np.argsort(nonzero_importance)[::-1][:n]
            result[label] = [str(nonzero_names[i]) for i in top_indices]

    except Exception:
        # Never fabricate explanation values; return empty on any failure.
        return {label: [] for label in candidate_labels}

    return result
