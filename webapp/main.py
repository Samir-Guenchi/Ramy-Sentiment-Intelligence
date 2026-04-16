from __future__ import annotations

import csv
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Body, FastAPI, HTTPException, Query  # type: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[reportMissingImports]
from fastapi.responses import HTMLResponse, Response  # type: ignore[reportMissingImports]
from fastapi.staticfiles import StaticFiles  # type: ignore[reportMissingImports]
from fastapi.templating import Jinja2Templates  # type: ignore[reportMissingImports]
from starlette.requests import Request  # type: ignore[reportMissingImports]


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = BASE_DIR / "data" / "augmented" / "Ramy_data_augmented_target_1500.csv"
_CACHE = {"path": None, "mtime": None, "rows": []}
_MODEL_CACHE: Dict[str, Any] = {
    "ready": False,
    "error": "",
    "pipe": None,
    "model_dir": "",
}
_XAI_CACHE: Dict[str, Any] = {
    "ready": False,
    "error": "",
    "explainer": None,
    "model_dir": "",
}


CATALOG = {
    "Boisson aux fruits": ["Classique", "EXTRA", "Frutty", "carton", "canette", "kids"],
    "Boisson gazéifiée": ["Water Fruits", "Boisson gazeifiée canette", "Boisson gazeifiée verre"],
    "Boisson au lait": ["milky : 1l", "milky : 20cl", "milky : 300ml", "milky : 25cl"],
    "Produits laitiers": ["lais", "yupty", "raib et lben", "cherebt", "ramy up duo"],
}

TARGET_CLASSES = ["positive", "negative", "neutral", "improvement", "question"]

QUESTION_TOKENS = {
    "wach", "wesh", "wash", "win", "where", "ou", "pourquoi", "why", "comment", "how",
    "when", "what", "quoi", "fin", "kayen", "kayn", "علاه", "كيف", "فين", "وين", "متى", "وش",
}

NEGATION_TOKENS = {
    "machi", "machi", "moch", "مش", "ماشي", "موش", "pas", "not", "jamais",
}

POSITIVE_TOKENS = {
    "bnin", "bnina", "bninaa", "bon", "good", "excellent", "super", "top", "مليح", "بنين", "لذيذ",
}

NEGATIVE_TOKENS = {
    "khayeb", "khayba", "mauvais", "bad", "ghali", "cher", "trop", "رديء", "سيء", "خايب", "غالي",
}


def _extract_text_tokens(text: str) -> List[str]:
    return re.findall(r"[a-zA-ZÀ-ÿ0-9_]+|[\u0600-\u06FF]+", text.lower())


def _normalize_score_map(
    predicted_class: str,
    confidence: float,
    all_scores: Optional[Dict[str, Any]] = None,
) -> Dict[str, float]:
    scores = {cls: 0.0 for cls in TARGET_CLASSES}

    if all_scores:
        for k, v in all_scores.items():
            key = str(k).lower()
            if key in scores:
                try:
                    scores[key] = max(0.0, float(v))
                except (TypeError, ValueError):
                    scores[key] = 0.0

    total = sum(scores.values())
    pred = str(predicted_class or "").lower()
    conf = max(0.0, min(float(confidence or 0.0), 1.0))

    if total <= 0:
        if pred not in scores:
            pred = "neutral"
        remainder = max(0.0, 1.0 - conf)
        spread = remainder / (len(TARGET_CLASSES) - 1)
        for cls in TARGET_CLASSES:
            scores[cls] = conf if cls == pred else spread
        total = sum(scores.values())

    if total > 0:
        for cls in TARGET_CLASSES:
            scores[cls] = scores[cls] / total

    return scores


def _boost_class(scores: Dict[str, float], target: str, floor: float) -> Dict[str, float]:
    floor = max(0.0, min(floor, 1.0))
    cur = float(scores.get(target, 0.0))
    if cur >= floor:
        total = sum(scores.values())
        if total > 0:
            return {k: v / total for k, v in scores.items()}
        return scores

    remain = max(0.0, 1.0 - floor)
    other_total = max(1e-12, sum(v for k, v in scores.items() if k != target))

    boosted = {}
    for k, v in scores.items():
        if k == target:
            boosted[k] = floor
        else:
            boosted[k] = remain * (v / other_total)

    total = sum(boosted.values())
    return {k: v / total for k, v in boosted.items()}


def _apply_rule_calibration(
    text: str,
    predicted_class: str,
    confidence: float,
    all_scores: Optional[Dict[str, Any]] = None,
) -> Tuple[str, float, Dict[str, float], List[str]]:
    """
    Apply lightweight lexical calibration for Darija/French-Latin edge cases.

    The fine-tuned model can overpredict positive on transliterated short text
    such as "machi bnin". These rules correct obvious polarity/question cues.
    """
    tokens = _extract_text_tokens(text)
    token_set = set(tokens)
    raw = (text or "").lower()

    has_qmark = "?" in raw or "؟" in raw
    has_question_token = any(t in token_set for t in QUESTION_TOKENS)
    explicit_question = has_qmark or has_question_token

    explicit_negative = any(t in token_set for t in NEGATIVE_TOKENS)

    negated_positive = False
    for i, tok in enumerate(tokens):
        if tok in NEGATION_TOKENS:
            window = tokens[i + 1:i + 4]
            if any(w in POSITIVE_TOKENS for w in window):
                negated_positive = True
                break

    scores = _normalize_score_map(predicted_class, confidence, all_scores)
    applied_rules: List[str] = []

    if negated_positive:
        scores = _boost_class(scores, "negative", 0.80)
        applied_rules.append("negation_over_positive_pattern")
    elif explicit_negative:
        scores = _boost_class(scores, "negative", 0.70)
        applied_rules.append("explicit_negative_lexicon")
    elif explicit_question:
        scores = _boost_class(scores, "question", 0.70)
        applied_rules.append("question_cue")

    calibrated_class = max(scores, key=scores.get)
    calibrated_conf = float(scores[calibrated_class])
    return calibrated_class, calibrated_conf, scores, applied_rules


def _resolve_model_source_path() -> Path:
    configured = os.getenv("FINETUNED_MODEL_PATH", "").strip()
    if configured:
        p = Path(configured)
        if p.exists():
            return p

    defaults = [
        BASE_DIR / "ramy_h100_finetuned_model.zip",
        BASE_DIR / "models" / "checkpoints" / "h100_arabert_ft" / "final_model",
        BASE_DIR / "models" / "runtime" / "ramy_h100_finetuned_model",
    ]
    for candidate in defaults:
        if candidate.exists():
            return candidate

    return defaults[0]


def _resolve_runtime_model_dir(source: Path) -> Path:
    if source.is_dir():
        return source

    runtime_dir = BASE_DIR / "models" / "runtime" / "ramy_h100_finetuned_model"
    runtime_dir.parent.mkdir(parents=True, exist_ok=True)

    if source.suffix.lower() == ".zip":
        if runtime_dir.exists():
            return runtime_dir
        shutil.unpack_archive(str(source), str(runtime_dir))
        return runtime_dir

    raise FileNotFoundError(f"Unsupported model source: {source}")


def _load_prediction_pipeline() -> Any:
    if _MODEL_CACHE["ready"] and _MODEL_CACHE["pipe"] is not None:
        return _MODEL_CACHE["pipe"]

    try:
        import torch  # type: ignore[reportMissingImports]
        from transformers import (  # type: ignore[reportMissingImports]
            AutoModelForSequenceClassification,
            AutoTokenizer,
            pipeline,
        )

        source = _resolve_model_source_path()
        if not source.exists():
            raise FileNotFoundError(
                f"Fine-tuned model not found at: {source}. "
                "Set FINETUNED_MODEL_PATH to your model folder or zip."
            )

        model_dir = _resolve_runtime_model_dir(source)
        device = 0 if torch.cuda.is_available() else -1
        try:
            clf = pipeline(
                task="text-classification",
                model=str(model_dir),
                tokenizer=str(model_dir),
                device=device,
            )
        except Exception as first_exc:
            # Some environments trigger "meta tensor" issues on lazy loading.
            # Fallback to explicit model/tokenizer materialization on CPU.
            tokenizer = AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True)
            model = AutoModelForSequenceClassification.from_pretrained(
                str(model_dir),
                low_cpu_mem_usage=False,
                local_files_only=True,
            )
            clf = pipeline(
                task="text-classification",
                model=model,
                tokenizer=tokenizer,
                device=-1,
            )

        _MODEL_CACHE["ready"] = True
        _MODEL_CACHE["error"] = ""
        _MODEL_CACHE["pipe"] = clf
        _MODEL_CACHE["model_dir"] = str(model_dir)
        return clf
    except Exception as exc:
        _MODEL_CACHE["ready"] = False
        _MODEL_CACHE["error"] = str(exc)
        _MODEL_CACHE["pipe"] = None
        raise


def _load_xai_explainer() -> Any:
    if _XAI_CACHE["ready"] and _XAI_CACHE["explainer"] is not None:
        return _XAI_CACHE["explainer"]

    try:
        source = _resolve_model_source_path()
        if not source.exists():
            raise FileNotFoundError(
                f"Fine-tuned model not found at: {source}. "
                "Set FINETUNED_MODEL_PATH to your model folder or zip."
            )

        model_dir = _resolve_runtime_model_dir(source)

        from src.explainability.attention_explainer import AttentionExplainer

        explainer = AttentionExplainer(str(model_dir))
        _XAI_CACHE["ready"] = True
        _XAI_CACHE["error"] = ""
        _XAI_CACHE["explainer"] = explainer
        _XAI_CACHE["model_dir"] = str(model_dir)
        return explainer
    except Exception as exc:
        _XAI_CACHE["ready"] = False
        _XAI_CACHE["error"] = str(exc)
        _XAI_CACHE["explainer"] = None
        raise


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def _resolve_data_path() -> Path:
    configured = os.getenv("REVIEW_DATA_PATH", "").strip()
    if configured:
        path = Path(configured)
        if path.exists():
            return path
    return DEFAULT_DATA_PATH


def _classify_catalog(product: str, text: str = "") -> Tuple[str, str]:
    source = f"{product} {text}".lower()

    if "milky" in source:
        if re.search(r"\b1\s?l\b|\b1l\b", source):
            return "Boisson au lait", "milky : 1l"
        if re.search(r"\b20\s?cl\b|\b20cl\b", source):
            return "Boisson au lait", "milky : 20cl"
        if re.search(r"\b300\s?ml\b|\b300ml\b", source):
            return "Boisson au lait", "milky : 300ml"
        if re.search(r"\b25\s?cl\b|\b25cl\b", source):
            return "Boisson au lait", "milky : 25cl"
        return "Boisson au lait", "milky : 1l"

    if any(k in source for k in ["lait", "yupty", "raib", "lben", "cherebt", "duo"]):
        if "yupty" in source:
            return "Produits laitiers", "yupty"
        if "raib" in source or "lben" in source:
            return "Produits laitiers", "raib et lben"
        if "cherebt" in source:
            return "Produits laitiers", "cherebt"
        if "duo" in source:
            return "Produits laitiers", "ramy up duo"
        return "Produits laitiers", "lais"

    if any(k in source for k in ["gaze", "gaz", "sparkling", "verre", "water fruits"]):
        if "canette" in source:
            return "Boisson gazéifiée", "Boisson gazeifiée canette"
        if "verre" in source:
            return "Boisson gazéifiée", "Boisson gazeifiée verre"
        return "Boisson gazéifiée", "Water Fruits"

    if "frutty" in source:
        return "Boisson aux fruits", "Frutty"
    if "kids" in source:
        return "Boisson aux fruits", "kids"
    if "canette" in source:
        return "Boisson aux fruits", "canette"
    if "carton" in source or "fardeau" in source or "pack" in source:
        return "Boisson aux fruits", "carton"
    if "extra" in source:
        return "Boisson aux fruits", "EXTRA"

    return "Boisson aux fruits", "Classique"


def _normalize_row(parts: List[str], has_header: bool = False) -> Dict[str, Any]:
    if has_header:
        raise RuntimeError("Header parsing should be handled outside this function.")

    text = parts[0].strip() if len(parts) > 0 else ""
    product = parts[1].strip() if len(parts) > 1 else ""
    label = parts[2].strip().lower() if len(parts) > 2 else ""

    if not text or not label:
        return {}

    category, subcategory = _classify_catalog(product, text)

    return {
        "text": text,
        "product": product or "Unknown",
        "sentiment": label,
        "platform": "dataset",
        "wilaya": "غير محدد",
        "rating": 3,
        "timestamp": datetime.now().isoformat(),
        "aspects": {},
        "category": category,
        "subcategory": subcategory,
    }


def _load_reviews() -> List[Dict[str, Any]]:
    path = _resolve_data_path()
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    mtime = path.stat().st_mtime
    if _CACHE["path"] == str(path) and _CACHE["mtime"] == mtime:
        return _CACHE["rows"]

    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        first = next(reader, None)

        if not first:
            return []

        lowered = [cell.strip().lower() for cell in first]
        has_header = {"text", "product"}.issubset(set(lowered)) and (
            "label" in lowered or "sentiment" in lowered
        )

        if has_header:
            header = lowered
            for parts in reader:
                if not parts:
                    continue
                row = {header[i]: parts[i].strip() if i < len(parts) else "" for i in range(len(header))}
                text = row.get("text", "").strip()
                label = (row.get("sentiment") or row.get("label") or "").strip().lower()
                if not text or not label:
                    continue

                product = row.get("product", "Unknown") or "Unknown"
                category, subcategory = _classify_catalog(product, text)

                aspects_raw = row.get("aspects", "")
                try:
                    aspects = json.loads(aspects_raw) if aspects_raw else {}
                except (json.JSONDecodeError, TypeError):
                    aspects = {}

                rows.append(
                    {
                        "text": text,
                        "product": product,
                        "sentiment": label,
                        "platform": row.get("platform", "dataset") or "dataset",
                        "wilaya": row.get("wilaya", "غير محدد") or "غير محدد",
                        "rating": float(row.get("rating", 3) or 3),
                        "timestamp": row.get("timestamp", datetime.now().isoformat()),
                        "aspects": aspects,
                        "category": row.get("category", category) or category,
                        "subcategory": row.get("subcategory", subcategory) or subcategory,
                    }
                )
        else:
            normalized = _normalize_row(first)
            if normalized:
                rows.append(normalized)
            for parts in reader:
                normalized = _normalize_row(parts)
                if normalized:
                    rows.append(normalized)

    _CACHE["path"] = str(path)
    _CACHE["mtime"] = mtime
    _CACHE["rows"] = rows
    return rows


def _filter_reviews(
    reviews: List[Dict[str, Any]],
    sentiment: Optional[str] = None,
    product: Optional[str] = None,
    wilaya: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    filtered = reviews

    if sentiment:
        v = sentiment.strip().lower()
        filtered = [r for r in filtered if r.get("sentiment", "").lower() == v]

    if product:
        v = product.strip().lower()
        filtered = [r for r in filtered if r.get("product", "").lower() == v]

    if wilaya:
        v = wilaya.strip().lower()
        filtered = [r for r in filtered if r.get("wilaya", "").lower() == v]

    if category:
        v = category.strip().lower()
        filtered = [r for r in filtered if r.get("category", "").lower() == v]

    if subcategory:
        v = subcategory.strip().lower()
        filtered = [r for r in filtered if r.get("subcategory", "").lower() == v]

    if search:
        q = search.strip().lower()
        filtered = [r for r in filtered if q in r.get("text", "").lower()]

    return filtered


def _overview(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    sentiments = Counter(r["sentiment"] for r in reviews)
    total = len(reviews)
    products = Counter(r["product"] for r in reviews)
    categories = Counter(r["category"] for r in reviews)

    recent = reviews[-10:]
    recent.reverse()

    return {
        "total": total,
        "distribution": dict(sentiments),
        "products": dict(products.most_common(8)),
        "categories": dict(categories),
        "recent": recent,
    }


def _trends(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    trend: Dict[str, Counter] = defaultdict(Counter)
    for r in reviews:
        ts = r.get("timestamp") or datetime.now().isoformat()
        try:
            month = datetime.fromisoformat(str(ts).replace("Z", "")).strftime("%Y-%m")
        except ValueError:
            month = "unknown"
        trend[month][r["sentiment"]] += 1

    series = []
    for month in sorted(trend.keys()):
        row: Dict[str, Any] = {"month": month}
        row.update(trend[month])
        series.append(row)
    return {"series": series}


def _geo(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_wilaya: Dict[str, Counter] = defaultdict(Counter)
    for r in reviews:
        by_wilaya[r.get("wilaya", "غير محدد")][r["sentiment"]] += 1

    rows = []
    for wilaya, counts in by_wilaya.items():
        total = sum(counts.values())
        score = ((counts.get("positive", 0) - counts.get("negative", 0)) / total * 100) if total else 0
        rows.append({"wilaya": wilaya, "score": round(score, 2), "total": total})

    rows.sort(key=lambda x: x["score"], reverse=True)
    return {
        "rows": rows,
        "best": rows[0] if rows else None,
        "worst": rows[-1] if rows else None,
    }


def _aspects(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    aspect_counts: Dict[str, Counter] = defaultdict(Counter)
    for r in reviews:
        aspects = r.get("aspects") or {}
        if isinstance(aspects, str):
            try:
                aspects = json.loads(aspects)
            except (json.JSONDecodeError, TypeError):
                aspects = {}
        if not isinstance(aspects, dict):
            aspects = {}

        for aspect, sent in aspects.items():
            aspect_counts[aspect][sent] += 1

    rows = []
    for aspect, counts in aspect_counts.items():
        total = sum(counts.values())
        if not total:
            continue
        rows.append(
            {
                "aspect": aspect,
                "positive": counts.get("positive", 0),
                "negative": counts.get("negative", 0),
                "neutral": counts.get("neutral", 0),
                "score": round((counts.get("positive", 0) - counts.get("negative", 0)) / total * 100, 2),
            }
        )
    rows.sort(key=lambda x: x["score"], reverse=True)
    return {"rows": rows}


app = FastAPI(title="Ramy Enterprise Dashboard", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/api/health")
def api_health() -> Dict[str, str]:
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "dataset": str(_resolve_data_path()),
    }


@app.get("/api/model/status")
def api_model_status() -> Dict[str, Any]:
    try:
        _load_prediction_pipeline()
        return {
            "ready": True,
            "model_dir": _MODEL_CACHE.get("model_dir", ""),
            "error": "",
            "xai_ready": _XAI_CACHE.get("ready", False),
            "xai_error": _XAI_CACHE.get("error", ""),
        }
    except Exception as exc:
        return {
            "ready": False,
            "model_dir": _MODEL_CACHE.get("model_dir", ""),
            "error": str(exc),
            "xai_ready": _XAI_CACHE.get("ready", False),
            "xai_error": _XAI_CACHE.get("error", ""),
        }


@app.post("/api/model/predict")
def api_model_predict(payload: Dict[str, Any] = Body(default={})):  # type: ignore[reportUnknownParameterType]
    comments_raw = payload.get("comments", [])
    if isinstance(comments_raw, str):
        comments = [line.strip() for line in comments_raw.splitlines() if line.strip()]
    elif isinstance(comments_raw, list):
        comments = [str(item).strip() for item in comments_raw if str(item).strip()]
    else:
        comments = []

    if not comments:
        raise HTTPException(status_code=400, detail="Provide at least one comment in 'comments'.")

    if len(comments) > 1000:
        raise HTTPException(status_code=400, detail="Too many comments. Max allowed is 1000.")

    include_xai = _to_bool(payload.get("include_xai", False), default=False)
    xai_method = str(payload.get("xai_method", "combined") or "combined")
    xai_top_k_raw = payload.get("xai_top_k", 8)
    try:
        xai_top_k = max(1, min(int(xai_top_k_raw), 20))
    except (TypeError, ValueError):
        xai_top_k = 8

    use_xai = include_xai and len(comments) <= 20
    xai_error = ""

    if use_xai:
        try:
            explainer = _load_xai_explainer()
            rows = []
            for text in comments:
                explanation = explainer.explain(text, method=xai_method, top_k=xai_top_k)
                raw_pred = str(explanation.get("predicted_class", "unknown")).lower()
                raw_conf = float(explanation.get("confidence", 0.0))
                raw_scores = explanation.get("all_scores", {})
                cal_pred, cal_conf, cal_scores, cal_rules = _apply_rule_calibration(
                    text=text,
                    predicted_class=raw_pred,
                    confidence=raw_conf,
                    all_scores=raw_scores,
                )

                explanation_text = explanation.get("explanation_text", "")
                if cal_rules and cal_pred != raw_pred:
                    top_tokens = explanation.get("top_tokens", [])
                    top_preview = ", ".join(
                        [
                            f"{str(tok[0])} ({float(tok[1]):.0%})"
                            for tok in top_tokens[:3]
                            if isinstance(tok, (list, tuple)) and len(tok) >= 2
                        ]
                    )
                    explanation_text = (
                        f"Final prediction: {cal_pred.upper()} ({cal_conf:.0%}) after calibration. "
                        f"Base model output was {raw_pred.upper()} ({raw_conf:.0%}). "
                        f"Applied rule(s): {', '.join(cal_rules)}. "
                        f"Top relative tokens: {top_preview if top_preview else 'n/a'}."
                    ).strip()

                rows.append(
                    {
                        "text": text,
                        "predicted_class": cal_pred,
                        "confidence": cal_conf,
                        "all_scores": cal_scores,
                        "top_tokens": explanation.get("top_tokens", []),
                        "word_attributions": explanation.get("word_attributions", []),
                        "explanation_text": explanation_text,
                        "xai_method": explanation.get("method", xai_method),
                        "calibration_rules": cal_rules,
                    }
                )

            distribution = Counter(r["predicted_class"] for r in rows)
            return {
                "total": len(rows),
                "rows": rows,
                "distribution": dict(distribution),
                "model_dir": _MODEL_CACHE.get("model_dir", "") or _XAI_CACHE.get("model_dir", ""),
                "xai_used": True,
                "xai_method": xai_method,
                "xai_error": "",
            }
        except Exception as exc:
            xai_error = str(exc)
            use_xai = False

    try:
        clf = _load_prediction_pipeline()
        raw_preds = clf(comments, truncation=True, max_length=256)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Model not available: {exc}") from exc

    rows = []
    for text, pred in zip(comments, raw_preds):
        raw_pred = str(pred.get("label", "unknown")).lower()
        raw_conf = float(pred.get("score", 0.0))
        cal_pred, cal_conf, cal_scores, cal_rules = _apply_rule_calibration(
            text=text,
            predicted_class=raw_pred,
            confidence=raw_conf,
            all_scores=None,
        )
        rows.append(
            {
                "text": text,
                "predicted_class": cal_pred,
                "confidence": cal_conf,
                "all_scores": cal_scores,
                "calibration_rules": cal_rules,
            }
        )

    distribution = Counter(r["predicted_class"] for r in rows)

    return {
        "total": len(rows),
        "rows": rows,
        "distribution": dict(distribution),
        "model_dir": _MODEL_CACHE.get("model_dir", ""),
        "xai_used": False,
        "xai_method": "",
        "xai_error": xai_error,
    }


@app.get("/api/model/predict")
def api_model_predict_help() -> Dict[str, Any]:
    return {
        "detail": "Method Not Allowed for GET. Use POST with JSON body: {'comments': ['text1', 'text2']}",
        "example": {
            "comments": [
                "ramy tres bon et naturel",
                "prix trop cher",
            ]
        },
    }


@app.get("/api/catalog")
def api_catalog() -> Dict[str, List[str]]:
    return CATALOG


@app.get("/api/options")
def api_options() -> Dict[str, List[str]]:
    reviews = _load_reviews()
    return {
        "products": sorted({r.get("product", "Unknown") for r in reviews}),
        "sentiments": sorted({r.get("sentiment", "unknown") for r in reviews}),
        "wilayas": sorted({r.get("wilaya", "غير محدد") for r in reviews}),
        "categories": sorted({r.get("category", "") for r in reviews}),
        "subcategories": sorted({r.get("subcategory", "") for r in reviews}),
    }


@app.get("/api/overview")
def api_overview(
    sentiment: Optional[str] = None,
    product: Optional[str] = None,
    wilaya: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
):
    try:
        reviews = _load_reviews()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _overview(_filter_reviews(reviews, sentiment, product, wilaya, category, subcategory, search))


@app.get("/api/trends")
def api_trends(
    sentiment: Optional[str] = None,
    product: Optional[str] = None,
    wilaya: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
):
    reviews = _load_reviews()
    return _trends(_filter_reviews(reviews, sentiment, product, wilaya, category, subcategory, search))


@app.get("/api/geo")
def api_geo(
    sentiment: Optional[str] = None,
    product: Optional[str] = None,
    wilaya: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
):
    reviews = _load_reviews()
    return _geo(_filter_reviews(reviews, sentiment, product, wilaya, category, subcategory, search))


@app.get("/api/aspects")
def api_aspects(
    sentiment: Optional[str] = None,
    product: Optional[str] = None,
    wilaya: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
):
    reviews = _load_reviews()
    return _aspects(_filter_reviews(reviews, sentiment, product, wilaya, category, subcategory, search))


@app.get("/api/reviews")
def api_reviews(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=5, le=100),
    sentiment: Optional[str] = None,
    product: Optional[str] = None,
    wilaya: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
):
    reviews = _load_reviews()
    filtered = _filter_reviews(reviews, sentiment, product, wilaya, category, subcategory, search)

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    rows = filtered[start:end]

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": max((total + page_size - 1) // page_size, 1),
        "rows": rows,
    }


@app.get("/api/export/reviews.csv")
def api_export_reviews(
    sentiment: Optional[str] = None,
    product: Optional[str] = None,
    wilaya: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
):
    reviews = _load_reviews()
    filtered = _filter_reviews(reviews, sentiment, product, wilaya, category, subcategory, search)

    output = StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(
        [
            "text",
            "product",
            "category",
            "subcategory",
            "sentiment",
            "platform",
            "wilaya",
            "rating",
            "timestamp",
        ]
    )
    for r in filtered:
        writer.writerow(
            [
                r.get("text", ""),
                r.get("product", ""),
                r.get("category", ""),
                r.get("subcategory", ""),
                r.get("sentiment", ""),
                r.get("platform", ""),
                r.get("wilaya", ""),
                r.get("rating", ""),
                r.get("timestamp", ""),
            ]
        )

    filename = f"ramy_reviews_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
