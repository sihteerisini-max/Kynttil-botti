"""Historiatesti Kraken-perpetualeilla samoilla säännöillä kuin live-paperikauppa.

Esimerkit:
    python -m kynttilatulkki.backtest --rules v1 --top 5 --start 2026-09-20 --end 2026-09-27
    python -m kynttilatulkki.backtest --rules v1 --symbols PF_XBTUSD,PF_ETHUSD --days 3
    python -m kynttilatulkki.backtest --rules v1 --demo            # synteettinen, ei verkkoa

Ladattu data tallennetaan kansioon data/ (uudelleenkäyttö ja toistettavuus),
tulokset kansioon results/<versio>_<alku>_<loppu>/.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import time
from datetime import datetime, timezone

from .models import Candle
from .paper import PaperEngine, summarize, trades_to_jsonl
from .strategy import RULESETS

MIN = 60_000
HOUR = 3_600_000


def parse_date(s: str) -> int:
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M")


def save_csv(path: str, candles: list[Candle]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["open_time", "open", "high", "low", "close", "volume"])
        for c in candles:
            w.writerow([c.open_time, c.open, c.high, c.low, c.close, c.volume])


def load_csv(path: str, symbol: str) -> list[Candle]:
    out = []
    with open(path) as f:
        for row in csv.DictReader(f):
            t = int(row["open_time"])
            out.append(Candle(symbol, t, float(row["open"]), float(row["high"]), float(row["low"]),
                              float(row["close"]), float(row["volume"]), True, t + MIN - 1))
    return out


def synthetic(symbol: str, start: int, minutes: int, seed: int) -> list[Candle]:
    """Satunnaiskulku ilman todellista ennustettavuutta – vain koneiston testaamiseen."""
    rnd = random.Random(seed)
    p, drift, out = 100.0 * (1 + seed % 7), 0.0, []
    for m in range(minutes):
        if m % 30 == 0:
            drift = rnd.choice([-0.08, 0.0, 0.08])
        o = p
        path = [o]
        for _ in range(6):
            p *= 1 + (drift + rnd.gauss(0, 0.15)) / 100
            path.append(p)
        t = start + m * MIN
        out.append(Candle(symbol, t, o, max(path), min(path), p, rnd.uniform(50, 150) * rnd.choice([1, 1, 1, 2.5]),
                          True, t + MIN - 1))
    return out


def run(candles_by_sym: dict[str, list[Candle]], rules_key: str, half_spreads: dict[str, float],
        funding: dict[str, dict[int, float]], log=print) -> PaperEngine:
    rules = RULESETS[rules_key]

    def hs_fn(sym: str, t: int) -> float:
        return max(half_spreads.get(sym, 0.0), rules.min_half_spread_backtest)

    def funding_fn(sym: str, t: int):
        return funding.get(sym, {}).get(t - t % HOUR)

    eng = PaperEngine(rules, hs_fn, funding_fn, log=log)
    by_time: dict[int, list[Candle]] = {}
    for cs in candles_by_sym.values():
        for c in cs:
            by_time.setdefault(c.open_time, []).append(c)
    last: dict[str, Candle] = {}
    for t in sorted(by_time):
        bar = sorted(by_time[t], key=lambda c: c.symbol)
        for c in bar:                       # 1) kaikkien markkinoiden avaukset
            eng.on_bar_open(c.symbol, t, c.open)
        for c in bar:                       # 2) sitten sulkeutumiset
            eng.on_bar_close(c)
            last[c.symbol] = c
    if last:
        t_end = max(c.open_time for c in last.values()) + MIN
        eng.close_all(t_end, {s: c.close for s, c in last.items()}, "testijakson loppu")
    return eng


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Historiatesti (paperikauppa, Kraken-perpetualit)")
    ap.add_argument("--rules", default="v1", choices=sorted(RULESETS))
    ap.add_argument("--symbols", help="esim. PF_XBTUSD,PF_ETHUSD")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--start", help="UTC, esim. 2026-09-20 tai 2026-09-20T12:00")
    ap.add_argument("--end", help="UTC (ei sisälly)")
    ap.add_argument("--days", type=float, default=3, help="jos --start puuttuu: viimeiset N päivää")
    ap.add_argument("--demo", action="store_true", help="synteettinen data, ei verkkoa")
    ap.add_argument("--quiet", action="store_true", help="tulosta vain kaupat ja yhteenveto")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out-dir", default="results")
    a = ap.parse_args(argv)

    now = int(time.time() * 1000) // MIN * MIN
    end = parse_date(a.end) if a.end else now
    start = parse_date(a.start) if a.start else end - int(a.days * 86_400_000)
    candles: dict[str, list[Candle]] = {}
    half_spreads: dict[str, float] = {}
    funding: dict[str, dict[int, float]] = {}
    spread_note = ""

    if a.demo:
        symbols = [s.strip() for s in (a.symbols or "PF_DEMO1USD,PF_DEMO2USD,PF_DEMO3USD").split(",")]
        start = 1_767_225_600_000
        for i, s in enumerate(symbols):
            candles[s] = synthetic(s, start, int(a.days * 1440), seed=i + 1)
            half_spreads[s] = 0.0001
        end = start + int(a.days * 86_400_000)
        spread_note = "demo: oletettu puolikas spread 0,010 %"
    else:
        from . import kraken
        tickers = kraken.fetch_tickers()
        symbols = ([s.strip().upper() for s in a.symbols.split(",")] if a.symbols
                   else [s for s, _ in sorted(tickers.items(), key=lambda kv: -kv[1].volume_quote)[:a.top]])
        os.makedirs(a.data_dir, exist_ok=True)
        for s in symbols:
            path = os.path.join(a.data_dir, f"{s}_{iso(start).replace(':', '')}_{iso(end).replace(':', '')}.csv")
            if os.path.exists(path):
                cs = load_csv(path, s)
            else:
                print(f"Ladataan {s} {iso(start)} – {iso(end)} …", flush=True)
                cs = [c for c in kraken.fetch_candles(s, start, end) if c.closed]
                cs = kraken.fill_gaps(cs)
                save_csv(path, cs)
            candles[s] = cs
            half_spreads[s] = tickers[s].half_spread if s in tickers else 0.0
            try:
                funding[s] = kraken.fetch_funding_history(s)
            except Exception:
                funding[s] = {}
        spread_note = ("puolikas spread = max(testin alussa mitattu, 0,010 %): " +
                       ", ".join(f"{s} {max(v, 0.0001):.4%}" for s, v in half_spreads.items()))

    rules = RULESETS[a.rules]
    print(f"Sääntöversio {rules.version} | jakso {iso(start)} – {iso(end)} UTC | markkinat: {', '.join(symbols)}")
    print(f"Kulut: taker {rules.taker_fee:.3%}/suunta, liukuma {rules.slippage:.3%} (stop {rules.stop_slippage:.3%}), {spread_note}\n")

    trade_lines: list[str] = []

    def log(msg: str):
        if not a.quiet or "AVAUS" in msg or "SULKU" in msg or msg.lstrip().startswith("!"):
            print(msg)
        trade_lines.append(msg)

    eng = run(candles, a.rules, half_spreads, funding, log=log)
    summary = summarize(eng.trades, eng)
    print("\n" + "=" * 70 + "\n" + summary)

    tag = "demo_" if a.demo else ""
    out = os.path.join(a.out_dir, f"{tag}{rules.version}_{iso(start).replace(':', '')}_{iso(end).replace(':', '')}")
    os.makedirs(out, exist_ok=True)
    trades_to_jsonl(eng.trades, os.path.join(out, "kaupat.jsonl"))
    with open(os.path.join(out, "yhteenveto.md"), "w", encoding="utf-8") as f:
        f.write(f"# Historiatesti {rules.version}\n\n")
        f.write(f"* Jakso: {iso(start)} – {iso(end)} UTC\n* Markkinat: {', '.join(symbols)}\n")
        f.write(f"* Data: {'synteettinen' if a.demo else 'Kraken Derivatives charts API, 1 min trade-kynttilät'}\n")
        f.write(f"* {spread_note}\n* Ajettu: {iso(now)} UTC\n\n```\n{summary}\n```\n")
    with open(os.path.join(out, "loki.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(trade_lines))
    with open(os.path.join(out, "meta.json"), "w") as f:
        json.dump({"ruleset": rules.version, "start": iso(start), "end": iso(end), "symbols": symbols,
                   "half_spreads": half_spreads, "demo": a.demo}, f, indent=2)
    print(f"\nTulokset: {out}/")


if __name__ == "__main__":
    main()
