# Windows quick setup

1. Install Python 3.11+.
2. Open PowerShell in this folder.
3. Run:

```powershell
py -m pip install -r requirements.txt
```

4. Open MetaTrader 5, sign in and make sure the desired forex symbol is visible in Market Watch.
5. Run `run_bridge.bat`.
6. Run `ipconfig` and note the laptop's IPv4 address, for example `192.168.1.10`.
7. On the phone, enter `http://192.168.1.10:8765`.

If Windows Firewall blocks the connection, allow the Python process/port only on the **Private** network profile. Do not expose the bridge to the public internet.
