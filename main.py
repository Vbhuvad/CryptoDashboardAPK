"""Crypto Live Market Analyzer for Android (Kivy).
Signals only; this app does not place orders.
"""
import json
import threading
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle

API_BASE = "https://api.binance.com"
DEFAULT_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
    "XRPUSDT", "ADAUSDT", "DOGEUSDT"
]
INTERVALS = ["5m", "15m", "1h"]
REFRESH_SECONDS = 30
TIMEOUT = 12

BG = (0.055, 0.07, 0.10, 1)
PANEL = (0.105, 0.13, 0.18, 1)
TEXT = (0.93, 0.95, 0.98, 1)
MUTED = (0.63, 0.68, 0.76, 1)
GREEN = (0.20, 0.86, 0.52, 1)
RED = (1.0, 0.35, 0.40, 1)
BLUE = (0.25, 0.55, 1.0, 1)


def api_get(path, params=None):
    query = urllib.parse.urlencode(params or {})
    url = API_BASE + path + (("?" + query) if query else "")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "CryptoLiveMarketAnalyzer-Android/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def ema(values, period):
    if len(values) < period:
        return None
    value = sum(values[:period]) / period
    alpha = 2.0 / (period + 1.0)
    for item in values[period:]:
        value = item * alpha + value * (1.0 - alpha)
    return value


def rsi(values, period=14):
    if len(values) < period + 1:
        return None
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(x, 0.0) for x in changes]
    losses = [max(-x, 0.0) for x in changes]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(changes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def fmt_price(value):
    if value is None:
        return "--"
    if value >= 1000:
        return f"{value:,.2f}"
    if value >= 1:
        return f"{value:,.4f}"
    return f"{value:.8f}".rstrip("0").rstrip(".")


def analyze_symbol(symbol, interval, ticker):
    candles = api_get("/api/v3/klines", {
        "symbol": symbol, "interval": interval, "limit": 100
    })
    # Ignore the still-forming candle: signals are based on closed candles.
    closed = candles[:-1] if len(candles) > 1 else candles
    closes = [float(c[4]) for c in closed]
    volumes = [float(c[5]) for c in closed]
    e9 = ema(closes, 9)
    e21 = ema(closes, 21)
    value_rsi = rsi(closes, 14)
    if not closes:
        raise ValueError("No candle data")
    avg_volumes = volumes[-21:-1]
    avg_volume = sum(avg_volumes) / len(avg_volumes) if avg_volumes else 0.0
    volume_confirm = bool(volumes and avg_volume and volumes[-1] > avg_volume)
    last_close = closes[-1]

    if e9 is None or e21 is None or value_rsi is None:
        signal = "WAIT"
    elif last_close > e9 > e21 and value_rsi >= 50 and volume_confirm:
        signal = "BUY WATCH"
    elif last_close < e9 < e21 and value_rsi <= 50 and volume_confirm:
        signal = "SELL WATCH"
    else:
        signal = "WAIT"

    return {
        "symbol": symbol,
        "price": float(ticker["lastPrice"]),
        "change": float(ticker["priceChangePercent"]),
        "high": float(ticker["highPrice"]),
        "low": float(ticker["lowPrice"]),
        "quote_volume": float(ticker["quoteVolume"]),
        "ema9": e9,
        "ema21": e21,
        "rsi": value_rsi,
        "signal": signal,
        "interval": interval,
        "volume_confirm": volume_confirm,
    }


class MarketCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(88),
            padding=(dp(12), dp(8)),
            spacing=dp(3),
            **kwargs,
        )
        with self.canvas.before:
            Color(*PANEL)
            self._background = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(10)]
            )
        self.bind(pos=self._sync_bg, size=self._sync_bg)
        self.title = Label(
            text="Loading...", color=TEXT, bold=True,
            font_size="15sp", halign="left", valign="middle",
            size_hint_y=None, height=dp(25)
        )
        self.details = Label(
            text="", color=MUTED, font_size="12sp",
            halign="left", valign="middle"
        )
        self.add_widget(self.title)
        self.add_widget(self.details)

    def _sync_bg(self, *_):
        self._background.pos = self.pos
        self._background.size = self.size

    def update_row(self, row):
        symbol = row["symbol"].replace("USDT", "/USDT")
        signal = row["signal"]
        self.title.text = (
            f"{symbol}    {fmt_price(row['price'])}    "
            f"{row['change']:+.2f}%"
        )
        rsi_value = "--" if row["rsi"] is None else f"{row['rsi']:.1f}"
        self.details.text = (
            f"{signal}   |   RSI {rsi_value}   |   "
            f"EMA9 {fmt_price(row['ema9'])} / EMA21 {fmt_price(row['ema21'])}"
        )
        self.details.color = GREEN if signal == "BUY WATCH" else (
            RED if signal == "SELL WATCH" else MUTED
        )


class CryptoDashboardApp(App):
    def build(self):
        self.title = "Crypto Live Market"
        self.interval = "5m"
        self.busy = False
        self.data = {}
        self.last_signals = {}
        self.cards = {}

        root = BoxLayout(
            orientation="vertical", padding=dp(12), spacing=dp(8)
        )
        root.canvas.before.add(Color(*BG))
        self._root_bg = RoundedRectangle(pos=root.pos, size=root.size)
        root.canvas.before.add(self._root_bg)
        root.bind(pos=self._sync_root_bg, size=self._sync_root_bg)

        header = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        title = Label(
            text="CRYPTO LIVE", color=TEXT, bold=True,
            font_size="20sp", halign="left"
        )
        header.add_widget(title)
        self.interval_spinner = Spinner(
            text=self.interval, values=INTERVALS,
            size_hint_x=None, width=dp(82), background_color=PANEL,
            color=TEXT
        )
        self.interval_spinner.bind(text=self._interval_changed)
        header.add_widget(self.interval_spinner)
        root.add_widget(header)

        controls = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        self.refresh_button = Button(
            text="Refresh", background_normal="", background_color=BLUE,
            color=TEXT
        )
        self.refresh_button.bind(on_press=lambda *_: self.refresh_data())
        controls.add_widget(self.refresh_button)
        self.status = Label(
            text="Connecting to public market data…",
            color=MUTED, font_size="11sp", halign="left"
        )
        controls.add_widget(self.status)
        root.add_widget(controls)

        self.summary = Label(
            text="BUY 0   SELL 0   WAIT 0",
            color=TEXT, font_size="14sp", bold=True,
            size_hint_y=None, height=dp(30)
        )
        root.add_widget(self.summary)

        scroll = ScrollView(do_scroll_x=False)
        self.list_box = BoxLayout(
            orientation="vertical", spacing=dp(8),
            size_hint_y=None
        )
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        for symbol in DEFAULT_SYMBOLS:
            card = MarketCard()
            self.cards[symbol] = card
            self.list_box.add_widget(card)
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)

        footer = Label(
            text="EMA 9/21 • RSI 14 • Volume confirmation • Signals only",
            color=MUTED, font_size="10sp",
            size_hint_y=None, height=dp(22)
        )
        root.add_widget(footer)
        Clock.schedule_once(lambda _dt: self.refresh_data(), 0.5)
        Clock.schedule_interval(lambda _dt: self.refresh_data(), REFRESH_SECONDS)
        return root

    def _sync_root_bg(self, widget, *_):
        self._root_bg.pos = widget.pos
        self._root_bg.size = widget.size

    def _interval_changed(self, _spinner, value):
        self.interval = value
        self.refresh_data()

    def refresh_data(self):
        if self.busy:
            return
        self.busy = True
        self.refresh_button.disabled = True
        self.status.text = "Fetching live data…"
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        results, errors = {}, []
        try:
            symbols_json = json.dumps(DEFAULT_SYMBOLS, separators=(",", ":"))
            tickers = api_get("/api/v3/ticker/24hr", {"symbols": symbols_json})
            ticker_map = {item["symbol"]: item for item in tickers}
            for symbol in DEFAULT_SYMBOLS:
                try:
                    if symbol not in ticker_map:
                        raise ValueError("Ticker missing from API response")
                    results[symbol] = analyze_symbol(
                        symbol, self.interval, ticker_map[symbol]
                    )
                except Exception as exc:
                    errors.append(f"{symbol}: {str(exc)[:100]}")
                time.sleep(0.10)
        except Exception as exc:
            errors.append(str(exc)[:160])
        try:
            Clock.schedule_once(
                lambda _dt: self._apply_results(results, errors), 0
            )
        except Exception:
            self.busy = False

    def _apply_results(self, results, errors):
        self.busy = False
        self.refresh_button.disabled = False
        self.data.update(results)
        for symbol, row in results.items():
            self.cards[symbol].update_row(row)
            self.last_signals[symbol] = row["signal"]

        buy_count = sum(r["signal"] == "BUY WATCH" for r in results.values())
        sell_count = sum(r["signal"] == "SELL WATCH" for r in results.values())
        wait_count = sum(r["signal"] == "WAIT" for r in results.values())
        self.summary.text = (
            f"BUY {buy_count}     SELL {sell_count}     WAIT {wait_count}"
        )
        stamp = datetime.now().strftime("%H:%M:%S")
        if errors:
            self.status.text = f"{len(results)}/{len(DEFAULT_SYMBOLS)} loaded • {stamp} • {errors[0]}"
        else:
            self.status.text = f"Live • {len(results)} coins • {self.interval} • Updated {stamp}"

    def on_pause(self):
        return True


if __name__ == "__main__":
    CryptoDashboardApp().run()
