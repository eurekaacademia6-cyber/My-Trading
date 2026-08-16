# Validation protocol

Do not report a headline win rate until all of the following are complete:

- Train / validation / test periods are chronological.
- No candle from the future is available at decision time.
- Costs include spread, commission, slippage and realistic execution delay.
- The forming candle is never used as completed evidence.
- Performance is broken down by pair, timeframe, session and market regime.
- A completely untouched final test period is preserved.
- Monte Carlo analysis is run over the trade sequence.
- Forward paper trading is performed before any live execution capability is considered.

Metrics: expectancy, profit factor, max drawdown, Sharpe/Sortino, win rate, average R, median R, 95th percentile loss, longest losing streak, trade frequency and regime-level stability.
