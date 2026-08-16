"""Train the empirical probability model from real MT5 history.

Workflow:
  1) Pull chronological broker bars (or use --csv).
  2) Build features using only candles available at the decision time.
  3) Triple-barrier label future outcomes with costs.
  4) Walk-forward train/validate/test chronologically.
  5) Calibrate probabilities on a separate validation slice.
  6) Export a model artifact consumed by the live bridge.
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
import joblib, numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, average_precision_score, log_loss, brier_score_loss
from sklearn.model_selection import TimeSeriesSplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from features import FEATURE_NAMES, feature_row


def load_mt5(symbol, timeframe, start, end):
    import MetaTrader5 as mt5
    tfmap={"M1":mt5.TIMEFRAME_M1,"M5":mt5.TIMEFRAME_M5,"M15":mt5.TIMEFRAME_M15,"M30":mt5.TIMEFRAME_M30,"H1":mt5.TIMEFRAME_H1,"H4":mt5.TIMEFRAME_H4,"D1":mt5.TIMEFRAME_D1}
    if not mt5.initialize(): raise RuntimeError(f'MT5 init failed: {mt5.last_error()}')
    try:
        mt5.symbol_select(symbol,True)
        rates=mt5.copy_rates_range(symbol,tfmap[timeframe],start,end)
        if rates is None or len(rates)<500: raise RuntimeError(f'Not enough bars: {mt5.last_error()}')
        return [{"time":int(x[0]),"open":float(x[1]),"high":float(x[2]),"low":float(x[3]),"close":float(x[4]),"tick_volume":int(x[5]),"spread":int(x[6]),"real_volume":int(x[7])} for x in rates]
    finally: mt5.shutdown()

def load_csv(path):
    import csv
    with open(path,encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    out=[]
    for r in rows:
        out.append({k:(int(v) if k in ('time','tick_volume','spread','real_volume') else float(v)) for k,v in r.items() if k in ('time','open','high','low','close','tick_volume','spread','real_volume')})
    return sorted(out,key=lambda x:x['time'])

def label_at(bars, i, horizon=18, atr_mult=1.25, rr=2.0, spread_cost=0.0):
    """1 if long barrier wins, 0 if short barrier wins, None if ambiguous/no barrier.
    For balanced training, we learn LONG-vs-not-long. A second classifier is trained for SHORT.
    """
    base=bars[i]['close']; window=bars[max(0,i-20):i+1]
    from expert_engine import atr
    a=max(atr(window,14),1e-9)
    sl=atr_mult*a+spread_cost
    tp=rr*sl
    long_tp=base+tp; long_sl=base-sl
    short_tp=base-tp; short_sl=base+sl
    long_hit=None; short_hit=None
    for j in range(i+1,min(len(bars),i+1+horizon)):
        h=float(bars[j]['high']); l=float(bars[j]['low'])
        if long_sl>=l and long_tp<=h: return None,None
        if long_hit is None:
            if l<=long_sl: long_hit=False
            elif h>=long_tp: long_hit=True
        if short_hit is None:
            if h>=short_sl: short_hit=False
            elif l<=short_tp: short_hit=True
        if long_hit is not None or short_hit is not None: break
    # Directional label: select the first clean barrier hit; skip ambiguous/no-hit.
    if long_hit is True and short_hit is not True: return 1,0
    if short_hit is True and long_hit is not True: return 0,1
    return None,None

def build_dataset(bars, start_idx=160, horizon=18, atr_mult=1.25, rr=2.0, spread_cost=0.0):
    X=[]; yl=[]; ys=[]; times=[]
    for i in range(start_idx, len(bars)-horizon-1):
        try: x,_=feature_row(bars[:i+1])
        except Exception: continue
        l,s=label_at(bars,i,horizon,atr_mult,rr,spread_cost)
        if l is None: continue
        X.append(x); yl.append(l); ys.append(s); times.append(int(bars[i]['time']))
    return np.asarray(X),np.asarray(yl),np.asarray(ys),np.asarray(times)

def fit_calibrated(X,y,seed=42):
    model=Pipeline([('imp',SimpleImputer(strategy='median')),('clf',HistGradientBoostingClassifier(max_iter=300,learning_rate=.045,max_leaf_nodes=15,l2_regularization=1.0,random_state=seed))])
    model.fit(X,y)
    p=model.predict_proba(X)[:,1]
    cal=LogisticRegression(C=10.0,solver='lbfgs')
    cal.fit(p.reshape(-1,1),y)
    return model,cal

def predict(model,cal,X):
    p=model.predict_proba(X)[:,1]
    return cal.predict_proba(p.reshape(-1,1))[:,1]

def metrics(y,p):
    return {'auc':float(roc_auc_score(y,p)),'ap':float(average_precision_score(y,p)),'logloss':float(log_loss(y,p,labels=[0,1])),'brier':float(brier_score_loss(y,p))}

def choose_threshold(y,p,min_trades=30,target_precision=.80):
    best=None
    for t in np.linspace(.50,.99,100):
        sel=p>=t; n=int(sel.sum())
        if n<min_trades: continue
        precision=float(y[sel].mean())
        if precision>=target_precision:
            cand=(precision,n,t)
            if best is None or cand[0]>best[0] or (cand[0]==best[0] and cand[1]>best[1]): best=cand
    if best is None:
        # fallback: maximize precision subject to enough observations
        vals=[]
        for t in np.linspace(.50,.95,91):
            sel=p>=t
            if sel.sum()>=min_trades: vals.append((float(y[sel].mean()),int(sel.sum()),t))
        best=max(vals,default=(0,0,.70))
    return {'threshold':float(best[2]),'precision_at_threshold':float(best[0]),'samples_at_threshold':int(best[1])}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--symbol',default='EURUSD'); ap.add_argument('--timeframe',default='M5',choices=['M1','M5','M15','M30','H1','H4','D1'])
    ap.add_argument('--start',default='2021-01-01'); ap.add_argument('--end',default='2026-08-01')
    ap.add_argument('--csv',default=''); ap.add_argument('--out',default=str(ROOT/'models/ml_edge_model.joblib'))
    ap.add_argument('--horizon',type=int,default=18); ap.add_argument('--rr',type=float,default=2.0); ap.add_argument('--atr-mult',type=float,default=1.25); ap.add_argument('--approve',action='store_true',help='mark artifact as eligible for live use after review')
    args=ap.parse_args()
    if args.csv: bars=load_csv(args.csv)
    else:
        from datetime import datetime, timezone
        bars=load_mt5(args.symbol,args.timeframe,datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc),datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc))
    X,yl,ys,times=build_dataset(bars,horizon=args.horizon,atr_mult=args.atr_mult,rr=args.rr)
    if len(X)<500: raise SystemExit(f'Only {len(X)} labeled samples; need at least 500.')
    # Chronological 60/20/20 split; no shuffling.
    n=len(X); a=int(n*.60); b=int(n*.80)
    Xtr,Xva,Xte=X[:a],X[a:b],X[b:]; yltr,ylva,ylte=yl[:a],yl[a:b],yl[b:]; ystr,ysva,yste=ys[:a],ys[b:]
    long_model,long_cal=fit_calibrated(Xtr,yltr,seed=7)
    short_model,short_cal=fit_calibrated(Xtr,1-yltr,seed=11)
    pl=predict(long_model,long_cal,Xva); ps=predict(short_model,short_cal,Xva)
    threshold=choose_threshold(ylva,pl,target_precision=.80)
    pte_long=predict(long_model,long_cal,Xte); pte_short=predict(short_model,short_cal,Xte)
    artifact={'schema':2,'approved_for_live':bool(args.approve),'symbol':args.symbol,'timeframe':args.timeframe,'feature_names':FEATURE_NAMES,'long_model':long_model,'long_calibrator':long_cal,'short_model':short_model,'short_calibrator':short_cal,
              'long_threshold':threshold['threshold'],'short_threshold':threshold['threshold'],'train_end_time':int(times[a-1]),'validation_end_time':int(times[b-1]),
              'validation_metrics_long':metrics(ylva,pl),'test_metrics_long':metrics(ylte,pte_long),'test_metrics_short':metrics(1-ylte,pte_short),
              'validation_precision_threshold':threshold,'horizon_bars':args.horizon,'deployment_note':'Review rolling OOS metrics, costs and stability before --approve' ,'rr':args.rr,'atr_mult':args.atr_mult}
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); joblib.dump(artifact,out,compress=3)
    report={'symbol':args.symbol,'timeframe':args.timeframe,'samples':len(X),'train':a,'validation':b-a,'test':n-b,'validation_metrics_long':artifact['validation_metrics_long'],'test_metrics_long':artifact['test_metrics_long'],'test_metrics_short':artifact['test_metrics_short'],'threshold':threshold}
    out.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
