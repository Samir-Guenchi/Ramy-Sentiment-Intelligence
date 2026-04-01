from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query  # type: ignore[reportMissingImports]
from fastapi.responses import HTMLResponse, Response  # type: ignore[reportMissingImports]
from fastapi.staticfiles import StaticFiles  # type: ignore[reportMissingImports]
from fastapi.templating import Jinja2Templates  # type: ignore[reportMissingImports]
from starlette.requests import Request  # type: ignore[reportMissingImports]


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = BASE_DIR / "data" / "augmented" / "Ramy_data_augmented_target_1500.csv"
_CACHE = {"path": None, "mtime": None, "rows": []}


CATALOG = {
    "Boisson aux fruits": ["Classique", "EXTRA", "Frutty", "carton", "canette", "kids"],
    "Boisson gazéifiée": ["Water Fruits", "Boisson gazeifiée canette", "Boisson gazeifiée verre"],
    "Boisson au lait": ["milky : 1l", "milky : 20cl", "milky : 300ml", "milky : 25cl"],
    "Produits laitiers": ["lais", "yupty", "raib et lben", "cherebt", "ramy up duo"],
}


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
