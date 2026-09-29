"""Laskee sokkoarvioinnin tulokset: ihmisen arvio vs. botin muoto- ja taustaehdot.

    python -m validointi.arviointi_tulokset validointi/arviointi_A.json arviot_A.json

arviot_A.json = {"A001": {"muoto": "on"|"ei"|"epaselva", "tausta": ...}, ...}
(tietokannan kokoelma "arviot" tai sivun varmuuskopioteksti).
Epäselvät arviot raportoidaan omana ryhmänään, eikä niitä lasketa oikeisiin tai vääriin.
"""
import json
import sys
from collections import defaultdict


def tally(items, ratings, part):
    rows = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0, "TN": 0, "EP_botti_kylla": 0, "EP_botti_ei": 0,
                                "FP_id": [], "FN_id": [], "EP_id": []})
    for it in items:
        r = ratings.get(it["id"])
        if not r:
            continue
        if part == "koko":
            if not r.get("muoto") or not r.get("tausta"):
                continue
            h = "ei" if "ei" in (r["muoto"], r["tausta"]) else "epaselva" if "epaselva" in (r["muoto"], r["tausta"]) else "on"
            b = it["botti"]["muoto"] and it["botti"]["tausta"]
        else:
            h, b = r.get(part), it["botti"][part]
            if not h:
                continue
        t = rows[it["kuvio"]]
        if h == "epaselva":
            t["EP_botti_kylla" if b else "EP_botti_ei"] += 1
            t["EP_id"].append(it["id"])
        elif h == "on":
            t["TP" if b else "FN"] += 1
            if not b:
                t["FN_id"].append(it["id"])
        else:
            t["FP" if b else "TN"] += 1
            if b:
                t["FP_id"].append(it["id"])
    return rows


def main(argv):
    data = json.load(open(argv[0], encoding="utf-8"))
    ratings = json.load(open(argv[1], encoding="utf-8"))
    ratings = {k: (v.get("data", v) if isinstance(v, dict) else v) for k, v in ratings.items()}
    names = {k: v[0] for k, v in data["maaritelmat"].items()}
    done = sum(1 for it in data["tapaukset"] if ratings.get(it["id"], {}).get("muoto") and ratings[it["id"]].get("tausta"))
    print(f"# Sokkoarviointi, sarja {data['sarja']}: arvioitu {done}/{len(data['tapaukset'])}\n")
    for part, title in (("muoto", "Muotoehdot"), ("tausta", "Taustaehdot"), ("koko", "Koko kuvio")):
        rows = tally(data["tapaukset"], ratings, part)
        print(f"## {title}\n\n| Kuvio | Oikein | Väärä hälytys | Löytämättä | Oikein hylätty | Epäselvä (botti kyllä/ei) | Poikkeavat |\n|---|---|---|---|---|---|---|")
        for k in data["maaritelmat"]:
            if k in rows:
                t = rows[k]
                print(f"| {names[k]} | {t['TP']} | {t['FP']} | {t['FN']} | {t['TN']} | {t['EP_botti_kylla']}/{t['EP_botti_ei']} | "
                      f"{' '.join('FP:' + i for i in t['FP_id'])} {' '.join('FN:' + i for i in t['FN_id'])} |")
        print()


if __name__ == "__main__":
    main(sys.argv[1:])
