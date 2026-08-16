# Future ML layer

The current engine is intentionally deterministic and auditable. To make it genuinely adaptive, collect a feature row for every eligible setup and its forward outcome.

### Feature groups
- OHLC geometry, ATR, RSI, EMA slopes
- swing structure, BOS/CHOCH state
- liquidity sweep state
- distance to recent high/low and session levels
- spread and volatility regime
- higher-timeframe alignment
- time-of-day/session
- news proximity
- chart-vision quality score

### Labels
Primary label: whether TP2 was reached before SL within a defined horizon.
Secondary labels: MAE, MFE, time-to-target, and whether TP1 was reached first.

### Recommended model stack
Gradient-boosted tree ensemble + calibrated logistic/meta learner. Add a lightweight chart-vision model only for visual confirmation and metadata extraction.

### Anti-overfitting rules
Chronological splits, purged/embargoed validation, pair/timeframe holdouts, feature ablation, probability calibration and drift monitoring.
