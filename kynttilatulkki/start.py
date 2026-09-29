"""Railwayn käynnistyspiste. Toiminta valitaan ympäristömuuttujilla:

    MODE=observe (oletus)  -> vain kynttilöiden havainnointi (Binance-data)
    MODE=paper             -> live-paperikauppa Kraken-perpetualeilla
    BACKTEST_DAYS=7        -> ajaa ensin historiatestin viimeisiltä N päivältä
                              (tulokset lokiin), sitten valitun MODEn
"""
from __future__ import annotations

import os
import sys


def main() -> None:
    days = os.environ.get("BACKTEST_DAYS")
    rules = os.environ.get("RULES", "v1")
    if days:
        from . import backtest
        args = ["--rules", rules, "--days", days, "--quiet"]
        if os.environ.get("SYMBOLS", "").startswith("PF_"):
            args += ["--symbols", os.environ["SYMBOLS"]]
        else:
            args += ["--top", os.environ.get("TOP", "5")]
        try:
            backtest.main(args)
        except Exception as e:   # historiatestin virhe ei estä varsinaista ajoa
            print(f"Historiatesti epäonnistui: {e}", file=sys.stderr, flush=True)
    mode = os.environ.get("MODE", "observe").lower()
    if mode == "paper":
        from . import paper_live
        paper_live.main([])
    else:
        from . import live
        live.main([])


if __name__ == "__main__":
    main()
