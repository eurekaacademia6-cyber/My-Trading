"""Walk-forward evaluator for a CSV exported from MT5.

CSV columns required: time,open,high,low,close
The script evaluates the expert using only candles available up to each decision point.
This is deliberately simple so it can be audited and extended.
"""
import argparse, csv, json
from expert_engine import analyze

def load(path):
    with open(path,newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

def mk(row):
    return {k:(int(v) if k=='time' else float(v)) for k,v in row.items() if k in ('time','open','high','low','close')}

def evaluate(rows, horizon=12, tp_r=2.2):
    wins=losses=skips=0; samples=[]
    for i in range(160, len(rows)-horizon-1):
        p=[mk(x) for x in rows[:i]]
        # For offline testing use same series as placeholder HTF only; production should resample true HTF data.
        snap={'symbol':'TEST','timeframe':'M5','bid':p[-1]['close'],'ask':p[-1]['close'],'serverTime':p[-1]['time']*1000,'spreadPoints':0,'primary':p,'higher1':p,'higher2':p}
        d=analyze(snap, news_events=[], strict_news=False)
        if d.action=='NO_TRADE': skips+=1; continue
        future=[mk(x) for x in rows[i:i+horizon]]
        hit=None
        for b in future:
            if d.action=='BUY':
                if b['low']<=d.stop: hit='loss'; break
                if b['high']>=d.target2: hit='win'; break
            else:
                if b['high']>=d.stop: hit='loss'; break
                if b['low']<=d.target2: hit='win'; break
        if hit=='win': wins+=1
        elif hit=='loss': losses+=1
        else: skips+=1
        samples.append({'i':i,'action':d.action,'score':d.score,'outcome':hit})
    total=wins+losses
    return {'wins':wins,'losses':losses,'skips':skips,'trades':total,'win_rate':(wins/total if total else 0),'samples':samples}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('csv');ap.add_argument('--horizon',type=int,default=12);ap.add_argument('--out',default='backtest_result.json');a=ap.parse_args()
    result=evaluate(load(a.csv),a.horizon)
    with open(a.out,'w',encoding='utf-8') as f: json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='samples'},indent=2))
