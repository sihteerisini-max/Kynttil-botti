"""Ajaa luokitellut esimerkit tunnistuksen läpi ja vertaa käsin kirjattuihin vastauksiin.

    python -m validointi.aja            # raportti + validointi/tulokset.json (näkymän data)

Tunnistus saa kynttilät yksi kerrallaan aikajärjestyksessä (SymbolAnalyzer.update), joten
se ei näe tulevia kynttilöitä. Oikeat vastaukset tulevat tiedostosta tapaukset.py.
"""
from __future__ import annotations

import csv
import glob
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kynttilatulkki.analyzer import SymbolAnalyzer  # noqa: E402
from kynttilatulkki.models import Candle  # noqa: E402
from validointi.tapaukset import M, T0, build, history  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = {
    "doji": "Doji", "long_legged_doji": "Pitkäjalkainen doji", "dragonfly_doji": "Sudenkorento-doji",
    "gravestone_doji": "Hautakivi-doji", "hammer": "Vasara", "hanging_man": "Hirttäytyjä",
    "hammer_shape": "Vasaran muoto (ei trendiä)", "inverted_hammer": "Käänteinen vasara",
    "shooting_star": "Tähdenlento", "inverted_shape": "Käänteisen vasaran muoto (ei trendiä)",
    "bullish_engulfing": "Nouseva peittävä", "bearish_engulfing": "Laskeva peittävä",
    "bullish_marubozu": "Nouseva marubozu", "bearish_marubozu": "Laskeva marubozu",
    "bullish_harami": "Nouseva harami (ei toteutettu)",
}


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def cdict(c: Candle) -> dict:
    return {"t": c.open_time, "o": c.open, "h": c.high, "l": c.low, "c": c.close, "v": c.volume,
            "closed": c.closed}


def valid(o, h, l, c) -> bool:
    return l <= min(o, c) + 1e-12 and h >= max(o, c) - 1e-12 and h >= l


def make_history(cs: dict) -> list[Candle]:
    rows = history(cs["historia"], cs["n_hist"])
    if cs["prev_override"]:
        po = cs["prev_override"]
        shift = po[0] - rows[-2][3]          # siirretään historia niin, että hinnat jatkuvat
        rows = [(o + shift, h + shift, l + shift, c + shift, v) for o, h, l, c, v in rows[:-1]] + [po]
    out = []
    for i, (o, h, l, c, v) in enumerate(rows):
        assert valid(o, h, l, c), (cs["id"], i)
        t = T0 + i * M
        out.append(Candle("TEST", t, o, h, l, c, v, True, t + M - 1))
    return out


def obs_json(o) -> dict:
    d = o.to_dict()
    d["detected_at_iso"] = iso(o.detected_at) if o.detected_at else ""
    return d


def run_case(cs: dict) -> dict:
    hist = make_history(cs)
    an = SymbolAnalyzer("TEST")
    an.warmup(hist)
    t = hist[-1].open_time + M
    res = {"id": cs["id"], "luokka": cs["luokka"], "kuvaus": cs["kuvaus"], "trendi": cs["historia"],
           "korjaus": cs.get("korjaus", ""),
           "historia": [cdict(c) for c in hist], "vaiheet": []}
    if cs["ticks"]:
        shown: set[str] = set()
        for sec, (o, h, l, c), expected in cs["ticks"]:
            assert valid(o, h, l, c), cs["id"]
            closed = sec >= 60
            cand = Candle("TEST", t, o, h, l, c, 100.0 * sec / 60, closed, t + M - 1)
            now = t + sec * 1000 - (1 if closed else 0)
            evs = an.update(cand, now_ms=now)
            kind = "vahvistettu" if closed else "keskeneräinen"
            if closed:
                obs = [o_ for e in evs if e.kind == "confirmed" for o_ in e.observations]
                got = {o_.key for o_ in obs}
            else:
                obs = [o_ for e in evs if e.kind == "provisional" for o_ in e.observations]
                if obs:
                    shown = {o_.key for o_ in obs}
                elif sec / 60 < 0.25:
                    shown = set()
                got = set(shown)
            exp = set() if isinstance(expected, dict) else set(expected)
            res["vaiheet"].append({"sekunti": sec, "tila": kind, "kynttila": cdict(cand),
                                   "odotettu": sorted(exp), "tunnistettu": sorted(got),
                                   "havainnot": [obs_json(x) for x in obs],
                                   "ei_vahvistunut": [e.text for e in evs if e.kind == "not_confirmed"]})
        last = res["vaiheet"][-1]
        res["maaritelma"] = last["odotettu"]
        res["kirjallisuus"] = last["odotettu"]
        res["tunnistettu"] = last["tunnistettu"]
        res["kohde"] = last["kynttila"]
        res["havainnot"] = last["havainnot"]
        return res
    o, h, l, c, v = cs["target"]
    assert valid(o, h, l, c), cs["id"]
    cand = Candle("TEST", t, o, h, l, c, v, True, t + M - 1)
    evs = an.update(cand, now_ms=t + M)
    obs = [x for e in evs if e.kind == "confirmed" for x in e.observations]
    res.update({"kohde": cdict(cand), "maaritelma": sorted(cs["maaritelma"]),
                "kirjallisuus": sorted(cs["kirjallisuus"]), "tunnistettu": sorted({x.key for x in obs}),
                "havainnot": [obs_json(x) for x in obs]})
    return res


def score(results: list[dict], label: str) -> dict:
    tab = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0, "tapaukset": defaultdict(list)})
    units = []
    for r in results:
        if r["vaiheet"]:
            for s in r["vaiheet"]:
                units.append((f"{r['id']} {s['sekunti']} s", set(s["odotettu"]), set(s["tunnistettu"])))
        else:
            units.append((r["id"], set(r[label]), set(r["tunnistettu"])))
    for uid, exp, got in units:
        for k in exp | got:
            kind = "TP" if (k in exp and k in got) else "FP" if k in got else "FN"
            tab[k][kind] += 1
            tab[k]["tapaukset"][kind].append(uid)
    return {k: {"TP": v["TP"], "FP": v["FP"], "FN": v["FN"], "tapaukset": dict(v["tapaukset"])}
            for k, v in sorted(tab.items())}


def real_sample(per_key: int = 3) -> list[dict]:
    """Otos oikeista jakson A tunnistuksista silmämääräiseen tarkistukseen (EI luokiteltu)."""
    files = sorted(glob.glob(os.path.join(os.path.dirname(HERE), "data", "PF_*_2026-09-22T1843_*.csv")))
    found: dict[str, list] = defaultdict(list)
    total = 0
    for f in files:
        sym = os.path.basename(f).split("_2026")[0]
        rows = []
        with open(f) as fh:
            for row in csv.DictReader(fh):
                t = int(row["open_time"])
                rows.append(Candle(sym, t, float(row["open"]), float(row["high"]), float(row["low"]),
                                   float(row["close"]), float(row["volume"]), True, t + M - 1))
        an = SymbolAnalyzer(sym)
        total += sum(1 for c in rows[20:] if c.volume > 0)
        for i, c in enumerate(rows):
            for e in an.update(c, now_ms=c.open_time + M):
                if e.kind == "confirmed":
                    for o in e.observations:
                        found[o.key].append((sym, i, rows, o))
    out = []
    for k, lst in sorted(found.items()):
        step = max(1, len(lst) // per_key)
        for sym, i, rows, o in lst[::step][:per_key]:
            out.append({"id": f"{sym} {iso(o.open_time)[:16]}", "symboli": sym, "avain": k,
                        "maara_jaksolla": len(lst),
                        "historia": [cdict(c) for c in rows[max(0, i - 20):i]],
                        "kohde": cdict(rows[i]), "havainnot": [obs_json(o)]})
    counts = {k: len(v) for k, v in found.items()}
    return out, counts, total


def main() -> None:
    cases = build()
    results = [run_case(c) for c in cases]
    sm = score(results, "maaritelma")
    sk = score(results, "kirjallisuus")
    real, counts, total = real_sample()
    data = {"jakso_A_maarat": counts, "jakso_A_kynttiloita": total,"luotu": iso(int(datetime.now(tz=timezone.utc).timestamp() * 1000)), "nimet": NAMES,
            "tapaukset": results, "tulos_maaritelma": sm, "tulos_kirjallisuus": sk, "oikea_otos": real}
    with open(os.path.join(HERE, "tulokset.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=list)

    lines = ["# Kynttiläkuvioiden tunnistuksen tarkistus", "",
             f"Tapauksia {len(results)} (luokat: " + ", ".join(
                 f"{l} {sum(1 for r in results if r['luokka'] == l)}" for l in "PNBGK") + ")", ""]
    for title, sc in (("Määritelmän mukaan (docs/KUVIOT.md)", sm),
                      ("Kirjallisuuden mukaan (sis. tunnetut aukot)", sk)):
        lines += [f"## {title}", "", "| Kuvio | Oikein (TP) | Väärä hälytys (FP) | Löytämättä (FN) | Tapaukset FP / FN |",
                  "|---|---|---|---|---|"]
        for k, v in sc.items():
            lines.append(f"| {NAMES.get(k, k)} | {v['TP']} | {v['FP']} | {v['FN']} | "
                         f"{', '.join(v['tapaukset'].get('FP', [])) or '–'} / {', '.join(v['tapaukset'].get('FN', [])) or '–'} |")
        lines.append("")
    lines += ["## Tapaukset", "", "| Id | Luokka | Kuvaus | Määritelmä | Kirjallisuus | Tunnistettu | OK |",
              "|---|---|---|---|---|---|---|"]
    for r in results:
        ok = set(r["maaritelma"]) == set(r["tunnistettu"])
        lines.append(f"| {r['id']} | {r['luokka']} | {r['kuvaus']} | {', '.join(r['maaritelma']) or '–'} | "
                     f"{', '.join(r['kirjallisuus']) or '–'} | {', '.join(r['tunnistettu']) or '–'} | {'✓' if ok else '✗'} |")
    fixes = [r for r in results if r.get("korjaus")]
    if fixes:
        lines += ["", "## Luokittelijan korjaukset", ""]
        lines += [f"* **{r['id']}**: {r['korjaus']}" for r in fixes]
    lines += ["", "## Jakso A: tunnistusten määrät (1 min, 5 markkinaa)", "",
              f"Tulkittavia kynttilöitä (historiaa ≥ 20, volyymi > 0): {total}", "",
              "| Kuvio | Vahvistettuja | Osuus kynttilöistä |", "|---|---|---|"]
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {NAMES.get(k, k)} | {v} | {v / total:.1%} |")
    with open(os.path.join(HERE, "RAPORTTI.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
