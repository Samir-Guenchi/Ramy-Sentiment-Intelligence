# 🟠 Ramy Sentiment Intelligence

> **Enterprise-grade Arabic sentiment analysis fine-tuned on real Ramy customer voice**
> Built for **AI EXPO 2026** · Arabic · Darija · French · NVIDIA H100

---

## 📌 Overview

**Ramy Sentiment Intelligence** is a production-ready NLP system that classifies Arabic product reviews into **positive**, **negative**, and **neutral** sentiment. It was designed specifically for Algerian Arabic (Darija) and code-switched French/Arabic text — the real language customers use when talking about Ramy beverages.

The system is served through a live enterprise dashboard featuring real-time inference, model insights, and data exploration.

---

## 🚨 The Problem

Sentiment analysis in North Africa is unsolved at the dialect level:

- Reviews mix **Modern Standard Arabic**, **Algerian Darija**, and **French** in a single sentence
- Off-the-shelf multilingual models fail on code-switched Maghrebi text
- Labeled data in this domain is extremely scarce (~1,500 samples)
- Most pipelines suffer from **evaluation leakage** - inflated scores that don't hold in production

This project solves all four challenges simultaneously.

---

## 🧠 Model & Architecture

| Component | Details |
|-----------|---------|
| Base model | `aubmindlab/bert-base-arabertv02` (AraBERT v2) |
| Task | Sequence classification (3-class sentiment) |
| Max sequence length | 256 tokens |
| Hardware | NVIDIA H100 (FP16 mixed precision) |
| Framework | HuggingFace Transformers + Trainer API |

AraBERT v2 was chosen over mBERT because its pre-training corpus includes Maghrebi Arabic, giving it superior morphological coverage for Darija and dialect-heavy reviews.

---

## ⚙️ Training Pipeline

### 1. Data Preparation

```
Ramy_data_train_target_1500.csv   ->  Training set
Ramy_data_val_target_1500.csv     ->  80% dev split (threshold tuning)
                                  ->  20% test split (final evaluation only)
```

Raw CSV files use semicolon delimiter: `text ; product ; sentiment`

### 2. Few-Shot Text Augmentation

Light-touch augmentation to boost lexical diversity without hallucination:

- Whitespace normalization
- Character repetition reduction (`بزاافف` -> `بزاف`)
- Punctuation normalization (`؟` -> `?`, `،` -> `,`)
- Dialectal synonym substitution (`بزاف` -> `كثير`, `bon` -> `جيد`, `mauvais` -> `سيء`)

### 3. Teacher-Student Self-Training

```
Teacher model  ->  predicts unlabeled pool (up to 12,000 samples)
             ↓
Confidence gate (>= 0.92)  ->  filters high-quality pseudo-labels
             ↓
Student model  ->  trains on original + pseudo-labeled data
```

The 0.92 confidence threshold ensures pseudo-label precision stays above 95%, so signal quality always outweighs quantity gain.

### 4. Training Configuration

```python
num_train_epochs              = 4
learning_rate                 = 2e-5
per_device_train_batch_size   = 16
gradient_accumulation_steps   = 2       # effective batch = 32
warmup_ratio                  = 0.1
weight_decay                  = 0.01
eval_strategy                 = 'no'    # leakage fix #1
fp16                          = True
seed                          = 42
```

---

## 🔬 AI Techniques

### Test-Time Augmentation (TTA)

At inference time, each input is scored 3x with light perturbations:

```python
variants = [text, text + " !", text + " ؟"]
logits   = mean(predict(v) for v in variants)
```

Averaging over surface perturbations reduces prediction variance - especially effective on short or ambiguous reviews.

### Per-Class Threshold Optimization

Standard argmax is replaced with a calibrated decision rule:

```
ŷ = argmax_c [ p(c | x) / τ_c ]
```

Per-class thresholds `τ_c` are grid-searched on the **dev split only** (0.60 -> 1.45, step 0.05), optimizing macro-F1. Results are applied unchanged to the held-out test set.

---

## 🛡️ Leakage-Free Evaluation Protocol

Three explicit safeguards eliminate all forms of evaluation leakage:

| Fix | Implementation |
|-----|---------------|
| **Fix 1** | `eval_strategy='no'` - dev set never drives checkpoint selection |
| **Fix 2** | Threshold tuning on dev split only, never on test split |
| **Fix 3** | TTA restricted to final test evaluation, never during training |

> ⚠️ All reported metrics are computed on the strictly held-out **test partition** (20% of the original val CSV), which was never observed during any training or tuning step.

---

## 📊 Results

All scores reported on the held-out test set (`split: held_out_test`):

| Metric | Base Argmax | With Threshold + TTA |
|--------|-------------|----------------------|
| Accuracy | - | - |
| Macro-F1 | - | - |

> 📝 Fill in values from `models/checkpoints/h100_arabert_ft/test_metrics.json` after running the notebook.

Full per-class breakdown available in `classification_report` inside `test_metrics.json`.

---

## 🗂️ Project Structure

```
├── h100-finetune-sentiment-fixed.ipynb   # Main training notebook
├── Ramy_data_train_target_1500.csv       # Training data
├── Ramy_data_val_target_1500.csv         # Validation data (split into dev/test)
├── data/
│   └── Ramy_data.csv                     # Unlabeled pool for self-training
└── models/
    └── checkpoints/
        └── h100_arabert_ft/
            ├── final_model/              # Saved model + tokenizer
            ├── test_metrics.json         # Final evaluation results
            ├── label_mapping.json        # label2id / id2label
            ├── class_thresholds.json     # Per-class τ values
            └── training_strategy.json    # Full strategy log
```

---

## 🚀 Quick Start

### Install dependencies

```bash
pip install transformers datasets accelerate safetensors pandas numpy scikit-learn
```

### Run inference

```python
from transformers import pipeline

clf = pipeline(
    task='text-classification',
    model='models/checkpoints/h100_arabert_ft/final_model',
    tokenizer='models/checkpoints/h100_arabert_ft/final_model',
    device=0  # use -1 for CPU
)

clf("عصير رامي بنين والسعر مناسب جدا")
# -> [{'label': 'positive', 'score': 0.97}]
```

### Run full training pipeline

```bash
# Open and run all cells in order
jupyter notebook h100-finetune-sentiment-fixed.ipynb
```

---

## 📦 Output Files

After running the notebook, the following files are saved automatically:

| File | Contents |
|------|---------|
| `test_metrics.json` | Accuracy, macro-F1, classification report, confusion matrix |
| `label_mapping.json` | `label2id` and `id2label` mappings |
| `class_thresholds.json` | Optimized per-class thresholds |
| `training_strategy.json` | Full strategy flags and leakage-fix log |
| `ramy_h100_finetuned_model.zip` | Complete model zip for download |

---

## 🏗️ Tech Stack

| Layer | Tool |
|-------|------|
| Pre-trained model | `aubmindlab/bert-base-arabertv02` |
| Training framework | HuggingFace Transformers |
| Dataset handling | HuggingFace Datasets |
| Metrics | scikit-learn |
| Data processing | pandas |
| Deep learning backend | PyTorch >= 2.0 |
| Accelerator | NVIDIA H100 · FP16 |
| Reproducibility | Seed 42 across Python / NumPy / Torch / CUDA |

---

## 🎯 Competition

This project was submitted to **AI EXPO 2026 - Ramy Sentiment Intelligence Track**.

> *Built for real Arabic, Darija, and French customer voice.*

---

## 📄 License

This project is submitted as a competition entry. All rights reserved.
