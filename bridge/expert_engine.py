"""Forex Expert Engine: deterministic, auditable, no-lookahead signal engine.

This module intentionally separates *setup score* from empirical win probability.
A probability should only be displayed after calibration on out-of-sample data.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from math import isfinite, log
from typing import Dict, List, Tuple

import numpy as np


@dataclass
class Decision:
    action: str
    score: float
    buy_score: float
    sell_score: float
    trend: str
    structure: str
    momentum: str
    regime: str
    location: str
    liquidity: str
    session: str
    risk_reward: float
    entry: float
    stop: float
    target1: float
    target2: float
    risk_pct: float
    lot_size: float
    vetoes: List[str]
    reasons: List[str]
    timeframe_alignment: Dict[str, str]
    ml_long: float = 0.0
    ml_short: float = 0.0
    ml_ready: bool = False
    model_version: str = "U8.1-hybrid-empirical-optional"

    def json(self):
        return asdict(self)


def _arr(bars, key):
    return np.asarray([float(x[key]) for x in bars], dtype=float)


def ema(x, n):
    x = np.asarray(x, float)
    if len(x) < n:
        return float("nan")
    alpha = 2.0 / (n + 1)
    y = x[0]
    for v in x[1:]:
        y = alpha * v + (1 - alpha) * y
    return y


def ema_series(x, n):
    x = np.asarray(x, float)
    out = np.empty_like(x)
    alpha = 2.0 / (n + 1)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = alpha * x[i] + (1 - alpha) * out[i - 1]
    return out


def atr(bars, n=14):
    h, l, c = _arr(bars, "high"), _arr(bars, "low"), _arr(bars, "close")
    if len(c) <= n:
        return float("nan")
    prev = np.roll(c, 1); prev[0] = c[0]
    tr = np.maximum(h - l, np.maximum(abs(h - prev), abs(l - prev)))
    return float(np.mean(tr[-n:]))


def rsi(bars, n=14):
    c = _arr(bars, "close")
    if len(c) <= n:
        return 50.0
    d = np.diff(c)
    up = np.maximum(d, 0.0); down = np.maximum(-d, 0.0)
    au = np.mean(up[-n:]); ad = np.mean(down[-n:])
    if ad == 0: return 100.0
    rs = au / ad
    return float(100 - 100 / (1 + rs))


def adx_like(bars, n=14):
    """Lightweight directional-strength approximation; avoids external TA packages."""
    h, l, c = _arr(bars, "high"), _arr(bars, "low"), _arr(bars, "close")
    if len(c) < n + 2: return 0.0
    up = np.diff(h); dn = -np.diff(l)
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    atrv = np.mean(tr[-n:]) + 1e-12
    pdi = 100 * np.mean(plus[-n:]) / atrv
    mdi = 100 * np.mean(minus[-n:]) / atrv
    dx = 100 * abs(pdi - mdi) / max(pdi + mdi, 1e-12)
    return float(dx)


def zscore_last(x, n=30):
    a = np.asarray(x[-n:], float)
    if len(a) < 5: return 0.0
    s = np.std(a)
    return float((a[-1] - np.mean(a)) / (s + 1e-12))


def pivots(bars, left=2, right=2):
    h, l = _arr(bars, "high"), _arr(bars, "low")
    highs=[]; lows=[]
    for i in range(left, len(bars)-right):
        if h[i] == max(h[i-left:i+right+1]): highs.append((i,h[i]))
        if l[i] == min(l[i-left:i+right+1]): lows.append((i,l[i]))
    return highs, lows


def structure(bars):
    highs, lows = pivots(bars)
    if len(highs) < 3 or len(lows) < 3:
        return "UNCLEAR", 0.0
    hh = highs[-1][1] > highs[-2][1]
    hl = lows[-1][1] > lows[-2][1]
    lh = highs[-1][1] < highs[-2][1]
    ll = lows[-1][1] < lows[-2][1]
    if hh and hl: return "HH_HL", 1.0
    if lh and ll: return "LH_LL", -1.0
    return "TRANSITION", 0.0


def bos_choch(bars):
    highs, lows = pivots(bars)
    if len(highs) < 2 or len(lows) < 2: return "NONE", 0.0
    last_close = float(bars[-1]["close"])
    prev_high = highs[-1][1]; prev_low = lows[-1][1]
    if last_close > prev_high: return "BOS_UP", 1.0
    if last_close < prev_low: return "BOS_DOWN", -1.0
    # transition proxy: last swing direction disagrees with earlier structure
    s, d = structure(bars)
    return ("CHOCH_UP", 0.75) if s == "HH_HL" and d > 0 else (("CHOCH_DOWN", -0.75) if s == "LH_LL" and d < 0 else ("NONE", 0.0))


def liquidity_sweep(bars, lookback=20):
    if len(bars) <= lookback + 2: return "NONE", 0.0
    prior = bars[-lookback-2:-2]
    prior_high = max(float(x["high"]) for x in prior)
    prior_low = min(float(x["low"]) for x in prior)
    b1, b2 = bars[-2], bars[-1]
    # Sweep high then close back below = bearish liquidity event.
    if float(b2["high"]) > prior_high and float(b2["close"]) < prior_high:
        return "SWEEP_HIGH", -1.0
    if float(b2["low"]) < prior_low and float(b2["close"]) > prior_low:
        return "SWEEP_LOW", 1.0
    return "NONE", 0.0


def candle_features(bars):
    b = bars[-1]
    o,h,l,c = map(float, (b["open"],b["high"],b["low"],b["close"]))
    rng=max(h-l,1e-12); body=abs(c-o); up=h-max(o,c); lo=min(o,c)-l
    bull = c > o; bear = c < o
    prev=bars[-2]
    po,pc=float(prev["open"]),float(prev["close"])
    bull_eng = bear and False
    bull_eng = bull and pc < po and c > po and o < pc
    bear_eng = bear and pc > po and c < po and o > pc
    hammer = lo >= body*2.0 and up <= max(body*0.8, rng*0.15) and c > o
    shooting = up >= body*2.0 and lo <= max(body*0.8, rng*0.15) and c < o
    return {
        "bull_engulf": bull_eng, "bear_engulf": bear_eng,
        "hammer": hammer, "shooting": shooting,
        "body_atr_ratio": body/(atr(bars,14)+1e-12), "range":rng,
    }


def session(utc_epoch_ms):
    dt=datetime.fromtimestamp(utc_epoch_ms/1000, tz=timezone.utc)
    h=dt.hour+dt.minute/60
    if dt.weekday() >= 5: return "WEEKEND"
    if 21.90 <= h <= 22.20: return "ROLLOVER"
    if 0 <= h < 7: return "ASIA"
    if 7 <= h < 12: return "LONDON"
    if 12 <= h < 17: return "NY"
    return "LATE_NY"


def trend_state(bars):
    c=_arr(bars,"close")
    e9,e21,e50=ema(c,9),ema(c,21),ema(c,50)
    s=(ema_series(c,21)[-1]-ema_series(c,21)[-5]) if len(c)>=5 else 0
    if e9>e21>e50 and s>0: return "BULLISH", 1.0
    if e9<e21<e50 and s<0: return "BEARISH", -1.0
    return "MIXED", 0.0


def regime(bars):
    a=atr(bars,14); c=_arr(bars,"close")
    recent = np.asarray([float(x["high"]-x["low"]) for x in bars[-30:]], float)
    ratio = np.mean(recent[-5:])/(np.mean(recent)+1e-12) if len(recent)>=5 else 1
    adx=adx_like(bars)
    if a <= 0: return "UNKNOWN", 0.0
    if ratio > 1.8: return "EXPANSION", 0.2
    if ratio < 0.55: return "COMPRESSION", -0.2
    if adx >= 28: return "TRENDING", 0.8
    if adx <= 15: return "RANGING", -0.4
    return "BALANCED", 0.0


def location(bars):
    c=float(bars[-1]["close"]); rh=max(float(x["high"]) for x in bars[-30:]); rl=min(float(x["low"]) for x in bars[-30:])
    pos=(c-rl)/(rh-rl+1e-12)
    if pos <= 0.20: return "VALUE_LOW", 1.0
    if pos >= 0.80: return "VALUE_HIGH", -1.0
    return "MID_RANGE", 0.0


def high_impact_veto(events, symbol, now_ms, minutes=25):
    """events: list of {time_ms,currency,impact}. Empty list means unknown, not safe."""
    if events is None: return True, "NEWS_UNKNOWN"
    base=symbol[:3]; quote=symbol[3:6]
    for e in events:
        if str(e.get("impact","high")).lower() != "high": continue
        cur=str(e.get("currency","")).upper()
        if cur not in (base,quote): continue
        if abs(int(e["time_ms"])-now_ms) <= minutes*60*1000:
            return True, f"HIGH_IMPACT_{cur}"
    return False, "SAFE_WINDOW"


def _clamp(x,a=0,b=100): return max(a,min(b,x))


def analyze(snapshot, news_events=None, strict_news=True, ml_score=None):
    # MT5 bar index 0 is the live/forming candle. Never use it for strategic confirmation.
    p=snapshot["primary"][:-1]
    h1=snapshot["higher1"][:-1]; h2=snapshot["higher2"][:-1]
    symbol=snapshot["symbol"]; tf=snapshot["timeframe"]
    now=int(snapshot["serverTime"])
    vetoes=[]; reasons=[]
    if len(p)<120 or len(h1)<100 or len(h2)<100: vetoes.append("INSUFFICIENT_HISTORY")
    bid=float(snapshot["bid"]); ask=float(snapshot["ask"]); mid=(bid+ask)/2
    if not all(isfinite(x) and x>0 for x in (bid,ask,mid)): vetoes.append("BAD_QUOTE")
    spread=float(snapshot.get("spreadPoints",9999))
    if not isfinite(spread) or spread>35: vetoes.append("SPREAD_TOO_WIDE")
    sess=session(now)
    if sess in ("WEEKEND","ROLLOVER"): vetoes.append(sess)

    t,td=trend_state(p); ht1,hd1=trend_state(h1); ht2,hd2=trend_state(h2)
    st,sd=structure(p); event,ed=bos_choch(p); liq,ld=liquidity_sweep(p)
    reg,rd=regime(p); loc,locd=location(p); cf=candle_features(p)
    rv=rsi(p,14); adx=adx_like(p); a=atr(p,14)
    # Momentum composite
    momentum = (1 if rv>55 else -1 if rv<45 else 0) + (1 if td>0 else -1 if td<0 else 0)
    mom_state="BULLISH" if momentum>=2 else "BEARISH" if momentum<=-2 else "NEUTRAL"

    # Higher timeframe agreement. Never use the forming candle: caller provides bars from MT5.
    align_long=(hd1>0 and hd2>0); align_short=(hd1<0 and hd2<0)
    # Setup score starts from zero, then adds independent evidence.
    buy=sell=50.0
    if td>0: buy+=8
    if td<0: sell+=8
    if align_long: buy+=15
    if align_short: sell+=15
    if sd>0: buy+=10
    if sd<0: sell+=10
    if ed>0: buy+=8
    if ed<0: sell+=8
    if ld>0: buy+=10
    if ld<0: sell+=10
    if locd>0: buy+=6
    if locd<0: sell+=6
    if rv>=52 and rv<=68: buy+=7
    if rv>=32 and rv<=48: sell+=7
    if cf["bull_engulf"] or cf["hammer"]: buy+=8
    if cf["bear_engulf"] or cf["shooting"]: sell+=8
    if 18<=adx<=45: buy+=3 if td>0 else 0; sell+=3 if td<0 else 0

    # Independent vetoes against chasing/mean-reversion traps.
    if cf["body_atr_ratio"]>2.0:
        if rv>72: buy-=12; vetoes.append("BULLISH_EXHAUSTION")
        if rv<28: sell-=12; vetoes.append("BEARISH_EXHAUSTION")
    if reg=="COMPRESSION" and event=="NONE":
        vetoes.append("COMPRESSION_WITHOUT_BREAK")
    if reg=="EXPANSION" and abs(cf["body_atr_ratio"])>2.4:
        vetoes.append("EXPANSION_TOO_FAST")
    if t=="MIXED" and align_long is False and align_short is False:
        vetoes.append("TREND_DISAGREEMENT")
    if strict_news:
        veto,news_state=high_impact_veto(news_events,symbol,now)
        if news_events is None: vetoes.append("NEWS_DATA_UNKNOWN")
        elif veto: vetoes.append(news_state)
    else:
        news_state="NOT_ENFORCED"

    top=max(buy,sell); other=min(buy,sell); edge=top-other
    # This is a setup score, not a calibrated win probability.
    score=_clamp(50 + (top-50)*0.55 + edge*0.45)
    action="NO_TRADE"
    atrv=max(a,1e-12)
    entry=mid; stop=target1=target2=0.0; rr=0.0; risk_pct=0.0

    ml_long=float((ml_score or {}).get("long",0.0))
    ml_short=float((ml_score or {}).get("short",0.0))
    ml_ready=bool((ml_score or {}).get("ready",False))
    ml_threshold=float((ml_score or {}).get("threshold",0.78))
    if ml_ready:
        # Empirical model is a gate, not a replacement for deterministic risk/structure checks.
        if buy>=92 and ml_long < ml_threshold:
            buy-=18; vetoes.append("ML_LONG_EDGE_BELOW_THRESHOLD")
        if sell>=92 and ml_short < ml_threshold:
            sell-=18; vetoes.append("ML_SHORT_EDGE_BELOW_THRESHOLD")
        reasons.append(f"ML edge long={ml_long:.3f} short={ml_short:.3f}")

    if buy>=92 and buy-sell>=18 and align_long and td>0 and (not ml_ready or ml_long >= ml_threshold) and "NEWS_DATA_UNKNOWN" not in vetoes and not any(v in vetoes for v in ("WEEKEND","ROLLOVER","SPREAD_TOO_WIDE","BAD_QUOTE","ML_LONG_EDGE_BELOW_THRESHOLD")):
        # Structure-based invalidation, not a fixed pip distance.
        lows=[float(x["low"]) for x in p[-12:]]
        stop=min(lows)-0.20*atrv
        risk=entry-stop
        target1=entry+1.35*risk; target2=entry+2.2*risk; rr=2.2
        action="BUY"; risk_pct=0.50 if score>=90 else 0.25
        reasons += ["HTF alignment", "trend + structure agreement", "liquidity/price-action confirmation"]
    elif sell>=92 and sell-buy>=18 and align_short and td<0 and (not ml_ready or ml_short >= ml_threshold) and "NEWS_DATA_UNKNOWN" not in vetoes and not any(v in vetoes for v in ("WEEKEND","ROLLOVER","SPREAD_TOO_WIDE","BAD_QUOTE","ML_SHORT_EDGE_BELOW_THRESHOLD")):
        highs=[float(x["high"]) for x in p[-12:]]
        stop=max(highs)+0.20*atrv
        risk=stop-entry
        target1=entry-1.35*risk; target2=entry-2.2*risk; rr=2.2
        action="SELL"; risk_pct=0.50 if score>=90 else 0.25
        reasons += ["HTF alignment", "trend + structure agreement", "liquidity/price-action confirmation"]
    else:
        reasons.append("No setup cleared every mandatory gate")

    if vetoes:
        action="NO_TRADE"; entry=stop=target1=target2=0.0; rr=0.0; risk_pct=0.0
        reasons.insert(0," | ".join(vetoes))

    # Lot size is intentionally left at zero here; the bridge can calculate it using
    # the broker's contract specification and account currency.
    # Strengthen the no-trade policy if confirmation is weak.
    if action != "NO_TRADE" and score < 89:
        action="NO_TRADE"; entry=stop=target1=target2=0.0; rr=0.0; risk_pct=0.0
        reasons.append("SETUP_SCORE_BELOW_ELITE_THRESHOLD")

    return Decision(action,round(score,1),round(buy,1),round(sell,1),t,st,mom_state,reg,loc,liq,sess,round(rr,2),entry,stop,target1,target2,risk_pct,0.0,vetoes,reasons,{
        "primary":t,"higher1":ht1,"higher2":ht2,"event":event,"news":news_state,"ml_ready":ml_ready
    }, ml_long, ml_short, ml_ready)
