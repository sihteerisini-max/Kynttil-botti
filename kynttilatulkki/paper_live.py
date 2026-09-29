"""Reaaliaikainen PAPERIKAUPPA Kraken-perpetualeilla. Ei oikeita toimeksiantoja.

Useampi sääntöversio voi ajaa rinnakkain erillisillä paperitileillä samasta
datavirrasta ja samasta käynnistyshetkestä:

    python -m kynttilatulkki.paper_live --rules v1.1,v2 --top 5

Ympäristömuuttujat (Railway): RULES, SYMBOLS, TOP, INTERVAL, STATE_DIR, LOG_DIR, RESET_STATE.
Kunkin version tila tallennetaan tiedostoon STATE_DIR/paper_<versio>.pkl, joten
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


class Account:
    """Yksi paperitili = yksi sääntöversio, oma pääoma, tila ja lokit."""

    def __init__(self, version: str, state_dir: str, log_dir: str, tickers: dict, reset: bool):
        self.rules = r = RULESETS[version]
        self.version = version
        self.state_path = os.path.join(state_dir, f"paper_{version}.pkl")
        self.tickers = tickers
        self.trades_f = open(os.path.join(log_dir, f"kaupat_{version}.jsonl"), "a", encoding="utf-8")
        self.events_f = open(os.path.join(log_dir, f"tapahtumat_{version}.jsonl"), "a", encoding="utf-8")
        tag = f"[{version}] "
        self.engine = PaperEngine(r, self._hs, self._funding,
                                  log=lambda m: print(tag + m, flush=True),
                                  on_trade=self._on_trade, on_event=self._on_event)
        self.last_closed: dict[str, Candle] = {}
        self.opened: dict[str, int] = {}
        self.symbols: list[str] | None = None
        self.started_at: int | None = None
        if os.path.exists(self.state_path) and not reset:
            with open(self.state_path, "rb") as f:
                st = pickle.load(f)
            if st.get("ruleset") != version:
                sys.exit(f"{self.state_path}: tallennettu versio {st.get('ruleset')} ≠ {version}")
            e = self.engine
            e.state, e.positions, e.analyzers = st["state"], st["positions"], st["analyzers"]
            e.skipped = st.get("skipped", {})
            self.last_closed, self.opened = st["last_closed"], st["opened"]
            self.symbols, self.started_at = st["symbols"], st.get("started_at")
            print(f"{tag}jatketaan tallennetusta tilasta: pääoma {e.state.equity:,.2f} USD, "
                  f"avoimia positioita {len(e.positions)}", flush=True)

    def _hs(self, sym: str, t: int) -> float:
        tk = self.tickers.get(sym)
        return tk.half_spread if tk else self.rules.min_half_spread_backtest

    def _funding(self, sym: str, t: int):
        tk = self.tickers.get(sym)
        return tk.funding_rel_per_hour if tk else None

    def _on_event(self, ev: dict):
        self.events_f.write(json.dumps(ev, ensure_ascii=False, default=str) + "\n")
        self.events_f.flush()

    def _on_trade(self, tr):
        line = json.dumps(asdict(tr), ensure_ascii=False)
        self.trades_f.write(line + "\n")
        self.trades_f.flush()
        print(f"KAUPPA_JSON {line}", flush=True)      # myös lokiin, jotta kaupat voi poimia Railwayn lokeista

    def save(self):
        tmp = self.state_path + ".tmp"
        e = self.engine
        with open(tmp, "wb") as f:
            pickle.dump({"ruleset": self.version, "state": e.state, "positions": e.positions,
                         "analyzers": e.analyzers, "skipped": e.skipped, "last_closed": self.last_closed,
                         "opened": self.opened, "symbols": self.symbols, "started_at": self.started_at}, f)
        os.replace(tmp, self.state_path)

    def feed(self, sym: str, cs: list[Candle], entries: bool):
        """Syöttää uudet suljetut kynttilät ja muodostuvan kynttilän avauksen."""
        eng = self.engine
        eng.allow_entries = entries
        lc = self.last_closed.get(sym)
        closed = [c for c in cs if c.closed and (lc is None or c.open_time > lc.open_time)]
        if closed and lc is not None:
            closed = kraken.fill_gaps([lc] + closed)[1:]
        for c in closed:
            if self.opened.get(sym, 0) < c.open_time:
                eng.on_bar_open(sym, c.open_time, c.open)
                self.opened[sym] = c.open_time
            eng.on_bar_close(c)
            self.last_closed[sym] = c
        forming = [c for c in cs if not c.closed]
        if forming and entries:
            f = forming[-1]
            if self.opened.get(sym, 0) < f.open_time:
                eng.on_bar_open(sym, f.open_time, f.open)
                self.opened[sym] = f.open_time
        eng.allow_entries = True

    def status(self, now: int) -> str:
        e, st = self.engine, self.engine.state
        pos = ", ".join(f"{p.symbol} {p.side} {p.bars_held}/{self.rules.max_hold_bars}"
                        for p in e.positions.values()) or "ei avoimia"
        flags = " PYSÄYTETTY" if st.halted else (" päiväraja täynnä" if st.day_blocked else "")
        return (f"[{self.version}] [tila {ts(now)}] pääoma {st.equity:,.2f} USD | päivän tulos "
                f"{st.day_pnl:+,.2f} | kauppoja tällä ajolla {len(e.trades)} | positiot: {pos}{flags}")


def main(argv=None) -> None:
    env = os.environ.get
    ap = argparse.ArgumentParser(description="Live-paperikauppa (Kraken-perpetualit, ei oikeita toimeksiantoja)")
    ap.add_argument("--rules", default=env("RULES", "v1.1,v2"), help="pilkuilla eroteltu, esim. v1.1,v2")
    ap.add_argument("--symbols", default=env("SYMBOLS"))
    ap.add_argument("--top", type=int, default=int(env("TOP", "5")))
    ap.add_argument("--interval", type=float, default=float(env("INTERVAL", "3")))
    ap.add_argument("--state-dir", default=env("STATE_DIR", "state"))
    ap.add_argument("--log-dir", default=env("LOG_DIR", "logs"))
    ap.add_argument("--reset", action="store_true", default=env("RESET_STATE", "0") in ("1", "true"),
                    help="aloita puhtaalta pöydältä (esim. maksimipudotuksen pysäytyksen jälkeen)")
    a = ap.parse_args(argv)
    versions = [v.strip() for v in a.rules.split(",") if v.strip()]
    for v in versions:
        if v not in RULESETS:
            sys.exit(f"Tuntematon sääntöversio {v}. Saatavilla: {', '.join(RULESETS)}")
    os.makedirs(a.log_dir, exist_ok=True)
    os.makedirs(a.state_dir, exist_ok=True)

    tickers: dict[str, kraken.Ticker] = {}
    accounts = [Account(v, a.state_dir, a.log_dir, tickers, a.reset) for v in versions]

    # Sama markkinalista kaikille tileille: tallennettu lista tai uusi valinta
    saved = next((acc.symbols for acc in accounts if acc.symbols), None)
    if saved:
        symbols = saved
    elif a.symbols and a.symbols.upper().startswith("PF_"):
        symbols = [s.strip().upper() for s in a.symbols.split(",") if s.strip()]
    else:
        symbols = kraken.top_perpetuals(a.top)
    now = int(time.time() * 1000)
    for acc in accounts:
        acc.symbols = symbols
        acc.started_at = acc.started_at or now

    print(f"PAPERIKAUPPA – versiot {', '.join(versions)} rinnakkain erillisillä paperitileillä")
    print(f"Kraken Derivatives perpetualit: {', '.join(symbols)}")
    print(f"Tilien aloitushetki: {', '.join(f'{acc.version} {ts(acc.started_at)}' for acc in accounts)}")
    print("Ei oikeita toimeksiantoja. Säännöt: docs/SAANNOT_v1.md, docs/SAANNOT_v2.md\n", flush=True)

    # --- lämmittely / kiinniotto (ei uusia kauppoja) ------------------------
    tickers.update(kraken.fetch_tickers())
    for s in symbols:
        known = [acc.last_closed[s].open_time for acc in accounts if s in acc.last_closed]
        since = (min(known) + MIN) if known else now - 60 * MIN
        since = max(since, now - 24 * 60 * MIN)
        cs = kraken.fetch_candles(s, since, now + MIN)
        for acc in accounts:
            acc.feed(s, cs, entries=False)
        print(f"  {s}: historiaa {len(accounts[0].engine.analyzer(s).history)} kynttilää", flush=True)
    for acc in accounts:
        acc.engine.pending.clear()
        acc.save()
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
                for acc in accounts:
                    acc.feed(s, cs, entries=True)
            for acc in accounts:
                acc.save()
            if now - last_status >= 15 * MIN:
                last_status = now
                for acc in accounts:
                    print(acc.status(now), flush=True)
            time.sleep(max(0.0, a.interval - (time.time() - t0)))
    except KeyboardInterrupt:
        for acc in accounts:
            acc.save()
            print(f"\n[{acc.version}] lopetettu (avoimet positiot säilyvät tallennetussa tilassa).")
            print(summarize(acc.engine.trades, acc.engine))


if __name__ == "__main__":
    main()
