package com.forexchartexpert.pro.model;

import java.util.List;

public final class MarketSnapshot {
    public final String provider;
    public final String symbol;
    public final String timeframe;
    public final double bid;
    public final double ask;
    public final long serverTime;
    public final List<Candle> primary;
    public final List<Candle> higher1;
    public final List<Candle> higher2;
    public final double spreadPoints;
    public final boolean newsKnownSafe;

    public MarketSnapshot(String provider, String symbol, String timeframe, double bid, double ask, long serverTime,
                          List<Candle> primary, List<Candle> higher1, List<Candle> higher2,
                          double spreadPoints, boolean newsKnownSafe) {
        this.provider=provider; this.symbol=symbol; this.timeframe=timeframe; this.bid=bid; this.ask=ask;
        this.serverTime=serverTime; this.primary=primary; this.higher1=higher1; this.higher2=higher2;
        this.spreadPoints=spreadPoints; this.newsKnownSafe=newsKnownSafe;
    }
    public double mid(){ return (bid+ask)/2.0; }
}
