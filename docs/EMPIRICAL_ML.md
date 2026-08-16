# Empirical ML Layer — Production Design

The system now supports a real historical-data-trained probability layer. It is **optional until a model artifact has been trained and passed out-of-sample checks**.

## Why this is separate

The deterministic engine handles market structure, risk, spread, sessions and safety vetoes. ML answers a narrower question:

> Given the current measurable market state, how often has this kind of long/short setup reached its barrier before invalidation?

The ML probability is a **gate**, not a command.

## Labeling

The training script uses a forward horizon and ATR-scaled triple-barrier outcome:

- entry = completed candle close
- stop = ATR multiple
- target = stop distance × configured R multiple
- first unambiguous barrier hit determines outcome
- ambiguous/no-hit samples are skipped

This prevents using future prices as input features.

## Features

The initial vector combines:

- recent returns
- range/body/wick normalized by ATR
- EMA gaps and slope
- RSI / directional strength
- market structure
- BOS/CHOCH proxy
- liquidity sweep state
- location in recent range
- session/time-of-week encodings
- candle patterns
- tick-volume anomaly

The schema is versioned so changing the feature definition invalidates an old model artifact.

## Training and calibration

The trainer:

1. pulls the exact broker's MT5 bars or reads a broker-exported CSV;
2. constructs features chronologically;
3. uses separate long/short classifiers;
4. calibrates predicted scores on a future validation segment;
5. chooses a conservative threshold from validation precision;
6. reports untouched test metrics;
7. exports `models/ml_edge_model.joblib`.

## Production acceptance gate

Do not enable the ML gate merely because AUC is high. Require:

- stable OOS precision across multiple rolling windows;
- acceptable Brier/log-loss calibration;
- positive net expectancy after spread/slippage;
- no single regime contributing most of the profits;
- robustness on at least several major FX pairs;
- no catastrophic degradation in the latest holdout window.

The live bridge remains deterministic-only when no valid artifact exists.
