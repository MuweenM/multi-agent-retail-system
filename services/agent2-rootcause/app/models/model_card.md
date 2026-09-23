# Agent 2 Root Cause Classifier

## Dataset

The model is trained on the synthetic labelled returns dataset at
`data/returns/returns.csv`. Inputs are the catalog product name and return issue
text only. Customer references, district, gender, channel, and protected attributes
are excluded. The dataset contains planted patterns and approximately five percent
label noise.

## Model

The selected model is chosen by held-out macro-F1 after comparing five classifiers,
three imbalance strategies, and stratified five-fold cross-validation. The selected
pipeline is saved as `rootcause_model.joblib` beside this card.

Selected model: TF-IDF + LinearSVC wrapped in CalibratedClassifierCV with
`class_weight="balanced"`.

## Training date

2026-09-22.

## Metric

Macro-F1 is the selection metric. The measured held-out macro-F1 is `0.9034730581`,
held-out accuracy is `0.9500000000`, and misclassification error is `0.0500000000`.
The five-fold validation macro-F1 mean is `0.9318473566`. The results file records accuracy,
misclassification error, per-class precision, recall, F1, confusion matrix output,
and train-versus-validation scores.

## Known weaknesses

- Synthetic text and planted patterns may overstate real-world performance.
- Approximately five percent label noise limits the attainable score.
- English-only training does not establish Sinhala or Tamil performance.
- The temporary local tokenizer is used until the shared analyzer is available.
- The classifier cannot infer unseen product names or novel root causes reliably.
- Class imbalance remains material even after fold-local resampling comparisons.
