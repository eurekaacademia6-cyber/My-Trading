"""Calibration diagnostics for a saved ML artifact and an evaluation CSV."""
import argparse, json
from pathlib import Path
import joblib, numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'bridge')); sys.path.insert(0,str(Path(__file__).resolve().parent))
from features import feature_row
from train_ml import load_csv, build_dataset

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--csv',required=True); ap.add_argument('--model',default=str(ROOT/'models/ml_edge_model.joblib')); ap.add_argument('--bins',type=int,default=10); ap.add_argument('--out',default='calibration.json'); a=ap.parse_args()
    art=joblib.load(a.model); bars=load_csv(a.csv); X,y,_,_=build_dataset(bars)
    raw=art['long_model'].predict_proba(X)[:,1]; p=art['long_calibrator'].predict_proba(raw.reshape(-1,1))[:,1]
    frac,mean=calibration_curve(y,p,n_bins=a.bins,strategy='quantile')
    report={'brier':float(brier_score_loss(y,p)),'bins':[{'pred':float(m),'obs':float(f)} for m,f in zip(mean,frac)]}
    Path(a.out).write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
