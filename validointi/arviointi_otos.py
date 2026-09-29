"""Muodostaa ihmisen arvioitavan otoksen ja rakentaa arviointisivun.

    python -m validointi.arviointi_otos [--data-glob 'data/PF_*_<jakso>.csv'] [--tag A] [--n 3]

Otos kuviota kohden: n tapausta, joissa botti tunnisti MUODON (sekä taustaehdot täyttäviä että
täyttämättömiä), ja n satunnaista kynttiläjaksoa. Jokaisesta tapauksesta näytetään vain arvioitavaa
kynttilää edeltävä historia ja kynttilä itse – ei myöhempää hintakehitystä.
Botin vastaukset tallennetaan sivulle piiloon ja näytetään vasta erillisestä tulosnäkymästä.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kynttilatulkki.backtest import load_csv  # noqa: E402
from kynttilatulkki.komponentit import PATTERNS, components  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WINDOW = 30

# Kirjallisuuden sanalliset määritelmät (docs/LAHTEET.md). Näytetään arvioinnissa.
DEFS = {
    "doji": ("Doji", 1,
             "Avaus ja päätös käytännössä yhtä suuret (runko hyvin ohut); varjoja voi olla ylös, alas tai molempiin.",
             "Ei vaadittua edeltävää trendiä. Kynttilä ei ole lähes liikkumaton minuutti (ei selvästi pienempi kuin edeltävät).",
             "[SC] [TB]"),
    "dragonfly_doji": ("Sudenkorento-doji", 1,
                       "Doji, jonka avaus ja päätös ovat kynttilän huipussa: pitkä alavarjo, ei tai tuskin yläsvarjoa.",
                       "Ei vaadittua trendiä. Kynttilä ei ole selvästi pienempi kuin edeltävät.", "[SC] [TB]"),
    "gravestone_doji": ("Hautakivi-doji", 1,
                        "Doji, jonka avaus ja päätös ovat kynttilän pohjassa: pitkä yläsvarjo, ei tai tuskin alavarjoa.",
                        "Ei vaadittua trendiä. Kynttilä ei ole selvästi pienempi kuin edeltävät.", "[SC] [TB]"),
    "hammer": ("Vasara", 1,
               "Pieni runko kynttilän yläosassa, alavarjo vähintään 2–3 × rungon korkeus, vähän tai ei yläsvarjoa. Rungon väri vapaa.",
               "Edeltävä hintaliike on laskeva. Kynttilä ei ole selvästi pienempi kuin edeltävät.", "[TB] [SC]"),
    "hanging_man": ("Hirttäytyjä", 1,
                    "Sama muoto kuin vasaralla: pieni runko pitkän alavarjon päällä, vähän tai ei yläsvarjoa.",
                    "Edeltävä hintaliike on nouseva. Kynttilä ei ole selvästi pienempi kuin edeltävät.", "[TB] [SC]"),
    "inverted_hammer": ("Käänteinen vasara", 1,
                        "Pieni runko kynttilän alaosassa (ei doji), pitkä yläsvarjo, vähän tai ei alavarjoa.",
                        "Edeltävä hintaliike on laskeva. Kynttilä ei ole selvästi pienempi kuin edeltävät.",
                        "[SC]; [TB] käyttää kahden kynttilän muotoa"),
    "shooting_star": ("Tähdenlento", 1,
                      "Pieni runko (ei doji) kynttilän alaosassa, yläsvarjo vähintään 2 × rungon korkeus, vähän tai ei alavarjoa.",
                      "Edeltävä hintaliike on nouseva. Kynttilä ei ole selvästi pienempi kuin edeltävät.", "[TB] [SC]"),
    "bullish_engulfing": ("Nouseva peittävä kuvio", 2,
                          "Edellinen kynttilä on laskeva, arvioitava kynttilä nouseva, ja sen runko peittää edellisen rungon (varjoilla ei väliä).",
                          "Edeltävä hintaliike on laskeva. Kynttilä ei ole selvästi pienempi kuin edeltävät.",
                          "[SC] [TB]; [TB] vaatii lisäksi avauksen edellisen päätöksen alapuolelle"),
    "bearish_engulfing": ("Laskeva peittävä kuvio", 2,
                          "Edellinen kynttilä on nouseva, arvioitava kynttilä laskeva, ja sen runko peittää edellisen rungon (varjoilla ei väliä).",
                          "Edeltävä hintaliike on nouseva. Kynttilä ei ole selvästi pienempi kuin edeltävät.", "[SC]"),
    "bullish_marubozu": ("Nouseva marubozu", 1,
                         "Nouseva kynttilä, jossa ei ole ylä- eikä alavarjoa (tai ne ovat hyvin lyhyet).",
                         "Ei vaadittua trendiä. Kynttilä on pitkä verrattuna edeltäviin.", "[SC] [TB]"),
    "bearish_marubozu": ("Laskeva marubozu", 1,
                         "Laskeva kynttilä, jossa ei ole ylä- eikä alavarjoa (tai ne ovat hyvin lyhyet).",
                         "Ei vaadittua trendiä. Kynttilä on pitkä verrattuna edeltäviin.", "[SC] [TB]"),
}


def cd(c):
    return {"t": c.open_time, "o": c.open, "h": c.high, "l": c.low, "c": c.close, "v": c.volume}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-glob", default=os.path.join(ROOT, "data", "PF_*_2026-09-22T1843_2026-09-29T1843.csv"))
    ap.add_argument("--tag", default="A")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--seed", type=int, default=20260929)
    a = ap.parse_args(argv)
    rnd = random.Random(a.seed)

    rows = []          # (sym, i, candles, comp)
    for f in sorted(glob.glob(a.data_glob)):
        sym = os.path.basename(f).split("_20")[0]
        cs = load_csv(f, sym)
        for i in range(WINDOW, len(cs)):
            c = cs[i]
            if c.volume <= 0 or c.high == c.low:
                continue                          # kauppattomia täytettyjä minuutteja ei arvioida
            comp = components(cs[max(0, i - 100):i], c)
            if comp:
                rows.append((sym, i, cs, comp))
    items = []
    for k in PATTERNS:
        pos = [r for r in rows if r[3][k]["muoto"]]
        with_ctx = [r for r in pos if r[3][k]["tausta"]]
        no_ctx = [r for r in pos if not r[3][k]["tausta"]]
        n_ctx = min(len(with_ctx), a.n - min(1, len(no_ctx)))
        picks = rnd.sample(with_ctx, n_ctx) + rnd.sample(no_ctx, min(len(no_ctx), a.n - n_ctx))
        picks += [("satunnainen", r) for r in rnd.sample(rows, a.n)]
        for p in picks:
            src = "botti" if not (isinstance(p, tuple) and p[0] == "satunnainen") else "satunnainen"
            r = p if src == "botti" else p[1]
            sym, i, cs, comp = r
            items.append({"kuvio": k, "lahde": src, "symboli": sym, "aika": cs[i].open_time,
                          "historia": [cd(x) for x in cs[i - WINDOW:i]], "kohde": cd(cs[i]),
                          "botti": {"muoto": comp[k]["muoto"], "tausta": comp[k]["tausta"],
                                    "muoto_ehdot": comp[k]["muoto_ehdot"], "tausta_ehdot": comp[k]["tausta_ehdot"]}})
    rnd.shuffle(items)
    for n, it in enumerate(items, 1):
        it["id"] = f"{a.tag}{n:03d}"
    data = {"sarja": a.tag, "maaritelmat": DEFS, "tapaukset": items,
            "lahteet": {"SC": "StockCharts ChartSchool: Candlestick Pattern Dictionary",
                        "TB": "Thomas N. Bulkowski, ThePatternSite.com – Identification Guidelines"}}
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tpl = open(os.path.join(HERE, "arviointi_pohja.html"), encoding="utf-8").read()
    out = os.path.join(HERE, f"arviointi_{a.tag}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(tpl.replace("__DATA__", blob))
    with open(os.path.join(HERE, f"arviointi_{a.tag}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    from collections import Counter
    print(out, len(items), "tapausta", Counter((i["kuvio"], i["lahde"]) for i in items).most_common(3))


if __name__ == "__main__":
    main()
