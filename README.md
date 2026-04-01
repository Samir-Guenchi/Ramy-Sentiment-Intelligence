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
  <img src="https://img.shields.io/badge/Dashboard-Streamlit-red?logo=streamlit&logoColor=white" alt="Streamlit"/>
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
uvicorn webapp.main:app --reload --port 8080
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
5. **Evaluation** — F1-macro, precision, recall, confusion matrix, Cohen's kappa

---

## 🎯 Innovation: Generative Insight Engine

Our standout feature: **AI-generated Arabic business reports** that automatically summarize findings into actionable paragraphs for Ramy's decision-makers. Example output:

> *"تحليل 2,847 مراجعة يكشف أن 73% من التعليقات السلبية في ولاية البليدة تتعلق بنسبة السكر في عصير رامي أب. نقترح تطوير نسخة منخفضة السكر لهذه المنطقة."*

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
