"""Optional empirical ML edge scorer used by the live MT5 bridge."""
from __future__ import annotations
import os, sys, joblib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RESEARCH=ROOT/'research'
if str(RESEARCH) not in sys.path: sys.path.insert(0,str(RESEARCH))
from features import feature_row, FEATURE_NAMES

class MLEdgeRuntime:
    def __init__(self):
        self.path=Path(os.getenv('ML_MODEL_PATH',ROOT/'models/ml_edge_model.joblib'))
        self.art=None
        self.reload()
    def reload(self):
        try:
            if self.path.exists():
                art=joblib.load(self.path)
                if art.get('feature_names')==FEATURE_NAMES and bool(art.get('approved_for_live',False)):
                    self.art=art; return True
        except Exception: self.art=None
        return False
    @property
    def ready(self): return self.art is not None
    def score(self,bars):
        if not self.ready: return {'ready':False,'long':0.0,'short':0.0,'edge':0.0}
        x,_=feature_row(bars); X=x.reshape(1,-1)
        lm,lc=self.art['long_model'],self.art['long_calibrator']; sm,sc=self.art['short_model'],self.art['short_calibrator']
        pl=lc.predict_proba(lm.predict_proba(X)[:,1].reshape(-1,1))[:,1][0]
        ps=sc.predict_proba(sm.predict_proba(X)[:,1].reshape(-1,1))[:,1][0]
        return {'ready':True,'long':float(pl),'short':float(ps),'edge':float(pl-ps),'threshold':float(self.art['long_threshold'])}
