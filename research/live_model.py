"""Live inference wrapper for the empirical ML edge model."""
from __future__ import annotations
import os, time, joblib, numpy as np
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'bridge'))
from features import FEATURE_NAMES, feature_row

class MLEdgeModel:
    def __init__(self,path=None):
        self.path=Path(path or os.getenv('ML_MODEL_PATH',ROOT/'models/ml_edge_model.joblib'))
        self.artifact=None; self.loaded_at=0
        self.reload()
    @property
    def ready(self): return self.artifact is not None
    def reload(self):
        try:
            if self.path.exists():
                art=joblib.load(self.path)
                if art.get('feature_names')==FEATURE_NAMES:
                    self.artifact=art; self.loaded_at=time.time(); return True
        except Exception:
            self.artifact=None
        return False
    def score(self,bars):
        if not self.ready: return {'ready':False,'long':0.0,'short':0.0,'edge':0.0}
        x,_=feature_row(bars); X=x.reshape(1,-1)
        lm,lc=self.artifact['long_model'],self.artifact['long_calibrator']; sm,sc=self.artifact['short_model'],self.artifact['short_calibrator']
        raw_l=lm.predict_proba(X)[:,1][0]; p_l=lc.predict_proba([[raw_l]])[:,1][0]
        raw_s=sm.predict_proba(X)[:,1][0]; p_s=sc.predict_proba([[raw_s]])[:,1][0]
        return {'ready':True,'long':float(p_l),'short':float(p_s),'edge':float(p_l-p_s),'long_threshold':float(self.artifact['long_threshold']),'short_threshold':float(self.artifact['short_threshold']), 'model_time':self.loaded_at}
