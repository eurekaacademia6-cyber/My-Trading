@echo off
cd /d %~dp0..\bridge
py ..\research\train_ml.py --symbol EURUSD --timeframe M5 --start 2021-01-01 --end 2026-08-01
pause
