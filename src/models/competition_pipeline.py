"""
Competition-grade sentiment pipeline for Arabic/Darja review classification.

This module focuses on leaderboard-oriented techniques:
- Stratified Group K-Fold validation to reduce leakage
- Diverse model ensemble with out-of-fold predictions
- Per-class threshold optimization for macro-F1
- Optional pseudo-labeling from unlabeled data
- Test-time augmentation (TTA) at inference time
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import json

import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.data_pipeline.preprocessor import ArabicPreprocessor


def _safe_log_probs(probs: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    return np.log(np.clip(probs, eps, 1.0))


def _temperature_scale_probs(probs: np.ndarray, temperature: float) -> np.ndarray:
    logits = _safe_log_probs(probs)
    return softmax(logits / max(temperature, 1e-6), axis=1)


def _normalize_text_key(preprocessor: ArabicPreprocessor, text: str) -> str:
    return preprocessor.clean_text(str(text)).strip().lower()


def _tta_variants(text: str, preprocessor: ArabicPreprocessor) -> List[str]:
    raw = str(text)
    v1 = raw
    v2 = preprocessor.clean_text(raw)
    darja_pre = ArabicPreprocessor(normalize_darja=True)
    v3 = darja_pre.clean_text(raw)
    variants = [v.strip() for v in [v1, v2, v3] if v and v.strip()]
    # Keep order while removing duplicates.
    return list(dict.fromkeys(variants))


@dataclass
class CompetitionConfig:
    n_splits: int = 5
    random_state: int = 42
    pseudo_label_min_confidence: float = 0.92
    enable_pseudo_labeling: bool = False
    enable_tta: bool = True
    temperature_search_grid: Tuple[float, ...] = (
        0.70,
        0.80,
        0.90,
        1.00,
        1.10,
        1.20,
        1.30,
        1.50,
        1.80,
        2.00,
    )


class CompetitionSentimentPipeline:
    def __init__(self, labels: Sequence[str], config: Optional[CompetitionConfig] = None):
        self.labels = [str(l).strip().lower() for l in labels]
        self.label_to_idx = {label: i for i, label in enumerate(self.labels)}
        self.idx_to_label = {i: label for label, i in self.label_to_idx.items()}
        self.config = config or CompetitionConfig()
        self.preprocessor = ArabicPreprocessor()

        self.models: Dict[str, Pipeline] = {}
        self.model_weights: Dict[str, float] = {}
        self.class_thresholds = np.ones(len(self.labels), dtype=float)
        self.temperature: float = 1.0
        self.fitted = False

    def _build_model_specs(self) -> Dict[str, Pipeline]:
        return {
            "word_lr": Pipeline(
                [
                    (
                        "tfidf",
                        TfidfVectorizer(
                            analyzer="word",
                            ngram_range=(1, 2),
                            min_df=2,
                            max_features=120000,
                            sublinear_tf=True,
                        ),
                    ),
                    (
                        "clf",
                        LogisticRegression(
                            max_iter=3000,
                            class_weight="balanced",
                            n_jobs=None,
                            C=3.0,
                        ),
                    ),
                ]
            ),
            "char_svm_calibrated": Pipeline(
                [
                    (
                        "tfidf",
                        TfidfVectorizer(
                            analyzer="char_wb",
                            ngram_range=(3, 5),
                            min_df=2,
                            max_features=180000,
                            sublinear_tf=True,
                        ),
                    ),
                    (
                        "clf",
                        CalibratedClassifierCV(
                            estimator=LinearSVC(C=1.2),
                            cv=3,
                            method="sigmoid",
                        ),
                    ),
                ]
            ),
            "word_sgd": Pipeline(
                [
                    (
                        "tfidf",
                        TfidfVectorizer(
                            analyzer="word",
                            ngram_range=(1, 3),
                            min_df=2,
                            max_features=160000,
                            sublinear_tf=True,
                        ),
                    ),
                    (
                        "clf",
                        SGDClassifier(
                            loss="log_loss",
                            alpha=2e-5,
                            penalty="l2",
                            max_iter=2000,
                            class_weight="balanced",
                            random_state=self.config.random_state,
                        ),
                    ),
                ]
            ),
        }

    def _prepare_df(self, df: pd.DataFrame, text_col: str, label_col: str) -> pd.DataFrame:
        work = df.copy()
        work[text_col] = work[text_col].astype(str)
        work[label_col] = work[label_col].astype(str).str.strip().str.lower()
        work = work[work[text_col].str.len() > 0]
        work = work[work[label_col].isin(self.labels)]
        work = work.drop_duplicates(subset=[text_col, label_col]).reset_index(drop=True)
        work["_text_clean"] = work[text_col].map(self.preprocessor.clean_text)
        work["_group_key"] = work[text_col].map(
            lambda t: _normalize_text_key(self.preprocessor, t)
        )
        return work

    def _weighted_blend(self, probs_by_model: Dict[str, np.ndarray], weights: Dict[str, float]) -> np.ndarray:
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("Model weights sum must be positive.")
        blend = None
        for name, probs in probs_by_model.items():
            w = weights.get(name, 0.0) / total
            blend = probs * w if blend is None else blend + probs * w
        return blend

    def _pred_with_thresholds(self, probs: np.ndarray, thresholds: np.ndarray) -> np.ndarray:
        adjusted = probs / np.clip(thresholds.reshape(1, -1), 1e-6, None)
        return np.argmax(adjusted, axis=1)

    def _optimize_weights(self, y_true: np.ndarray, oof_probs_by_model: Dict[str, np.ndarray]) -> Dict[str, float]:
        names = list(oof_probs_by_model.keys())
        best = {n: 1.0 / len(names) for n in names}
        best_score = -1.0

        if len(names) == 1:
            return best

        step = 0.1
        for w0 in np.arange(0.1, 1.0, step):
            for w1 in np.arange(0.1, 1.0, step):
                if len(names) == 2:
                    weights = {names[0]: float(w0), names[1]: float(w1)}
                else:
                    for w2 in np.arange(0.1, 1.0, step):
                        weights = {names[0]: float(w0), names[1]: float(w1), names[2]: float(w2)}
                        blend = self._weighted_blend(oof_probs_by_model, weights)
                        preds = np.argmax(blend, axis=1)
                        score = f1_score(y_true, preds, average="macro")
                        if score > best_score:
                            best_score = score
                            best = weights
                    continue

                blend = self._weighted_blend(oof_probs_by_model, weights)
                preds = np.argmax(blend, axis=1)
                score = f1_score(y_true, preds, average="macro")
                if score > best_score:
                    best_score = score
                    best = weights

        return best

    def _optimize_thresholds(self, y_true: np.ndarray, probs: np.ndarray) -> np.ndarray:
        thresholds = np.ones(len(self.labels), dtype=float)
        search = np.arange(0.50, 1.51, 0.05)
        best_score = f1_score(y_true, np.argmax(probs, axis=1), average="macro")

        for c in range(len(self.labels)):
            best_t = thresholds[c]
            for t in search:
                cand = thresholds.copy()
                cand[c] = t
                preds = self._pred_with_thresholds(probs, cand)
                score = f1_score(y_true, preds, average="macro")
                if score > best_score:
                    best_score = score
                    best_t = t
            thresholds[c] = best_t

        return thresholds

    def _optimize_temperature(self, y_true: np.ndarray, probs: np.ndarray) -> float:
        best_t = 1.0
        best_score = f1_score(y_true, np.argmax(probs, axis=1), average="macro")
        for t in self.config.temperature_search_grid:
            scaled = _temperature_scale_probs(probs, t)
            score = f1_score(y_true, np.argmax(scaled, axis=1), average="macro")
            if score > best_score:
                best_score = score
                best_t = float(t)
        return best_t

    def _fit_models_with_oof(self, X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> Dict[str, np.ndarray]:
        specs = self._build_model_specs()
        splitter = StratifiedGroupKFold(
            n_splits=self.config.n_splits,
            shuffle=True,
            random_state=self.config.random_state,
        )
        oof = {name: np.zeros((len(X), len(self.labels)), dtype=float) for name in specs}

        for fold_idx, (tr_idx, va_idx) in enumerate(splitter.split(X, y, groups), start=1):
            X_tr, X_va = X[tr_idx], X[va_idx]
            y_tr = y[tr_idx]
            for name, model in specs.items():
                model.fit(X_tr, y_tr)
                fold_probs = model.predict_proba(X_va)
                oof[name][va_idx] = fold_probs
            print(f"Fold {fold_idx}/{self.config.n_splits} done.")

        # Refit full models for final inference.
        self.models = self._build_model_specs()
        for name, model in self.models.items():
            model.fit(X, y)
            print(f"Trained full model: {name}")

        return oof

    def _predict_ensemble_proba_single_text(self, text: str) -> np.ndarray:
        variants = _tta_variants(text, self.preprocessor) if self.config.enable_tta else [str(text)]
        per_variant = []
        for variant in variants:
            probs_by_model = {
                name: model.predict_proba([variant]) for name, model in self.models.items()
            }
            blend = self._weighted_blend(probs_by_model, self.model_weights)
            blend = _temperature_scale_probs(blend, self.temperature)
            per_variant.append(blend[0])
        return np.mean(per_variant, axis=0)

    def _pseudo_label(
        self,
        train_df: pd.DataFrame,
        unlabeled_df: pd.DataFrame,
        text_col: str,
        label_col: str,
    ) -> pd.DataFrame:
        if unlabeled_df.empty:
            return train_df

        work = unlabeled_df.copy()
        work[text_col] = work[text_col].astype(str)
        work = work[work[text_col].str.len() > 0].reset_index(drop=True)

        if work.empty:
            return train_df

        probs = np.vstack([self._predict_ensemble_proba_single_text(t) for t in work[text_col]])
        conf = probs.max(axis=1)
        pred_idx = probs.argmax(axis=1)

        keep = conf >= self.config.pseudo_label_min_confidence
        selected = work.loc[keep, [text_col]].copy()
        if selected.empty:
            return train_df

        selected[label_col] = [self.idx_to_label[int(i)] for i in pred_idx[keep]]
        selected["is_pseudo"] = True

        base = train_df.copy()
        if "is_pseudo" not in base.columns:
            base["is_pseudo"] = False

        combined = pd.concat([base, selected], ignore_index=True)
        combined = combined.drop_duplicates(subset=[text_col, label_col]).reset_index(drop=True)
        print(f"Pseudo-labeling added {len(selected)} high-confidence rows.")
        return combined

    def fit(
        self,
        train_df: pd.DataFrame,
        text_col: str = "text",
        label_col: str = "sentiment",
        unlabeled_df: Optional[pd.DataFrame] = None,
    ) -> Dict:
        df = self._prepare_df(train_df, text_col=text_col, label_col=label_col)
        if df.empty:
            raise ValueError("Training data is empty after filtering.")

        X = df["_text_clean"].astype(str).to_numpy()
        y_labels = df[label_col].astype(str).tolist()
        y = np.array([self.label_to_idx[v] for v in y_labels], dtype=int)
        groups = df["_group_key"].astype(str).to_numpy()

        oof_probs = self._fit_models_with_oof(X=X, y=y, groups=groups)
        self.model_weights = self._optimize_weights(y_true=y, oof_probs_by_model=oof_probs)

        blended_oof = self._weighted_blend(oof_probs, self.model_weights)
        self.temperature = self._optimize_temperature(y_true=y, probs=blended_oof)
        blended_oof = _temperature_scale_probs(blended_oof, self.temperature)

        self.class_thresholds = self._optimize_thresholds(y_true=y, probs=blended_oof)
        preds = self._pred_with_thresholds(blended_oof, self.class_thresholds)

        metrics = {
            "cv_accuracy": float(accuracy_score(y, preds)),
            "cv_f1_macro": float(f1_score(y, preds, average="macro")),
            "weights": self.model_weights,
            "temperature": self.temperature,
            "class_thresholds": {
                self.idx_to_label[i]: float(t) for i, t in enumerate(self.class_thresholds)
            },
            "labels": self.labels,
            "classification_report": classification_report(
                y,
                preds,
                labels=list(range(len(self.labels))),
                target_names=self.labels,
                zero_division=0,
            ),
            "confusion_matrix": confusion_matrix(
                y,
                preds,
                labels=list(range(len(self.labels))),
            ).tolist(),
            "rows_used": int(len(df)),
        }

        self.fitted = True

        if self.config.enable_pseudo_labeling and unlabeled_df is not None and not unlabeled_df.empty:
            expanded = self._pseudo_label(
                train_df=df[[text_col, label_col]],
                unlabeled_df=unlabeled_df,
                text_col=text_col,
                label_col=label_col,
            )
            # Refit final models on expanded data after pseudo-labeling.
            expanded = self._prepare_df(expanded, text_col=text_col, label_col=label_col)
            X_full = expanded["_text_clean"].astype(str).to_numpy()
            y_full = np.array([self.label_to_idx[v] for v in expanded[label_col].tolist()], dtype=int)
            self.models = self._build_model_specs()
            for name, model in self.models.items():
                model.fit(X_full, y_full)
            metrics["rows_after_pseudo_labeling"] = int(len(expanded))

        return metrics

    def predict_proba(self, texts: Sequence[str]) -> np.ndarray:
        if not self.fitted:
            raise RuntimeError("Pipeline is not fitted.")
        probs = [self._predict_ensemble_proba_single_text(t) for t in texts]
        return np.vstack(probs)

    def predict(self, texts: Sequence[str]) -> List[str]:
        probs = self.predict_proba(texts)
        pred_idx = self._pred_with_thresholds(probs, self.class_thresholds)
        return [self.idx_to_label[int(i)] for i in pred_idx]

    def predict_with_routing(
        self,
        texts: Sequence[str],
        low_confidence_threshold: float = 0.55,
    ) -> List[Dict]:
        """
        Predict with a confidence gate. Low-confidence items are explicitly flagged
        so downstream systems can route them for manual review or secondary models.
        """
        probs = self.predict_proba(texts)
        pred_idx = self._pred_with_thresholds(probs, self.class_thresholds)
        rows = []
        for i, idx in enumerate(pred_idx):
            confidence = float(np.max(probs[i]))
            rows.append(
                {
                    "text": str(texts[i]),
                    "label": self.idx_to_label[int(idx)],
                    "confidence": confidence,
                    "route": "review" if confidence < low_confidence_threshold else "direct",
                }
            )
        return rows

    def evaluate(self, df: pd.DataFrame, text_col: str = "text", label_col: str = "sentiment") -> Dict:
        work = df.copy()
        work[text_col] = work[text_col].astype(str)
        work[label_col] = work[label_col].astype(str).str.strip().str.lower()
        work = work[work[label_col].isin(self.labels)].reset_index(drop=True)
        if work.empty:
            raise ValueError("Evaluation dataset is empty after filtering.")

        y_true_labels = work[label_col].tolist()
        y_true = np.array([self.label_to_idx[v] for v in y_true_labels], dtype=int)
        probs = self.predict_proba(work[text_col].tolist())
        y_pred = self._pred_with_thresholds(probs, self.class_thresholds)

        hard_examples = []
        for i in range(len(work)):
            if int(y_pred[i]) != int(y_true[i]):
                hard_examples.append(
                    {
                        "text": str(work.iloc[i][text_col]),
                        "true_label": self.idx_to_label[int(y_true[i])],
                        "pred_label": self.idx_to_label[int(y_pred[i])],
                        "pred_confidence": float(np.max(probs[i])),
                    }
                )
        hard_examples = sorted(
            hard_examples,
            key=lambda x: x["pred_confidence"],
            reverse=True,
        )

        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
            "classification_report": classification_report(
                y_true,
                y_pred,
                labels=list(range(len(self.labels))),
                target_names=self.labels,
                zero_division=0,
            ),
            "confusion_matrix": confusion_matrix(
                y_true,
                y_pred,
                labels=list(range(len(self.labels))),
            ).tolist(),
            "labels": self.labels,
            "rows": int(len(work)),
            "hard_examples_top50": hard_examples[:50],
        }

    def save(self, output_dir: Path | str) -> None:
        import joblib

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        payload = {
            "labels": self.labels,
            "weights": self.model_weights,
            "temperature": self.temperature,
            "class_thresholds": self.class_thresholds.tolist(),
            "enable_tta": self.config.enable_tta,
        }

        (out / "competition_meta.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        for name, model in self.models.items():
            joblib.dump(model, out / f"{name}.joblib")

    @classmethod
    def load(cls, output_dir: Path | str) -> "CompetitionSentimentPipeline":
        import joblib

        out = Path(output_dir)
        meta = json.loads((out / "competition_meta.json").read_text(encoding="utf-8"))
        pipe = cls(labels=meta["labels"], config=CompetitionConfig(enable_tta=bool(meta.get("enable_tta", True))))
        pipe.model_weights = {k: float(v) for k, v in meta["weights"].items()}
        pipe.temperature = float(meta["temperature"])
        pipe.class_thresholds = np.array(meta["class_thresholds"], dtype=float)

        pipe.models = {}
        for name in pipe.model_weights.keys():
            pipe.models[name] = joblib.load(out / f"{name}.joblib")

        pipe.fitted = True
        return pipe