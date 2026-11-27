# Crypto Live Market (Android)

A Kivy Android dashboard for public crypto market monitoring.

## Features
- Live 24-hour ticker data from Binance public market endpoints.
- BTC, ETH, SOL, BNB, XRP, ADA and DOGE USDT pairs.
- 5-minute, 15-minute and 1-hour closed-candle analysis.
- EMA 9 / EMA 21, RSI 14 and relative-volume confirmation.
- BUY WATCH / SELL WATCH / WAIT labels.
- Manual refresh and automatic refresh every 30 seconds.
- No exchange login, API keys, order placement or trading automation.

## Build an APK
Use Ubuntu or WSL2. Buildozer's Android toolchain is intended for Linux:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo6 cmake libffi-dev libssl-dev
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip buildozer cython
buildozer android debug
```

The generated APK is under `bin/`. GitHub Actions also builds a debug APK and uploads it as a workflow artifact.

## Important
- Internet access is required.
- Prices and candles use Binance public endpoints; availability and regional access can vary.
- Signals are rule-based indicators, not guaranteed predictions or financial advice.
- Volume compares the latest completed candle with the previous 20 completed candles.
- The 1-hour option analyses 1-hour candles; it is not automatic higher-timeframe confirmation for a 5-minute trade.
- No real-money orders are placed.

## Project files
- `main.py`: Kivy UI, market data client and calculations.
- `buildozer.spec`: Android package configuration.
- `.github/workflows/android-apk.yml`: GitHub Actions APK build.
