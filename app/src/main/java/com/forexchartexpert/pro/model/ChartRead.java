package com.forexchartexpert.pro.model;

import java.util.List;

public final class ChartRead {
    public final List<Candle> candles;
    public final double visionConfidence;
    public final String symbol;
    public final String timeframe;
    public final String qualityNote;
    public final boolean stable;
    public ChartRead(List<Candle> candles, double visionConfidence, String symbol, String timeframe, String qualityNote, boolean stable){
        this.candles=candles; this.visionConfidence=visionConfidence; this.symbol=symbol; this.timeframe=timeframe; this.qualityNote=qualityNote; this.stable=stable;
    }
}
