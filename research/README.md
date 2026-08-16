# Empirical ML Layer

This layer is intentionally **training-code-first**. No model weights are bundled because they must be trained on the broker/market data you will actually trade.

## Setup

```powershell
py -m pip install -r ../bridge/requirements.txt
```

The requirements include `scikit-learn` and `joblib` in addition to MetaTrader5/numpy.

## Train from the logged-in MT5 terminal

```powershell
cd bridge
py ..\research\train_ml.py --symbol EURUSD --timeframe M5 --start 2021-01-01 --end 2026-08-01
```

The output is `models/ml_edge_model.joblib` plus a JSON report.

## Train from CSV

Export chronological OHLCV history from the exact broker/symbol/feed you plan to trade, then:

```powershell
py ..\research\train_ml.py --csv C:\data\EURUSD_M5.csv --symbol EURUSD --timeframe M5
```

## What the training does

- Uses completed candles only.
- Builds features from information available at each decision point.
- Uses a future-barrier label with ATR-based stop/target and a fixed horizon.
- Splits chronologically; no random shuffling.
- Trains separate long and short probability models.
- Calibrates probabilities on a validation slice.
- Chooses conservative thresholds instead of forcing a signal.
- Reports OOS AUC, average precision, log-loss, Brier score and precision at threshold.

## Walk-forward validation

```powershell
py ..\research\walk_forward.py C:\data\EURUSD_M5.csv --out walk_forward.json
```

A model is **not considered production-worthy merely because one backtest looks good**. Require stable out-of-sample performance across multiple rolling windows, pairs, regimes and realistic spread/slippage assumptions.
