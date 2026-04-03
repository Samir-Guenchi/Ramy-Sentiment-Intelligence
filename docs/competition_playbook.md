# Competition Playbook

## Objective
Maximize private leaderboard performance while maintaining reproducibility and preventing public leaderboard overfit.

## Implemented System Features
- StratifiedGroupKFold validation to reduce leakage.
- 3-model ensemble with out-of-fold blending.
- Per-class threshold optimization for macro-F1.
- Temperature scaling for probability calibration.
- Optional pseudo-labeling with confidence threshold.
- Test-time augmentation (TTA) for robust inference.
- Confidence routing for low-confidence predictions.
- Hard-example extraction for targeted error analysis.

## Daily Execution Loop
1. Train and evaluate using `python -m src.models.train_sentiment ...`.
2. Review `hard_examples_top50` in the metrics JSON.
3. Add focused data fixes for recurrent error patterns.
4. Retrain and compare with prior experiment.
5. Submit only candidate models with better CV and stable holdout behavior.

## Competition Safety Rules
- Keep one untouched holdout split for final checks.
- Never tune solely on public leaderboard jumps.
- Track every submission with code version and config.
- Freeze final model artifacts and random seed before deadline.

## Final Week Checklist
- Run 3 seeds for top 2 configurations.
- Blend seed-level predictions.
- Re-check class distribution and threshold stability.
- Prepare fallback submission from previous stable model.
