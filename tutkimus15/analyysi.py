"""Tutkimus 15M, vaihe "analyysi": ajoitus satunnaisvertailulla (vaihe 1), liikkeiden koko suhteessa
kuluihin (kuvaileva) ja ehdollinen kannattavuus (vaihe 2). Suunnitelma: docs/TUTKIMUS15_SUUNNITELMA.md.

Kaikki asetukset alla ovat suunnitelman mukaisia ja lukittuja.
"""
from __future__ import annotations

import csv
import json
import math
import os
import random
import statistics as st
from collections import defaultdict

from data15 import DAY, STEP15, iso, ms, read_csv, to_candles
from kt.paper import PaperEngine
from kt.strategy import RULESETS

# ---------------------------------------------------------------- LUKITUT ASETUKSET
TYYPIT = {"K": "aj1-kaanto", "J": "aj1-jatko"}
RYHMAT = [("K", "long"), ("K", "short"), ("J", "long"), ("J", "short")]
K1, K2 = 1.0, 2.0
H = 16                       # seuranta-aika 16 kynttilää = 4 h; aikaraja = 17. kynttilän avaus
AVG = 20
CONTROLS = 50
EXCLUDE = 16                 # vertailuhetki vähintään 16 kynttilän päässä signaalista
BOOT = 10_000
SEED = 20261004
ALPHA = 0.05
MIN_MARKETS = 4
MIN_N, MIN_DAYS = 300, 60
ALKU, LOPPU, PUOLI = ms("2025-01-01"), ms("2026-07-01"), ms("2025-10-01")
LATAUS_ALKU, LATAUS_LOPPU = ms("2024-12-29"), ms("2026-07-01T06:00")
FEE, SLIP, SLIP_STOP, HS_MIN = 0.0005, 0.0002, 0.0005, 0.00005
HOUR = 3_600_000


def vaadittu(m: int) -> int:
    return math.ceil(2 * m / 3)


# ---------------------------------------------------------------- signaalit ja A
def avg_range_before(cs) -> list:
    """A[i] = 20 edeltävän kynttilän keskimääräinen vaihteluväli, laskettu suoraan summana kuten botin
    kontekstissa. (Korjaus 4.10.2026: aiempi juokseva summa jätti täysin kaupattomille jaksoille
    liukulukujäännöksen ~1e-15, jolloin A = 0 -hetkiä ei suljettu pois.)"""
    out = [None] * len(cs)
    for i in range(AVG, len(cs)):
        out[i] = sum(cs[k].range for k in range(i - AVG, i)) / AVG
    return out


def signals_for(cs, version: str) -> list[tuple[int, str, float]]:
    """[(signaalikynttilän indeksi, suunta, A botin kontekstista)] botin omalla koodilla, avaukset estetty."""
    r = RULESETS[version]
    found = []
    eng = PaperEngine(r, lambda s, t: 0.0001, lambda s, t: None, log=lambda m: None,
                      on_signal=lambda sig, t: found.append(sig), verbose_signals=False)
    eng.allow_entries = False
    idx = {c.open_time: i for i, c in enumerate(cs)}
    out = []
    for c in cs:
        n0 = len(found)
        eng.on_bar_close(c)
        eng.allow_entries = False
        for sig in found[n0:]:
            out.append((idx[sig.candle.open_time], sig.side, sig.avg_range))
    return out


# ---------------------------------------------------------------- lopputulos
def outcome(cs, i: int, side: str, A: float, k: float) -> dict | None:
    """Avaus kynttilän i+1 avauksella, rajat ±k·A markkinahinnasta, seuranta H kynttilää."""
    if A is None or A <= 0 or i + H + 1 >= len(cs):
        return None
    sg = 1 if side == "long" else -1
    e = cs[i + 1].open
    tgt, stp = e + sg * k * A, e - sg * k * A
    res = None
    for j in range(i + 1, i + 1 + H):
        c = cs[j]
        if j > i + 1:
            if (c.open - tgt) * sg >= 0:
                res = ("tavoite", 1.0, j, c.open, c.open)
                break
            if (stp - c.open) * sg >= 0:
                res = ("stop", -1.0, j, c.open, c.open)
                break
        hit_t = (c.high >= tgt) if sg > 0 else (c.low <= tgt)
        hit_s = (c.low <= stp) if sg > 0 else (c.high >= stp)
        if hit_t and hit_s:
            res = ("epäselvä", 0.0, j, stp, tgt)     # (stop-hinta, tavoitehinta) vaihetta 2 varten
            break
        if hit_t:
            res = ("tavoite", 1.0, j, tgt, tgt)
            break
        if hit_s:
            res = ("stop", -1.0, j, stp, stp)
            break
    if res is None:
        x = cs[i + 1 + H].open
        res = ("aikaraja", max(-1.0, min(1.0, sg * (x - e) / (k * A))), i + 1 + H, x, x)
    hi = max(c.high for c in cs[i + 1:i + 1 + H])
    lo = min(c.low for c in cs[i + 1:i + 1 + H])
    return {"tulos": res[0], "pisteet": res[1], "j": res[2], "px": res[3], "px_alt": res[4], "e": e,
            "mfe": ((hi - e) if sg > 0 else (e - lo)) / A, "mae": ((e - lo) if sg > 0 else (hi - e)) / A,
            "r1": sg * (cs[i + 1].close - e) / A, "r4": sg * (cs[i + 4].close - e) / A,
            "r16": sg * (cs[i + 16].close - e) / A}


def controls(cs, A, i: int, side: str, k: float, rnd: random.Random, by_day: dict) -> list[dict]:
    cand = [j for j in by_day.get(cs[i].open_time // DAY, []) if abs(j - i) >= EXCLUDE]
    out = []
    if not cand:
        return out
    tries = 0
    while len(out) < CONTROLS and tries < 20 * CONTROLS:
        tries += 1
        j = cand[rnd.randrange(len(cand))]
        o = outcome(cs, j, side, A[j], k)
        if o:
            out.append(o)
    return out


# ---------------------------------------------------------------- vaihe 2: kauppa kuluineen
def net_trade(o: dict, side: str, hs: float, t_entry: int, t_exit: int, fund: dict[int, float],
              ambiguous_as_target: bool = False) -> dict:
    sg = 1 if side == "long" else -1
    entry = o["e"] * (1 + sg * (hs + SLIP))
    if o["tulos"] == "epäselvä":
        px, slip = (o["px_alt"], SLIP) if ambiguous_as_target else (o["px"], SLIP_STOP)
    elif o["tulos"] == "stop":
        px, slip = o["px"], SLIP_STOP
    else:
        px, slip = o["px"], SLIP
    exit_ = px * (1 - sg * (hs + slip))
    gross = sg * (exit_ - entry) / entry
    fees = FEE * (entry + exit_) / entry
    hours = max(0.0, (t_exit - t_entry) / HOUR)
    h0 = t_entry - t_entry % HOUR
    rates = [fund.get(h0 + k * HOUR, 0.0) for k in range(int(math.ceil(hours)) or 1)]
    fr = st.mean(rates) if rates else 0.0
    funding = sg * fr * hours
    return {"brutto": gross, "palkkiot": fees, "funding": funding, "netto": gross - fees - funding}


# ---------------------------------------------------------------- tilastot
def cluster_boot(by_cluster: dict, rnd: random.Random, boot: int = BOOT):
    keys = list(by_cluster)
    allv = [v for k in keys for v in by_cluster[k]]
    if len(keys) < 2 or not allv:
        return (st.mean(allv) if allv else float("nan"), float("-inf"), float("inf"), 1.0)
    m = st.mean(allv)
    S = [sum(by_cluster[k]) for k in keys]
    N = [len(by_cluster[k]) for k in keys]
    nk = len(keys)
    rng = range(nk)
    bs = []
    for _ in range(boot):
        idx = rnd.choices(rng, k=nk)
        n = sum(map(N.__getitem__, idx))
        bs.append(sum(map(S.__getitem__, idx)) / n if n else 0.0)
    bs.sort()
    lo, hi = bs[int(0.025 * boot)], bs[int(0.975 * boot) - 1]
    p = 2 * min(sum(1 for x in bs if x <= 0) / boot, sum(1 for x in bs if x >= 0) / boot)
    return m, lo, hi, min(1.0, p)


def holm(ps: dict) -> dict:
    items = sorted(ps.items(), key=lambda x: x[1])
    m, out, prev = len(items), {}, 0.0
    for r, (k, p) in enumerate(items):
        adj = min(1.0, max(prev, (m - r) * p))
        out[k], prev = adj, adj
    return out


def bh(ps: dict) -> dict:
    items = sorted(ps.items(), key=lambda x: x[1])
    m, out, prev = len(items), {}, 1.0
    for r in range(m - 1, -1, -1):
        k, p = items[r]
        prev = min(prev, p * m / (r + 1))
        out[k] = prev
    return out


def paatos(n, nd, p_holm, m, h1, h2, pos, neg, n_mukana) -> str:
    if n_mukana < MIN_MARKETS:
        return f"KOKONAISPÄÄTÖS AVOIN (mukana {n_mukana} < {MIN_MARKETS} markkinaa)"
    if n < MIN_N or nd < MIN_DAYS:
        return f"AINEISTO EI RIITÄ (n = {n}, päiviä {nd}; vaaditaan ≥ {MIN_N} ja ≥ {MIN_DAYS})"
    need = vaadittu(n_mukana)
    halves = h1 is not None and h2 is not None
    if p_holm < ALPHA and m > 0 and halves and h1 > 0 and h2 > 0 and pos >= need:
        return "AJOITUSETU OSOITETTU (ennen kuluja)"
    if p_holm < ALPHA and m < 0 and halves and h1 < 0 and h2 < 0 and neg >= need:
        return "SIGNAALIT SATTUMAA HUONOMPIA"
    if p_holm < ALPHA:
        return "TILASTOLLINEN ERO, EI JOHDONMUKAINEN (puoliskot tai markkinat ristiriidassa) – ei osoitettu"
    return "EI NÄYTTÖÄ AJOITUSEDUSTA"


def kannattavuus_paatos(m, lo, h1, h2, pos, need) -> str:
    if m > 0 and lo > 0 and h1 is not None and h2 is not None and h1 > 0 and h2 > 0 and pos >= need:
        return "KANNATTAVA ENNEN PAPERITESTIÄ (signaalikohtainen odotusarvo kulujen jälkeen)"
    return "EI KANNATTAVA"


# ---------------------------------------------------------------- data
def load_market(path: str, sym: str):
    raw = read_csv(path)
    cs, missing = to_candles(sym, raw, LATAUS_ALKU, LATAUS_LOPPU, STEP15)
    return cs


def analyse_market(sym: str, cs, rnd: random.Random) -> list[dict]:
    A = avg_range_before(cs)
    by_day = defaultdict(list)
    for i, c in enumerate(cs):
        if ALKU <= c.open_time < LOPPU and A[i] and i + H + 1 < len(cs):
            by_day[c.open_time // DAY].append(i)
    rows = []
    for typ, ver in TYYPIT.items():
        for i, side, A_bot in signals_for(cs, ver):
            if not (ALKU <= cs[i].open_time < LOPPU) or i + H + 1 >= len(cs):
                continue
            if A[i] is None or abs(A[i] - A_bot) > 1e-9 * max(1.0, abs(A_bot)):
                raise SystemExit(f"A-ristiriita {sym} {iso(cs[i].open_time)}: {A[i]} vs botti {A_bot}")
            row = {"tyyppi": typ, "suunta": side, "markkina": sym, "signaali_utc": iso(cs[i].open_time),
                   "t": cs[i].open_time, "paiva": cs[i].open_time // DAY, "i": i, "A": A[i], "avaus": cs[i + 1].open}
            for k, tag in ((K1, "k1"), (K2, "k2")):
                o = outcome(cs, i, side, A[i], k)
                ctr = controls(cs, A, i, side, k, rnd, by_day)
                row[f"{tag}_tulos"] = o["tulos"]
                row[f"{tag}_pisteet"] = o["pisteet"]
                row[f"{tag}_vk"] = st.mean(c["pisteet"] for c in ctr) if ctr else None
                row[f"{tag}_v_tavoite"] = (sum(c["tulos"] == "tavoite" for c in ctr) / len(ctr)) if ctr else None
                row[f"{tag}_v_epaselva"] = (sum(c["tulos"] == "epäselvä" for c in ctr) / len(ctr)) if ctr else None
                if tag == "k1":
                    row["_o"] = o
                    for f in ("mfe", "mae", "r1", "r4", "r16"):
                        row[f] = o[f]
                        row[f + "_v"] = st.mean(c[f] for c in ctr) if ctr else None
            rows.append(row)
    return rows


# ---------------------------------------------------------------- pääohjelma
def aja(out_dir: str, log=print) -> dict:
    with open(os.path.join(out_dir, "eheys.json"), encoding="utf-8") as f:
        eh = json.load(f)
    symbols = list(eh["markkinat"])
    mukana = eh["mukana"]
    n_m = len(mukana)
    rnd = random.Random(SEED)
    rows, cs_by = [], {}
    for s in mukana:
        cs = load_market(os.path.join(out_dir, "data", f"{s}_15m.csv"), s)
        cs_by[s] = cs
        r = analyse_market(s, cs, rnd)
        log(f"analyysi {s}: {len(r)} signaalia")
        rows.extend(r)
    hs = {s: max(eh["spread"][s]["mediaani"] or 0.0, HS_MIN) for s in symbols}
    fund = {}
    for s in mukana:
        with open(os.path.join(out_dir, "data", f"{s}_funding.json")) as f:
            fund[s] = {int(k): v for k, v in json.load(f).items()}

    # CSV
    if rows:
        keys = [k for k in rows[0] if not k.startswith("_")]
        with open(os.path.join(out_dir, "signaalit.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    def diff(sel, key="k1_pisteet", ckey="k1_vk", rb=None):
        byc = defaultdict(list)
        for r in sel:
            if r[ckey] is not None:
                byc[r["paiva"]].append(r[key] - r[ckey])
        return cluster_boot(byc, rb), sum(len(v) for v in byc.values()), len(byc)

    rb = random.Random(SEED + 1)
    L = ["# Tutkimus 15M – tulokset\n",
         f"Suunnitelma `docs/TUTKIMUS15_SUUNNITELMA.md` (lukittu ennen dataa). Testijakso {iso(ALKU)} – {iso(LOPPU)} UTC, "
         f"15m-kynttilät, seuranta-aika {H} kynttilää (4 h), rajat ±1·A, siemen {SEED}. Ei kuluja vaiheessa 1.\n",
         f"Markkinat: {', '.join(symbols)}. Mukana analyysissa (kattavuus ja eheys): **{', '.join(mukana) or '–'}** ({n_m}).\n"]

    # ---- vaihe 1 ensisijainen
    prim, pvals = {}, {}
    for typ, side in RYHMAT:
        sel = [r for r in rows if r["tyyppi"] == typ and r["suunta"] == side]
        (m, lo, hi, p), n, nd = diff(sel, rb=rb)
        prim[(typ, side)] = {"m": m, "lo": lo, "hi": hi, "p": p, "n": n, "nd": nd, "sel": sel}
        pvals[(typ, side)] = p
    ph = holm(pvals)
    L.append("## Vaihe 1: ajoitus (ensisijainen, Holm 4 testille)\n")
    L.append("| Ryhmä | Signaaleja | Päiviä | Signaali ka | Vertailu ka | D | 95 % LV | p | p (Holm) | 1. puolisko | 2. puolisko | Markkinoita D > 0 | Päätös |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    decisions = {}
    for (typ, side), d in prim.items():
        sel = d["sel"]
        h1 = [r["k1_pisteet"] - r["k1_vk"] for r in sel if r["t"] < PUOLI and r["k1_vk"] is not None]
        h2 = [r["k1_pisteet"] - r["k1_vk"] for r in sel if r["t"] >= PUOLI and r["k1_vk"] is not None]
        byc = defaultdict(list)
        for r in sel:
            if r["k1_vk"] is not None:
                byc[r["markkina"]].append(r["k1_pisteet"] - r["k1_vk"])
        pos = sum(1 for v in byc.values() if v and st.mean(v) > 0)
        neg = sum(1 for v in byc.values() if v and st.mean(v) < 0)
        h1m = st.mean(h1) if h1 else None
        h2m = st.mean(h2) if h2 else None
        dec = paatos(d["n"], d["nd"], ph[(typ, side)], d["m"], h1m, h2m, pos, neg, n_m)
        decisions[(typ, side)] = dec
        d.update(h1=h1m, h2=h2m, pos=pos, neg=neg, dec=dec, ph=ph[(typ, side)])
        sm = st.mean(r["k1_pisteet"] for r in sel) if sel else float("nan")
        cm = st.mean(r["k1_vk"] for r in sel if r["k1_vk"] is not None) if sel else float("nan")
        f = lambda x: "–" if x is None else f"{x:+.4f}"
        L.append(f"| {typ} {side} | {d['n']} | {d['nd']} | {sm:+.4f} | {cm:+.4f} | **{d['m']:+.4f}** | {d['lo']:+.4f} … {d['hi']:+.4f} | "
                 f"{d['p']:.4f} | {ph[(typ, side)]:.4f} | {f(h1m)} | {f(h2m)} | {pos}/{len(byc)} (vaad. {vaadittu(n_m)}) | **{dec}** |")
    L.append("\nD = signaalin pisteet − 50 satunnaisen vertailuhetken keskiarvo (sama markkina, suunta ja UTC-päivä). "
             "Epävarmuus päiväklusteribootstrapilla. D = +0,10 ≈ 55 % tavoiteosuus 50 %:n sijaan.\n")

    # markkinakohtaiset
    rc = random.Random(SEED + 2)
    L.append("### Markkinakohtaiset tulokset (ensisijainen mittari, ei erillistä päätöstä)\n")
    L.append("| Ryhmä | Markkina | Signaaleja | D | 95 % LV | p (korjaamaton) |\n|---|---|---|---|---|---|")
    for (typ, side), d in prim.items():
        for s in sorted({r["markkina"] for r in d["sel"]}):
            (m, lo, hi, p), n, nd = diff([r for r in d["sel"] if r["markkina"] == s], rb=rc)
            L.append(f"| {typ} {side} | {s} | {n} | {m:+.4f} | {lo:+.4f} … {hi:+.4f} | {p:.4f} |")

    # ---- täydentävät
    L.append("\n## Täydentävät mittarit (eksploratiivisia, Benjamini–Hochberg)\n")
    sec, secp = [], {}
    for typ in TYYPIT:
        sel = [r for r in rows if r["tyyppi"] == typ]
        cands = [(f"{typ} yhteensä (±1·A)", sel, "k1_pisteet", "k1_vk")]
        for side in ("long", "short"):
            ss = [r for r in sel if r["suunta"] == side]
            cands += [(f"{typ} {side} ±2·A", ss, "k2_pisteet", "k2_vk"),
                      (f"{typ} {side} tuotto 1 kynttilä (A)", ss, "r1", "r1_v"),
                      (f"{typ} {side} tuotto 4 kynttilää (A)", ss, "r4", "r4_v"),
                      (f"{typ} {side} tuotto 16 kynttilää (A)", ss, "r16", "r16_v"),
                      (f"{typ} {side} MFE (A)", ss, "mfe", "mfe_v"),
                      (f"{typ} {side} MAE (A)", ss, "mae", "mae_v")]
        for name, s_, k_, c_ in cands:
            (m, lo, hi, p), n, nd = diff(s_, k_, c_, rb)
            sec.append((name, n, nd, m, lo, hi, p))
            secp[name] = p
    q = bh(secp) if secp else {}
    L.append("| Mittari | n | Päiviä | Ero (signaali − vertailu) | 95 % LV | p | q (BH) |\n|---|---|---|---|---|---|---|")
    for name, n, nd, m, lo, hi, p in sec:
        L.append(f"| {name} | {n} | {nd} | {m:+.4f} | {lo:+.4f} … {hi:+.4f} | {p:.4f} | {q.get(name, 1):.4f} |")

    # ---- epäselvät ja jakauma
    L.append("\n## Lopputulosten jakauma ja epäselvien herkkyys (±1·A)\n")
    L.append("| Ryhmä | tavoite | stop | aikaraja | epäselvä | Signaalien tavoiteosuus | Vertailujen tavoiteosuus | D, jos epäselvä = +1 | D, jos epäselvä = −1 |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for (typ, side), d in prim.items():
        sel = [r for r in d["sel"] if r["k1_vk"] is not None]
        if not sel:
            continue
        c = defaultdict(int)
        for r in sel:
            c[r["k1_tulos"]] += 1
        ct = st.mean(r["k1_v_tavoite"] for r in sel)
        plus = st.mean((1.0 if r["k1_tulos"] == "epäselvä" else r["k1_pisteet"]) - (r["k1_vk"] + r["k1_v_epaselva"]) for r in sel)
        minus = st.mean((-1.0 if r["k1_tulos"] == "epäselvä" else r["k1_pisteet"]) - (r["k1_vk"] - r["k1_v_epaselva"]) for r in sel)
        L.append(f"| {typ} {side} | {c['tavoite']} | {c['stop']} | {c['aikaraja']} | {c['epäselvä']} | {c['tavoite'] / len(sel):.1%} | {ct:.1%} | {plus:+.4f} | {minus:+.4f} |")

    # ---- liikkeiden koko suhteessa kuluihin (kuvaileva)
    L.append("\n## Liikkeiden koko suhteessa kuluihin (kuvaileva, ei päätöstä)\n")
    L.append(f"Kulumalli: taker {FEE:.2%} × 2, liukuma {SLIP:.2%} avaus + {SLIP_STOP:.2%} stop, puolikas spread × 2 "
             f"(nykyinen mitattu {eh.get('spread_mitattu', '–')} UTC, vähintään {HS_MIN:.3%}). C = edestakainen kulu stop-skenaariossa. "
             "p* = ½ + C/(2A) on tavoiteosuus, jolla symmetrinen ±1·A-kauppa olisi kulujen jälkeen nollatuloksessa.\n")
    L.append("| Markkina | Puolikas spread | C (% hinnasta) | A mediaani (% hinnasta) | C/A mediaani | p* mediaani | Signaaleja, joissa p* > 100 % |")
    L.append("|---|---|---|---|---|---|---|")
    for s in mukana:
        sel = [r for r in rows if r["markkina"] == s]
        if not sel:
            continue
        C = 2 * FEE + 2 * hs[s] + SLIP + SLIP_STOP
        a_rel = sorted(r["A"] / r["avaus"] for r in sel)
        ca = sorted(C / x for x in a_rel)
        ps = [0.5 + x / 2 for x in ca]
        L.append(f"| {s} | {hs[s]:.4%} | {C:.3%} | {st.median(a_rel):.3%} | {st.median(ca):.2f} | {st.median(ps):.1%} | {sum(p > 1 for p in ps) / len(ps):.1%} |")
    L.append("\n| Ryhmä | Signaalien tavoiteosuus | p* keskiarvo | Ero (tavoiteosuus − p*) |\n|---|---|---|---|")
    for (typ, side), d in prim.items():
        sel = d["sel"]
        if not sel:
            continue
        ps = [0.5 + (2 * FEE + 2 * hs[r["markkina"]] + SLIP + SLIP_STOP) / (2 * r["A"] / r["avaus"]) for r in sel]
        tg = sum(r["k1_tulos"] == "tavoite" for r in sel) / len(sel)
        L.append(f"| {typ} {side} | {tg:.1%} | {st.mean(ps):.1%} | {tg - st.mean(ps):+.1%} |")

    # ---- vaihe 2
    L.append("\n## Vaihe 2: kannattavuus kulujen jälkeen (ehdollinen)\n")
    ran2 = False
    r2 = random.Random(SEED + 3)
    for (typ, side), d in prim.items():
        if not decisions[(typ, side)].startswith("AJOITUSETU OSOITETTU"):
            L.append(f"* **{typ} {side}:** vaihetta 2 ei ajettu – vaiheen 1 päätös: {decisions[(typ, side)]}.")
            continue
        ran2 = True
        byc, byc_alt, h1, h2, bym = defaultdict(list), defaultdict(list), [], [], defaultdict(list)
        parts = defaultdict(float)
        for r in d["sel"]:
            o, cs = r["_o"], cs_by[r["markkina"]]
            t_in, t_out = cs[r["i"] + 1].open_time, cs[o["j"]].open_time + (STEP15 if o["tulos"] != "aikaraja" else 0)
            x = net_trade(o, side, hs[r["markkina"]], t_in, t_out, fund[r["markkina"]])
            xa = net_trade(o, side, hs[r["markkina"]], t_in, t_out, fund[r["markkina"]], ambiguous_as_target=True)
            byc[r["paiva"]].append(x["netto"])
            byc_alt[r["paiva"]].append(xa["netto"])
            (h1 if r["t"] < PUOLI else h2).append(x["netto"])
            bym[r["markkina"]].append(x["netto"])
            for k in ("brutto", "palkkiot", "funding", "netto"):
                parts[k] += x[k]
        m, lo, hi, p = cluster_boot(byc, r2)
        ma = cluster_boot(byc_alt, r2)[0]
        pos = sum(1 for v in bym.values() if st.mean(v) > 0)
        dec2 = kannattavuus_paatos(m, lo, st.mean(h1) if h1 else None, st.mean(h2) if h2 else None, pos, vaadittu(n_m))
        n = len(d["sel"])
        L.append(f"* **{typ} {side}:** n = {n}, netto ka **{m:+.4%}** / kauppa (95 % LV {lo:+.4%} … {hi:+.4%}); "
                 f"brutto täyttöhinnoin (spread ja liukuma mukana) ka {parts['brutto'] / n:+.4%}, palkkiot {parts['palkkiot'] / n:.4%}, funding {parts['funding'] / n:+.5%}; "
                 f"puoliskot {st.mean(h1) if h1 else float('nan'):+.4%} / {st.mean(h2) if h2 else float('nan'):+.4%}; "
                 f"markkinoita > 0: {pos}/{len(bym)}; epäselvä = tavoite -> {ma:+.4%}. **{dec2}**")
    if not ran2:
        L.append("\nVaihetta 2 ei ajettu yhdellekään ryhmälle, koska ajoitusetua ei osoitettu suunnitelman mukaisesti.")
    L.append("\nKaikki luvut ovat paperilaskentaa historiadatalla. Toimeksiantoja ei lähetetty.")
    with open(os.path.join(out_dir, "raportti.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    summary = {"mukana": mukana, "ryhmat": {f"{t} {s}": {k: v for k, v in d.items() if k != "sel"} for (t, s), d in prim.items()},
               "vaihe2_ajettu": ran2, "signaaleja": len(rows)}
    with open(os.path.join(out_dir, "tulos.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, default=str)
    log("analyysi valmis")
    return summary
