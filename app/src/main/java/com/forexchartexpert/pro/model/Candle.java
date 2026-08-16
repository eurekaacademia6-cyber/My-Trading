package com.forexchartexpert.pro.model;

public final class Candle {
    public final double open, high, low, close;
    public final long time;
    public Candle(double open, double high, double low, double close, long time) {
        this.open=open; this.high=high; this.low=low; this.close=close; this.time=time;
    }
    public double body(){ return Math.abs(close-open); }
    public double range(){ return high-low; }
    public double upperWick(){ return high-Math.max(open,close); }
    public double lowerWick(){ return Math.min(open,close)-low; }
    public boolean bull(){ return close>open; }
    public boolean bear(){ return close<open; }
}
