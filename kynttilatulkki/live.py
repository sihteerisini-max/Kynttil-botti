"""Reaaliaikainen havainnointi useammalle kolikolle.

Esimerkit:
    python -m kynttilatulkki.live --symbols BTCUSDT,ETHUSDT,SOLUSDT
    python -m kynttilatulkki.live --top 8
    python -m kynttilatulkki.live --top 5 --quiet     # vain kuviot, ei jokaista kynttilää
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
from collections import Counter

from .analyzer import DISCLAIMER, SymbolAnalyzer, format_event
from .feed import BASE_URL, fetch_klines, top_symbols


def main(argv=None) -> None:
    env = os.environ.get
    truthy = lambda v: str(v).lower() in ("1", "true", "yes", "kyllä")
    ap = argparse.ArgumentParser(description="Kynttilöiden reaaliaikainen tulkinta (vain havainnointi)")
    # Oletukset voi antaa myös ympäristömuuttujina (Railway: Variables-välilehti)
    ap.add_argument("--symbols", default=env("SYMBOLS"), help="pilkuilla eroteltu lista, esim. BTCUSDT,ETHUSDT")
    ap.add_argument("--top", type=int, default=int(env("TOP", "0")), help="seuraa N vaihdetuinta USDT-paria")
    ap.add_argument("--interval", type=float, default=float(env("INTERVAL", "3")), help="kyselyväli sekunteina")
    ap.add_argument("--quiet", action="store_true", default=truthy(env("QUIET", "0")),
                    help="älä tulosta jokaista suljettua kynttilää")
    ap.add_argument("--brief", action="store_true", default=truthy(env("BRIEF", "0")), help="älä tulosta perusteluja")
    ap.add_argument("--log", default=env("LOG_PATH", "logs/havainnot.jsonl"), help="JSONL-loki (tyhjä = ei lokia)")
    ap.add_argument("--base-url", default=env("BINANCE_BASE_URL", BASE_URL))
    a = ap.parse_args(argv)

    try:
        if a.symbols:
            symbols = [s.strip().upper() for s in a.symbols.split(",") if s.strip()]
        else:
            symbols = top_symbols(a.top or 5, base=a.base_url)
    except urllib.error.HTTPError as e:
        if e.code in (403, 451):
            sys.exit(f"Binance esti yhteyden (HTTP {e.code}) – palvelimen sijainti on todennäköisesti "
                     "rajoitetulla alueella (esim. USA). Vaihda Railwayssä alueeksi EU West.")
        raise
    print(f"Seurataan: {', '.join(symbols)}  (1 min kynttilät, päivitys {a.interval:g} s välein)")
    print(DISCLAIMER + "\n")

    logf = None
    if a.log:
        os.makedirs(os.path.dirname(a.log) or ".", exist_ok=True)
        logf = open(a.log, "a", encoding="utf-8")

    analyzers: dict[str, SymbolAnalyzer] = {}
    for s in symbols:
        an = SymbolAnalyzer(s)
        hist = fetch_klines(s, limit=100, base=a.base_url)
        an.warmup([c for c in hist if c.closed])
        analyzers[s] = an
        print(f"  {s}: {len(an.history)} suljettua kynttilää taustaksi")
    print()

    stats: Counter = Counter()
    try:
        while True:
            t0 = time.time()
            for s, an in analyzers.items():
                try:
                    kl = fetch_klines(s, limit=3, base=a.base_url)
                except Exception as e:   # verkko- tai rajapintavirhe: yritetään uudelleen
                    print(f"[{s}] tiedonhaku epäonnistui: {e}", file=sys.stderr)
                    continue
                now_ms = int(time.time() * 1000)
                for c in kl:
                    for ev in an.update(c, now_ms=now_ms):
                        if ev.kind == "candle" and a.quiet:
                            continue
                        print(format_event(ev, verbose=not a.brief))
                        if ev.kind == "confirmed":
                            stats.update(o.key for o in ev.observations)
                        if logf and ev.kind in ("provisional", "confirmed", "not_confirmed"):
                            rec = {"kind": ev.kind, "symbol": s, "open_time": c.open_time,
                                   "logged_at": now_ms, "text": ev.text,
                                   "observations": [o.to_dict() for o in ev.observations]}
                            logf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                            logf.flush()
            time.sleep(max(0.0, a.interval - (time.time() - t0)))
    except KeyboardInterrupt:
        print("\nLopetettu. Vahvistetut havainnot tällä ajolla:",
              ", ".join(f"{k} {v}" for k, v in stats.most_common()) or "ei yhtään")
    finally:
        if logf:
            logf.close()


if __name__ == "__main__":
    main()
