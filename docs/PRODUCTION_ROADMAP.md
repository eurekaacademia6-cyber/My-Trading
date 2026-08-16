# Roadmap to a statistically validated expert system

### Phase A — already implemented in this package
- broker/terminal live data bridge
- bid/ask awareness
- completed-candle discipline
- multi-timeframe quantitative engine
- spread/volatility/overextension vetoes
- Android live polling UI
- audit logging

### Phase B
- camera OCR hard-verification of symbol/timeframe
- economic-calendar provider
- historical replay viewer
- trade outcome tracking
- per-symbol/per-timeframe metrics

### Phase C
- labeled chart-state dataset
- vision model for setup classification
- probability calibration
- walk-forward validation
- confidence threshold learned from validation, not guessed

### Phase D
- optional ONNX/TFLite inference
- online drift checks
- broker-specific spread/slippage models
- push alerts
- paper-trading mode

### Phase E
- only after extensive validation: optional broker execution integration, protected by a separate explicit user confirmation layer.
