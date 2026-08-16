package com.forexchartexpert.pro.model;

public final class ExpertAnalysis {
    public final MarketSnapshot snapshot;
    public final Signal signal;
    public final String regime;
    public final String liquidity;
    public final String session;
    public final double setupScore;
    public final double buyScore;
    public final double sellScore;
    public final double lotSize;
    public ExpertAnalysis(MarketSnapshot snapshot, Signal signal, String regime, String liquidity, String session,
                          double setupScore, double buyScore, double sellScore, double lotSize) {
        this.snapshot=snapshot; this.signal=signal; this.regime=regime; this.liquidity=liquidity; this.session=session;
        this.setupScore=setupScore; this.buyScore=buyScore; this.sellScore=sellScore; this.lotSize=lotSize;
    }
}
