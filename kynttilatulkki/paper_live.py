"""Reaaliaikainen PAPERIKAUPPA Kraken-perpetualeilla. Ei oikeita toimeksiantoja.

Useampi sääntöversio voi ajaa rinnakkain erillisillä paperitileillä samasta
datavirrasta ja samasta käynnistyshetkestä:

    python -m kynttilatulkki.paper_live --rules v1.1,v2 --top 5

Ympäristömuuttujat (Railway): RULES, SYMBOLS, TOP, INTERVAL, STATE_DIR, LOG_DIR, RESET_STATE,
TEST_DAYS, LOG_TOKEN (+ PORT).
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


def serve_logs(log_dir: str, token: str, port: int) -> None:
    """Lukuoikeus kauppa- ja tapahtumalokeihin selaimella (vain jos LOG_TOKEN on asetettu):
    https://<railway-domain>/<tiedosto>?token=<LOG_TOKEN>, esim. /kaupat_v1.1-T2.jsonl"""
    import re
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, urlparse

    ok_name = re.compile(r"^(kaupat|tapahtumat)_[A-Za-z0-9.\-]+\.jsonl$")

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            u = urlparse(self.path)
            name = u.path.lstrip("/")
            if parse_qs(u.query).get("token", [""])[0] != token:
                return self.send_error(403)
            if name == "":
                body = "\n".join(sorted(f for f in os.listdir(log_dir) if ok_name.match(f))).encode()
            elif ok_name.match(name) and os.path.exists(os.path.join(log_dir, name)):
                with open(os.path.join(log_dir, name), "rb") as f:
                    body = f.read()
            else:
                return self.send_error(404)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("0.0.0.0", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"Lokit luettavissa portissa {port} (LOG_TOKEN vaaditaan)", flush=True)


class Account:
    """Yksi paperitili = yksi sääntöversio, oma pääoma, tila ja lokit."""

    def __init__(self, version: str, state_dir: str, log_dir: str, tickers: dict, reset: bool,
                 specs: dict):
        self.rules = r = RULESETS[version]
        self.version = version
        self.state_path = os.path.join(state_dir, f"paper_{version}.pkl")
        self.tickers = tickers
        self.trades_f = open(os.path.join(log_dir, f"kaupat_{version}.jsonl"), "a", encoding="utf-8")
        self.events_f = open(os.path.join(log_dir, f"tapahtumat_{version}.jsonl"), "a", encoding="utf-8")
        tag = f"[{version}] "
        self.engine = PaperEngine(r, self._hs, self._funding,
                                  log=lambda m: print(tag + m, flush=True),
                                  on_trade=self._on_trade, on_event=self._on_event, specs=specs)
        self.last_closed: dict[str, Candle] = {}
        self.opened: dict[str, int] = {}
        self.symbols: list[str] | None = None
        self.started_at: int | None = None
        self.symbol_changes: list[dict] = []     # markkinalistan vaihdot {time, old, new}
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
            self.symbol_changes = st.get("symbol_changes", [])
            print(f"{tag}jatketaan tallennetusta tilasta: pääoma {e.state.equity:,.2f} USD, "
                  f"avoimia positioita {len(e.positions)}", flush=True)

    def _hs(self, sym: str, t: int) -> float:
        tk = self.tickers.get(sym)
        return tk.half_spread if tk else self.rules.min_half_spread_backtest

    def _funding(self, sym: str, t: int):
        tk = self.tickers.get(sym)
        return tk.funding_rel_per_hour if tk else None

    def _on_event(self, ev: dict):
        if ev.get("kind") == "open":
            # Herkkyystarkistusta varten: Krakenin noteeraus sillä hetkellä, kun avaus käsiteltiin.
            # Ei vaikuta kauppaan (avaushinta = avauskynttilän avaus + kulumalli, kuten historiatestissä).
            tk = self.tickers.get(ev.get("symbol"))
            ev["havaittu_noteeraus"] = ({"bid": tk.bid, "ask": tk.ask, "t": int(time.time() * 1000)}
                                        if tk else None)
            print(f"AVAUS_JSON {json.dumps(ev, ensure_ascii=False, default=str)}", flush=True)
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
                         "opened": self.opened, "symbols": self.symbols, "started_at": self.started_at,
                         "symbol_changes": self.symbol_changes}, f)
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

    if env("LOG_TOKEN"):
        serve_logs(a.log_dir, env("LOG_TOKEN"), int(env("PORT", "8080")))

    tickers: dict[str, kraken.Ticker] = {}
    specs = kraken.fetch_instruments()
    accounts = [Account(v, a.state_dir, a.log_dir, tickers, a.reset, specs) for v in versions]

    # Sama markkinalista kaikille tileille. Tallennettu lista pysyy, ellei SYMBOLS-muuttujassa
    # anneta eri listaa: silloin markkinat vaihdetaan (kirjataan), tilit ja säännöt pysyvät ennallaan.
    saved = next((acc.symbols for acc in accounts if acc.symbols), None)
    wanted = ([s.strip().upper() for s in a.symbols.split(",") if s.strip()]
              if a.symbols and a.symbols.upper().startswith("PF_") else None)
    exit_only: list[str] = []          # poistuneet markkinat, joilla on vielä avoin paperipositio
    if saved and wanted and wanted != saved:
        now0 = int(time.time() * 1000)
        exit_only = [s for s in saved if s not in wanted and any(s in acc.engine.positions for acc in accounts)]
        for acc in accounts:
            ch = {"time": now0, "old": list(saved), "new": list(wanted)}
            acc.symbol_changes.append(ch)
            acc._on_event({"kind": "markkinat_vaihdettu", "ruleset": acc.version, **ch,
                           "avoimet_poistuvilla": [s for s in exit_only if s in acc.engine.positions]})
            for s in saved:
                if s not in wanted:
                    acc.engine.pending.pop(s, None)
        print(f"MARKKINAT VAIHDETTU {ts(now0)}: {', '.join(saved)} -> {', '.join(wanted)}"
              + (f" | poistuvilla avoimia positioita (vain sulku): {', '.join(exit_only)}" if exit_only else ""),
              flush=True)
        symbols = wanted
    elif saved:
        symbols = saved
    elif wanted:
        symbols = wanted
    else:
        symbols = kraken.top_perpetuals(a.top)
    for acc in accounts:
        acc.symbols = symbols
        if acc.symbol_changes:
            print(f"[{acc.version}] markkinavaihdot: " + "; ".join(
                f"{ts(c['time'])} {','.join(c['new'])}" for c in acc.symbol_changes), flush=True)

    print(f"PAPERIKAUPPA – versiot {', '.join(versions)} rinnakkain erillisillä paperitileillä")
    print(f"Kraken Derivatives perpetualit: {', '.join(symbols)}")
    miss = [s for s in symbols if s not in specs]
    print("Sopimustiedot: " + ", ".join(f"{s} askel {specs[s].qty_step:g}" for s in symbols if s in specs)
          + (f" | PUUTTUU (ei kauppoja näissä): {', '.join(miss)}" if miss else ""))
    print("Ei oikeita toimeksiantoja. Säännöt: docs/SAANNOT_v1.md, docs/SAANNOT_v2.md, docs/TESTI_T2.md")
    print(f"Koodiversio (commit): {os.environ.get('RAILWAY_GIT_COMMIT_SHA', 'tuntematon')}\n", flush=True)

    # --- lämmittely / kiinniotto (ei uusia kauppoja) ------------------------
    now = int(time.time() * 1000)
    tickers.update(kraken.fetch_tickers())
    for s in symbols + exit_only:
        known = [acc.last_closed[s].open_time for acc in accounts if s in acc.last_closed]
        since = (min(known) + MIN) if known else now - 60 * MIN
        since = max(since, now - 24 * 60 * MIN)
        cs = kraken.fetch_candles(s, since, now + MIN)
        for acc in accounts:
            acc.feed(s, cs, entries=False)
        print(f"  {s}: historiaa {len(accounts[0].engine.analyzer(s).history)} kynttilää", flush=True)
    start = int(time.time() * 1000)
    for acc in accounts:
        acc.engine.pending.clear()
        acc.started_at = acc.started_at or start
        acc.save()
    starts = {acc.started_at for acc in accounts}
    print(f"Tilien todellinen aloitushetki: "
          + ", ".join(f"{acc.version} {ts(acc.started_at)}" for acc in accounts))
    test_days = float(os.environ.get("TEST_DAYS", "28"))
    for acc in accounts:
        print(f"TESTIJAKSO [{acc.version}]: {ts(acc.started_at)} – "
              f"{ts(acc.started_at + int(test_days * 24 * 60 * MIN))} (kiinteä, {test_days:g} vrk)")
    if len(starts) > 1:
        print("VAROITUS: tilien aloitushetket eroavat – versioiden vertailu ei ole samalta jaksolta.")
    print(flush=True)

    last_status = 0
    try:
        while True:
            t0 = time.time()
            try:
                tickers.update(kraken.fetch_tickers())
            except Exception as e:
                print(f"tickerien haku epäonnistui: {e}", file=sys.stderr, flush=True)
            now = int(time.time() * 1000)
            exit_only = [s for s in exit_only if any(s in acc.engine.positions for acc in accounts)]
            for s in symbols + exit_only:
                try:
                    cs = kraken.fetch_candles(s, now - 5 * MIN, now + MIN, now_ms=now)
                except Exception as e:
                    print(f"[{s}] kynttilöiden haku epäonnistui: {e}", file=sys.stderr, flush=True)
                    continue
                for acc in accounts:
                    acc.feed(s, cs, entries=s in symbols)
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
