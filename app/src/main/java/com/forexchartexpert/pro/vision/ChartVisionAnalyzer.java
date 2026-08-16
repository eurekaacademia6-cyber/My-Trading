package com.forexchartexpert.pro.vision;

import android.graphics.Bitmap;
import android.graphics.Color;
import com.forexchartexpert.pro.model.*;
import java.util.*;

/**
 * Camera-frame chart reconstruction. It looks for clusters of saturated red/green
 * pixels, groups them by x-position, estimates candle body/wick geometry, and
 * returns normalized OHLC-like candles. This is deliberately conservative: when
 * the chart is too noisy or candle detection is unstable, confidence drops and
 * the strategy engine vetoes the trade.
 */
public final class ChartVisionAnalyzer {
    public ChartRead analyze(Bitmap src){
        if(src==null) return new ChartRead(Collections.emptyList(),0,"—","—","No frame",false);
        Bitmap b=scale(src,900,600);
        int w=b.getWidth(), h=b.getHeight();
        // Ignore UI edges and likely axis/toolbar regions.
        int y0=(int)(h*.12), y1=(int)(h*.89), x0=(int)(w*.05), x1=(int)(w*.95);
        int[] density=new int[w];
        for(int x=x0;x<x1;x+=1){
            int count=0;
            for(int y=y0;y<y1;y+=2){
                int p=b.getPixel(x,y); int r=Color.red(p),g=Color.green(p),bl=Color.blue(p);
                boolean red=r>120 && r>g*1.22 && r>bl*1.08;
                boolean green=g>100 && g>r*1.12 && g>bl*1.04;
                if(red||green) count++;
            }
            density[x]=count;
        }
        List<int[]> clusters=new ArrayList<>(); boolean on=false; int s=0;
        for(int x=x0;x<x1;x++){
            boolean hit=density[x]>=2;
            if(hit&&!on){s=x;on=true;} if(!hit&&on){if(x-s>=2)clusters.add(new int[]{s,x-1});on=false;}
        }
        if(on) clusters.add(new int[]{s,x1-1});
        // Merge gaps that belong to a candle body/wick.
        List<int[]> merged=new ArrayList<>();
        for(int[] q:clusters){
            if(merged.isEmpty()||q[0]-merged.get(merged.size()-1)[1]>12) merged.add(q);
            else merged.get(merged.size()-1)[1]=q[1];
        }
        if(merged.size()>120) merged=merged.subList(merged.size()-120,merged.size());
        List<Candle> out=new ArrayList<>();
        for(int[] q:merged){
            int cx=(q[0]+q[1])/2; int ys=h, ye=0; int green=0,red=0;
            for(int x=q[0];x<=q[1];x++) for(int y=y0;y<y1;y++){
                int p=b.getPixel(x,y); int r=Color.red(p),g=Color.green(p),bl=Color.blue(p);
                if(g>100&&g>r*1.12&&g>bl*1.04){green++;ys=Math.min(ys,y);ye=Math.max(ye,y);} 
                if(r>120&&r>g*1.22&&r>bl*1.08){red++;ys=Math.min(ys,y);ye=Math.max(ye,y);} 
            }
            if(ye<=ys) continue;
            boolean bull=green>=red; double high=y1-ys, low=y1-ye;
            double top=y1-ys, bottom=y1-ye; double mid=(top+bottom)/2.0; double body=Math.max(2,(q[1]-q[0])*0.8);
            double open=bull?mid+body*.25:mid-body*.25, close=bull?mid-body*.25:mid+body*.25;
            // Invert screen y so price rises upward.
            double o=-open,c=-close,hh=-top,ll=-bottom;
            out.add(new Candle(o,Math.max(hh,Math.max(o,c)),Math.min(ll,Math.min(o,c)),c,System.nanoTime()));
        }
        // A good read needs enough candles and reasonable spacing.
        double spacing=0; for(int i=1;i<merged.size();i++) spacing+=merged.get(i)[0]-merged.get(i-1)[0]; spacing=Math.max(1,spacing/Math.max(1,merged.size()-1));
        double densityScore=Math.min(1.0,out.size()/55.0), spacingScore=spacing>=3&&spacing<=55?1:0.55;
        double conf=Math.min(0.98, densityScore*.65+spacingScore*.2+(out.size()>=35?.15:0));
        return new ChartRead(out,conf,"AUTO-DETECT","AUTO","Detected "+out.size()+" candle groups",conf>=.78);
    }
    private Bitmap scale(Bitmap src,int mw,int mh){ double s=Math.min(1.0,Math.min(mw/(double)src.getWidth(),mh/(double)src.getHeight())); if(s>=.999)return src; return Bitmap.createScaledBitmap(src,(int)(src.getWidth()*s),(int)(src.getHeight()*s),true); }
}
