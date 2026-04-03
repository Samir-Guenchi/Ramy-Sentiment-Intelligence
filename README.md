<h1 align="center">🧠 Ramy — Product Sentiment Intelligence System</h1>

<p align="center">
  <strong>AI-Powered Arabic & Algerian Darja Sentiment Analysis for Product Reviews</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#methodology">Methodology</a> •
  <a href="#team">Team</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/NLP-AraBERT-green?logo=huggingface&logoColor=white" alt="AraBERT"/>
  <img src="https://img.shields.io/badge/Dashboard-FastAPI%20%2B%20React-red" alt="FastAPI + React"/>
  <img src="https://img.shields.io/badge/Track-Industry-orange" alt="Industry Track"/>
  <img src="https://img.shields.io/badge/AI_EXPO-2026-purple" alt="AI EXPO 2026"/>
</p>

---

## 📌 About

**Ramy Sentiment Intelligence** is a full-stack NLP system that analyzes consumer sentiment from Arabic and Algerian Darja product reviews. Built for the **AI EXPO 2026** at **Blida 1 University** (Industry Track), this system provides actionable business intelligence to **Ramy** — Algeria's leading food & beverage company.

### The Problem

Algerian consumers express opinions across social media in a mix of Modern Standard Arabic (MSA), Algerian Darja (dialect), and French. Traditional sentiment analysis tools fail on this multilingual, code-switched text. Ramy needs an intelligent system that **understands its customers' real voice**.

### The Solution

A pipeline that:
1. **Collects** reviews from Facebook, Instagram, and YouTube
2. **Analyzes** sentiment using fine-tuned AraBERT models
3. **Extracts** aspect-level opinions (taste, price, packaging, availability, quality, health)
4. **Visualizes** insights through an interactive dashboard with geographic intelligence

### 2026 Web Dashboard (Current)

- Frontend: React + Recharts (served by FastAPI templates/static)
- Backend: FastAPI (`webapp/main.py`)
- Model APIs:
  - `GET /api/model/status`
  - `POST /api/model/predict` with JSON body:

```json
{
  "comments": [
    "ramy tres bon et naturel",
    "prix trop cher"
  ]
}
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Sentiment Classification** | Configurable labels (default: 5-class) using AraBERT |
| 🎯 **Aspect-Based Analysis** | Per-aspect sentiment for taste, price, packaging, availability, quality, health |
| 🗺️ **Geographic Intelligence** | Per-wilaya sentiment mapping across Algeria's 58 wilayas |
| 📊 **Interactive Dashboard** | 5-page Streamlit dashboard with real-time analytics |
| 🧪 **Live Analyzer** | Type any Arabic/Darja text → instant AI analysis |
| 📝 **Auto Reports** | Generative business summaries in Arabic |
| 🌐 **Dialect-Aware** | Handles MSA, Darja, Franco-Arabic code-switching |

---

## 🏗️ Architecture

```
ramy-sentiment/
├── config/                    # Configuration & settings
├── data/                      # Raw, processed & sample data
├── src/
│   ├── data_pipeline/         # Scraping, simulation, preprocessing
│   ├── models/                # AraBERT sentiment & ABSA models
│   ├── analytics/             # Business intelligence & reporting
│   └── utils/                 # Arabic text utilities & logging
├── dashboard/                 # Streamlit multi-page dashboard
│   ├── pages/                 # Dashboard pages
│   └── components/            # Reusable UI components
├── tests/                     # Unit tests
└── docs/                      # Documentation & report structure
```

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/your-username/ramy-sentiment.git
cd ramy-sentiment

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 Usage

### Generate Sample Data
```bash
python -m src.data_pipeline.simulator
```

### Run the Dashboard
```bash
streamlit run dashboard/app.py
```

### Run the Professional Web Dashboard (No Streamlit)
```bash
uvicorn webapp.main:app --host 127.0.0.1 --port 8081
```

Windows example (verified):
```bash
"C:\Users\Samir Guenchi\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn webapp.main:app --host 127.0.0.1 --port 8081
```

### Train with Competition Pipeline (CV Ensemble + Threshold Tuning)
```bash
python -m src.models.train_sentiment \
  --trainer competition \
  --train-file data/augmented/Ramy_data_train_target_1500.csv \
  --val-file data/augmented/Ramy_data_val_target_1500.csv \
  --output-dir models/competition \
  --metrics-output data/processed/competition_metrics.json \
  --cv-folds 5
```

### Fine-Tune AraBERT on GPU (RTX 3050 Ti)
```bash
python -m src.models.train_sentiment \
  --trainer transformer \
  --data-dir data \
  --output-dir models/checkpoints/arabert_ft \
  --metrics-output data/processed/transformer_metrics.json \
  --epochs 4 \
  --batch-size 16 \
  --learning-rate 2e-5
```

Notes:
- If `--train-file` and `--val-file` are omitted, the script auto-resolves from `data/augmented`.
- GPU is auto-detected (`cuda`) when available.

Optional pseudo-labeling from unlabeled data:
```bash
python -m src.models.train_sentiment \
  --train-file data/augmented/Ramy_data_train_target_1500.csv \
  --val-file data/augmented/Ramy_data_val_target_1500.csv \
  --unlabeled-file data/raw/unlabeled_reviews.csv \
  --enable-pseudo-labeling \
  --pseudo-label-min-confidence 0.92
```

### Analyze a Single Review
```python
from src.models.sentiment_classifier import SentimentClassifier

classifier = SentimentClassifier()
result = classifier.predict("عصير رامي بزاف بنين والسعر معقول")
print(result)
# {'sentiment': 'positive', 'confidence': 0.94, 'scores': {...}}
```

---

## 🔬 Methodology

1. **Data Collection** — Simulated realistic reviews + social media scraping pipeline
2. **Preprocessing** — Arabic normalization, diacritics removal, Darja handling, emoji extraction
3. **Model** — `aubmindlab/bert-base-arabertv02` fine-tuned on Algerian product reviews
4. **ABSA** — Dual-task: Aspect Term Extraction + Aspect Sentiment Classification
5. **Evaluation** — stratified group K-fold OOF F1-macro, validation F1-macro, confusion matrix
6. **Leaderboard Optimizations** — weighted ensemble, per-class threshold tuning, temperature scaling, TTA

## 🏆 Competition Workflow

- Playbook: `docs/competition_playbook.md`
- Submission tracker template: `docs/submission_log_template.csv`
- Training entrypoint: `python -m src.models.train_sentiment`

---

## 🎯 Innovation: Generative Insight Engine

Our standout feature: **AI-generated Arabic business reports** that automatically summarize findings into actionable paragraphs for Ramy's decision-makers. Example output:

> *"تحليل 2,847 مراجعة يكشف أن 73% من التعليقات السلبية في ولاية البليدة تتعلق بنسبة السكر في عصير رامي أب. نقترح تطوير نسخة منخفضة السكر لهذه المنطقة."*

---

## 🏭 Industry Track Alignment

This project is explicitly designed for the **Industry Track: AI for Sentiment Analysis** and maps to real business needs.

### Business Problems Addressed

1. Customer feedback analysis at scale for product lines.
2. Opinion mining from social and review-style text.
3. Brand and reputation monitoring through sentiment trends.
4. Marketing intelligence by product, aspect, and geography.
5. Decision support for product, pricing, and packaging strategy.

### Ramy-Focused Enterprise Use Cases

1. Detect negative sentiment spikes for specific products in near real time.
2. Identify root causes using aspect-level analysis (taste, price, packaging, availability, quality, health).
3. Compare brand perception by wilaya to support regional campaign planning.
4. Export filtered review evidence for internal quality and marketing teams.
5. Generate executive-ready summaries for strategic meetings.

### Why This Fits Industry Deployment

1. Uses production-friendly APIs (FastAPI) and dashboard analytics.
2. Supports reproducible model training and evaluation metrics.
3. Includes taxonomy-driven product categorization for reporting consistency.
4. Provides explainable outputs (confusion matrix, class reports, hard examples).
5. Bridges NLP research and actionable business decisions.

### Suggested Demo Narrative (Competition Pitch)

1. Start with a live dashboard overview of sentiment by category and subcategory.
2. Drill into a negative trend and show aspect-level diagnosis.
3. Export supporting reviews and show evidence-backed recommendation.
4. Close with KPI impact: faster response time, improved customer satisfaction, better product-market fit.

---

## 🏫 Academic Context

- **Event**: AI EXPO 2026 — Blida 1 University
- **Track**: Industry
- **Focus**: Product Review Analysis
- **Partner Company**: Ramy Group (Algeria)
- **Academic Year**: 2025–2026

---

## 👥 Team

| Name | Role |
|---|---|
| *Your Name* | Project Lead & NLP Engineer |
| *Team Member* | Data Engineer |
| *Team Member* | Frontend Developer |

---

## 📄 License

This project is developed for academic purposes as part of the AI EXPO 2026 exhibition.

---

<p align="center">
  Made with ❤️ for Algeria's AI community
</p>
