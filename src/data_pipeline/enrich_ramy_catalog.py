from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path


OFFICIAL_TAXONOMY = {
    "Boisson aux fruits": ["Classique", "EXTRA", "Frutty", "carton", "canette", "kids"],
    "Boisson gazéifiée": ["Water Fruits", "Boisson gazeifiée canette", "Boisson gazeifiée verre"],
    "Boisson au lait": ["milky : 1l", "milky : 20cl", "milky : 300ml", "milky : 25cl"],
    "Produits laitiers": ["lais", "yupty", "raib et lben", "cherebt", "ramy up duo"],
}


def classify_catalog(product: str, text: str = ""):
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


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    input_path = root / "data" / "augmented" / "Ramy_data_augmented_target_1500.csv"
    output_path = root / "data" / "processed" / "Ramy_data_catalog_enriched.csv"
    summary_path = root / "data" / "processed" / "Ramy_taxonomy_coverage.csv"

    rows = []
    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        for parts in reader:
            if len(parts) < 3:
                continue
            text = parts[0].strip()
            product = parts[1].strip()
            sentiment = parts[2].strip().lower()
            if not text or not sentiment:
                continue
            category, subcategory = classify_catalog(product, text)
            rows.append([text, product, category, subcategory, sentiment])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["text", "product", "category", "subcategory", "sentiment"])
        writer.writerows(rows)

    category_counts = Counter()
    subcategory_counts = Counter()
    for _, _, category, subcategory, _ in rows:
        category_counts[category] += 1
        subcategory_counts[(category, subcategory)] += 1

    with summary_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["category", "subcategory", "count"])
        for category, subcategories in OFFICIAL_TAXONOMY.items():
            for subcategory in subcategories:
                writer.writerow([category, subcategory, subcategory_counts.get((category, subcategory), 0)])

        writer.writerow([])
        writer.writerow(["category", "total_count"])
        for category in OFFICIAL_TAXONOMY:
            writer.writerow([category, category_counts.get(category, 0)])

    print(f"Saved {len(rows)} rows to {output_path}")
    print(f"Saved taxonomy coverage to {summary_path}")


if __name__ == "__main__":
    main()
