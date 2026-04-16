#!/usr/bin/env python3
"""Generate an A2 print-ready poster with embedded logos and refined design."""

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read_b64(name):
    with open(ROOT / name, "rb") as f:
        return base64.b64encode(f.read()).decode()

univ_b64 = read_b64("LogoUnivOriginal.png")
ai_b64   = read_b64("LogoL.png")
ramy_b64 = read_b64("Ramylogo.png")

html = r"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8">
<title>AI EXPO 2026 — Ramy Sentiment Intelligence</title>
<style>
/* ================================================================
   A2 Portrait Academic Poster  —  420 mm x 594 mm
   AI EXPO 2026 — University of Blida 1
   Fully self-contained — zero external dependencies
   ================================================================ */

@page { size: 420mm 594mm; margin: 0; }

*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    width: 420mm;
    height: 594mm;
    margin: 0 auto;
    background: #ffffff;
    color: #1e293b;
    display: flex;
    flex-direction: column;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

/* ── HEADER ──────────────────────────────────────────── */

.hdr {
    background: linear-gradient(160deg, #040d1a 0%, #0c1d3a 45%, #132d52 100%);
    color: #fff;
    padding: 9mm 14mm 8mm;
    text-align: center;
    flex-shrink: 0;
    position: relative;
    overflow: hidden;
}

/* subtle geometric decoration */
.hdr::before {
    content: '';
    position: absolute;
    top: -40mm;
    right: -30mm;
    width: 120mm;
    height: 120mm;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(212,160,21,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.hdr::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2.5mm;
    background: linear-gradient(90deg, #b8860b, #d4a015, #f0c040, #d4a015, #b8860b);
}

.hdr-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    z-index: 1;
}

.logo {
    height: 32mm;
    width: auto;
    object-fit: contain;
}
.logo.univ {
    background: #fff;
    border-radius: 50%;
    padding: 1.5mm;
    height: 30mm;
    width: 30mm;
}

.hdr-center { flex: 1; padding: 0 6mm; }

.title {
    font-size: 36pt;
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -0.3pt;
    margin-bottom: 2mm;
}
.gold { color: #e8b828; }

.sub {
    font-size: 13pt;
    font-weight: 300;
    color: #7a93b8;
    letter-spacing: 2pt;
    text-transform: uppercase;
    margin-bottom: 3mm;
}

.badge {
    display: inline-block;
    font-size: 13pt;
    font-weight: 600;
    color: #e8b828;
    padding: 1.5mm 6mm;
    border: 1pt solid rgba(232,184,40,0.35);
    border-radius: 2mm;
    background: rgba(232,184,40,0.06);
}

/* ── BODY ────────────────────────────────────────────── */

.body {
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3.5mm;
    padding: 4mm 8mm 3mm;
    min-height: 0;
}
.col { display: flex; flex-direction: column; gap: 3mm; }

/* ── SECTIONS ────────────────────────────────────────── */

.s {
    background: #f8f9fb;
    border: 0.5pt solid #dfe5ee;
    border-radius: 2.5mm;
    padding: 4mm 5mm 3.5mm;
    break-inside: avoid;
}

.sh {
    font-size: 15pt;
    font-weight: 700;
    color: #0c1d3a;
    margin-bottom: 2mm;
    padding-bottom: 1.8mm;
    border-bottom: 1.2pt solid #d4a015;
    display: flex;
    align-items: center;
    gap: 2mm;
}

.sn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 6mm;
    height: 6mm;
    background: linear-gradient(135deg, #0c1d3a, #1a3060);
    color: #e8b828;
    font-size: 9.5pt;
    font-weight: 800;
    border-radius: 1.5mm;
    flex-shrink: 0;
}

.sb {
    font-size: 10pt;
    line-height: 1.42;
    color: #334155;
    text-align: justify;
    hyphens: auto;
}
.sb p { margin-bottom: 1.5mm; }
.sb ul { padding-left: 4mm; margin: 1mm 0; }
.sb li { margin-bottom: 1mm; font-size: 9.5pt; line-height: 1.38; }
.sb li::marker { color: #d4a015; font-weight: 700; }

.b { font-weight: 700; }

/* ── TAGS ────────────────────────────────────────────── */
.t {
    display: inline-block;
    padding: 0.6mm 2.5mm;
    border-radius: 1mm;
    font-size: 8pt;
    font-weight: 600;
    margin: 0.3mm;
    vertical-align: middle;
}
.tp { background: #d1fae5; color: #065f46; }
.tn { background: #fee2e2; color: #991b1b; }
.tu { background: #fef3c7; color: #92400e; }
.ti { background: #dbeafe; color: #1e40af; }
.tq { background: #ede9fe; color: #5b21b6; }
.tt { background: #0c1d3a; color: #e8b828; }

/* ── PIPELINE ────────────────────────────────────────── */
.pipe {
    background: #fff;
    border: 0.5pt solid #dfe5ee;
    border-radius: 2mm;
    padding: 2.5mm 3mm;
    margin: 2mm 0;
}
.pr { display: flex; align-items: center; gap: 1.5mm; margin-bottom: 1.5mm; }
.pr:last-child { margin-bottom: 0; }
.pb {
    flex: 1;
    text-align: center;
    padding: 1.8mm 2mm;
    border-radius: 1.5mm;
    font-size: 8pt;
    font-weight: 600;
    line-height: 1.25;
}
.pb small { font-weight: 400; font-size: 7pt; display: block; margin-top: 0.3mm; opacity: 0.85; }
.pd { background: #0c1d3a; color: #fff; }
.pg { background: linear-gradient(135deg, #d4a015, #c08a0e); color: #0c1d3a; }
.pe { background: #166534; color: #fff; }
.px { background: #5b21b6; color: #fff; border: 0.8pt solid #e8b828; }
.pa { font-size: 11pt; color: #94a3b8; font-weight: 700; flex-shrink: 0; }

/* ── METRICS ─────────────────────────────────────────── */
.mg { display: grid; grid-template-columns: 1fr 1fr; gap: 2mm; margin: 2mm 0; }
.mc {
    background: linear-gradient(135deg, #0c1d3a, #1a3060);
    color: #fff;
    padding: 3mm 2mm;
    border-radius: 2mm;
    text-align: center;
}
.mv { display: block; font-size: 20pt; font-weight: 800; color: #e8b828; line-height: 1.1; }
.ml { font-size: 8pt; color: #7a93b8; margin-top: 0.3mm; }

/* ── TABLES ──────────────────────────────────────────── */
.tb {
    width: 100%;
    border-collapse: collapse;
    margin: 2mm 0;
    font-size: 9pt;
}
.tb th {
    background: #0c1d3a;
    color: #e8b828;
    padding: 1.5mm 2mm;
    font-size: 8.5pt;
    font-weight: 600;
    text-align: center;
}
.tb td {
    padding: 1.2mm 2mm;
    text-align: center;
    border-bottom: 0.3pt solid #e2e8f0;
}
.tb tr:nth-child(even) { background: #f0f2f6; }
.tb .rh { font-weight: 700; color: #0c1d3a; text-align: left; }

/* confusion matrix */
.cm { font-size: 8.5pt; }
.cm th, .cm td { padding: 1.2mm 1.8mm; border: 0.3pt solid #cbd5e1; }
.cm th { font-size: 8pt; }
.ch { background: #166534; color: #fff; font-weight: 700; }
.cl { background: #fee2e2; color: #991b1b; }
.cz { background: #f8f9fb; color: #b0b8c8; }

.cap { font-size: 7.5pt; color: #64748b; font-style: italic; text-align: center; margin-top: 1mm; }

/* ── XAI BOX ─────────────────────────────────────────── */
.xb {
    background: linear-gradient(135deg, #f5f3ff, #ede9fe);
    border: 0.8pt solid #c4b5fd;
    border-left: 3pt solid #7c3aed;
    border-radius: 2mm;
    padding: 2.5mm 3.5mm;
    margin: 2mm 0;
}
.xb .xt { color: #5b21b6; font-weight: 700; font-size: 10pt; margin-bottom: 1mm; }
.xb p { font-size: 9pt; line-height: 1.35; color: #3b3060; }

/* ── TEAM ────────────────────────────────────────────── */
.team {
    background: #0c1d3a;
    color: #fff;
    padding: 4mm 10mm;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10mm;
    flex-shrink: 0;
    border-top: 1pt solid #d4a015;
}
.tm { text-align: center; }
.tn2 { font-size: 12pt; font-weight: 700; }
.ta { font-size: 9pt; color: #e8b828; font-weight: 500; margin-top: 0.3mm; }

/* ── FOOTER ──────────────────────────────────────────── */
.ftr {
    background: linear-gradient(135deg, #040d1a, #0c1d3a);
    padding: 4mm 10mm;
    text-align: center;
    flex-shrink: 0;
    border-top: 1.8mm solid #d4a015;
}
.fl { font-size: 12pt; font-weight: 600; color: #e8b828; letter-spacing: 2.5pt; text-transform: uppercase; margin-bottom: 2mm; }
.fr { height: 14mm; width: auto; object-fit: contain; }

/* PRINT */
@media print {
    body { width: 420mm; height: 594mm; }
    .hdr, .team, .ftr, .mc, .tb th, .cm th, .ch, .pb, .t, .sn, .xb {
        -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }
}
</style>
</head>
<body>

<!-- HEADER -->
<div class="hdr">
  <div class="hdr-row">
    <img class="logo univ" src="data:image/png;base64,""" + univ_b64 + r""""  alt="University of Blida 1">
    <div class="hdr-center">
      <div class="title"><span class="gold">AI EXPO 2026</span><br>at Blida University</div>
      <div class="sub">Artificial Intelligence Exposition &middot; April 2026</div>
      <div class="badge">Ramy Sentiment Intelligence &mdash; Arabic NLP for Consumer Voice</div>
    </div>
    <img class="logo" src="data:image/png;base64,""" + ai_b64 + r""""  alt="House of AI Blida">
  </div>
</div>

<!-- BODY -->
<div class="body">

  <!-- LEFT -->
  <div class="col">

    <div class="s">
      <div class="sh"><span class="sn">1</span> Abstract</div>
      <div class="sb">
        <p>We present <span class="b">Ramy Sentiment Intelligence</span>, a production-ready NLP system that classifies Arabic product reviews into five intent categories:
        <span class="t tp">positive</span> <span class="t tn">negative</span> <span class="t tu">neutral</span> <span class="t ti">improvement</span> <span class="t tq">question</span>.</p>
        <p>Tailored for Algerian Arabic (Darija) and code-switched French/Arabic text, the system achieves <span class="b">95.06% accuracy</span> and <span class="b">94.37% macro-F1</span> on a leakage-free held-out test set. A novel Explainable AI module provides attention-based token attributions for transparent, auditable predictions.</p>
      </div>
    </div>

    <div class="s">
      <div class="sh"><span class="sn">2</span> Introduction</div>
      <div class="sb">
        <p><span class="b">Problem.</span> Sentiment analysis in North Africa remains unsolved at the dialect level. Consumer reviews mix Modern Standard Arabic, Algerian Darija, and French within a single sentence. Off-the-shelf multilingual models fail on this code-switched Maghrebi text, and labeled data is scarce (~1,500 samples).</p>
        <p><span class="b">Objectives:</span></p>
        <ul>
          <li>Build a 5-class sentiment classifier for Algerian consumer voice</li>
          <li>Eliminate evaluation leakage common in low-data NLP</li>
          <li>Provide explainable predictions with token-level attribution</li>
          <li>Deploy via real-time enterprise inference dashboard</li>
        </ul>
      </div>
    </div>

    <div class="s">
      <div class="sh"><span class="sn">3</span> System Design &amp; Methodology</div>
      <div class="sb">
        <p><span class="b">Architecture:</span></p>
        <div class="pipe">
          <div class="pr">
            <div class="pb pd">Raw Reviews<small>Darija + FR + AR</small></div>
            <span class="pa">&rarr;</span>
            <div class="pb pd">Preprocessing<small>Normalise &middot; Clean</small></div>
            <span class="pa">&rarr;</span>
            <div class="pb pg">Augmentation<small>Few-Shot Synonyms</small></div>
          </div>
          <div class="pr">
            <div class="pb pg">9,481 Samples</div>
            <span class="pa">&rarr;</span>
            <div class="pb pe">AraBERT v2<small>Fine-tune &middot; 4 epochs</small></div>
            <span class="pa">&rarr;</span>
            <div class="pb pe">TTA + Thresholds<small>Calibrated output</small></div>
          </div>
          <div class="pr">
            <div class="pb pe">95.06% Accuracy</div>
            <span class="pa">&rarr;</span>
            <div class="pb px">XAI Module<small>Attn Rollout + Grad&times;Attn</small></div>
            <span class="pa">&rarr;</span>
            <div class="pb px">Live Dashboard<small>Real-Time Demo</small></div>
          </div>
        </div>
        <p><span class="b">Model:</span> aubmindlab/bert-base-arabertv02, 5-class, 256 max tokens, NVIDIA H100 80GB FP16, HuggingFace Trainer API.</p>
        <p><span class="b">Leakage-Free Protocol:</span></p>
        <ul>
          <li>eval_strategy='no' &mdash; dev set never drives checkpoint selection</li>
          <li>Threshold tuning on dev split only, never on test</li>
          <li>TTA restricted to final held-out evaluation only</li>
        </ul>
      </div>
    </div>

  </div>

  <!-- RIGHT -->
  <div class="col">

    <div class="s">
      <div class="sh"><span class="sn">4</span> Implementation &amp; Results</div>
      <div class="sb">
        <p><span class="b">Stack:</span>
          <span class="t tt">PyTorch 2.8</span>
          <span class="t tt">Transformers</span>
          <span class="t tt">scikit-learn</span>
          <span class="t tt">FastAPI</span>
          <span class="t tt">Streamlit</span>
        </p>
        <p><span class="b">Data:</span> Train 9,481 (augmented from ~1,500 raw) &middot; Dev 324 &middot; Test 81 (held-out).</p>
        <p><span class="b">Training:</span> 4 epochs, LR 2e-5, batch 16 (grad accum 2 &rarr; eff. 32), warmup 10%, decay 0.01, seed 42.</p>

        <div class="mg">
          <div class="mc"><span class="mv">95.06%</span><span class="ml">Accuracy</span></div>
          <div class="mc"><span class="mv">94.37%</span><span class="ml">Macro-F1</span></div>
          <div class="mc"><span class="mv">5</span><span class="ml">Classes</span></div>
          <div class="mc"><span class="mv">H100</span><span class="ml">GPU</span></div>
        </div>

        <p><span class="b">Per-Class (Held-Out Test):</span></p>
        <table class="tb">
          <thead><tr><th>Class</th><th>Prec.</th><th>Rec.</th><th>F1</th><th>N</th></tr></thead>
          <tbody>
            <tr><td class="rh">Improvement</td><td>1.00</td><td>0.85</td><td>0.92</td><td>13</td></tr>
            <tr><td class="rh">Negative</td><td>0.94</td><td>1.00</td><td>0.97</td><td>16</td></tr>
            <tr><td class="rh">Neutral</td><td>0.92</td><td>0.86</td><td>0.89</td><td>14</td></tr>
            <tr><td class="rh">Positive</td><td>0.96</td><td>1.00</td><td>0.98</td><td>25</td></tr>
            <tr><td class="rh">Question</td><td>0.93</td><td>1.00</td><td>0.96</td><td>13</td></tr>
          </tbody>
        </table>

        <p><span class="b">Confusion Matrix:</span></p>
        <table class="tb cm">
          <thead><tr><th></th><th>Imp</th><th>Neg</th><th>Neu</th><th>Pos</th><th>Que</th></tr></thead>
          <tbody>
            <tr><th>Imp</th><td class="ch">11</td><td class="cz">0</td><td class="cl">1</td><td class="cl">1</td><td class="cz">0</td></tr>
            <tr><th>Neg</th><td class="cz">0</td><td class="ch">16</td><td class="cz">0</td><td class="cz">0</td><td class="cz">0</td></tr>
            <tr><th>Neu</th><td class="cz">0</td><td class="cl">1</td><td class="ch">12</td><td class="cl">1</td><td class="cz">0</td></tr>
            <tr><th>Pos</th><td class="cz">0</td><td class="cz">0</td><td class="cz">0</td><td class="ch">25</td><td class="cz">0</td></tr>
            <tr><th>Que</th><td class="cz">0</td><td class="cz">0</td><td class="cz">0</td><td class="cz">0</td><td class="ch">13</td></tr>
          </tbody>
        </table>
        <div class="cap">Rows = true labels &middot; Columns = predicted</div>
      </div>
    </div>

    <div class="s">
      <div class="sh"><span class="sn">5</span> Analysis &amp; Discussion</div>
      <div class="sb">
        <ul>
          <li><span class="b">Positive</span> and <span class="b">Question</span> achieve perfect recall (1.00) &mdash; robust handling of affirmative reviews and information-seeking queries.</li>
          <li><span class="b">Improvement</span> has 1.00 precision, 0.85 recall &mdash; some suggestions are absorbed into neutral, reflecting the subtle linguistic boundary.</li>
          <li><span class="b">Code-switching</span> (Darija/French) handled effectively via AraBERT v2's Maghrebi pre-training.</li>
          <li>Few-shot augmentation expanded training from 1,500 to 9,481 samples without hallucinated content.</li>
        </ul>
        <div class="xb">
          <div class="xt">Explainable AI (XAI) &mdash; Key Innovation</div>
          <p>Combines <span class="b">Attention Rollout</span> (Abnar &amp; Zuidema, 2020) with <span class="b">Gradient &times; Attention</span> for per-token attribution maps. Answers <em>"why did the model predict this class?"</em> with real-time visual evidence at word level. No additional training required.</p>
        </div>
      </div>
    </div>

    <div class="s">
      <div class="sh"><span class="sn">6</span> Conclusion &amp; Future Work</div>
      <div class="sb">
        <ul>
          <li>Achieved <span class="b">95% accuracy</span> on 5-class Arabic sentiment with only 1,500 labeled samples.</li>
          <li>Leakage-free evaluation ensures genuine generalisation metrics.</li>
          <li>Attention-based XAI brings interpretability critical for enterprise trust.</li>
          <li><span class="b">Future:</span> multi-turn dialogue, real-time social media streams, production API for Ramy customer intelligence.</li>
        </ul>
      </div>
    </div>

  </div>
</div>

<!-- TEAM -->
<div class="team">
  <div class="tm"><div class="tn2">Samir Guenchi</div><div class="ta">ENSIA</div></div>
  <div class="tm"><div class="tn2">Senouci Amira</div><div class="ta">ENSIA</div></div>
  <div class="tm"><div class="tn2">Abdennour Guerroudj</div><div class="ta">USTHB</div></div>
  <div class="tm"><div class="tn2">Megamez Abderrahmane</div><div class="ta">USTHB</div></div>
</div>

<!-- FOOTER -->
<div class="ftr">
  <div class="fl">Sponsored by Ramy</div>
  <img class="fr" src="data:image/png;base64,""" + ramy_b64 + r""""  alt="Ramy">
</div>

</body>
</html>"""

(ROOT / "poster.html").write_text(html, encoding="utf-8")
print(f"A2 poster.html written ({len(html):,} bytes)")
