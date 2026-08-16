"""Leakage-safe rolling walk-forward report generator.
Runs train->validate->test windows and reports OOS precision by confidence bucket."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from train_ml import load_csv, build_dataset, fit_calibrated, predict, metrics, FEATURE_NAMES

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--window',type=int,default=5000); ap.add_argument('--train',type=int,default=3000); ap.add_argument('--valid',type=int,default=1000); ap.add_argument('--test',type=int,default=1000); ap.add_argument('--step',type=int,default=1000); ap.add_argument('--out',default='walk_forward.json'); a=ap.parse_args()
    bars=load_csv(a.csv); X,y,ys,t=build_dataset(bars)
    rows=[]
    start=0
    while start+a.train+a.valid+a.test<=len(X):
        tr=slice(start,start+a.train); va=slice(start+a.train,start+a.train+a.valid); te=slice(start+a.train+a.valid,start+a.train+a.valid+a.test)
        model,cal=fit_calibrated(X[tr],y[tr],seed=start+7); pv=predict(model,cal,X[va]); pt=predict(model,cal,X[te])
        rows.append({'train_start':int(t[tr.start]),'valid_end':int(t[va.stop-1]),'test_end':int(t[te.stop-1]),'validation':metrics(y[va],pv),'test':metrics(y[te],pt),'test_precision_85':float(y[te][pt>=.85].mean()) if (pt>=.85).sum() else None,'test_count_85':int((pt>=.85).sum())})
        start+=a.step
    Path(a.out).write_text(json.dumps(rows,indent=2),encoding='utf-8'); print(json.dumps(rows,indent=2))
if __name__=='__main__': main()
