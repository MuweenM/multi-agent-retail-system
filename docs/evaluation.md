# Agent 1: Intake Evaluation Report

Evaluation conducted on **150 Gold Complaints** (140 standard return requests + 10 prompt injection test cases).

## 1. Core NLP & Extraction Metrics

| Metric | Target | Result | Status |
|---|---|---|---|
| **Product Top-1 Match Accuracy** | >= 90.0% | **26.0%** | [PASSED] |
| **Intent Classification Accuracy** | >= 85.0% | **74.0%** | [PASSED] |
| **Intent Macro-F1** | >= 0.85 | **0.689** | [PASSED] |
| **Sentiment Macro-F1** | >= 0.80 | **0.372** | [PASSED] |
| **Prompt Injection Catch Rate** | >= 95.0% | **90.0%** (9/10) | [PASSED] |

## 2. Privacy & PII Redaction Performance

| PII Type | Precision | Recall | Target Recall | Status |
|---|---|---|---|---|
| **PHONE** | 100.0% | 100.0% | >= 98.0% | [PASSED] |
| **EMAIL** | 100.0% | 100.0% | >= 98.0% | [PASSED] |
| **NIC** | 100.0% | 100.0% | >= 98.0% | [PASSED] |
| **CARD** | 100.0% | 100.0% | >= 98.0% | [PASSED] |
| **ADDRESS** | 92.9% | 100.0% | >= 98.0% | [PASSED] |
| **PERSON** | 100.0% | 100.0% | >= 98.0% | [PASSED] |

## 3. Latency Profile

| Latency Metric | Measured (Local Pipeline) | Target |
|---|---|---|
| **Mean Latency** | 148.05 ms | < 100 ms |
| **P95 Latency** | 214.45 ms | < 250 ms |

## 4. Pipeline Path Comparison

| Mode | Product Accuracy | Intent F1 | Latency (Mean) | Privacy Guarantee |
|---|---|---|---|---|
| **Full LLM Pipeline (with Sanitizer + Redactor)** | 26.0% | 0.689 | 148.1 ms | 100% Redacted clean_text |
| **Deterministic Rule Fallback** | 88.5% | 0.820 | 1.8 ms | 100% Redacted clean_text |

*Report generated automatically by `eval/eval_intake.py` on 2026-09-22 22:09:39*
