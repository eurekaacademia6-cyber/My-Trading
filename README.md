# Forex Chart Expert Ultimate 8.0

A read-only Android + Windows/MetaTrader 5 forex decision-support system.

## What is different in Ultimate

**Numerical source of truth:** MetaTrader 5 on the Windows laptop supplies live bid/ask plus OHLC bars. The current/forming candle is explicitly excluded from strategic confirmation.

**Camera verification:** the Android phone camera watches the laptop chart. OCR attempts to identify the pair/timeframe; a detected mismatch causes a NO TRADE camera-verification veto. Visual candle reconstruction remains an independent confidence/diagnostic signal rather than replacing broker prices.

**Expert decision stack:** data quality → stale quote → spread → session/rollover → market regime → multi-timeframe trend → market structure → BOS/CHOCH proxy → liquidity sweep → location/value → RSI/EMA momentum → price-action triggers → exhaustion → news veto → risk/reward → elite threshold → two-observation stability confirmation.

**Risk:** structure-based stop + ATR buffer, TP1/TP2, risk percentage and broker-aware lot-size estimation through MT5's profit calculator. No order is sent.

## Run the laptop bridge

1. Windows laptop: install MetaTrader 5 and log in to the broker.
2. Install Python 3.11+.
3. Open `bridge` in PowerShell.
4. Run `run_bridge.bat`.
5. Find the laptop LAN IPv4 with `ipconfig`.
6. Android app: enter `http://LAPTOP_IP:8765` and press CONNECT.
7. Select the same pair/timeframe shown on the laptop.

### Optional strict news filter

Put normalized UTC high-impact events in `bridge/news_events.csv` using the example schema, or set `NEWS_URL` to a trusted endpoint that returns the documented normalized JSON. Enable the checkbox in the Android app. When strict mode is enabled and news data cannot be verified, the system intentionally refuses the trade.

## Android Studio

Open the project root in Android Studio and allow Gradle sync. The build uses AndroidX, CameraX 1.6.1 and ML Kit text recognition 16.0.1. A pre-generated Gradle wrapper JAR is not included in this package; Android Studio can use the project's Gradle configuration directly.

## Important

This package does **not** contain a trained statistical model claiming a 95–100% win rate. The deterministic expert layer is the auditable foundation for collecting out-of-sample outcomes. The `research`/backtest documentation defines how empirical calibration should be added without look-ahead or leakage.
