package com.forexchartexpert.pro.analysis;

import com.forexchartexpert.pro.model.*;
import java.util.*;

/**
 * Live-data strategy engine. It deliberately uses COMPLETED candles for pattern/structure decisions.
 * The current quote is used only for entry/spread/risk calculations.
 */
public final class MarketStrategyEngine {
    private static final double MIN_SCORE = 82.0;
    private static final double MIN_MARGIN = 14.0;
    private final boolean strictNews;

    public MarketStrategyEngine(boolean strictNews){ this.strictNews=strictNews; }

    public Signal analyze(MarketSnapshot m){
        if(m==null || m.primary==null || m.primary.size()<80)
            return veto(m,"DATA VETO: not enough live OHLC history.");
        if(!Double.isFinite(m.bid) || !Double.isFinite(m.ask) || m.bid<=0 || m.ask<=0)
            return veto(m,"PRICE VETO: live bid/ask unavailable.");
        if(strictNews && !m.newsKnownSafe)
            return veto(m,"NEWS VETO: economic-calendar state is not confirmed safe.");
        if(Double.isFinite(m.spreadPoints) && m.spreadPoints>30)
            return veto(m,"SPREAD VETO: current spread is too wide for this setup.");

        List<Candle> c = closed(m.primary);
        List<Candle> h1 = closed(m.higher1);
        List<Candle> h2 = closed(m.higher2);
        if(c.size()<60 || h1.size()<40 || h2.size()<40) return veto(m,"MTF VETO: insufficient higher-timeframe history.");

        double last=m.mid();
        double atr=Indicators.atr(c,14), rsi=Indicators.rsi(c,14);
        double e9=Indicators.ema(c,9), e21=Indicators.ema(c,21), e50=Indicators.ema(c,50);
        double hs1=Indicators.ema(h1,21), hs2=Indicators.ema(h2,21);
        double hh1=Indicators.ema(h1,50), hh2=Indicators.ema(h2,50);
        int sd=Indicators.swingDirection(c,2);
        Candle b=c.get(c.size()-1);

        String trend = e9>e21&&e21>e50 ? "BULLISH" : e9<e21&&e21<e50 ? "BEARISH" : "MIXED";
        String hTrend = hs1>hh1 && hs2>hh2 ? "HTF BULLISH" : hs1<hh1 && hs2<hh2 ? "HTF BEARISH" : "HTF MIXED";
        boolean bullEngulf=Indicators.bullishEngulf(c), bearEngulf=Indicators.bearishEngulf(c);
        boolean bullReject=Indicators.hammer(b), bearReject=Indicators.shootingStar(b);
        double rh=Indicators.recentHigh(c,24), rl=Indicators.recentLow(c,24); double range=Math.max(1e-9,rh-rl); double pos=(last-rl)/range;
        boolean atSupport=pos<=.30, atResistance=pos>=.70;
        boolean bullishBreak=b.close>Indicators.recentHigh(c.subList(0,c.size()-1),12);
        boolean bearishBreak=b.close<Indicators.recentLow(c.subList(0,c.size()-1),12);

        double bull=0,bear=0;
        if(e9>e21) bull+=12; else if(e9<e21) bear+=12;
        if(e21>e50) bull+=10; else if(e21<e50) bear+=10;
        if(hTrend.equals("HTF BULLISH")) bull+=18; else if(hTrend.equals("HTF BEARISH")) bear+=18;
        if(sd>0) bull+=12; else if(sd<0) bear+=12;
        if(rsi>=54 && rsi<=70) bull+=9; else if(rsi<=46 && rsi>=30) bear+=9;
        if(bullEngulf) bull+=10; if(bullReject) bull+=7;
        if(bearEngulf) bear+=10; if(bearReject) bear+=7;
        if(atSupport) bull+=7; if(atResistance) bear+=7;
        if(bullishBreak) bull+=8; if(bearishBreak) bear+=8;

        double body=b.body();
        if(atr<=0 || range<atr*2.5 || range>atr*22) return veto(m,"REGIME VETO: market is too compressed or chaotic for the strategy.");
        if(body>atr*1.9 && ((rsi>74)||(rsi<26))) return veto(m,"EXHAUSTION VETO: move is statistically extended.");
        if(atResistance && bull>bear) bull-=8;
        if(atSupport && bear>bull) bear-=8;

        double top=Math.max(bull,bear), other=Math.min(bull,bear);
        String structure=sd>0?"HIGHER HIGHS / LOWS":sd<0?"LOWER HIGHS / LOWS":"UNCLEAR";
        String momentum=rsi>=55?"POSITIVE":rsi<=45?"NEGATIVE":"NEUTRAL";
        String location=atSupport?"SUPPORT ZONE":atResistance?"RESISTANCE ZONE":"MID-RANGE";
        int confidence=(int)Math.round(Math.min(99,52 + (top-50)*0.55 + (top-other)*0.45));

        if(bull>=MIN_SCORE && bull-other>=MIN_MARGIN && !atResistance){
            double stop=Math.min(Indicators.recentLow(c,8)-atr*.20, last-atr*.70);
            double r=Math.max(atr*.65,last-stop); double t1=last+r*1.4,t2=last+r*2.1;
            return new Signal(Signal.Action.BUY,confidence,bull/100.0,trend+" / "+hTrend,structure,momentum,location,
                    "LIVE OHLC consensus: trend, higher timeframe, structure, momentum and trigger agree.",
                    fmt(last,stop,t1,t2),last,stop,t1,t2,false);
        }
        if(bear>=MIN_SCORE && bear-other>=MIN_MARGIN && !atSupport){
            double stop=Math.max(Indicators.recentHigh(c,8)+atr*.20, last+atr*.70);
            double r=Math.max(atr*.65,stop-last); double t1=last-r*1.4,t2=last-r*2.1;
            return new Signal(Signal.Action.SELL,confidence,bear/100.0,trend+" / "+hTrend,structure,momentum,location,
                    "LIVE OHLC consensus: trend, higher timeframe, structure, momentum and trigger agree.",
                    fmt(last,stop,t1,t2),last,stop,t1,t2,false);
        }
        return veto(m,"NO TRADE: high-conviction alignment is not present.");
    }

    private static List<Candle> closed(List<Candle> bars){
        int n=bars.size(); if(n<=1)return new ArrayList<>(); return new ArrayList<>(bars.subList(0,n-1));
    }
    private static Signal veto(MarketSnapshot m,String reason){
        String symbol=m==null?"—":m.symbol; return new Signal(Signal.Action.NO_TRADE,0,0,"—","—","—","—",reason,
                "No entry / no stop / no target. ["+symbol+"]",m==null?0:m.mid(),0,0,0,true);
    }
    private static String fmt(double e,double s,double t1,double t2){return String.format(Locale.US,"Entry %.5f | SL %.5f | TP1 %.5f | TP2 %.5f",e,s,t1,t2);}
}
