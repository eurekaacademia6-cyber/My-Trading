package com.forexchartexpert.pro.analysis;

import com.forexchartexpert.pro.model.*;
import java.util.*;

public final class StrategyEngine {
    private static final double MIN_VISION=.78, MIN_QUALITY=.72;
    public Signal analyze(ChartRead read){
        List<Candle> c=read.candles;
        if(!read.stable || read.visionConfidence<MIN_VISION || c.size()<35)
            return noTrade(read,"DATA QUALITY VETO: need a stable, readable chart with enough candles.");
        double last=c.get(c.size()-1).close;
        double e9=Indicators.ema(c,9), e21=Indicators.ema(c,21), e50=Indicators.ema(c,50);
        double rsi=Indicators.rsi(c,14), atr=Indicators.atr(c,14); int sd=Indicators.swingDirection(c,2);
        double s9=Indicators.slopeEma(c,9,4), s21=Indicators.slopeEma(c,21,4);
        Candle b=c.get(c.size()-1);
        boolean bullPattern=Indicators.bullishEngulf(c)||Indicators.hammer(b);
        boolean bearPattern=Indicators.bearishEngulf(c)||Indicators.shootingStar(b);
        double rh=Indicators.recentHigh(c,20), rl=Indicators.recentLow(c,20);
        double range=Math.max(1e-9,rh-rl), pos=(last-rl)/range;
        boolean nearSupport=pos<.25, nearResistance=pos>.75;

        double bull=0,bear=0;
        if(e9>e21) bull+=20; else bear+=20;
        if(e21>e50) bull+=15; else bear+=15;
        if(s9>0&&s21>0) bull+=12; if(s9<0&&s21<0) bear+=12;
        if(sd>0) bull+=15; if(sd<0) bear+=15;
        if(rsi>=52&&rsi<=68) bull+=10; if(rsi<=48&&rsi>=32) bear+=10;
        if(bullPattern) bull+=13; if(bearPattern) bear+=13;
        if(nearSupport) bull+=9; if(nearResistance) bear+=9;

        // Overextension veto: don't chase after an abnormal move.
        double body=b.body(); boolean extended=atr>0 && body>atr*1.65;
        if(extended && rsi>72) bear-=8;
        if(extended && rsi<28) bull-=8;

        boolean volatilityOk=atr>0 && range>atr*2.0 && range<atr*18.0;
        if(!volatilityOk) return noTrade(read,"REGIME VETO: volatility/structure is not providing a clean setup.");

        String trend=e9>e21&&e21>e50?"BULLISH":e9<e21&&e21<e50?"BEARISH":"MIXED";
        String structure=sd>0?"HIGHER STRUCTURE":sd<0?"LOWER STRUCTURE":"UNCLEAR";
        String momentum=rsi>=55?"POSITIVE":rsi<=45?"NEGATIVE":"NEUTRAL";
        String location=nearSupport?"NEAR SUPPORT":nearResistance?"NEAR RESISTANCE":"MID-RANGE";
        double top=Math.max(bull,bear), second=Math.min(bull,bear), quality=top/100.0;
        int confidence=(int)Math.round(Math.min(99, 50 + top*0.42 + (top-second)*0.55 + read.visionConfidence*12));

        if(bull>=78 && bull>bear+12 && !nearResistance){
            double stop=Indicators.recentLow(c,7)-atr*.25, risk=Math.max(atr*.55,last-stop); double t1=last+risk*1.5,t2=last+risk*2.2;
            return new Signal(Signal.Action.BUY,confidence,quality,trend,structure,momentum,location,
                    "Trend + structure + momentum + bullish confirmation agree.",
                    fmt(last,stop,t1,t2),last,stop,t1,t2,false);
        }
        if(bear>=78 && bear>bull+12 && !nearSupport){
            double stop=Indicators.recentHigh(c,7)+atr*.25, risk=Math.max(atr*.55,stop-last); double t1=last-risk*1.5,t2=last-risk*2.2;
            return new Signal(Signal.Action.SELL,confidence,quality,trend,structure,momentum,location,
                    "Trend + structure + momentum + bearish confirmation agree.",
                    fmt(last,stop,t1,t2),last,stop,t1,t2,false);
        }
        return noTrade(read,"NO TRADE: the evidence does not meet the high-conviction threshold.");
    }
    private Signal noTrade(ChartRead r,String reason){ return new Signal(Signal.Action.NO_TRADE,0,r.visionConfidence*0.9,"—","—","—","—",reason,"No entry / no stop / no target.",0,0,0,0,true); }
    private String fmt(double e,double s,double t1,double t2){ return String.format(Locale.US,"Entry %.5f | SL %.5f | TP1 %.5f | TP2 %.5f",e,s,t1,t2); }
}
