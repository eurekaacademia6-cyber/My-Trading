# Live Trading Decision Engine

The engine separates **market state** from **entry trigger**.

## Market state

- Primary trend: EMA 9/21/50.
- Higher timeframe trend: EMA 21/50 on two higher timeframes.
- Market structure: swing highs/lows.
- Momentum: RSI(14).
- Volatility: ATR(14).
- Location: recent 24-bar range.

## Trigger

- Engulfing candle.
- Hammer/shooting-star rejection.
- Recent 12-bar breakout.
- Context/location agreement.

## Risk

Stop placement uses recent structure plus an ATR buffer. Targets are expressed in R multiples, not an arbitrary fixed pip count.

## Anti-hallucination rule

The decision engine never treats a camera-generated price estimate as equivalent to broker OHLC. The camera may validate identity and context; the quantitative engine requires real market data.
