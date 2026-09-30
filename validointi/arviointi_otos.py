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
from kynttilatulkki.patterns import TUNNISTUS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WINDOW = 30

# Kirjallisuuden sanalliset määritelmät (docs/LAHTEET.md). Näytetään arvioinnissa.
DOWN, UP = ("Edeltävien 10 kynttilän (tummempi alue) hintaliike on laskeva.",
            "Edeltävien 10 kynttilän (tummempi alue) hintaliike on nouseva.")
NOT_SMALL = ("Arvioitavan kynttilän vaihteluväli (ylin − alin) ei ole selvästi pienempi kuin "
             "vertailujakson (20 edeltävää kynttilää, vaalea alue) keskimääräinen vaihteluväli.")
LONG = ("Arvioitavan kynttilän vaihteluväli on selvästi suurempi kuin vertailujakson "
        "(20 edeltävää kynttilää, vaalea alue) keskimääräinen vaihteluväli.")
def _d(nimi, n, muoto, liike, koko, lahde):
    return {"nimi": nimi, "kynttiloita": n, "muoto": muoto, "liike": liike, "koko": koko, "lahde": lahde}
DEFS = {
    "doji": _d("Doji", 1, "Avaus ja päätös käytännössä yhtä suuret (runko hyvin ohut); varjoja voi olla ylös, alas tai molempiin.", None, NOT_SMALL, "[SC] [TB]"),
    "dragonfly_doji": _d("Sudenkorento-doji", 1, "Doji, jonka avaus ja päätös ovat kynttilän huipussa: pitkä alavarjo, ei tai tuskin yläsvarjoa.", None, NOT_SMALL, "[SC] [TB]"),
    "gravestone_doji": _d("Hautakivi-doji", 1, "Doji, jonka avaus ja päätös ovat kynttilän pohjassa: pitkä yläsvarjo, ei tai tuskin alavarjoa.", None, NOT_SMALL, "[SC] [TB]"),
    "hammer": _d("Vasara", 1, "Pieni runko kynttilän yläosassa, alavarjo vähintään 2–3 × rungon korkeus, vähän tai ei yläsvarjoa. Rungon väri vapaa.", DOWN, NOT_SMALL, "[TB] [SC]"),
    "hanging_man": _d("Hirttäytyjä", 1, "Sama muoto kuin vasaralla: pieni runko pitkän alavarjon päällä, vähän tai ei yläsvarjoa.", UP, NOT_SMALL, "[TB] [SC]"),
    "inverted_hammer": _d("Käänteinen vasara", 1, "Pieni runko kynttilän alaosassa (ei doji), pitkä yläsvarjo, vähän tai ei alavarjoa.", DOWN, NOT_SMALL, "[SC]; [TB] käyttää kahden kynttilän muotoa"),
    "shooting_star": _d("Tähdenlento", 1, "Pieni runko (ei doji) kynttilän alaosassa, yläsvarjo vähintään 2 × rungon korkeus, vähän tai ei alavarjoa.", UP, NOT_SMALL, "[TB] [SC]"),
    "bullish_engulfing": _d("Nouseva peittävä kuvio", 2, "Edellinen kynttilä on laskeva, arvioitava kynttilä nouseva, ja sen runko peittää edellisen rungon (varjoilla ei väliä).", DOWN, NOT_SMALL, "[SC] [TB]; [TB] vaatii lisäksi avauksen edellisen päätöksen alapuolelle"),
    "bearish_engulfing": _d("Laskeva peittävä kuvio", 2, "Edellinen kynttilä on nouseva, arvioitava kynttilä laskeva, ja sen runko peittää edellisen rungon (varjoilla ei väliä).", UP, NOT_SMALL, "[SC]"),
    "bullish_marubozu": _d("Nouseva marubozu", 1, "Nouseva kynttilä, jossa ei ole ylä- eikä alavarjoa (tai ne ovat hyvin lyhyet).", None, LONG, "[SC] [TB]"),
    "bearish_marubozu": _d("Laskeva marubozu", 1, "Laskeva kynttilä, jossa ei ole ylä- eikä alavarjoa (tai ne ovat hyvin lyhyet).", None, LONG, "[SC] [TB]"),
}
QUESTIONS = [
    {"id": "muoto", "lyhyt": "muoto", "otsikko": "Täyttääkö kynttilä kuvion muotoehdot?", "napit": ["On kuvio", "Ei ole", "Epäselvä"]},
    {"id": "liike", "lyhyt": "edeltävä liike", "teksti_avain": "liike", "otsikko": "Onko edeltävä hintaliike vaaditun suuntainen?", "napit": ["Kyllä", "Ei", "Epäselvä"]},
    {"id": "koko", "lyhyt": "suhteellinen koko", "otsikko": "Täyttyykö suhteellisen koon ehto?", "napit": ["Kyllä", "Ei", "Epäselvä"]},
]


def bot_answer(comp_k):
    """Botin vastaus eriteltynä: muoto, liike (None jos ei vaatimusta), koko, tausta."""
    liike = next((c["ok"] for c in comp_k["tausta_ehdot"] if "liike" in c["ehto"]), None)
    koko = all(c["ok"] for c in comp_k["tausta_ehdot"] if "liike" not in c["ehto"])
    return {"muoto": comp_k["muoto"], "liike": liike, "koko": koko, "tausta": comp_k["tausta"],
            "muoto_ehdot": comp_k["muoto_ehdot"], "tausta_ehdot": comp_k["tausta_ehdot"]}


def cd(c):
    return {"t": c.open_time, "o": c.open, "h": c.high, "l": c.low, "c": c.close, "v": c.volume}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-glob", default=os.path.join(ROOT, "data", "PF_*_2026-09-22T1843_2026-09-29T1843.csv"))
    ap.add_argument("--tag", default="A")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--seed", type=int, default=20260929)
    ap.add_argument("--versiot", default="T2,T1", help="ensimmäinen = arvioitava tunnistusmääritelmä, muut vertailuja")
    ap.add_argument("--ohita", nargs="*", default=[], help="aiempien sarjojen json-tiedostot: niissä näytettyjä kynttilöitä ei käytetä (ei edes historiaikkunassa)")
    ap.add_argument("--alku", help="ota vain kynttilät tästä UTC-hetkestä alkaen (esim. jakson A jälkeen)")
    a = ap.parse_args(argv)
    rnd = random.Random(a.seed)
    versions = a.versiot.split(",")
    v0 = versions[0]
    alku = None
    if a.alku:
        from kynttilatulkki.backtest import parse_date
        alku = parse_date(a.alku)

    shown: dict[str, set] = {}
    for pth in a.ohita:
        for it in json.load(open(pth, encoding="utf-8"))["tapaukset"]:
            sset = shown.setdefault(it["symboli"], set())
            for c in it["historia"] + [it["kohde"]]:
                sset.add(c["t"])
    rows = []          # (sym, i, candles, comp)
    for f in sorted(glob.glob(a.data_glob)):
        sym = os.path.basename(f).split("_20")[0]
        cs = load_csv(f, sym)
        for i in range(WINDOW, len(cs)):
            c = cs[i]
            if c.volume <= 0 or c.high == c.low:
                continue                          # kauppattomia täytettyjä minuutteja ei arvioida
            if alku and c.open_time < alku:
                continue
            if shown and any(x.open_time in shown.get(sym, ()) for x in cs[i - WINDOW:i + 1]):
                continue                          # ikkunassa aiemmin näytetty kynttilä
            comp = {v: components(cs[max(0, i - 100):i], c, TUNNISTUS[v]) for v in versions}
            if all(comp.values()):
                rows.append((sym, i, cs, comp))
    items = []
    for k in PATTERNS:
        pos = [r for r in rows if r[3][v0][k]["muoto"]]
        # 1) arvioitava versio: tausta täyttyy, 2) versiot ovat eri mieltä taustasta (jos on), 3) muu muodon täyttävä
        g1 = [r for r in pos if r[3][v0][k]["tausta"]]
        g2 = [r for r in pos if len({r[3][v][k]["tausta"] for v in versions}) > 1]
        g3 = [r for r in pos if not r[3][v0][k]["tausta"]]
        picks, used = [], set()
        for g, tag in ((g1, "botin_tunnistama"), (g2, "t1_t2_erimielisyys"), (g3, "botin_tunnistama")) + ((pos, "botin_tunnistama"),) * a.n:
            if len(picks) >= a.n:
                break
            cand = [r for r in g if (r[0], r[1]) not in used]
            if cand:
                r = rnd.choice(cand); used.add((r[0], r[1])); picks.append((tag, r))
        picks += [("satunnainen", r) for r in rnd.sample(rows, a.n)]
        for src, r in picks:
            sym, i, cs, comp = r
            items.append({"kuvio": k, "lahde": src, "symboli": sym, "aika": cs[i].open_time,
                          "historia": [cd(x) for x in cs[i - WINDOW:i]], "kohde": cd(cs[i]),
                          "botti": {v: bot_answer(comp[v][k]) for v in versions}})
    rnd.shuffle(items)
    for n, it in enumerate(items, 1):
        it["id"] = f"{a.tag}{n:03d}"
    data = {"sarja": a.tag, "maaritelmat": DEFS, "tapaukset": items, "kysymykset": QUESTIONS,
            "versiot": versions, "ensisijainen": v0,
            "vertailu": {"koko": TUNNISTUS[v0].avg_window, "liike": TUNNISTUS[v0].trend_window},
            "lahteet": {"SC": "StockCharts ChartSchool: Candlestick Pattern Dictionary",
                        "TB": "Thomas N. Bulkowski, ThePatternSite.com – Identification Guidelines"}}
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    tpl = open(os.path.join(HERE, "arviointi_pohja.html"), encoding="utf-8").read()
    out = os.path.join(HERE, f"arviointi_{a.tag}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(tpl.replace("__DATA__", blob).replace(
            "<title>Kynttilöiden sokkoarviointi</title>", f"<title>Kynttilöiden sokkoarviointi {a.tag}</title>"))
    with open(os.path.join(HERE, f"arviointi_{a.tag}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    from collections import Counter
    print(out, len(items), "tapausta", Counter((i["kuvio"], i["lahde"]) for i in items).most_common(3))


if __name__ == "__main__":
    main()
