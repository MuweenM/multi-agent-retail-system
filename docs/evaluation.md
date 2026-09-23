# Evaluation Plan

TODO: fill in the metric each agent will be evaluated on.

| Agent                | Metric                                                                                         |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| Agent 1 (Intake)     | ?                                                                                              |
| Agent 2 (Root Cause) | Held-out macro-F1: 0.9034730581; accuracy: 0.9500000000; misclassification error: 0.0500000000 |
| Agent 3 (Retrieval)  | ?                                                                                              |
| Agent 4 (Decision)   | ?                                                                                              |

## Agent 2

- Dataset: `data/returns/returns.csv` (4,000 synthetic labelled returns).
- Inputs: product name and issue text only. Customer, district, gender, channel,
  and protected attributes were excluded.
- Evaluation: stratified 5-fold cross-validation plus a held-out 20% test split.
- Selection metric: held-out macro-F1.
- Selected pipeline: TF-IDF + calibrated LinearSVC with `class_weight="balanced"`.
- Cross-validation train macro-F1 mean: `0.9329002800`.
- Cross-validation validation macro-F1 mean: `0.9318473566`.
- Held-out macro-F1: `0.9034730581`.
- Held-out accuracy: `0.9500000000`.
- Held-out misclassification error: `0.0500000000`.
- Artifacts: `services/agent2-rootcause/app/models/training_results.json`,
  `rootcause_model.joblib`, and `confusion_matrix_heatmap.png`.

### Bulk Pattern Analysis & Clustering Evaluation

- **Clustering Algorithm**: TF-IDF + KMeans with automatic $k$ selection via silhouette score over $k \in [4..12]$.
- **200-Row Planted Evaluation Sample**:
  - Selected $k$: `12`
  - Silhouette score: `0.919511`
  - Clustering purity against gold taxonomy labels: `1.000000` (100.0%)
  - **Planted Pattern Recovery (5 of 5 recovered)**:
    1. Pattern a (`P-014` battery swelling from supplier `S-03`, batch `B-2026-07`): **Recovered** (Cluster with terms `['swelling', 'charging', 'battery', 'charge', '20000']`, 21/21 manufacturing defect).
    2. Pattern b (`P-027` size/fit issue "runs small"): **Recovered** (Cluster with terms `['though', 'shirt', 'runs', 'size', 'small']`, 40/40 size fit issue).
    3. Pattern c (Courier `C-2` transit damage spike on electronics): **Recovered** (Cluster with terms `['arrived', 'courier', 'delivery', 'damaged', 'after']`, 40/40 damaged in transit).
    4. Pattern d (Repeat high-value returns `change_of_mind`): **Recovered** (Clusters capturing repeat smartphone/electronics returns, 100% change of mind).
    5. Pattern e (`P-009` not as described noise cancelling distractor): **Recovered** (Cluster with terms `['product', 'claimed', 'great', 'have', 'life']`, 27/27 not as described).
- **Full 4,000-Row Dataset**:
  - Selected $k$: `12`
  - Silhouette score: `0.163872`
  - Clustering purity against gold labels: `0.725000` (72.5%)
  - Total financial value at risk evaluated: `51,760,000.00 LKR`
  - Top 3 impact products ($\text{returns} \times \text{average order value}$):
    1. `P-012` (5G Android Smartphone 128GB): 125 returns $\times$ 62,000 LKR = `7,750,000.00 LKR`
    2. `P-011` (4G Android Smartphone 64GB): 127 returns $\times$ 38,500 LKR = `4,889,500.00 LKR`
    3. `P-033` (Ceramic Dinner Set 16-Piece): 109 returns $\times$ 14,500 LKR = `1,580,500.00 LKR`
