"""Binancen julkinen markkinadata (ei API-avainta, ei kaupankäyntiä).

Käyttää REST-kyselyä muutaman sekunnin välein: viimeisin palautettu kynttilä
on muodostumassa oleva, sitä edeltävät ovat suljettuja.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

from .models import Candle

BASE_URL = "https://data-api.binance.vision"   # Binancen julkinen markkinadata-osoite
STABLE = {"USDC", "FDUSD", "TUSD", "USDP", "DAI", "EUR", "BUSD", "USD1", "USDE", "XUSD"}


def _get(path: str, params: dict, base: str = BASE_URL, timeout: float = 10):
    url = f"{base}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "kynttilabotti/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def parse_kline(symbol: str, k: list, now_ms: int) -> Candle:
    close_time = int(k[6])
    return Candle(symbol=symbol, open_time=int(k[0]), open=float(k[1]), high=float(k[2]),
                  low=float(k[3]), close=float(k[4]), volume=float(k[5]),
                  closed=close_time < now_ms, close_time=close_time)


def fetch_klines(symbol: str, limit: int = 100, base: str = BASE_URL,
                 end_time: int | None = None) -> list[Candle]:
    params = {"symbol": symbol, "interval": "1m", "limit": limit}
    if end_time is not None:
        params["endTime"] = end_time
    data = _get("/api/v3/klines", params, base)
    now = int(time.time() * 1000)
    return [parse_kline(symbol, k, now) for k in data]


def top_symbols(n: int, quote: str = "USDT", base: str = BASE_URL) -> list[str]:
    """N vaihdetuinta paria (24 h vaihto), stablecoin-parit pois lukien."""
    rows = _get("/api/v3/ticker/24hr", {}, base)
    pairs = []
    for r in rows:
        s = r["symbol"]
        if not s.endswith(quote):
            continue
        asset = s[: -len(quote)]
        if asset in STABLE or asset.endswith(("UP", "DOWN", "BULL", "BEAR")):
            continue
        pairs.append((float(r["quoteVolume"]), s))
    pairs.sort(reverse=True)
    return [s for _, s in pairs[:n]]
