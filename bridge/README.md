# MT5 Live Data Bridge

This bridge runs on the Windows laptop that has MetaTrader 5 open. It reads broker-supplied OHLC bars and the current bid/ask from the MT5 terminal through the official MetaTrader 5 Python integration. MT5 exposes `copy_rates_from_pos` for bars and `symbol_info_tick` for the current tick. See the MQL5 Python integration documentation. 

## Install

```powershell
py -m pip install -r requirements.txt
```

## Run

```powershell
py bridge.py --bind 0.0.0.0 --port 8765
```

Find the laptop's LAN IPv4 address with:

```powershell
ipconfig
```

Use something like `http://192.168.1.10:8765` in the Android app.

## Important

Keep this bridge on a trusted private LAN. For public internet access, put it behind authentication + TLS rather than exposing port 8765 directly.

The bridge intentionally does not send broker credentials to the phone. The Android app receives market data only.
