"""Reaaliaikainen PAPERIKAUPPA Kraken-perpetualeilla. Ei oikeita toimeksiantoja.

    python -m kynttilatulkki.paper_live --rules v1 --top 5
    python -m kynttilatulkki.paper_live --symbols PF_XBTUSD,PF_ETHUSD,PF_SOLUSD

Ympäristömuuttujat (Railway): RULES, SYMBOLS, TOP, INTERVAL, STATE_PATH, LOG_DIR, RESET_STATE.
Tila (pääoma, positiot, tappiorajat) tallennetaan STATE_PATH-tiedostoon, joten
uudelleenkäynnistys jatkaa samasta kohdasta. Katkon aikana suljetut kynttilät
ajetaan moottorin läpi (stopit/tavoitteet), mutta niistä ei avata uusia kauppoja.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
from dataclasses import asdict

from . import kraken
from .models import Candle
from .paper import PaperEngine, summarize, ts
from .strategy import RULESETS

MIN = 60_000


def main(argv=None) -> None:
    env = os.environ.get
    ap = argparse.ArgumentParser(description="Live-paperikauppa (Kraken-perpetualit, ei oikeita toimeksiantoja)")
    ap.add_argument("--rules", default=env("RULES", "v1"), choices=sorted(RULESETS))
    ap.add_argument("--symbols", default=env("SYMBOLS"))
    ap.add_argument("--top", type=int, default=int(env("TOP", "5")))
    ap.add_argument("--interval", type=float, default=float(env("INTERVAL", "3")))
    ap.add_argument("--state", default=env("STATE_PATH", "state/paper_state.pkl"))
    ap.add_argument("--log-dir", default=env("LOG_DIR", "logs"))
    ap.add_argument("--reset", action="store_true", default=env("RESET_STATE", "0") in ("1", "true"),
                    help="aloita puhtaalta pöydältä (esim. maksimipudotuksen pysäytyksen jälkeen)")
    a = ap.parse_args(argv)
    rules = RULESETS[a.rules]
    os.makedirs(a.log_dir, exist_ok=True)
    os.makedirs(os.path.dirname(a.state) or ".", exist_ok=True)

    tickers: dict[str, kraken.Ticker] = {}

    def hs_fn(sym: str, t: int) -> float:
        tk = tickers.get(sym)
        return tk.half_spread if tk else rules.min_half_spread_backtest

    def funding_fn(sym: str, t: int):
        tk = tickers.get(sym)
        return tk.funding_rel_per_hour if tk else None

    trades_f = open(os.path.join(a.log_dir, f"kaupat_{rules.version}.jsonl"), "a", encoding="utf-8")
    events_f = open(os.path.join(a.log_dir, f"tapahtumat_{rules.version}.jsonl"), "a", encoding="utf-8")

    def on_event(ev: dict):
        events_f.write(json.dumps(ev, ensure_ascii=False, default=str) + "\n")
        events_f.flush()

    def on_trade(tr):
        trades_f.write(json.dumps(asdict(tr), ensure_ascii=False) + "\n")
        trades_f.flush()

    eng = PaperEngine(rules, hs_fn, funding_fn, log=lambda m: print(m, flush=True),
                      on_trade=on_trade, on_event=on_event)
    last_closed: dict[str, Candle] = {}
    opened: dict[str, int] = {}

    # --- tila -------------------------------------------------------------
    if os.path.exists(a.state) and not a.reset:
        with open(a.state, "rb") as f:
            st = pickle.load(f)
        if st.get("ruleset") != rules.version:
            sys.exit(f"Tallennettu tila on sääntöversiolle {st.get('ruleset')}, nyt {rules.version}. "
                     f"Käytä eri STATE_PATH-tiedostoa tai RESET_STATE=1.")
        eng.state, eng.positions, eng.analyzers = st["state"], st["positions"], st["analyzers"]
        eng.skipped = st.get("skipped", {})
        last_closed, opened = st["last_closed"], st["opened"]
        symbols = st["symbols"]
        print(f"Jatketaan tallennetusta tilasta: pääoma {eng.state.equity:,.2f} USD, "
              f"avoimia positioita {len(eng.positions)}", flush=True)
    else:
        symbols = ([s.strip().upper() for s in a.symbols.split(",") if s.strip()] if a.symbols
                   else kraken.top_perpetuals(a.top))

    def save():
        tmp = a.state + ".tmp"
        with open(tmp, "wb") as f:
            pickle.dump({"ruleset": rules.version, "state": eng.state, "positions": eng.positions,
                         "analyzers": eng.analyzers, "skipped": eng.skipped,
                         "last_closed": last_closed, "opened": opened, "symbols": symbols}, f)
        os.replace(tmp, a.state)

    print(f"PAPERIKAUPPA – sääntöversio {rules.version} – Kraken Derivatives perpetualit: {', '.join(symbols)}")
    print("Ei oikeita toimeksiantoja. Säännöt: docs/SAANNOT_v1.md\n", flush=True)

    def feed(sym: str, cs: list[Candle], entries: bool):
        """Syöttää uudet suljetut kynttilät ja muodostuvan kynttilän avauksen."""
        eng.allow_entries = entries
        closed = [c for c in cs if c.closed and (sym not in last_closed or c.open_time > last_closed[sym].open_time)]
        if closed and sym in last_closed:
            closed = kraken.fill_gaps([last_closed[sym]] + closed)[1:]
        for c in closed:
            if opened.get(sym, 0) < c.open_time:
                eng.on_bar_open(sym, c.open_time, c.open)
                opened[sym] = c.open_time
            eng.on_bar_close(c)
            last_closed[sym] = c
        forming = [c for c in cs if not c.closed]
        if forming and entries:
            f = forming[-1]
            if opened.get(sym, 0) < f.open_time:
                eng.on_bar_open(sym, f.open_time, f.open)
                opened[sym] = f.open_time
        eng.allow_entries = True

    # --- lämmittely / kiinniotto (ei uusia kauppoja) ------------------------
    now = int(time.time() * 1000)
    tickers.update(kraken.fetch_tickers())
    for s in symbols:
        since = last_closed[s].open_time + MIN if s in last_closed else now - 60 * MIN
        since = max(since, now - 24 * 60 * MIN)
        feed(s, kraken.fetch_candles(s, since, now + MIN), entries=False)
        print(f"  {s}: historiaa {len(eng.analyzer(s).history)} kynttilää", flush=True)
    eng.pending.clear()
    save()
    print()

    last_status = 0
    try:
        while True:
            t0 = time.time()
            try:
                tickers.update(kraken.fetch_tickers())
            except Exception as e:
                print(f"tickerien haku epäonnistui: {e}", file=sys.stderr, flush=True)
            now = int(time.time() * 1000)
            for s in symbols:
                try:
                    cs = kraken.fetch_candles(s, now - 5 * MIN, now + MIN, now_ms=now)
                except Exception as e:
                    print(f"[{s}] kynttilöiden haku epäonnistui: {e}", file=sys.stderr, flush=True)
                    continue
                feed(s, cs, entries=True)
            save()
            if now - last_status >= 15 * MIN:
                last_status = now
                pos = ", ".join(f"{p.symbol} {p.side} {p.bars_held}/{rules.max_hold_bars}"
                                for p in eng.positions.values()) or "ei avoimia"
                st = eng.state
                flags = " PYSÄYTETTY" if st.halted else (" päiväraja täynnä" if st.day_blocked else "")
                print(f"[tila {ts(now)}] pääoma {st.equity:,.2f} USD | päivän tulos {st.day_pnl:+,.2f} | "
                      f"positiot: {pos}{flags}", flush=True)
            time.sleep(max(0.0, a.interval - (time.time() - t0)))
    except KeyboardInterrupt:
        save()
        print("\nLopetettu (avoimet positiot säilyvät tallennetussa tilassa).")
        print(summarize(eng.trades, eng))


if __name__ == "__main__":
    main()
