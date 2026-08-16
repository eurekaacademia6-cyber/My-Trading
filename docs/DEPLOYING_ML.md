# Deploying the empirical ML model

The project now has a complete train -> validate -> approve -> live workflow.

## 1. Install research dependencies

```powershell
cd bridge
py -m pip install -r requirements.txt
```

## 2. Train on the exact broker/data feed

Example:

```powershell
py ..\research\train_ml.py --symbol EURUSD --timeframe M5 --start 2021-01-01 --end 2026-08-01
```

This creates:

- `models/ml_edge_model.joblib`
- `models/ml_edge_model.json`

The job is chronological and does not shuffle candles.

## 3. Review the untouched test metrics

Do not approve a model because one headline number is high. Review AUC, average precision, Brier score, log-loss, threshold precision, number of trades, and rolling walk-forward stability.

Run:

```powershell
py ..\research\walk_forward.py C:\data\EURUSD_M5.csv --out walk_forward.json
```

## 4. Approve the artifact for live inference

After reviewing the report, train again with:

```powershell
py ..\research\train_ml.py --symbol EURUSD --timeframe M5 --start 2021-01-01 --end 2026-08-01 --approve
```

The bridge intentionally ignores a model artifact unless `approved_for_live=true`.

## 5. Point the bridge at the model

Optionally override the default path:

```powershell
$env:ML_MODEL_PATH="C:\Path\To\ForexChartExpertUltimate\ForexChartExpertProPro\models\ml_edge_model.joblib"
py bridge.py --bind 0.0.0.0 --port 8765
```

## 6. Multi-pair / multi-timeframe deployment

For a serious deployment, train separate artifacts for combinations such as:

- EURUSD M1/M5/M15
- GBPUSD M1/M5/M15
- USDJPY M1/M5/M15
- XAUUSD M1/M5/M15 (with a separate cost/volatility profile)

Do not assume a model trained on EURUSD M5 transfers perfectly to another asset.
