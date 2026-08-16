"""Forex Chart Expert Ultimate - MT5 live data + expert analysis bridge.

IMPORTANT: the bridge is intentionally advisory. It does not place orders.
MetaTrader 5 provides bars/ticks through the official Python integration.
"""
import argparse, json, csv, os, time, threading, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import MetaTrader5 as mt5
from expert_engine import analyze
from ml_runtime import MLEdgeRuntime

TF={
 "M1":mt5.TIMEFRAME_M1,"M5":mt5.TIMEFRAME_M5,"M15":mt5.TIMEFRAME_M15,
 "M30":mt5.TIMEFRAME_M30,"H1":mt5.TIMEFRAME_H1,"H4":mt5.TIMEFRAME_H4,
 "D1":mt5.TIMEFRAME_D1,"W1":mt5.TIMEFRAME_W1,
}
HIGHER={"M1":("M5","M15"),"M5":("M15","H1"),"M15":("H1","H4"),"M30":("H1","H4"),"H1":("H4","D1"),"H4":("D1","W1"),"D1":("W1","W1")}
NEWS_FILE="news_events.csv"
NEWS_URL=os.getenv("NEWS_URL","")
NEWS_CACHE={"at":0,"events":None}
STABILITY={}
STABILITY_LOCK=threading.Lock()
MAX_SPREAD_POINTS=float(os.getenv("MAX_SPREAD_POINTS","25"))
ML=MLEdgeRuntime()

def load_news(path=NEWS_FILE):
    if os.path.exists(path):
        out=[]
        with open(path,newline="",encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try: out.append({"time_ms":int(r["time_ms"]),"currency":r["currency"].upper(),"impact":r.get("impact","high")})
                except Exception: pass
        return out
    if not NEWS_URL: return None
    if time.time()-NEWS_CACHE["at"]<60: return NEWS_CACHE["events"]
    try:
        with urllib.request.urlopen(NEWS_URL,timeout=3) as r: raw=json.loads(r.read().decode("utf-8"))
        events=[]
        for x in raw.get("events",raw if isinstance(raw,list) else []):
            events.append({"time_ms":int(x["time_ms"]),"currency":str(x["currency"]).upper(),"impact":str(x.get("impact","high")).lower()})
        NEWS_CACHE.update({"at":time.time(),"events":events})
        return events
    except Exception: return None

def bars(symbol,tf,count):
    arr=mt5.copy_rates_from_pos(symbol,TF[tf],0,int(count))
    if arr is None: raise RuntimeError(f"copy_rates_from_pos failed: {mt5.last_error()}")
    return [{"time":int(x[0]),"open":float(x[1]),"high":float(x[2]),"low":float(x[3]),"close":float(x[4]),"tick_volume":int(x[5]),"spread":int(x[6]),"real_volume":int(x[7])} for x in arr]

def snapshot(symbol,tf,bcount=260):
    symbol=symbol.strip().upper(); mt5.symbol_select(symbol,True)
    tick=mt5.symbol_info_tick(symbol); info=mt5.symbol_info(symbol)
    if tick is None or info is None: raise RuntimeError(f"No quote/info for {symbol}")
    tick_age=time.time()-float(getattr(tick,"time",time.time()))
    if tick_age>12: raise RuntimeError(f"Stale quote for {symbol}: {tick_age:.1f}s old")
    h1,h2=HIGHER[tf]
    p=bars(symbol,tf,bcount); a=bars(symbol,h1,max(140,bcount//2)); b=bars(symbol,h2,max(120,bcount//3))
    spread=(float(tick.ask)-float(tick.bid))/float(info.point) if info.point else float("inf")
    # Symbol metadata is useful for position sizing later without exposing credentials.
    server_ms=int(getattr(tick,"time_msc",int(tick.time*1000)))
    return {"provider":"MT5","symbol":symbol,"timeframe":tf,"bid":float(tick.bid),"ask":float(tick.ask),"point":float(info.point or 0),"digits":int(info.digits or 0),"serverTime":server_ms,"spreadPoints":spread,"newsKnownSafe":False,"higher1Timeframe":h1,"higher2Timeframe":h2,"primary":p,"higher1":a,"higher2":b}

def lot_size_for_risk(symbol, action, entry, stop, risk_pct):
    try:
        acct=mt5.account_info(); info=mt5.symbol_info(symbol)
        if acct is None or info is None or risk_pct<=0 or entry<=0 or stop<=0: return 0.0
        balance=float(acct.balance); risk_money=balance*risk_pct/100.0
        order_type=mt5.ORDER_TYPE_BUY if action=="BUY" else mt5.ORDER_TYPE_SELL
        loss_1lot=mt5.order_calc_profit(order_type, symbol, 1.0, entry, stop)
        if loss_1lot is None: return 0.0
        loss_1lot=abs(float(loss_1lot))
        if loss_1lot<=0: return 0.0
        raw=risk_money/loss_1lot
        step=float(info.volume_step or 0.01); vmin=float(info.volume_min or step); vmax=float(info.volume_max or 100.0)
        sized=max(vmin, min(vmax, (raw//step)*step))
        return round(sized, 2)
    except Exception:
        return 0.0

def stabilized(symbol, tf, decision):
    key=f"{symbol}:{tf}"
    now=time.time()
    with STABILITY_LOCK:
        seq=STABILITY.setdefault(key, [])
        seq.append((now,decision.action,decision.score))
        seq[:]=[x for x in seq if now-x[0] <= 12]
        recent=seq[-3:]
        actionable=[x for x in recent if x[1] != "NO_TRADE"]
        if decision.action != "NO_TRADE":
            same=sum(1 for x in recent if x[1]==decision.action and x[2]>=88)
            if same < 2:
                decision.action="NO_TRADE"; decision.entry=decision.stop=decision.target1=decision.target2=0.0; decision.risk_pct=0.0; decision.lot_size=0.0
                decision.vetoes.append("CONFIRMATION_WAIT")
                decision.reasons.insert(0,"WAIT: setup must persist across at least two fresh analyses")
        return decision

class H(BaseHTTPRequestHandler):
    def sendj(self,code,obj):
        body=json.dumps(obj,separators=(",",":"),allow_nan=False).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): return
    def do_GET(self):
        q=parse_qs(urlparse(self.path).query)
        try:
            if self.path.startswith('/health'):
                self.sendj(200,{"ok":True,"mt5":bool(mt5.terminal_info()),"version":"ultimate-8.2-empirical-ml"}); return
            symbol=q.get('symbol',['EURUSD'])[0]; tf=q.get('timeframe',['M5'])[0]; count=min(max(int(q.get('bars',['260'])[0]),160),500)
            snap=snapshot(symbol,tf,count)
            if self.path.startswith('/snapshot'):
                self.sendj(200,snap); return
            if self.path.startswith('/analysis'):
                strict=q.get('strict_news',['0'])[0] != '0'
                ml=ML.score(snap["primary"][:-1]) if ML.ready else {"ready":False,"long":0.0,"short":0.0,"edge":0.0}
                decision=analyze(snap, load_news(q.get('news_file',[NEWS_FILE])[0]), strict_news=strict, ml_score=ml)
                if decision.action != "NO_TRADE":
                    decision.lot_size=lot_size_for_risk(symbol, decision.action, decision.entry, decision.stop, decision.risk_pct)
                decision=stabilized(symbol, tf, decision)
                self.sendj(200,{"snapshot":snap,"ml":ml,"decision":decision.json(),"account":{"balance":float(mt5.account_info().balance) if mt5.account_info() else None,"currency":str(mt5.account_info().currency) if mt5.account_info() else None}}); return
            self.sendj(404,{"error":"Use /health, /snapshot or /analysis"})
        except Exception as e:
            self.sendj(500,{"error":str(e)})

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--bind',default='0.0.0.0'); ap.add_argument('--port',type=int,default=8765); args=ap.parse_args()
    if not mt5.initialize(): raise SystemExit(f'MT5 initialize failed: {mt5.last_error()}')
    print(f'Forex Expert Ultimate bridge: http://{args.bind}:{args.port}')
    print('Read-only advisory mode: no order placement.')
    try: ThreadingHTTPServer((args.bind,args.port),H).serve_forever()
    finally: mt5.shutdown()
