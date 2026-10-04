"""Tutkimus 15M, vaihe "lataus": testijakson 15m-data, puuttuvien rivien erottelu, eheystarkistus
1m-datalla, nykyiset spreadit ja historiallinen funding (suunnitelma luvut 2, 4 ja 9)."""
from __future__ import annotations

import json
import os
import random
import statistics as st
import time

from data15 import (BASE, DAY, MIN, STEP15, aggregate, charts, http_json, iso, ms, same, to_candles,
                    write_csv)

LATAUS_ALKU = ms("2024-12-29")          # lämmittely
TESTI_ALKU = ms("2025-01-01")
TESTI_LOPPU = ms("2026-07-01")
LATAUS_LOPPU = ms("2026-07-01T06:00")    # jälkidata lopputuloksille
SEED = 20261004
OTOS = 200
NOLLA_MAX = 300
MIN_KAUPALLISET = 0.98
MAX_PUUTTUVAT = 0.005
MIN_TASMAYS = 0.99
SPREAD_NAYTTEITA = 20
SPREAD_VALI_S = 15


def lataa_markkina(sym: str, data_dir: str, get=http_json, log=print) -> dict:
    raw = charts(sym, "15m", LATAUS_ALKU, LATAUS_LOPPU, get)
    _, missing = to_candles(sym, raw, LATAUS_ALKU, LATAUS_LOPPU, STEP15)
    # puuttuvien päivien uudelleenhaku kerran
    days = sorted({t - t % DAY for t in missing})
    for d in days:
        again = charts(sym, "15m", d, min(d + DAY, LATAUS_LOPPU), get)
        for t, c in again.items():
            raw.setdefault(t, c)
    _, missing = to_candles(sym, raw, LATAUS_ALKU, LATAUS_LOPPU, STEP15)
    write_csv(os.path.join(data_dir, f"{sym}_15m.csv"), raw)
    test_slots = (TESTI_LOPPU - TESTI_ALKU) // STEP15
    in_test = [t for t in range(TESTI_ALKU, TESTI_LOPPU, STEP15)]
    traded = sum(1 for t in in_test if t in raw and raw[t]["volume"] > 0)
    miss_test = [t for t in missing if TESTI_ALKU <= t < TESTI_LOPPU]
    zero_test = [t for t in in_test if t in raw and raw[t]["volume"] == 0]
    log(f"lataus {sym}: {len(raw)} riviä, testijaksolla kaupallisia {traded / test_slots:.4f}, puuttuvia {len(miss_test)}")
    return {"raw": raw, "slots": test_slots, "kaupalliset": traded / test_slots, "puuttuvat": len(miss_test),
            "puuttuvat_osuus": len(miss_test) / test_slots, "nollat": zero_test,
            "puuttuvat_esim": [iso(t) for t in miss_test[:20]], "ensimmainen": iso(min(raw)) if raw else None,
            "viimeinen": iso(max(raw)) if raw else None}


def tarkista(sym: str, raw: dict, nollat: list[int], get=http_json) -> dict:
    rnd = random.Random(f"{SEED}-{sym}")
    pool = [t for t in range(TESTI_ALKU, TESTI_LOPPU, STEP15) if t in raw]
    sample = rnd.sample(pool, min(OTOS, len(pool)))
    ok = 0
    bad = []
    for t in sample:
        m = charts(sym, "1m", t, t + STEP15, get)
        agg = aggregate([m[k] for k in sorted(m)])
        if agg is not None and len(m) == 15 and same(agg, raw[t]):
            ok += 1
        else:
            bad.append({"aika": iso(t), "minuutteja": len(m), "15m": raw[t], "1m_koottu": agg})
    zsel = nollat if len(nollat) <= NOLLA_MAX else rnd.sample(nollat, NOLLA_MAX)
    z_ok, z_bad = 0, []
    for t in zsel:
        m = charts(sym, "1m", t, t + STEP15, get)
        if all(c["volume"] == 0 for c in m.values()):
            z_ok += 1
        else:
            z_bad.append({"aika": iso(t), "kauppaminuutteja_1m": sum(1 for c in m.values() if c["volume"] > 0)})
    return {"otos": len(sample), "tasmaa": ok, "tasmays": ok / len(sample) if sample else 0.0,
            "poikkeamat": bad[:20], "nollia_tarkistettu": len(zsel), "nollia_aitoja": z_ok, "nolla_virheet": z_bad[:20]}


def spreadit(symbols: list[str], get=http_json, log=print, n=SPREAD_NAYTTEITA, pause=SPREAD_VALI_S) -> dict:
    obs = {s: [] for s in symbols}
    for k in range(n):
        d = get(f"{BASE}/derivatives/api/v3/tickers")
        for x in d.get("tickers", []):
            s = x.get("symbol")
            if s in obs and x.get("bid") and x.get("ask"):
                b, a = float(x["bid"]), float(x["ask"])
                if a > b > 0:
                    obs[s].append((a - b) / 2 / ((a + b) / 2))
        if k < n - 1:
            time.sleep(pause)
    out = {s: {"mediaani": st.median(v) if v else None, "n": len(v)} for s, v in obs.items()}
    log(f"spreadit: {json.dumps({s: v['mediaani'] for s, v in out.items()})}")
    return out


def funding(sym: str, get=http_json) -> dict[int, float]:
    from datetime import datetime
    rows = get(f"{BASE}/derivatives/api/v4/historicalfundingrates?symbol={sym}").get("rates", [])
    out = {}
    for r in rows:
        t = int(datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")).timestamp() * 1000)
        if LATAUS_ALKU <= t < LATAUS_LOPPU:
            out[t] = float(r.get("relativeFundingRate") or 0.0)
    return out


def aja(out_dir: str, symbols: list[str], log=print, get=http_json) -> dict:
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    res = {"testijakso": [iso(TESTI_ALKU), iso(TESTI_LOPPU)], "markkinat": {}}
    for s in symbols:
        d = lataa_markkina(s, data_dir, get, log)
        chk = tarkista(s, d["raw"], d["nollat"], get)
        f = funding(s, get)
        with open(os.path.join(data_dir, f"{s}_funding.json"), "w") as fh:
            json.dump(f, fh)
        incl = (d["kaupalliset"] >= MIN_KAUPALLISET and d["puuttuvat_osuus"] <= MAX_PUUTTUVAT
                and chk["tasmays"] >= MIN_TASMAYS)
        res["markkinat"][s] = {k: v for k, v in d.items() if k not in ("raw", "nollat")} | {
            "nollia_testijaksolla": len(d["nollat"]), "eheys": chk, "funding_tunteja": len(f), "mukana": incl}
        log(f"eheys {s}: täsmäys {chk['tasmays']:.3f}, nollat {chk['nollia_aitoja']}/{chk['nollia_tarkistettu']} aitoja, mukana={incl}")
    res["spread"] = spreadit(symbols, get, log)
    res["spread_mitattu"] = iso(int(time.time() * 1000))
    res["mukana"] = [s for s in symbols if res["markkinat"][s]["mukana"]]
    with open(os.path.join(out_dir, "eheys.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    L = ["# Tutkimus 15M – data ja eheys (suunnitelma luku 4)\n",
         f"Testijakso {res['testijakso'][0]} – {res['testijakso'][1]} UTC. Spreadit mitattu {res['spread_mitattu']} UTC.\n",
         "| Markkina | Kaupallisia 15m | Puuttuvia rivejä | Kaupattomia (vol 0) | 1m-täsmäys (otos) | Nollat aitoja | Funding-tunteja | Puolikas spread nyt | Mukana |",
         "|---|---|---|---|---|---|---|---|---|"]
    for s in symbols:
        m = res["markkinat"][s]
        e = m["eheys"]
        hs = res["spread"][s]["mediaani"]
        L.append(f"| {s} | {m['kaupalliset']:.3%} | {m['puuttuvat']} ({m['puuttuvat_osuus']:.3%}) | {m['nollia_testijaksolla']} | "
                 f"{e['tasmaa']}/{e['otos']} | {e['nollia_aitoja']}/{e['nollia_tarkistettu']} | {m['funding_tunteja']} | "
                 f"{(hs * 100):.4f} % | {'kyllä' if m['mukana'] else 'EI'} |" if hs is not None else
                 f"| {s} | {m['kaupalliset']:.3%} | {m['puuttuvat']} | {m['nollia_testijaksolla']} | {e['tasmaa']}/{e['otos']} | "
                 f"{e['nollia_aitoja']}/{e['nollia_tarkistettu']} | {m['funding_tunteja']} | puuttuu | {'kyllä' if m['mukana'] else 'EI'} |")
    L.append(f"\nMukana analyysissa: **{', '.join(res['mukana']) or '–'}** ({len(res['mukana'])}/{len(symbols)}).")
    for s in symbols:
        e = res["markkinat"][s]["eheys"]
        if e["poikkeamat"] or e["nolla_virheet"] or res["markkinat"][s]["puuttuvat"]:
            L.append(f"\n### {s}: poikkeamat\n")
            if res["markkinat"][s]["puuttuvat_esim"]:
                L.append(f"* Puuttuvat rivit (esim.): {', '.join(res['markkinat'][s]['puuttuvat_esim'])}")
            for b in e["poikkeamat"]:
                L.append(f"* 1m ≠ 15m {b['aika']}: minuutteja {b['minuutteja']}, 15m {b['15m']}, 1m koottu {b['1m_koottu']}")
            for b in e["nolla_virheet"]:
                L.append(f"* Nollavolyymin 15m-kynttilä {b['aika']}, mutta 1m-datassa kauppaminuutteja {b['kauppaminuutteja_1m']} (datavirhe)")
    with open(os.path.join(out_dir, "eheys.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return res
