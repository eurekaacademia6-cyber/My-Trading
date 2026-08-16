package com.forexchartexpert.pro.ui;

import android.content.Context;
import android.graphics.*;
import android.util.AttributeSet;
import android.view.View;

public class ScanOverlayView extends View {
    private final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
    public ScanOverlayView(Context c, AttributeSet a){super(c,a); p.setStrokeWidth(3); p.setStyle(Paint.Style.STROKE);}
    protected void onDraw(Canvas c){
        super.onDraw(c); p.setColor(Color.argb(185,70,200,255));
        float l=getWidth()*.07f,r=getWidth()*.93f,t=getHeight()*.16f,b=getHeight()*.84f;
        c.drawRoundRect(l,t,r,b,18,18,p);
        p.setStyle(Paint.Style.FILL);p.setTextSize(12);p.setColor(Color.WHITE);
        c.drawText("ALIGN THE PLOT AREA INSIDE THIS FRAME",l+14,t-10,p);
        p.setColor(Color.argb(150,0,0,0)); c.drawRect(0,0,getWidth(),t-24,p); c.drawRect(0,b+10,getWidth(),getHeight(),p); p.setStyle(Paint.Style.STROKE);
    }
}
