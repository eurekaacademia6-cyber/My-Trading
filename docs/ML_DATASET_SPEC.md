# Custom model dataset specification

The supplied app is deliberately not shipped with a fake "AI trader" model. A real chart-vision model must be trained on labeled data.

Recommended sample JSON:

```json
{
  "image": "EURUSD_M5_2026-01-12_1030.jpg",
  "pair": "EURUSD",
  "timeframe": "M5",
  "candle_boxes": [[x,y,w,h]],
  "structure": {"trend":"bull","bos":"up","choch":false},
  "zones": {"support":[[x1,y1,x2,y2]],"resistance":[[x1,y1,x2,y2]]},
  "setup": "pullback_continuation",
  "entry_bar": 74,
  "outcome_horizon": 20,
  "outcome_r": 1.5
}
```

Collect across different monitors, chart themes, pairs, sessions and market regimes. Split train/validation/test by non-overlapping time blocks. Avoid random frame splits because neighboring frames are nearly duplicates.
