# Methodology — Ramy Sentiment Intelligence System

## 1. Data Strategy

### 1.1 Data Collection Approach
We employ a dual-track data strategy:

1. **Simulated Data** (primary for development): A custom simulator generates 2,000+ realistic Arabic/Darja reviews that model actual Algerian social media language patterns, including:
   - Code-switching between MSA, Darja, and French
   - Platform-specific patterns (Facebook, Instagram, YouTube)
   - Realistic sentiment distribution (~55% positive, ~25% negative, ~20% neutral)
   - Geographic distribution across Algeria's 58 wilayas

2. **Live Scraping** (production): API-based scrapers for Facebook Graph API, YouTube Data API, and Instagram Basic Display API with rate limiting and data anonymization.

### 1.2 Preprocessing Pipeline
Our preprocessing handles the unique challenges of Algerian Arabic:

| Step | Purpose | Example |
|------|---------|---------|
| Diacritics removal | Normalize tashkeel | عَصِيرٌ → عصير |
| Elongation normalization | Handle expressive text | بنييييين → بنين |
| Letter normalization | Unify letter variants | إ/أ/آ → ا |
| URL/mention removal | Clean social media artifacts | @user https://... → |
| Emoji extraction | Preserve sentiment signals | 😍→ positive signal |
| Darja detection | Flag dialectal text | بزاف, واش, كاين |
| French detection | Flag code-switching | très bon, qualité |

## 2. Model Architecture

### 2.1 Sentiment Classification
- **Base Model**: AraBERT v0.2 (`aubmindlab/bert-base-arabertv02`)
- **Architecture**: AraBERT → [CLS] pooling → Linear(768, 3) → Softmax
- **Training**: Transfer learning with fine-tuning on Ramy-specific data
- **Optimizer**: AdamW (lr=2e-5, warmup=10%)
- **Fallback**: Rule-based lexicon classifier when GPU unavailable

### 2.2 Aspect-Based Sentiment Analysis (ABSA)
Our ABSA pipeline:
1. **Aspect Detection**: Keyword matching with expanded Arabic/Darja lexicons (6 aspects × ~15 keywords)
2. **Aspect Sentiment**: Context window analysis with:
   - Positive/negative modifier detection
   - Negation handling (ما, مش, ماشي, pas)
   - Emoji signal incorporation

**Target Aspects**:
| Aspect | Arabic | Keywords |
|--------|--------|----------|
| Taste | المذاق | مذاق, طعم, نكهة, بنين, لذيذ |
| Price | السعر | سعر, ثمن, غالي, رخيص |
| Packaging | التغليف | تغليف, علبة, قارورة |
| Availability | التوفر | متوفر, نلقاه, مكانش |
| Quality | الجودة | جودة, نوعية, مليح |
| Health | الصحة | صحة, سكر, مواد حافظة |

## 3. Evaluation Framework

### 3.1 Metrics
- **Sentiment**: Accuracy, F1-macro, Precision, Recall per class
- **ABSA**: Per-aspect F1, weighted by frequency
- **Overall**: Cohen's Kappa for inter-annotator agreement

### 3.2 Baselines
1. Random baseline
2. Lexicon-based (AraSenTi)
3. TF-IDF + SVM
4. **AraBERT** (our approach)

## 4. Business Intelligence

The Insight Engine transforms raw analysis into decision-ready intelligence:
- Per-product sentiment scores
- Geographic heatmaps (per-wilaya analysis)
- Temporal trend detection
- Automated Arabic executive summaries (Generative Insight Engine)
- Priority-ranked actionable recommendations
