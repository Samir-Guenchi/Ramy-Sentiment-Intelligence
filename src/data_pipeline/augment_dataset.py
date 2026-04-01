"""
Dataset augmentation utility for sentiment/intention class balancing.

This script:
1) Reads a semicolon-delimited dataset with columns: text;product;label
2) Normalizes labels (e.g. Positive -> positive)
3) Augments classes with label-aware, controlled text variations
4) Saves balanced datasets, stratified train/validation splits, and summaries
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    from src.data_pipeline.validator import validate_row
except ImportError:
    # Support direct execution: python src/data_pipeline/augment_dataset.py
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from validator import validate_row


PREFIX_BY_LABEL = {
    "positive": ["بصراحة ", "عن تجربة ", "صراحةً ", "بكل أمانة "],
    "negative": ["للأسف ", "بصراحة ", "عن تجربة ", "صراحةً "],
    "neutral": ["معلومة فقط: ", "للتوضيح: ", "عادي ", "ملاحظة: "],
    "improvement": ["اقتراح: ", "ياليت ", "من الأفضل ", "نتمنى ", "حبذا "],
    "question": ["سؤال: ", "ممكن توضيح: ", "عندي استفسار: ", "لو سمحتوا "],
}


SUFFIX_BY_LABEL = {
    "positive": [" 👍", " 👏", " ممتاز", " يعطيكم الصحة"],
    "negative": [" 😕", " بصراحة", " هذا غير مقبول", " لازم تراجعو"],
    "neutral": [".", " فقط", " هذا رأيي", " عادي"],
    "improvement": [" من فضلكم", " وشكرًا", " باش يكون أحسن", " إذا أمكن"],
    "question": ["؟", " نحتاج إجابة", " من فضلكم", " وش رأيكم؟"],
}


TAG_BY_LABEL = {
    "positive": ["#ممتاز", "#يعطيكم_الصحة", "#Top"],
    "negative": ["#غير_راضي", "#لازم_تحسين", "#مشكل"],
    "neutral": ["#ملاحظة", "#عادي", "#تجربة"],
    "improvement": ["#اقتراح", "#تحسين", "#طلب"],
    "question": ["#سؤال", "#استفسار", "#محتاج_رد"],
}


WORD_VARIANTS = {
    "بزاف": ["كثير", "برشة"],
    "مليح": ["ممتاز", "هايل"],
    "هايل": ["مليح", "رائع"],
    "غالي": ["مرتفع", "سومو طالع"],
    "سكر": ["السكر", "التحلية"],
    "طعم": ["مذاق", "نكهة"],
    "عصير": ["jus", "مشروب"],
    "بصح": ["لكن", "لكن بصح"],
    "ماكانش": ["ماكانش كامل", "ما لقيتش"],
}


def load_rows(input_path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    invalid_counts = Counter()
    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        for parts in reader:
            valid, row, reason = validate_row(parts)
            if valid and row:
                rows.append(row)
            else:
                invalid_counts[reason or "invalid"] += 1

    if invalid_counts:
        print("Skipped invalid rows:", dict(sorted(invalid_counts.items())))

    return rows


def class_counts(rows: Iterable[Dict[str, str]]) -> Counter:
    c = Counter()
    for row in rows:
        c[row["label"]] += 1
    return c


def _replace_variant_word(text: str, rng: random.Random) -> str:
    tokens = text.split()
    if not tokens:
        return text

    idxs = list(range(len(tokens)))
    rng.shuffle(idxs)
    for idx in idxs:
        clean = tokens[idx].strip(".,!?؟!،\"'")
        if clean in WORD_VARIANTS:
            replacement = rng.choice(WORD_VARIANTS[clean])
            tokens[idx] = tokens[idx].replace(clean, replacement)
            return " ".join(tokens)

    return text


def _add_intensifier(text: str, rng: random.Random) -> str:
    intensifiers = ["جدا", "بزاف", "صراحة", "حقيقة"]
    pieces = text.split()
    if len(pieces) < 3:
        return f"{text} {rng.choice(intensifiers)}"
    insert_at = rng.randint(1, len(pieces) - 1)
    pieces.insert(insert_at, rng.choice(intensifiers))
    return " ".join(pieces)


def mutate_text(text: str, label: str, rng: random.Random) -> str:
    text = " ".join(text.split())

    operations = [
        "prefix",
        "suffix",
        "punctuation",
        "both",
        "word_variant",
        "intensifier",
        "tag",
    ]

    op = rng.choice(operations)

    prefix = rng.choice(PREFIX_BY_LABEL[label])
    suffix = rng.choice(SUFFIX_BY_LABEL[label])

    if op == "prefix":
        return f"{prefix}{text}"
    if op == "suffix":
        return f"{text}{suffix}"
    if op == "both":
        return f"{prefix}{text}{suffix}"
    if op == "word_variant":
        return _replace_variant_word(text, rng)
    if op == "intensifier":
        return _add_intensifier(text, rng)
    if op == "tag":
        return f"{text} {rng.choice(TAG_BY_LABEL[label])}"

    # punctuation
    if text.endswith("!"):
        return text.rstrip("!") + "!!"
    if text.endswith("؟"):
        return text.rstrip("؟") + "؟؟"
    if text.endswith("."):
        return text.rstrip(".") + ".."
    return text + rng.choice([".", "!", "؟"])


def augment_to_target(
    rows: List[Dict[str, str]],
    target_per_class: int,
    seed: int,
) -> Tuple[List[Dict[str, str]], Counter, Counter]:
    rng = random.Random(seed)
    by_label: Dict[str, List[Dict[str, str]]] = {}
    for r in rows:
        by_label.setdefault(r["label"], []).append(r)

    original_counts = class_counts(rows)
    augmented_rows = list(rows)

    for label in sorted(by_label):
        pool = by_label[label]
        existing_texts = {r["text"] for r in augmented_rows if r["label"] == label}
        need = max(0, target_per_class - len(pool))
        attempts = 0

        while need > 0 and attempts < target_per_class * 80:
            attempts += 1
            base = rng.choice(pool)
            new_text = mutate_text(base["text"], label, rng)
            # If collisions are frequent, force uniqueness with a label-specific tag.
            if new_text in existing_texts and attempts % 10 == 0:
                new_text = f"{new_text} {rng.choice(TAG_BY_LABEL[label])}"
            if new_text in existing_texts:
                continue

            new_row = {
                "text": new_text,
                "product": base["product"],
                "label": label,
            }
            augmented_rows.append(new_row)
            existing_texts.add(new_text)
            need -= 1

    return augmented_rows, original_counts, class_counts(augmented_rows)


def save_dataset(rows: List[Dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        for row in rows:
            writer.writerow([row["text"], row["product"], row["label"]])


def save_summary(before: Counter, after: Counter, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    labels = sorted(set(before.keys()) | set(after.keys()))
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["class", "before", "after", "added"])
        for label in labels:
            b = before.get(label, 0)
            a = after.get(label, 0)
            writer.writerow([label, b, a, a - b])


def save_quality_report(rows: List[Dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_texts = [r["text"] for r in rows]
    unique_count = len(set(all_texts))
    dup_ratio = 0.0 if not all_texts else 1.0 - (unique_count / len(all_texts))
    counts = class_counts(rows)

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["rows", len(rows)])
        writer.writerow(["unique_texts", unique_count])
        writer.writerow(["duplicate_ratio", round(dup_ratio, 6)])
        for label, n in sorted(counts.items()):
            writer.writerow([f"class_{label}", n])


def stratified_split(
    rows: List[Dict[str, str]],
    train_ratio: float,
    seed: int,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    rng = random.Random(seed)
    by_label: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        by_label.setdefault(row["label"], []).append(row)

    train_rows: List[Dict[str, str]] = []
    val_rows: List[Dict[str, str]] = []

    for label, items in sorted(by_label.items()):
        items_copy = list(items)
        rng.shuffle(items_copy)
        train_size = int(len(items_copy) * train_ratio)
        # Keep at least 1 sample for validation when possible.
        if len(items_copy) > 1:
            train_size = max(1, min(train_size, len(items_copy) - 1))

        train_rows.extend(items_copy[:train_size])
        val_rows.extend(items_copy[train_size:])

    rng.shuffle(train_rows)
    rng.shuffle(val_rows)
    return train_rows, val_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Augment and split Ramy dataset.")
    parser.add_argument(
        "--target-per-class",
        type=int,
        default=1500,
        help="Target number of rows per class in final augmented dataset.",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Train ratio for stratified split.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    input_path = project_root / "data" / "Ramy_data.csv"
    suffix = f"target_{args.target_per_class}"
    output_data = project_root / "data" / "augmented" / f"Ramy_data_augmented_{suffix}.csv"
    output_summary = project_root / "data" / "augmented" / f"class_distribution_{suffix}.csv"
    quality_report = project_root / "data" / "augmented" / f"quality_report_{suffix}.csv"
    train_output = project_root / "data" / "augmented" / f"Ramy_data_train_{suffix}.csv"
    val_output = project_root / "data" / "augmented" / f"Ramy_data_val_{suffix}.csv"
    val_quality_report = project_root / "data" / "augmented" / f"quality_report_val_{suffix}.csv"

    rows = load_rows(input_path)
    before = class_counts(rows)
    if not before:
        raise ValueError("No valid rows found in input dataset.")

    # Split first to avoid train/validation leakage from synthetic variants.
    raw_train_rows, raw_val_rows = stratified_split(
        rows=rows,
        train_ratio=args.train_ratio,
        seed=args.seed,
    )

    train_before = class_counts(raw_train_rows)
    target = max(max(train_before.values()), args.target_per_class)
    train_rows, original_counts, new_counts = augment_to_target(
        rows=raw_train_rows,
        target_per_class=target,
        seed=args.seed,
    )

    val_rows = raw_val_rows
    combined_rows = train_rows + val_rows

    save_dataset(combined_rows, output_data)
    save_summary(original_counts, new_counts, output_summary)
    save_quality_report(combined_rows, quality_report)
    save_quality_report(val_rows, val_quality_report)

    save_dataset(train_rows, train_output)
    save_dataset(val_rows, val_output)

    train_counts = class_counts(train_rows)
    val_counts = class_counts(val_rows)

    print(f"Input rows: {len(rows)}")
    print(f"Raw train rows: {len(raw_train_rows)}")
    print(f"Raw validation rows: {len(raw_val_rows)}")
    print(f"Combined output rows: {len(combined_rows)}")
    print("Train class counts before augmentation:", dict(sorted(original_counts.items())))
    print("Train class counts after augmentation:", dict(sorted(new_counts.items())))
    print("Train split counts:", dict(sorted(train_counts.items())))
    print("Validation split counts:", dict(sorted(val_counts.items())))
    print(f"Saved dataset: {output_data}")
    print(f"Saved summary: {output_summary}")
    print(f"Saved quality report: {quality_report}")
    print(f"Saved validation quality report: {val_quality_report}")
    print(f"Saved train split: {train_output}")
    print(f"Saved validation split: {val_output}")


if __name__ == "__main__":
    main()
