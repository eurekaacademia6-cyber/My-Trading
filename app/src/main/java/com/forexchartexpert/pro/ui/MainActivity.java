package com.forexchartexpert.pro.ui;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.graphics.Color;
import android.widget.*;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.core.*;
import android.graphics.Bitmap;
import com.forexchartexpert.pro.vision.ChartVisionAnalyzer;
import com.forexchartexpert.pro.vision.OcrMetadataReader;
import com.forexchartexpert.pro.util.ImageUtil;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import com.forexchartexpert.pro.R;
import com.forexchartexpert.pro.analysis.MarketStrategyEngine;
import com.forexchartexpert.pro.analysis.SignalAuditLog;
import com.forexchartexpert.pro.model.*;
import com.forexchartexpert.pro.network.MarketBridgeClient;
import com.google.common.util.concurrent.ListenableFuture;
import java.util.*;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private PreviewView preview; private TextView status,dataSource,symbol,timeframe,spread,action,confidence,reason,trend,structure,momentum,location,risk;
    private EditText host,pair; private Spinner tf; private Button connect; private CheckBox newsFilter;
    private MarketBridgeClient client; private final Handler handler=new Handler(Looper.getMainLooper());
    private final MarketStrategyEngine engine=new MarketStrategyEngine(false);
    private SignalAuditLog audit;
    private static final int REQ=41;
    private final String[] TF={"M1","M5","M15","M30","H1","H4"};
    private boolean connected=false;
    private final ChartVisionAnalyzer visionAnalyzer=new ChartVisionAnalyzer();
    private final OcrMetadataReader ocr=new OcrMetadataReader();
    private volatile String cameraSymbol="AUTO", cameraTimeframe="AUTO";
    private volatile double visionConfidence=0.0;
    private int visionEvery=0, ocrEvery=0;
    private final Runnable poller= new Runnable(){ public void run(){ if(connected && client!=null) fetch(); handler.postDelayed(this,2500); }};

    @Override protected void onCreate(Bundle b){super.onCreate(b);setContentView(R.layout.activity_main);bind(); audit=new SignalAuditLog(this); setupTf(); connect.setOnClickListener(v->toggleConnect());
        if(ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED) ActivityCompat.requestPermissions(this,new String[]{Manifest.permission.CAMERA},REQ); else startCamera(); }
    private void bind(){preview=findViewById(R.id.preview);status=findViewById(R.id.status);dataSource=findViewById(R.id.dataSource);symbol=findViewById(R.id.symbol);timeframe=findViewById(R.id.timeframe);spread=findViewById(R.id.spread);action=findViewById(R.id.action);confidence=findViewById(R.id.confidence);reason=findViewById(R.id.reason);trend=findViewById(R.id.trend);structure=findViewById(R.id.structure);momentum=findViewById(R.id.momentum);location=findViewById(R.id.location);risk=findViewById(R.id.risk);host=findViewById(R.id.host);pair=findViewById(R.id.pair);tf=findViewById(R.id.tf);connect=findViewById(R.id.connect);newsFilter=findViewById(R.id.newsFilter);}
    private void setupTf(){tf.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,TF));tf.setSelection(1);}
    private void toggleConnect(){
        if(connected){connected=false;connect.setText("CONNECT");status.setText("OFFLINE");return;}
        String u=host.getText().toString().trim(); if(u.isEmpty()){toast("Enter bridge URL");return;} if(!u.matches("^https?://.+")){u="http://"+u;host.setText(u);} client=new MarketBridgeClient(u); connected=true; connect.setText("STOP");status.setText("CONNECTING");handler.removeCallbacks(poller);handler.post(poller);
    }
    private void fetch(){String s=pair.getText().toString().trim().toUpperCase(Locale.US);String t=TF[tf.getSelectedItemPosition()];client.fetchAnalysis(s,t,260,newsFilter.isChecked(),new MarketBridgeClient.Callback(){
        public void onSuccess(ExpertAnalysis a){
            Signal finalSignal=a.signal;
            String wantedSymbol=s; String wantedTf=t;
            boolean symbolMismatch=!cameraSymbol.equals("AUTO") && !cameraSymbol.equals("—") && !cameraSymbol.equalsIgnoreCase(wantedSymbol);
            boolean tfMismatch=!cameraTimeframe.equals("AUTO") && !cameraTimeframe.equals("—") && !cameraTimeframe.equalsIgnoreCase(wantedTf);
            if(symbolMismatch || tfMismatch){
                finalSignal=new Signal(Signal.Action.NO_TRADE,0,0,finalSignal.trend,finalSignal.structure,finalSignal.momentum,finalSignal.location,
                        "CAMERA VERIFY VETO: laptop chart metadata does not match selected market ("+cameraSymbol+" / "+cameraTimeframe+").",
                        "No trade until chart selection matches.",0,0,0,0,true);
            }
            Signal fs=finalSignal; runOnUiThread(()->render(a.snapshot,fs));
        }
        public void onError(String e){runOnUiThread(()->{status.setText("BRIDGE ERROR");reason.setText(e);});}
    });}
    private void render(MarketSnapshot m,Signal s){
        dataSource.setText("DATA: "+m.provider+"  |  LIVE OHLC + BID/ASK"); symbol.setText("PAIR "+m.symbol);timeframe.setText("TF "+m.timeframe);spread.setText("SPREAD "+(Double.isFinite(m.spreadPoints)?String.format(Locale.US,"%.1f pt",m.spreadPoints):"—"));
        String a=s.action==Signal.Action.BUY?"BUY":s.action==Signal.Action.SELL?"SELL":"NO TRADE"; action.setText(a);int col=s.action==Signal.Action.BUY?getColor(R.color.green):s.action==Signal.Action.SELL?getColor(R.color.red):getColor(R.color.amber);action.setTextColor(col);status.setText(s.action==Signal.Action.NO_TRADE?"FILTERED":"LIVE SIGNAL");status.setTextColor(col);
        confidence.setText("Confidence "+(s.confidence>0?s.confidence+"%":"—"));reason.setText(s.reason);trend.setText("Trend "+s.trend);structure.setText("Structure "+s.structure);momentum.setText("Momentum "+s.momentum);location.setText("Location "+s.location);risk.setText("Risk: "+s.risk);
        if(s.action!=Signal.Action.NO_TRADE){audit.append(System.currentTimeMillis()+","+m.symbol+","+m.timeframe+","+a+","+s.confidence+","+m.bid+","+m.ask+","+s.stop+","+s.target1+","+s.target2);}
    }
    private void startCamera(){
        ListenableFuture<ProcessCameraProvider> future=ProcessCameraProvider.getInstance(this);
        future.addListener(()->{try{
            ProcessCameraProvider p=future.get(); p.unbindAll();
            Preview pv=new Preview.Builder().build(); pv.setSurfaceProvider(preview.getSurfaceProvider());
            ImageAnalysis analysis=new ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .build();
            analysis.setAnalyzer(Executors.newSingleThreadExecutor(), image->{
                try{
                    visionEvery++;
                    if(visionEvery%5==0){
                        Bitmap bmp=ImageUtil.toBitmap(image);
                        ChartRead cr=visionAnalyzer.analyze(bmp);
                        visionConfidence=cr.visionConfidence;
                        if(ocrEvery++%4==0){
                            ocr.read(bmp,(sym,frame,raw)->{ cameraSymbol=sym; cameraTimeframe=frame; });
                        }
                    }
                }catch(Exception ignored){} finally{ image.close(); }
            });
            p.bindToLifecycle(this,CameraSelector.DEFAULT_BACK_CAMERA,pv,analysis);
        }catch(Exception e){status.setText("CAMERA ERROR");}},ContextCompat.getMainExecutor(this));
    }
    private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_SHORT).show();}
    @Override public void onRequestPermissionsResult(int r,@NonNull String[] p,@NonNull int[] g){super.onRequestPermissionsResult(r,p,g);if(r==REQ&&g.length>0&&g[0]==PackageManager.PERMISSION_GRANTED)startCamera();}
    @Override protected void onDestroy(){handler.removeCallbacks(poller);if(client!=null)client.shutdown();ocr.close();super.onDestroy();}
}
