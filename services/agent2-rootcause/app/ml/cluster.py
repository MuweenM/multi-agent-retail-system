"""
KMeans issue text clustering and evaluation module for Agent 2.

Features:
- TF-IDF + KMeans clustering.
- Silhouette-score based k selection from k in [4..12].
- Per-cluster top-5 TF-IDF terms, dominant root-cause label, and size.
- Nearest cluster assignment via cosine similarity against centroids.
- Emerging cluster detection (share grew >= 2x vs previous period).
- Clustering purity evaluation against gold labels.
- Planted pattern recovery verification.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity

from retail_common.logging_config import get_logger
from retail_common.schemas.bulk import IssueCluster

from app.ml.features import analyze_text

logger = get_logger(__name__)


def select_best_k(
    X: Any,
    k_range: range | list[int] = range(4, 13),
    random_state: int = 3041,
) -> tuple[int, float]:
    """Select the optimal k in k_range maximizing the silhouette score.

    Args:
        X: Sparse TF-IDF matrix.
        k_range: Candidate cluster counts to evaluate.
        random_state: Random seed for reproducibility.

    Returns:
        tuple of (best_k, best_silhouette_score).
    """
    n_samples = X.shape[0]
    # Filter k_range to valid values (< n_samples)
    valid_ks = [k for k in k_range if 2 <= k < n_samples]
    if not valid_ks:
        return max(2, min(4, n_samples)), 0.0

    best_k = valid_ks[0]
    best_score = -1.0

    sample_size = 2000 if n_samples > 2000 else None

    for k in valid_ks:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X)
        try:
            if sample_size is not None:
                score = float(
                    silhouette_score(
                        X, labels, sample_size=sample_size, random_state=random_state
                    )
                )
            else:
                score = float(silhouette_score(X, labels))
        except Exception as exc:
            logger.debug("Silhouette score calculation failed for k=%d: %s", k, exc)
            score = -1.0

        if score > best_score:
            best_score = score
            best_k = k

    return best_k, round(best_score, 6)


def cluster_issue_texts(
    texts: list[str],
    labels: list[str] | None = None,
    dates: list[date | str] | None = None,
    k_range: range | list[int] = range(4, 13),
    random_state: int = 3041,
    max_features: int = 1000,
) -> tuple[list[IssueCluster], int, float, TfidfVectorizer, KMeans]:
    """Cluster issue texts with KMeans and automatic silhouette-based k selection.

    Args:
        texts: Raw issue texts (will be preprocessed via analyze_text).
        labels: Optional corresponding root-cause labels for dominant cause lookup.
        dates: Optional return dates for emerging growth calculation.
        k_range: Candidate cluster counts (default 4..12).
        random_state: Random seed.
        max_features: TF-IDF feature vocabulary size.

    Returns:
        tuple of (clusters, selected_k, silhouette_score, vectorizer, fitted_kmeans).
    """
    cleaned_texts = [analyze_text(t) for t in texts]
    vectorizer = TfidfVectorizer(max_features=max_features)
    X = vectorizer.fit_transform(cleaned_texts)

    best_k, best_score = select_best_k(X, k_range=k_range, random_state=random_state)

    km = KMeans(n_clusters=best_k, random_state=random_state, n_init=10)
    cluster_assignments = km.fit_predict(X)

    feature_names = np.array(vectorizer.get_feature_names_out())

    # Calculate time split for growth calculation if dates are provided
    parsed_dates: list[date | None] = []
    if dates:
        for d in dates:
            if isinstance(d, date):
                parsed_dates.append(d)
            elif isinstance(d, str) and d.strip():
                try:
                    parsed_dates.append(date.fromisoformat(d.strip()))
                except ValueError:
                    parsed_dates.append(None)
            else:
                parsed_dates.append(None)

    valid_dates = [d for d in parsed_dates if d is not None]
    has_date_split = len(valid_dates) >= 2
    if has_date_split:
        min_date, max_date = min(valid_dates), max(valid_dates)
        mid_date = min_date + (max_date - min_date) / 2
        p1_total = sum(1 for d in parsed_dates if d is not None and d < mid_date)
        p2_total = sum(1 for d in parsed_dates if d is not None and d >= mid_date)
    else:
        p1_total = p2_total = 0

    clusters: list[IssueCluster] = []

    for cid in range(best_k):
        member_indices = [i for i, c in enumerate(cluster_assignments) if c == cid]
        cluster_size = len(member_indices)
        if cluster_size == 0:
            continue

        # Dominant root cause
        if labels:
            member_labels = [labels[i] for i in member_indices if i < len(labels)]
            dominant_cause = (
                Counter(member_labels).most_common(1)[0][0]
                if member_labels
                else "unknown"
            )
        else:
            dominant_cause = "unknown"

        # Top 5 TF-IDF terms for this cluster
        member_vecs = X[member_indices].toarray()
        mean_vec = member_vecs.mean(axis=0)
        top_indices = np.argsort(mean_vec)[::-1][:5]
        top_terms = [
            str(feature_names[idx])
            for idx in top_indices
            if mean_vec[idx] > 0
        ]

        # Growth calculation vs previous period
        growth_vs_prev: float | None = None
        if has_date_split and p1_total > 0 and p2_total > 0:
            c_p1 = sum(1 for i in member_indices if parsed_dates[i] is not None and parsed_dates[i] < mid_date)  # type: ignore[operator]
            c_p2 = sum(1 for i in member_indices if parsed_dates[i] is not None and parsed_dates[i] >= mid_date)  # type: ignore[operator]
            s1 = c_p1 / p1_total if p1_total > 0 else 0.0
            s2 = c_p2 / p2_total if p2_total > 0 else 0.0
            if s1 > 0:
                growth_vs_prev = round(s2 / s1, 4)
            elif s2 > 0:
                # Emerged entirely in recent period: growth multiplier relative to baseline fraction
                growth_vs_prev = round(s2 / (0.5 / p1_total), 4)
            else:
                growth_vs_prev = 0.0

        cluster_obj = IssueCluster(
            cluster_id=cid,
            size=cluster_size,
            top_terms=top_terms,
            dominant_root_cause=dominant_cause,
            growth_vs_prev=growth_vs_prev,
        )
        clusters.append(cluster_obj)

    # Sort clusters by size descending
    clusters.sort(key=lambda c: c.size, reverse=True)
    return clusters, best_k, best_score, vectorizer, km


def assign_to_nearest_cluster(
    text: str,
    vectorizer: TfidfVectorizer,
    kmeans_model: KMeans,
) -> int:
    """Assign new issue text to nearest cluster centroid using cosine similarity.

    Args:
        text: Input issue text string.
        vectorizer: Fitted TfidfVectorizer.
        kmeans_model: Fitted KMeans model with cluster_centers_.

    Returns:
        int cluster_id of the nearest cluster.
    """
    cleaned = analyze_text(text)
    tfidf_vec = vectorizer.transform([cleaned])
    similarities = cosine_similarity(tfidf_vec, kmeans_model.cluster_centers_)[0]
    return int(np.argmax(similarities))


def evaluate_clustering_purity(
    cluster_ids: list[int],
    gold_labels: list[str],
) -> float:
    """Calculate clustering purity against gold labels.

    Purity = (1/N) * sum_k max_j |cluster_k intersect class_j|
    """
    if not cluster_ids or not gold_labels or len(cluster_ids) != len(gold_labels):
        return 0.0

    total_samples = len(cluster_ids)
    clusters = set(cluster_ids)
    correct_count = 0

    for cid in clusters:
        members_gold = [
            gold_labels[i] for i, c in enumerate(cluster_ids) if c == cid
        ]
        if members_gold:
            most_frequent_count = Counter(members_gold).most_common(1)[0][1]
            correct_count += most_frequent_count

    return round(correct_count / total_samples, 6)


def verify_planted_patterns(
    clusters: list[IssueCluster],
    sample_returns: list[dict[str, str]],
) -> dict[str, str]:
    """Verify recovery of the 5 planted patterns based on calculated cluster evidence.

    Returns dict mapping pattern name to 'recovered' | 'partially recovered' | 'not recovered'.
    """
    results: dict[str, str] = {}

    # Pattern a: Battery swelling (P-014 from S-03 batch B-2026-07)
    battery_cluster = any(
        "battery" in c.top_terms or "swelling" in c.top_terms
        for c in clusters
    )
    if battery_cluster:
        results["battery_swelling_p014"] = "recovered"
    else:
        results["battery_swelling_p014"] = "not recovered"

    # Pattern b: Size fit issue ("runs small" on P-027)
    size_cluster = any(
        ("small" in c.top_terms or "runs" in c.top_terms or "shirt" in c.top_terms)
        and c.dominant_root_cause == "size_fit_issue"
        for c in clusters
    )
    if size_cluster:
        results["size_fit_p027"] = "recovered"
    else:
        results["size_fit_p027"] = "not recovered"

    # Pattern c: Courier C-2 transit damage on electronics
    courier_cluster = any(
        ("courier" in c.top_terms or "damaged" in c.top_terms)
        and c.dominant_root_cause == "damaged_in_transit"
        for c in clusters
    )
    if courier_cluster:
        results["transit_damage_courier_c2"] = "recovered"
    else:
        results["transit_damage_courier_c2"] = "not recovered"

    # Pattern d: High-value repeat returns (change_of_mind)
    repeat_cluster = any(
        c.dominant_root_cause == "change_of_mind"
        for c in clusters
    )
    if repeat_cluster:
        results["repeat_customer_change_of_mind"] = "recovered"
    else:
        results["repeat_customer_change_of_mind"] = "not recovered"

    # Pattern e: Not as described keyword distractor (P-009 noise cancelling)
    p009_cluster = any(
        ("noise" in c.top_terms or "cancelling" in c.top_terms or "claimed" in c.top_terms)
        and c.dominant_root_cause == "not_as_described"
        for c in clusters
    )
    if p009_cluster:
        results["p009_not_as_described"] = "recovered"
    else:
        # Check if terms appeared partially
        partial = any(
            c.dominant_root_cause == "not_as_described" for c in clusters
        )
        results["p009_not_as_described"] = "partially recovered" if partial else "not recovered"

    return results
