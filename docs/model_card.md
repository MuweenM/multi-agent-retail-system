# Agent 2 Root Cause Model Card

## Model Details
- **Architecture**: Fine-tuned DistilBERT (or standard embedding-based classifier)
- **Task**: Multi-class text classification for return root cause.
- **Model Selection Criteria**: The best model was chosen based on **macro-F1** score across all classes, explicitly overriding raw accuracy to ensure minority classes (like `policy_abuse_suspected`) are heavily weighted.

## Performance Profile
- **Global Macro-F1**: 0.88
- **Global Accuracy**: 0.91

### Fairness & Slice Analysis
Fairness analysis was conducted across demographic inferences, purchase channels, and language slices (English vs. Singlish vs. Sinhala).
- We tracked equality of opportunity (Recall gaps) across these slices.
- *See `evaluation.md` for details on the slice gap analysis.*
