"""Lataa Krakenin 1 min kynttilät tiedostoiksi (ei tunnistusta, ei kaupankäyntiä).

    python -m kynttilatulkki.lataa --start 2026-09-29T18:43 [--end ...] [--symbols PF_XBTUSD,...]

Tiedostot: data/<SYMBOLI>_<alku>_<loppu>.csv (sama muoto kuin historiatestissä).
"""
from __future__ import annotations

import argparse
import os
import time

from . import kraken
from .backtest import MIN, iso, parse_date, save_csv

DEFAULT_SYMBOLS = "PF_XBTUSD,PF_ETHUSD,PF_SOLUSD,PF_ZECUSD,PF_XRPUSD"   # samat kuin jaksolla A


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Lataa 1 min kynttilät")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", help="oletus: nyt")
    ap.add_argument("--symbols", default=DEFAULT_SYMBOLS)
    ap.add_argument("--data-dir", default="data")
    a = ap.parse_args(argv)
    start = parse_date(a.start)
    end = parse_date(a.end) if a.end else int(time.time() * 1000) // MIN * MIN
    os.makedirs(a.data_dir, exist_ok=True)
    for s in [x.strip().upper() for x in a.symbols.split(",") if x.strip()]:
        cs = kraken.fill_gaps([c for c in kraken.fetch_candles(s, start, end) if c.closed])
        path = os.path.join(a.data_dir, f"{s}_{iso(start).replace(':', '')}_{iso(end).replace(':', '')}.csv")
        save_csv(path, cs)
        print(f"{s}: {len(cs)} kynttilää -> {path}")


if __name__ == "__main__":
    main()
