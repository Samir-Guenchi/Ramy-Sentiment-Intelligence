#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║              Ramy Sentiment Intelligence — Live Demo                ║
║          Explainable AI (XAI) for Arabic Sentiment Analysis         ║
║                       AI EXPO 2026 — Blida 1                        ║
╚══════════════════════════════════════════════════════════════════════╝

This demo showcases the Attention-Based Explainability module.
For each input review, it:
  1. Predicts sentiment (5-class: positive/negative/neutral/improvement/question)
  2. Extracts token-level attribution scores (WHY the model decided)
  3. Generates visual attention heatmaps and natural-language explanations
  4. Saves results and visualizations to results/

USAGE:
    python demo.py

REQUIREMENTS:
    pip install torch transformers matplotlib numpy
    + The fine-tuned model at models/checkpoints/h100_arabert_ft/final_model/

AUTHORS:
    Samir Guenchi (ENSIA) • Senouci Amira (ENSIA)
    Abdennour Guerroudj (USTHB) • Megamez Abderrahmane (USTHB)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# ── Setup path ───────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ── Styling constants ────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
MAGENTA= "\033[95m"

SENTIMENT_COLORS = {
    "positive":    GREEN,
    "negative":    RED,
    "neutral":     YELLOW,
    "improvement": BLUE,
    "question":    MAGENTA,
}


def print_header():
    """Print a professional header for the demo."""
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════════╗
║          🧠  Ramy Sentiment Intelligence — XAI Demo                  ║
║              Attention-Based Explainable AI (2026)                    ║
║                    AI EXPO 2026 — Blida University                    ║
╚══════════════════════════════════════════════════════════════════════╝{RESET}
""")


def print_separator():
    print(f"{CYAN}{'─' * 70}{RESET}")


def print_result(idx: int, result: dict):
    """Pretty-print a single explanation result."""
    color = SENTIMENT_COLORS.get(result["predicted_class"], YELLOW)
    emoji = result.get("emoji", "")

    print_separator()
    print(f"\n{BOLD}  Example {idx}{RESET}")
    print(f"  {BOLD}Input:{RESET}  {result['text']}")
    print(f"  {BOLD}Prediction:{RESET}  {color}{emoji} {result['predicted_class'].upper()}{RESET}"
          f"  ({result['confidence']:.1%} confidence)")

    # All class probabilities
    print(f"\n  {BOLD}Class Probabilities:{RESET}")
    for cls, score in sorted(result["all_scores"].items(), key=lambda x: -x[1]):
        bar_len = int(score * 40)
        bar = "█" * bar_len + "░" * (40 - bar_len)
        cls_color = SENTIMENT_COLORS.get(cls, YELLOW)
        print(f"    {cls_color}{cls:>12}{RESET}  {bar}  {score:.3f}")

    # Token attributions
    print(f"\n  {BOLD}Token Attribution (top words):{RESET}")
    for word, score in result["top_tokens"]:
        bar_len = int(score * 30)
        bar = "▓" * bar_len + "░" * (30 - bar_len)
        intensity = f"{color}" if score > 0.5 else YELLOW
        print(f"    {intensity}{word:>15}{RESET}  {bar}  {score:.3f}")

    # Full attribution
    print(f"\n  {BOLD}Full Word Attribution Map:{RESET}")
    words_line = "    "
    for word, score in result["word_attributions"]:
        intensity = color if score > 0.5 else (YELLOW if score > 0.2 else RESET)
        words_line += f"{intensity}[{word}:{score:.2f}]{RESET} "
    print(words_line)

    # Natural language explanation
    print(f"\n  {BOLD}Explanation:{RESET}")
    print(f"    {result['explanation_text']}")
    print()


def generate_attribution_chart(results: list, output_path: Path):
    """Generate a visual attribution chart and save as PNG."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib import rcParams
    except ImportError:
        print(f"  {YELLOW}⚠ matplotlib not available, skipping chart.{RESET}")
        return

    # Configure for Arabic text support
    rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']

    n_results = len(results)
    fig, axes = plt.subplots(n_results, 1, figsize=(14, 4 * n_results), dpi=150)
    if n_results == 1:
        axes = [axes]

    color_map = {
        "positive":    "#2D8B4E",
        "negative":    "#E31E24",
        "neutral":     "#F7B731",
        "improvement": "#1F6FEB",
        "question":    "#8B5CF6",
    }

    for idx, (ax, res) in enumerate(zip(axes, results)):
        words = [w for w, _ in res["word_attributions"]]
        scores = [s for _, s in res["word_attributions"]]
        pred = res["predicted_class"]
        bar_color = color_map.get(pred, "#94A3B8")

        # Create horizontal bar chart
        y_pos = range(len(words))
        colors = [bar_color if s > 0.3 else "#CBD5E1" for s in scores]

        ax.barh(y_pos, scores, color=colors, edgecolor="white", height=0.6)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(words, fontsize=10)
        ax.invert_yaxis()
        ax.set_xlim(0, 1.05)
        ax.set_xlabel("Attribution Score", fontsize=11)
        ax.set_title(
            f'Example {idx + 1}: {res["predicted_class"].upper()} '
            f'({res["confidence"]:.1%}) — "{res["text"][:50]}..."',
            fontsize=12, fontweight="bold", pad=12,
        )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(str(output_path), bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  {GREEN}✓ Attribution chart saved: {output_path}{RESET}")


def generate_confusion_summary_chart(results: list, output_path: Path):
    """Generate a class probability comparison chart."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return

    n = len(results)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4), dpi=150)
    if n == 1:
        axes = [axes]

    color_map = {
        "positive":    "#2D8B4E",
        "negative":    "#E31E24",
        "neutral":     "#F7B731",
        "improvement": "#1F6FEB",
        "question":    "#8B5CF6",
    }

    for ax, res in zip(axes, results):
        classes = list(res["all_scores"].keys())
        probs = [res["all_scores"][c] for c in classes]
        colors = [color_map.get(c, "#94A3B8") for c in classes]
        pred = res["predicted_class"]

        bars = ax.bar(classes, probs, color=colors, edgecolor="white", width=0.6)

        # Highlight predicted class
        for bar, cls in zip(bars, classes):
            if cls == pred:
                bar.set_edgecolor("#0a1628")
                bar.set_linewidth(2)

        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Probability")
        ax.set_title(f'Prediction: {pred.upper()}', fontweight="bold")
        ax.tick_params(axis='x', rotation=30)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(str(output_path), bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  {GREEN}✓ Class probability chart saved: {output_path}{RESET}")


def generate_html_report(results: list, explainer, output_path: Path):
    """Generate a full interactive HTML report with highlighted attributions."""
    cards = []
    for idx, res in enumerate(results, 1):
        card_html = explainer.generate_html_highlight(res, title=f"Example {idx}")
        cards.append(card_html)

    html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ramy XAI — Attention Attribution Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', 'Noto Sans Arabic', sans-serif;
            background: linear-gradient(135deg, #0a1628 0%, #1a2744 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 40px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{
            font-size: 2rem;
            background: linear-gradient(135deg, #f0c040, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .header p {{ color: #94a3b8; font-size: 0.95rem; }}
        .card {{
            background: rgba(255,255,255,0.95);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            color: #1a1a2e;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #64748b;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Ramy Sentiment Intelligence — XAI Report</h1>
            <p>Attention-Based Token Attribution · AI EXPO 2026 · {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        </div>
        {''.join(f'<div class="card">{c}</div>' for c in cards)}
        <div class="footer">
            <p>Generated by Ramy Sentiment Intelligence · Sponsored by RAMY</p>
            <p>Samir Guenchi (ENSIA) · Senouci Amira (ENSIA) ·
               Abdennour Guerroudj (USTHB) · Megamez Abderrahmane (USTHB)</p>
        </div>
    </div>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"  {GREEN}✓ Interactive HTML report saved: {output_path}{RESET}")


# ── Demo Samples ─────────────────────────────────────────────

DEMO_SAMPLES = [
    # Positive
    "عصير رامي بنين والسعر مناسب جدا",
    # Negative
    "المنتج فيه سكر بزاف وما عجبنيش الطعم تبدل",
    # Neutral
    "شريت عصير رامي من الحانوت ديال الحومة",
    # Improvement suggestion
    "لازم يزيدو نكهات جداد وينقصو السكر شوية",
    # Question
    "واش عصير رامي متوفر في باتنة ؟",
    # Mixed (code-switched Darija + French)
    "le goût de ramy c'est bon mais l'emballage خايب",
    # Strong positive
    "أحسن عصير في الجزائر رامي يجنن 😍🔥",
    # Health concern
    "هل عصير رامي فيه مواد حافظة ولا طبيعي ؟",
]


# ── Main ─────────────────────────────────────────────────────

def main():
    print_header()

    # ── Locate model ──
    model_path = PROJECT_ROOT / "models" / "checkpoints" / "h100_arabert_ft" / "final_model"
    if not model_path.exists():
        # Check for zip
        zip_path = PROJECT_ROOT / "ramy_h100_finetuned_model.zip"
        if zip_path.exists():
            print(f"  {YELLOW}⚠ Extracting model from zip...{RESET}")
            import shutil
            model_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.unpack_archive(str(zip_path), str(model_path))
        else:
            print(f"  {RED}✗ Model not found at: {model_path}{RESET}")
            print(f"  {YELLOW}  Run the training notebook first, or set FINETUNED_MODEL_PATH.{RESET}")
            print(f"\n  {BOLD}Running in DEMO MODE with simulated outputs...{RESET}\n")
            _run_demo_mode()
            return

    # ── Load explainer ──
    print(f"  {CYAN}Loading model from: {model_path}{RESET}")
    from src.explainability.attention_explainer import AttentionExplainer
    explainer = AttentionExplainer(str(model_path))
    print(f"  {GREEN}✓ Model loaded successfully on {explainer.device}{RESET}\n")

    # ── Run explanations ──
    print(f"  {BOLD}Running {len(DEMO_SAMPLES)} demo predictions with XAI explanations...{RESET}\n")

    results = []
    for idx, text in enumerate(DEMO_SAMPLES, 1):
        result = explainer.explain(text, method="combined", top_k=5)
        results.append(result)
        print_result(idx, result)

    print_separator()
    print(f"\n{BOLD}  Generating visual outputs...{RESET}\n")

    # ── Save visualisations ──
    generate_attribution_chart(results, RESULTS_DIR / "xai_attribution_chart.png")
    generate_confusion_summary_chart(results, RESULTS_DIR / "xai_class_probabilities.png")
    generate_html_report(results, explainer, RESULTS_DIR / "xai_report.html")

    # ── Save JSON results ──
    json_results = []
    for r in results:
        json_results.append({
            "text": r["text"],
            "predicted_class": r["predicted_class"],
            "confidence": r["confidence"],
            "all_scores": r["all_scores"],
            "top_tokens": r["top_tokens"],
            "explanation": r["explanation_text"],
            "method": r["method"],
        })

    json_path = RESULTS_DIR / "xai_results.json"
    json_path.write_text(
        json.dumps(json_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  {GREEN}✓ JSON results saved: {json_path}{RESET}")

    # ── Summary ──
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════════╗
║                        Demo Complete ✓                               ║
╚══════════════════════════════════════════════════════════════════════╝{RESET}

  Generated files in {RESULTS_DIR}/:
    • xai_attribution_chart.png   — Token attribution heatmap
    • xai_class_probabilities.png — Per-class probability distributions
    • xai_report.html             — Interactive HTML report (open in browser)
    • xai_results.json            — Machine-readable results

  {BOLD}To view the HTML report:{RESET}
    Open results/xai_report.html in your browser.

  {BOLD}Team:{RESET}
    Samir Guenchi (ENSIA) · Senouci Amira (ENSIA)
    Abdennour Guerroudj (USTHB) · Megamez Abderrahmane (USTHB)
""")


def _run_demo_mode():
    """Fallback demo with simulated outputs when model is not available."""
    print(f"  {BOLD}Demo Mode — Showing architecture and sample outputs{RESET}\n")

    print(f"""
  {BOLD}Explainable AI Architecture:{RESET}

  ┌─────────────────────────────────────────────────────────────┐
  │                    Input Review (Arabic/Darija)               │
  │                "عصير رامي بنين والسعر مناسب"                 │
  └──────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │              AraBERT v2 Tokenizer (WordPiece)                │
  │            → ["عصير", "رامي", "بنين", "##وال", ...]          │
  └──────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │              Fine-tuned AraBERT (12 layers)                  │
  │                                                              │
  │   Layer 1  ──▶  Attention Heads  ──▶  Layer 2 ──▶ ...       │
  │                                                              │
  │   ┌── Attention Rollout ─────────────────────────────┐      │
  │   │  Aggregated multi-layer attention flow from       │      │
  │   │  [CLS] token to all input tokens                  │      │
  │   └──────────────────────────────────────────────────┘      │
  │                                                              │
  │   ┌── Gradient × Attention ──────────────────────────┐      │
  │   │  Gradient of predicted class w.r.t. embeddings    │      │
  │   │  multiplied by attention weights                  │      │
  │   └──────────────────────────────────────────────────┘      │
  └──────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │              Combined Attribution Scores                     │
  │                                                              │
  │   "بنين"  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░  0.89           │
  │   "مناسب" ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░  0.71           │
  │   "رامي"  ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░  0.31           │
  │   "عصير"  ▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░  0.12           │
  │   "والسعر" ▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░  0.08           │
  └──────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  😊 POSITIVE (99.3%)                                        │
  │                                                              │
  │  Explanation: The model classified this as POSITIVE          │
  │  because "بنين" (tasty) and "مناسب" (suitable) carry        │
  │  strong positive semantic signal.                            │
  └─────────────────────────────────────────────────────────────┘

  {BOLD}Model Performance (from training notebook):{RESET}

  ┌────────────────┬──────────────┬────────────────────────┐
  │ Metric         │ Base Argmax  │ With Threshold + TTA   │
  ├────────────────┼──────────────┼────────────────────────┤
  │ Accuracy       │   0.9506     │     0.9506             │
  │ Macro-F1       │   0.9437     │     0.9437             │
  └────────────────┴──────────────┴────────────────────────┘

  Per-class results:
  ┌──────────────┬───────────┬────────┬──────────┬─────────┐
  │ Class        │ Precision │ Recall │ F1-Score │ Support │
  ├──────────────┼───────────┼────────┼──────────┼─────────┤
  │ improvement  │   1.00    │  0.85  │   0.92   │   13    │
  │ negative     │   0.94    │  1.00  │   0.97   │   16    │
  │ neutral      │   0.92    │  0.86  │   0.89   │   14    │
  │ positive     │   0.96    │  1.00  │   0.98   │   25    │
  │ question     │   0.93    │  1.00  │   0.96   │   13    │
  └──────────────┴───────────┴────────┴──────────┴─────────┘

  {GREEN}✓ Demo mode complete.{RESET}
  {YELLOW}→ Load the fine-tuned model for live XAI explanations.{RESET}
""")


if __name__ == "__main__":
    main()
