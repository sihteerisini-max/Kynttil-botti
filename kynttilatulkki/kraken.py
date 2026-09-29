"""Kraken Derivatives -julkinen markkinadata (ei API-avainta, ei toimeksiantoja).

* 1 min kynttilät: /api/charts/v1/trade/<symbol>/1m?from=<s>&to=<s>
* ticker: /derivatives/api/v3/tickers[/<symbol>] (bid, ask, markPrice, fundingRate)
* historiallinen funding: /derivatives/api/v4/historicalfundingrates?symbol=<symbol>
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime

from .models import Candle

BASE_URL = "https://futures.kraken.com"
MINUTE = 60_000


def _get(path: str, params: dict | None = None, base: str = BASE_URL, timeout: float = 15):
    url = f"{base}{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": "kynttilabotti/0.2"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


@dataclass
class Ticker:
    symbol: str
    bid: float
    ask: float
    mark: float
    funding_rel_per_hour: float   # fundingRate / markPrice (Krakenin fundingRate on USD/sopimus/h)
    volume_quote: float

    @property
    def half_spread(self) -> float:
        mid = (self.bid + self.ask) / 2
        return (self.ask - self.bid) / 2 / mid if mid > 0 else 0.0


def _ticker(d: dict) -> Ticker:
    mark = float(d.get("markPrice") or d.get("last") or 0)
    fr = float(d.get("fundingRate") or 0)
    return Ticker(d["symbol"], float(d.get("bid") or 0), float(d.get("ask") or 0), mark,
                  fr / mark if mark else 0.0, float(d.get("volumeQuote") or 0))


def fetch_ticker(symbol: str, base: str = BASE_URL) -> Ticker:
    return _ticker(_get(f"/derivatives/api/v3/tickers/{symbol}", base=base)["ticker"])


def fetch_tickers(base: str = BASE_URL) -> dict[str, Ticker]:
    rows = _get("/derivatives/api/v3/tickers", base=base)["tickers"]
    return {r["symbol"]: _ticker(r) for r in rows
            if r.get("tag") == "perpetual" and str(r.get("symbol", "")).startswith("PF_")
            and not r.get("suspended") and r.get("bid") and r.get("ask")}


def top_perpetuals(n: int, base: str = BASE_URL) -> list[str]:
    t = fetch_tickers(base)
    return [s for s, _ in sorted(t.items(), key=lambda kv: -kv[1].volume_quote)[:n]]


def fetch_candles(symbol: str, start_ms: int, end_ms: int, base: str = BASE_URL,
                  now_ms: int | None = None) -> list[Candle]:
    """1 min kynttilät väliltä [start, end). Keskeneräinen kynttilä merkitään closed=False."""
    now_ms = now_ms or int(time.time() * 1000)
    out: dict[int, Candle] = {}
    frm = start_ms // 1000
    to = end_ms // 1000
    while frm < to:
        data = _get(f"/api/charts/v1/trade/{symbol}/1m", {"from": frm, "to": to}, base)
        cs = data.get("candles") or []
        for c in cs:
            t = int(c["time"])
            if start_ms <= t < end_ms:
                out[t] = Candle(symbol, t, float(c["open"]), float(c["high"]), float(c["low"]),
                                float(c["close"]), float(c["volume"]),
                                closed=t + MINUTE <= now_ms, close_time=t + MINUTE - 1)
        if not cs or not data.get("more_candles"):
            break
        nxt = int(cs[-1]["time"]) // 1000 + 60
        if nxt <= frm:
            break
        frm = nxt
    return [out[k] for k in sorted(out)]


def fill_gaps(candles: list[Candle]) -> list[Candle]:
    """Minuutit ilman kauppoja puuttuvat datasta. Täytetään ne tasaisilla
    nollavolyymin kynttilöillä (hinta = edellinen päätös), jotta aika etenee
    tasaisesti ja pitoaika lasketaan oikein."""
    if not candles:
        return []
    out = [candles[0]]
    for c in candles[1:]:
        t = out[-1].open_time + MINUTE
        while t < c.open_time:
            p = out[-1].close
            out.append(Candle(c.symbol, t, p, p, p, p, 0.0, closed=True, close_time=t + MINUTE - 1))
            t += MINUTE
        out.append(c)
    return out


def fetch_funding_history(symbol: str, base: str = BASE_URL) -> dict[int, float]:
    """{tunnin alku ms: suhteellinen tuntikorko}"""
    rows = _get("/derivatives/api/v4/historicalfundingrates", {"symbol": symbol}, base).get("rates", [])
    out = {}
    for r in rows:
        ts = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
        out[int(ts.timestamp() * 1000)] = float(r.get("relativeFundingRate") or 0)
    return out


@dataclass(frozen=True)
class InstrumentSpec:
    """Kaupattavan koon ja marginaalin rajat (Kraken /derivatives/api/v3/instruments)."""
    symbol: str
    qty_step: float                       # 10^-contractValueTradePrecision
    max_position: float                   # maxPositionSize (yksikköä)
    margin_levels: tuple = ((0.0, 0.10),)  # ((nimellisarvon alaraja USD, alkumarginaali), ...)

    def initial_margin(self, notional: float) -> float:
        im = self.margin_levels[0][1]
        for lo, m in self.margin_levels:
            if notional >= lo:
                im = m
        return im


def fetch_instruments(base: str = BASE_URL) -> dict[str, InstrumentSpec]:
    rows = _get("/derivatives/api/v3/instruments", base=base).get("instruments", [])
    out = {}
    for r in rows:
        sym = str(r.get("symbol", "")).upper()
        if not sym.startswith("PF_") or "contractValueTradePrecision" not in r:
            continue
        levels = r.get("retailMarginLevels") or r.get("marginLevels") or []
        ml = tuple(sorted((float(x.get("numNonContractUnits") or x.get("contracts") or 0),
                           float(x["initialMargin"])) for x in levels)) or ((0.0, 0.10),)
        out[sym] = InstrumentSpec(sym, 10 ** -int(r["contractValueTradePrecision"]),
                                  float(r.get("maxPositionSize") or 1e18), ml)
    return out
