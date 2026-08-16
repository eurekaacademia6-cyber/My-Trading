package com.forexchartexpert.pro.network;

import com.forexchartexpert.pro.model.*;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

public final class MarketBridgeClient {
    public interface Callback { void onSuccess(ExpertAnalysis analysis); void onError(String message); }
    private final ExecutorService io=Executors.newFixedThreadPool(2);
    private volatile String baseUrl;
    public MarketBridgeClient(String baseUrl){this.baseUrl=baseUrl;}
    public void setBaseUrl(String url){this.baseUrl=url;}
    public void fetchAnalysis(String symbol,String timeframe,int bars,boolean strictNews,Callback cb){
        io.execute(()->{
            HttpURLConnection c=null;
            try{
                String u=baseUrl.replaceAll("/$","")+"/analysis?symbol="+URLEncoder.encode(symbol,"UTF-8")+
                        "&timeframe="+URLEncoder.encode(timeframe,"UTF-8")+"&bars="+bars+"&strict_news="+(strictNews?"1":"0");
                c=(HttpURLConnection)new URL(u).openConnection(); c.setConnectTimeout(2500); c.setReadTimeout(4500); c.setRequestMethod("GET");
                int code=c.getResponseCode(); if(code<200||code>=300) throw new IllegalStateException("Bridge HTTP "+code);
                JSONObject root=new JSONObject(read(c.getInputStream()));
                MarketSnapshot m=parseSnapshot(root.getJSONObject("snapshot"));
                JSONObject d=root.getJSONObject("decision");
                Signal.Action a=Signal.Action.valueOf(d.optString("action","NO_TRADE"));
                int conf=(int)Math.round(d.optDouble("score",0));
                String reason=joinReasons(d.optJSONArray("reasons"));
                double entry=d.optDouble("entry",0), stop=d.optDouble("stop",0), t1=d.optDouble("target1",0), t2=d.optDouble("target2",0);
                String risk="RR "+d.optDouble("risk_reward",0)+" | Risk "+d.optDouble("risk_pct",0)+"% | Lot "+d.optDouble("lot_size",0);
                Signal s=new Signal(a,conf,d.optDouble("score",0)/100.0,d.optString("trend","—"),d.optString("structure","—"),d.optString("momentum","—"),d.optString("location","—"),reason,risk,entry,stop,t1,t2,a==Signal.Action.NO_TRADE);
                cb.onSuccess(new ExpertAnalysis(m,s,d.optString("regime","—"),d.optString("liquidity","—"),d.optString("session","—"),d.optDouble("score",0),d.optDouble("buy_score",0),d.optDouble("sell_score",0),d.optDouble("lot_size",0)));
            }catch(Exception e){cb.onError(e.getMessage()==null?e.getClass().getSimpleName():e.getMessage());}
            finally{if(c!=null)c.disconnect();}
        });
    }
    private static String joinReasons(JSONArray a){if(a==null)return "No additional explanation.";StringBuilder b=new StringBuilder();for(int i=0;i<a.length();i++){if(i>0)b.append(" • ");b.append(a.optString(i));}return b.toString();}
    private static String read(InputStream is)throws Exception{StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))){String s;while((s=r.readLine())!=null)b.append(s);}return b.toString();}
    private static MarketSnapshot parseSnapshot(JSONObject o)throws Exception{
        return new MarketSnapshot(o.optString("provider","MT5"),o.getString("symbol"),o.getString("timeframe"),o.optDouble("bid",Double.NaN),o.optDouble("ask",Double.NaN),o.optLong("serverTime",0),parseCandles(o.optJSONArray("primary")),parseCandles(o.optJSONArray("higher1")),parseCandles(o.optJSONArray("higher2")),o.optDouble("spreadPoints",Double.NaN),o.optBoolean("newsKnownSafe",false));
    }
    private static List<Candle> parseCandles(JSONArray a){List<Candle> out=new ArrayList<>();if(a==null)return out;for(int i=0;i<a.length();i++){JSONObject x=a.optJSONObject(i);if(x!=null)out.add(new Candle(x.optDouble("open"),x.optDouble("high"),x.optDouble("low"),x.optDouble("close"),x.optLong("time")));}return out;}
    public void shutdown(){io.shutdownNow();}
}
