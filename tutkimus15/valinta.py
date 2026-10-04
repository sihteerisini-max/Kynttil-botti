"""Tutkimus 15M, vaihe "valinta": likvidien markkinoiden objektiivinen valinta (suunnitelma luku 3,
muutos 1.1 luvussa 13: kattavuusehto 15m-kynttilöistä, 1m-osuus vain tiedoksi).

Käyttää vain valintajakson 1.10.2024–1.1.2025 dataa (ennen testijaksoa).
"""
from __future__ import annotations

import json
import os
import statistics as st
from collections import defaultdict

from data15 import BASE, DAY, MIN, STEP15, charts, http_json, iso, ms

VALINTA_ALKU = ms("2024-10-01")
VALINTA_LOPPU = ms("2025-01-01")
AVAUS_VIIMEISTAAN = ms("2024-10-01")
DATA_ALKAA_VIIMEISTAAN = ms("2024-10-02")
TOP_LIKVIDI = 10
MIN_KAUPPAKYNTTILAT = 0.99     # muutos 1.1: 15m-kynttilöistä (oli 1m-minuuteista)
VALITTAVIA = 6
VAHIMMAISMAARA = 4


def ehdokkaat(instruments: list[dict]) -> list[dict]:
    out = []
    for x in instruments:
        s = x.get("symbol", "")
        if not (s.startswith("PF_") and s.endswith("USD")):
            continue
        if x.get("type") != "flexible_futures" or not x.get("tradeable") or x.get("tradfi"):
            continue
        od = x.get("openingDate")
        if not od or ms(od.replace("Z", "")[:16]) > AVAUS_VIIMEISTAAN:
            continue
        out.append({"symbol": s, "openingDate": od})
    return sorted(out, key=lambda r: r["symbol"])


def paivavolyymi_mediaani(raw15: dict[int, dict]) -> float:
    days: dict[int, float] = defaultdict(float)
    for t, c in raw15.items():
        days[t // DAY] += c["volume"] * c["close"]
    # päivät, joilta ei ole yhtään kynttilää, ovat 0 (valintajakso on kiinteä 92 vrk)
    n_days = (VALINTA_LOPPU - VALINTA_ALKU) // DAY
    vals = [days.get(VALINTA_ALKU // DAY + k, 0.0) for k in range(n_days)]
    return st.median(vals)


def valitse(rivit: list[dict]) -> tuple[list[str], str]:
    """rivit: [{symbol, mediaani, data_ok, kauppakynttilat (vain top10)}] -> (valitut, perustelu)."""
    ok = [r for r in rivit if r["data_ok"]]
    ok.sort(key=lambda r: -r["mediaani"])
    top = ok[:TOP_LIKVIDI]
    passed = [r for r in top if r.get("kauppakynttilat") is not None and r["kauppakynttilat"] >= MIN_KAUPPAKYNTTILAT]
    chosen = [r["symbol"] for r in passed[:VALITTAVIA]]
    if len(chosen) < VAHIMMAISMAARA:
        return chosen, f"vain {len(chosen)} markkinaa täyttää ehdot (< {VAHIMMAISMAARA}) – tutkimusta ei ajeta"
    return chosen, "ok"


def aja(out_dir: str, log=print, get=http_json) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    inst = get(f"{BASE}/derivatives/api/v3/instruments")["instruments"]
    cands = ehdokkaat(inst)
    log(f"valinta: {len(cands)} ehdokasta")
    rows = []
    for k, c in enumerate(cands):
        raw = charts(c["symbol"], "15m", VALINTA_ALKU, VALINTA_LOPPU, get)
        first = min(raw) if raw else None
        data_ok = first is not None and first <= DATA_ALKAA_VIIMEISTAAN
        rows.append({"symbol": c["symbol"], "openingDate": c["openingDate"], "data_alkaa": iso(first) if first else None,
                     "data_ok": data_ok, "kynttiloita_15m": len(raw),
                     "mediaani": paivavolyymi_mediaani(raw) if raw else 0.0, "kauppaminuutit": None,
                     "kauppakynttilat": None,
                     "_t15": sum(1 for c in raw.values() if c["volume"] > 0)})
        if k % 20 == 0:
            log(f"valinta: 15m {k + 1}/{len(cands)}")
    ranked = sorted([r for r in rows if r["data_ok"]], key=lambda r: -r["mediaani"])[:TOP_LIKVIDI]
    expected = (VALINTA_LOPPU - VALINTA_ALKU) // MIN
    expected15 = (VALINTA_LOPPU - VALINTA_ALKU) // STEP15
    for r in rows:
        if r in ranked:
            r["kauppakynttilat"] = r["_t15"] / expected15
        r.pop("_t15", None)
    for r in ranked:
        raw1 = charts(r["symbol"], "1m", VALINTA_ALKU, VALINTA_LOPPU, get)
        traded = sum(1 for c in raw1.values() if c["volume"] > 0)
        r["kauppaminuutit"] = traded / expected
        r["minuutteja_palautettu"] = len(raw1)
        log(f"valinta: {r['symbol']} kauppakynttilöitä (15m) {r['kauppakynttilat']:.4f}, kauppaminuutteja (1m, tiedoksi) {r['kauppaminuutit']:.4f}")
    chosen, why = valitse(rows)
    res = {"valintajakso": [iso(VALINTA_ALKU), iso(VALINTA_LOPPU)], "ehdokkaita": len(cands), "valitut": chosen,
           "perustelu": why, "rivit": sorted(rows, key=lambda r: -r["mediaani"])}
    with open(os.path.join(out_dir, "valinta.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    L = ["# Tutkimus 15M – markkinavalinta (suunnitelma luku 3, muutos 1.1)\n",
         f"Valintajakso {res['valintajakso'][0]} – {res['valintajakso'][1]} UTC (ennen testijaksoa). "
         f"Ehdokkaita {len(cands)} (PF_*USD, flexible_futures, tradeable, ei tradfi, avattu ≤ 1.10.2024).\n",
         f"**Valitut markkinat:** {', '.join(chosen) if chosen else '–'} ({why})\n",
         "| # | Markkina | Päivän nimellisvolyymin mediaani (USD) | 15m data alkaa | Kauppakynttilöitä (15m, ehto ≥ 99 %) | Kauppaminuutteja (1m, tiedoksi) | Tulos |",
         "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(res["rivit"][:30], 1):
        km = f"{r['kauppaminuutit']:.2%}" if r["kauppaminuutit"] is not None else "–"
        kk = f"{r['kauppakynttilat']:.2%}" if r["kauppakynttilat"] is not None else "–"
        if r["symbol"] in chosen:
            t = "VALITTU"
        elif not r["data_ok"]:
            t = "ei dataa koko jaksolta"
        elif r["kauppakynttilat"] is not None and r["kauppakynttilat"] < MIN_KAUPPAKYNTTILAT:
            t = "kauppakynttilät < 99 %"
        elif r["kauppakynttilat"] is not None:
            t = "täytti ehdon, ei kuuden joukossa"
        else:
            t = "ei 10 likvideimmän joukossa"
        L.append(f"| {i} | {r['symbol']} | {r['mediaani']:,.0f} | {r['data_alkaa'] or '–'} | {kk} | {km} | {t} |")
    with open(os.path.join(out_dir, "valinta.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return res
