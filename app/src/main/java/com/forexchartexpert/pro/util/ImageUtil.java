package com.forexchartexpert.pro.util;

import android.graphics.Bitmap;
import android.graphics.Matrix;
import androidx.camera.core.ImageProxy;
import java.nio.ByteBuffer;

public final class ImageUtil {
    private ImageUtil(){}
    public static Bitmap toBitmap(ImageProxy image){
        ImageProxy.PlaneProxy[] planes=image.getPlanes();
        int w=image.getWidth(),h=image.getHeight();
        ByteBuffer y=planes[0].getBuffer(),u=planes[1].getBuffer(),v=planes[2].getBuffer();
        byte[] yb=new byte[y.remaining()],ub=new byte[u.remaining()],vb=new byte[v.remaining()]; y.get(yb);u.get(ub);v.get(vb);
        int[] pixels=new int[w*h]; int yp=0;
        for(int j=0;j<h;j++){
            int uvRow=(j/2)*planes[1].getRowStride();
            for(int i=0;i<w;i++){
                int yIndex=Math.min(yb.length-1,j*planes[0].getRowStride()+i*planes[0].getPixelStride());
                int uvIndex=Math.min(ub.length-1,uvRow+(i/2)*planes[1].getPixelStride());
                int Y=(yb[yIndex]&0xff)-16, U=(ub[uvIndex]&0xff)-128,V=(vb[Math.min(vb.length-1,uvRow+(i/2)*planes[2].getPixelStride())]&0xff)-128;
                int r=clamp((298*Y+409*V+128)>>8),g=clamp((298*Y-100*U-208*V+128)>>8),b=clamp((298*Y+516*U+128)>>8);
                pixels[yp++]=(0xff<<24)|(r<<16)|(g<<8)|b;
            }
        }
        Bitmap out=Bitmap.createBitmap(pixels,w,h,Bitmap.Config.ARGB_8888);
        Matrix m=new Matrix(); m.postRotate(image.getImageInfo().getRotationDegrees());
        return Bitmap.createBitmap(out,0,0,out.getWidth(),out.getHeight(),m,true);
    }
    private static int clamp(int x){return Math.max(0,Math.min(255,x));}
}
