"""Historiadatan läpikäynti kynttilä kerrallaan ilman tulevaisuustietoa.

Jokaisen kynttilän kohdalla analysaattori näkee vain sitä edeltävät suljetut
kynttilät. Demo-tilassa kynttilät muodostuvat lisäksi tikki kerrallaan, joten
myös keskeneräiset havainnot näkyvät.

Esimerkit:
    python -m kynttilatulkki.replay --demo
    python -m kynttilatulkki.replay --binance BTCUSDT --minutes 600 --quiet
    python -m kynttilatulkki.replay --csv data.csv --symbol ETHUSDT
"""
from __future__ import annotations

import argparse
import csv
import random
from collections import Counter
from typing import Iterator

from .analyzer import DISCLAIMER, SymbolAnalyzer, format_event
from .models import Candle


def load_csv(path: str, symbol: str) -> list[Candle]:
    """CSV: open_time(ms),open,high,low,close,volume[,…] – otsikkorivi sallittu."""
    out = []
    with open(path, newline="") as f:
        for row in csv.reader(f):
            try:
                t = int(float(row[0]))
            except (ValueError, IndexError):
                continue
            if t < 10**12:          # sekunnit tai mikrosekunnit -> millisekunnit
                t *= 1000
            elif t > 10**14:
                t //= 1000
            out.append(Candle(symbol, t, *map(float, row[1:6]), closed=True))
    out.sort(key=lambda c: c.open_time)
    return out


def load_binance(symbol: str, minutes: int) -> list[Candle]:
    from .feed import fetch_klines
    import time
    end = int(time.time() * 1000)
    out: list[Candle] = []
    while len(out) < minutes:
        batch = [c for c in fetch_klines(symbol, limit=min(1000, minutes - len(out) + 1),
                                         end_time=end) if c.closed]
        if not batch:
            break
        out = batch + [c for c in out if c.open_time > batch[-1].open_time]
        end = batch[0].open_time - 1
    return out[-minutes:]


def synthetic_ticks(symbol: str = "DEMOUSDT", minutes: int = 240, seed: int = 7,
                    ticks_per_min: int = 6) -> Iterator[tuple[Candle, int]]:
    """Satunnaiskulku, jossa vaihtelevia trendijaksoja. Tuottaa (kynttilä, nyt_ms)
    -pareja: ensin keskeneräiset päivitykset, lopuksi suljettu kynttilä."""
    rnd = random.Random(seed)
    price, t0 = 100.0, 1_767_225_600_000   # 2026-01-01 00:00 UTC
    drift = 0.0
    for m in range(minutes):
        if m % 25 == 0:
            drift = rnd.choice([-0.06, -0.03, 0.0, 0.03, 0.06])
        o = h = l = price
        vol = 0.0
        base_vol = rnd.uniform(50, 150)
        for k in range(ticks_per_min):
            price *= 1 + (drift + rnd.gauss(0, 0.12)) / 100
            h, l = max(h, price), min(l, price)
            vol += base_vol / ticks_per_min * rnd.uniform(0.5, 1.8)
            last = k == ticks_per_min - 1
            now = t0 + m * 60_000 + int((k + 1) / ticks_per_min * 60_000) - (1 if last else 0)
            yield Candle(symbol, t0 + m * 60_000, o, h, l, price, vol, closed=last,
                         close_time=t0 + m * 60_000 + 59_999), now


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Historiadatan läpikäynti ilman tulevaisuustietoa")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--demo", action="store_true", help="synteettinen data (ei verkkoa)")
    g.add_argument("--csv", help="CSV-tiedosto")
    g.add_argument("--binance", metavar="SYMBOL", help="hae historia Binancesta")
    ap.add_argument("--symbol", default="CSVDATA")
    ap.add_argument("--minutes", type=int, default=500)
    ap.add_argument("--quiet", action="store_true", help="älä tulosta jokaista kynttilää")
    ap.add_argument("--brief", action="store_true", help="älä tulosta perusteluja")
    a = ap.parse_args(argv)

    if a.demo:
        stream = synthetic_ticks(minutes=a.minutes)
        sym = "DEMOUSDT"
    else:
        candles = load_csv(a.csv, a.symbol) if a.csv else load_binance(a.binance.upper(), a.minutes)
        sym = candles[0].symbol if candles else a.symbol
        stream = ((c, c.close_time or c.open_time + 59_999) for c in candles)

    an = SymbolAnalyzer(sym)
    confirmed, lost, n = Counter(), 0, 0
    print(DISCLAIMER + "\n")
    for c, now in stream:
        for ev in an.update(c, now_ms=now):
            if ev.kind == "candle":
                n += 1
                if a.quiet:
                    continue
            if ev.kind == "confirmed":
                confirmed.update(o.name for o in ev.observations)
            if ev.kind == "not_confirmed":
                lost += 1
            print(format_event(ev, verbose=not a.brief))
    print(f"\nKäyty läpi {n} suljettua kynttilää ({sym}).")
    print("Vahvistetut havainnot:")
    for k, v in confirmed.most_common():
        print(f"  {k:45s} {v}")
    print(f"Keskeneräisiä havaintoja, jotka eivät vahvistuneet: {lost}")


if __name__ == "__main__":
    main()
