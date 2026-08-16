package com.forexchartexpert.pro.model;

public final class Signal {
    public enum Action { BUY, SELL, NO_TRADE }
    public final Action action;
    public final int confidence;
    public final double quality;
    public final String trend, structure, momentum, location;
    public final String reason;
    public final String risk;
    public final double entry, stop, target1, target2;
    public final boolean vetoed;
    public Signal(Action action, int confidence, double quality, String trend, String structure, String momentum, String location,
                  String reason, String risk, double entry, double stop, double target1, double target2, boolean vetoed){
        this.action=action; this.confidence=confidence; this.quality=quality; this.trend=trend; this.structure=structure;
        this.momentum=momentum; this.location=location; this.reason=reason; this.risk=risk; this.entry=entry; this.stop=stop;
        this.target1=target1; this.target2=target2; this.vetoed=vetoed;
    }
}
