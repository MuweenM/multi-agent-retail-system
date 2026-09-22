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
