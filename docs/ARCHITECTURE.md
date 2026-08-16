# Production Architecture 3.0

## 1. Data truth hierarchy

1. Broker/terminal OHLC + live bid/ask: authoritative quantitative input.
2. Camera/OCR: independent chart identity/context verification.
3. Optional economic-calendar provider: news-risk gate.
4. ML chart model: pattern/regime/context classifier, never the sole numerical price source.

## 2. Components

### Android
- CameraX preview.
- MT5 bridge HTTP client.
- Live market snapshot model.
- Deterministic multi-timeframe strategy engine.
- Audit logger.
- Signal UI.

### Windows laptop
- MT5 bridge.
- Broker-connected market data via MT5 terminal.
- Future: optional authenticated WebSocket transport.

### Future model service
- Training pipeline.
- TFLite/ONNX inference.
- Calibrated probability model.
- Drift monitor.
- Walk-forward validation service.

## 3. Signal contract

A BUY/SELL may only be emitted if:

- live quote is valid;
- adequate closed-bar history is available;
- spread is acceptable;
- volatility is suitable;
- primary timeframe structure is coherent;
- higher timeframes agree;
- trigger confirmation exists;
- reward/risk is acceptable;
- no hard veto is active.

Otherwise: NO TRADE.

## 4. Camera role

The camera remains useful even after moving price computation to live market data. The production implementation should OCR the visible symbol/timeframe and compare it with the bridge request. A mismatch should create a hard warning and optionally veto the signal.
