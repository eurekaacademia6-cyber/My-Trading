"""Leakage-safe feature extraction shared by training and live inference."""
from __future__ import annotations
import math
from datetime import datetime, timezone
import numpy as np
from expert_engine import atr, rsi, adx_like, ema, ema_series, structure, bos_choch, liquidity_sweep, candle_features, trend_state, regime, location, session

FEATURE_NAMES = [
    'ret_1','ret_3','ret_6','ret_12','range_atr','body_atr','upper_wick_atr','lower_wick_atr',
    'ema9_gap_atr','ema21_gap_atr','ema50_gap_atr','ema21_slope_atr','rsi14','adx_like',
    'structure_dir','bos_dir','liq_dir','location_dir','trend_dir','regime_score',
    'distance_recent_high_atr','distance_recent_low_atr','range_pos','volume_z',
    'hour_sin','hour_cos','dow_sin','dow_cos',
    'bull_engulf','bear_engulf','hammer','shooting',
]

def _close(b): return np.asarray([float(x['close']) for x in b], dtype=float)
def _range(b): return np.asarray([float(x['high'])-float(x['low']) for x in b], dtype=float)

def _z_last(x, n=50):
    a=np.asarray(x[-n:],float)
    if len(a)<10: return 0.0
    s=np.std(a); return float((a[-1]-np.mean(a))/(s+1e-12))

def feature_row(bars):
    # bars must contain COMPLETED candles only.
    if len(bars) < 120: raise ValueError('need >=120 completed candles')
    c=_close(bars); rng=_range(bars); a=max(atr(bars,14),1e-12)
    last=c[-1]
    rets={n: float(last/c[-1-n]-1.0) for n in (1,3,6,12)}
    b=bars[-1]; o,h,l,cl=map(float,(b['open'],b['high'],b['low'],b['close']))
    body=abs(cl-o); up=h-max(o,cl); low=min(o,cl)-l
    e9=ema(c,9); e21=ema(c,21); e50=ema(c,50); e21s=ema_series(c,21)
    s,sd=structure(bars); ev,ed=bos_choch(bars); liq,ld=liquidity_sweep(bars)
    loc,locd=location(bars); tr,td=trend_state(bars); reg,rd=regime(bars)
    cf=candle_features(bars)
    hi=max(float(x['high']) for x in bars[-30:]); lo=min(float(x['low']) for x in bars[-30:])
    pos=(cl-lo)/(hi-lo+1e-12)
    volumes=np.asarray([float(x.get('tick_volume',0)) for x in bars],float)
    ts=int(b.get('time',0)); dt=datetime.fromtimestamp(ts, tz=timezone.utc)
    hour=dt.hour+dt.minute/60; dow=dt.weekday()
    row={
        'ret_1':rets[1],'ret_3':rets[3],'ret_6':rets[6],'ret_12':rets[12],
        'range_atr':rng[-1]/a,'body_atr':body/a,'upper_wick_atr':up/a,'lower_wick_atr':low/a,
        'ema9_gap_atr':(cl-e9)/a,'ema21_gap_atr':(cl-e21)/a,'ema50_gap_atr':(cl-e50)/a,
        'ema21_slope_atr':(e21s[-1]-e21s[-6])/a,'rsi14':rsi(bars,14),'adx_like':adx_like(bars),
        'structure_dir':sd,'bos_dir':ed,'liq_dir':ld,'location_dir':locd,'trend_dir':td,'regime_score':rd,
        'distance_recent_high_atr':(hi-cl)/a,'distance_recent_low_atr':(cl-lo)/a,'range_pos':pos,
        'volume_z':_z_last(volumes), 'hour_sin':math.sin(2*math.pi*hour/24),'hour_cos':math.cos(2*math.pi*hour/24),
        'dow_sin':math.sin(2*math.pi*dow/7),'dow_cos':math.cos(2*math.pi*dow/7),
        'bull_engulf':1.0 if cf['bull_engulf'] else 0.0,'bear_engulf':1.0 if cf['bear_engulf'] else 0.0,
        'hammer':1.0 if cf['hammer'] else 0.0,'shooting':1.0 if cf['shooting'] else 0.0,
    }
    return np.asarray([row[k] for k in FEATURE_NAMES], dtype=np.float32), row
