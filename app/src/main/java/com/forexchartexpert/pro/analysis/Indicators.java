package com.forexchartexpert.pro.analysis;

import com.forexchartexpert.pro.model.Candle;
import java.util.*;

public final class Indicators {
    private Indicators() {}
    public static double ema(List<Candle> c, int p){
        if(c.size()<p) return Double.NaN;
        double k=2.0/(p+1), e=c.get(0).close;
        for(int i=1;i<c.size();i++) e=c.get(i).close*k+e*(1-k);
        return e;
    }
    public static double emaAt(List<Candle> c, int p, int end){
        if(end< p-1) return Double.NaN;
        double k=2.0/(p+1), e=c.get(0).close;
        for(int i=1;i<=end;i++) e=c.get(i).close*k+e*(1-k);
        return e;
    }
    public static double rsi(List<Candle> c, int p){
        if(c.size()<=p) return Double.NaN;
        double gain=0, loss=0;
        for(int i=1;i<=p;i++){ double d=c.get(i).close-c.get(i-1).close; if(d>0) gain+=d; else loss-=d; }
        gain/=p; loss/=p;
        for(int i=p+1;i<c.size();i++){ double d=c.get(i).close-c.get(i-1).close; gain=(gain*(p-1)+Math.max(0,d))/p; loss=(loss*(p-1)+Math.max(0,-d))/p; }
        if(loss==0) return 100; return 100-(100/(1+gain/loss));
    }
    public static double atr(List<Candle> c, int p){
        if(c.size()<p+1) return Double.NaN;
        double sum=0;
        for(int i=1;i<c.size();i++){
            double tr=Math.max(c.get(i).high-c.get(i).low, Math.max(Math.abs(c.get(i).high-c.get(i-1).close), Math.abs(c.get(i).low-c.get(i-1).close)));
            if(i>=c.size()-p) sum+=tr;
        }
        return sum/p;
    }
    public static double slopeEma(List<Candle> c, int p, int lookback){
        if(c.size()<p+lookback) return 0;
        int n=c.size()-1; double now=emaAt(c,p,n), prev=emaAt(c,p,n-lookback); return now-prev;
    }
    public static int swingDirection(List<Candle> c, int w){
        if(c.size()<w*2+5) return 0;
        int last=-1, prev=-1;
        for(int i=w;i<c.size()-w;i++){
            boolean hi=true, lo=true; double h=c.get(i).high,l=c.get(i).low;
            for(int j=i-w;j<=i+w;j++){ if(j==i) continue; if(c.get(j).high>=h) hi=false; if(c.get(j).low<=l) lo=false; }
            if(hi||lo){ prev=last; last=i; }
        }
        if(prev<0||last<0) return 0;
        return c.get(last).close>c.get(prev).close ? 1 : -1;
    }
    public static double recentHigh(List<Candle> c,int n){ double x=-Double.MAX_VALUE; for(int i=Math.max(0,c.size()-n);i<c.size();i++) x=Math.max(x,c.get(i).high); return x; }
    public static double recentLow(List<Candle> c,int n){ double x=Double.MAX_VALUE; for(int i=Math.max(0,c.size()-n);i<c.size();i++) x=Math.min(x,c.get(i).low); return x; }
    public static boolean bullishEngulf(List<Candle> c){ if(c.size()<2)return false; Candle a=c.get(c.size()-2),b=c.get(c.size()-1); return a.bear()&&b.bull()&&b.open<=a.close&&b.close>=a.open; }
    public static boolean bearishEngulf(List<Candle> c){ if(c.size()<2)return false; Candle a=c.get(c.size()-2),b=c.get(c.size()-1); return a.bull()&&b.bear()&&b.open>=a.close&&b.close<=a.open; }
    public static boolean hammer(Candle b){ return b.range()>0 && b.lowerWick()>=b.body()*2.2 && b.upperWick()<=b.body()*0.8; }
    public static boolean shootingStar(Candle b){ return b.range()>0 && b.upperWick()>=b.body()*2.2 && b.lowerWick()<=b.body()*0.8; }
}
