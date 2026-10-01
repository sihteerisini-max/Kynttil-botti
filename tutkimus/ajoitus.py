"""VAIHE 1: ennustavatko signaalit suuntaa ja ajoitusta sattumaa paremmin (ilman kuluja)?

Ennakkoon lukittu suunnitelma: docs/VAIHE1_AJOITUSTUTKIMUS.md. Tämä skripti EI muuta botin
sääntöjä eikä koske livebottiin tai paperitileihin: se lukee historiallisia 1 min kynttilöitä ja
tuottaa signaalit botin omalla koodilla (PaperEngine.on_bar_close + on_signal, avaukset estetty).

    python -m tutkimus.ajoitus --data-glob "data/PF_*_2026-07-14T0000_2026-09-15T0000.csv" \\
        --alku 2026-07-15T00:00 --loppu 2026-09-15T00:00 --tulos tutkimus/tulokset/arviointi

Tulokset: <tulos>_raportti.md, <tulos>_signaalit.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import math
import os
import random
import statistics as st
from collections import defaultdict
from datetime import datetime, timezone

from kynttilatulkki import kraken
from kynttilatulkki.backtest import load_csv, parse_date
from kynttilatulkki.models import Candle
from kynttilatulkki.paper import PaperEngine
from kynttilatulkki.strategy import RULESETS

MIN = 60_000
DAY = 86_400_000

# ---------------------------------------------------------------- LUKITUT ASETUKSET
TYYPIT = {"K": "aj1-kaanto", "J": "aj1-jatko"}   # signaalit botin lukituista säännöistä (T2)
K_PRIMARY = 1.0          # tavoite ja stop ±1,0 × A markkinahinnasta (A = 20 edeltävän kynttilän keskim. vaihteluväli)
K_SECONDARY = 2.0
HORIZON = 15             # kynttilää; aikaraja = 16. kynttilän avaus (kuten botissa)
AVG_WINDOW = 20
CONTROLS = 50            # satunnaisvertailuja per signaali
EXCLUDE = 15             # vertailuhetki ei saa olla ±15 min signaalista
BOOT = 10_000
SEED = 20261001
ALPHA = 0.05
MIN_COVERAGE = 0.95      # markkina hylätään, jos kauppaminuutteja < 95 % (päätetään kattavuudesta, ei tuloksista)


# ---------------------------------------------------------------- data
def load(paths: list[str]) -> dict[str, list[Candle]]:
    out: dict[str, list[Candle]] = {}
    for p in sorted(paths):
        sym = os.path.basename(p).split("_20")[0]
        cs = load_csv(p, sym)
        out.setdefault(sym, []).extend(cs)
    for s in out:
        byt = {c.open_time: c for c in out[s]}
        out[s] = kraken.fill_gaps([byt[t] for t in sorted(byt)])
    return out


def avg_range_before(cs: list[Candle]) -> list[float | None]:
    """A[i] = keskimääräinen vaihteluväli kynttilöistä i−20 … i−1 (vain ennen kynttilää i)."""
    out: list[float | None] = [None] * len(cs)
    s = 0.0
    for i, c in enumerate(cs):
        if i >= AVG_WINDOW:
            out[i] = s / AVG_WINDOW
            s -= cs[i - AVG_WINDOW].range
        s += c.range
    return out


# ---------------------------------------------------------------- signaalit botin koodilla
def signals_for(sym: str, cs: list[Candle], version: str) -> list[tuple[int, str, str, float]]:
    """[(signaalikynttilän indeksi, suunta, peruste, A botin kontekstista)] – sama koodipolku kuin livebotissa."""
    r = RULESETS[version]
    found = []
    eng = PaperEngine(r, lambda s, t: 0.0001, lambda s, t: None, log=lambda m: None,
                      on_signal=lambda sig, t: found.append(sig), verbose_signals=False)
    eng.allow_entries = False          # ei kauppoja: vain signaalien tunnistus
    idx = {c.open_time: i for i, c in enumerate(cs)}
    out = []
    for c in cs:
        n0 = len(found)
        eng.on_bar_close(c)
        eng.allow_entries = False
        for sig in found[n0:]:
            out.append((idx[sig.candle.open_time], sig.side, sig.reason(), sig.avg_range))
    return out


# ---------------------------------------------------------------- lopputulos
def outcome(cs: list[Candle], i: int, side: str, A: float, k: float) -> dict | None:
    """Signaali kynttilässä i -> avaus kynttilän i+1 avauksella. Tavoite/stop ±k·A avaushinnasta.
    Pisteet: +1 tavoite ensin, −1 stop ensin, aikaraja: suunnattu muutos / (k·A) rajattuna [−1, 1],
    sama kynttilä osuu molempiin (järjestys tuntematon) -> 0 ('epäselvä')."""
    if i + HORIZON + 1 >= len(cs) or not A or A <= 0:
        return None
    sg = 1 if side == "long" else -1
    e = cs[i + 1].open
    tgt, stp = e + sg * k * A, e - sg * k * A
    res = None
    for j in range(i + 1, i + 1 + HORIZON):
        c = cs[j]
        if j > i + 1:            # hintakuilu avauksessa (ei avauskynttilässä: avaus = e)
            if (c.open - tgt) * sg >= 0:
                res = ("tavoite", 1.0, j)
                break
            if (stp - c.open) * sg >= 0:
                res = ("stop", -1.0, j)
                break
        hit_t = (c.high >= tgt) if sg > 0 else (c.low <= tgt)
        hit_s = (c.low <= stp) if sg > 0 else (c.high >= stp)
        if hit_t and hit_s:
            res = ("epäselvä", 0.0, j)
            break
        if hit_t:
            res = ("tavoite", 1.0, j)
            break
        if hit_s:
            res = ("stop", -1.0, j)
            break
    if res is None:
        x = cs[i + 1 + HORIZON].open
        res = ("aikaraja", max(-1.0, min(1.0, sg * (x - e) / (k * A))), i + 1 + HORIZON)
    hi = max(c.high for c in cs[i + 1:i + 1 + HORIZON])
    lo = min(c.low for c in cs[i + 1:i + 1 + HORIZON])
    mfe = (hi - e) / A if sg > 0 else (e - lo) / A
    mae = (e - lo) / A if sg > 0 else (hi - e) / A
    ret = {h: sg * (cs[i + h].close - e) / A for h in (1, 5, 15)}
    return {"tulos": res[0], "pisteet": res[1], "mfe": mfe, "mae": mae, "r1": ret[1], "r5": ret[5], "r15": ret[15]}


def controls(cs: list[Candle], A: list, i: int, side: str, k: float, rnd: random.Random,
             by_day: dict[int, list[int]]) -> list[dict]:
    """Sama markkina, sama suunta, sama UTC-päivä, satunnainen hetki (ei ±15 min signaalista).
    Vertailuhetkellä A lasketaan samalla tavalla vain sitä edeltävistä kynttilöistä."""
    cand = by_day.get(cs[i].open_time // DAY, [])
    out = []
    if len(cand) <= 2 * EXCLUDE + 1:
        return out
    while len(out) < CONTROLS:
        j = cand[rnd.randrange(len(cand))]
        if abs(j - i) <= EXCLUDE:
            continue
        o = outcome(cs, j, side, A[j], k)
        if o:
            out.append(o)
    return out


# ---------------------------------------------------------------- tilastot
def cluster_boot(vals_by_cluster: dict, rnd: random.Random) -> tuple[float, float, float, float]:
    """Klusteribootstrap (klusteri = UTC-päivä). Palauttaa (keskiarvo, ala, ylä, kaksisuuntainen p)."""
    keys = list(vals_by_cluster)
    allv = [v for k in keys for v in vals_by_cluster[k]]
    if len(keys) < 2 or not allv:
        return (st.mean(allv) if allv else float("nan"), float("-inf"), float("inf"), 1.0)
    m = st.mean(allv)
    sums = {k: (sum(vals_by_cluster[k]), len(vals_by_cluster[k])) for k in keys}
    bs = []
    for _ in range(BOOT):
        s = n = 0
        for _k in range(len(keys)):
            a, b = sums[keys[rnd.randrange(len(keys))]]
            s += a
            n += b
        bs.append(s / n if n else 0.0)
    bs.sort()
    lo, hi = bs[int(0.025 * BOOT)], bs[int(0.975 * BOOT) - 1]
    p = 2 * min(sum(1 for x in bs if x <= 0) / BOOT, sum(1 for x in bs if x >= 0) / BOOT)
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


MIN_COINS = 3   # "vähintään 3/5 markkinalla" – vaatii vähintään 3 kattavuusehdon täyttävää markkinaa


def paatos(n, nd, p_holm, m, h1m, h2m, pos_coins, neg_coins, n_mukana) -> str:
    """Ennakkoon lukittu päätössääntö (lisäys 1.10.2026 ennen toistojaksoa: jos alle 3 markkinaa
    täyttää kattavuusehdon, 3/5-ehto ei ole arvioitavissa -> kokonaispäätös jää avoimeksi)."""
    if n_mukana < MIN_COINS:
        return (f"KOKONAISPÄÄTÖS AVOIN (kattavuusehdon täyttäviä markkinoita {n_mukana} < {MIN_COINS}; "
                "3/5-ehtoa ei voi arvioida – markkinakohtaiset tulokset raportoidaan erikseen, eivät ole päätös)")
    if n < 300 or nd < 14:
        return f"AINEISTO EI RIITÄ (n = {n}, päiviä {nd}; vaaditaan ≥ 300 ja ≥ 14)"
    halves = h1m is not None and h2m is not None
    if p_holm < ALPHA and m > 0 and halves and h1m > 0 and h2m > 0 and pos_coins >= MIN_COINS:
        return "AJOITUSETU OSOITETTU (ennen kuluja)"
    if p_holm < ALPHA and m < 0 and halves and h1m < 0 and h2m < 0 and neg_coins >= MIN_COINS:
        return "SIGNAALIT SATTUMAA HUONOMPIA"
    if p_holm < ALPHA:
        return "TILASTOLLINEN ERO, MUTTA EI JOHDONMUKAINEN (puoliskot tai markkinat ristiriidassa) – ei osoitettu"
    return "EI NÄYTTÖÄ AJOITUSEDUSTA"


# ---------------------------------------------------------------- pääohjelma
def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Vaihe 1: signaalien ajoitus vs. satunnaisvertailu (ilman kuluja)")
    ap.add_argument("--data-glob", required=True)
    ap.add_argument("--alku", required=True, help="signaalit tästä alkaen (UTC); datassa oltava ≥ 1 vrk aiempaa historiaa")
    ap.add_argument("--loppu", required=True)
    ap.add_argument("--tulos", default="tutkimus/tulokset/arviointi")
    ap.add_argument("--aineisto", default="ARVIOINTI", help="KEHITYS tai ARVIOINTI (merkitään raporttiin)")
    a = ap.parse_args(argv)
    t0, t1 = parse_date(a.alku), parse_date(a.loppu)
    data = load(glob.glob(a.data_glob))
    if not data:
        raise SystemExit("Ei dataa: tarkista --data-glob")
    os.makedirs(os.path.dirname(a.tulos) or ".", exist_ok=True)
    rnd = random.Random(SEED)

    cover, rows = {}, []
    for sym, cs in sorted(data.items()):
        inside = [c for c in cs if t0 <= c.open_time < t1]
        traded = sum(1 for c in inside if c.volume > 0)
        cover[sym] = (traded / len(inside) if inside else 0.0, len(inside),
                      cs[0].open_time if cs else None, cs[-1].open_time if cs else None)
        if not inside or cover[sym][0] < MIN_COVERAGE or cs[0].open_time > t0 - DAY:
            continue
        A = avg_range_before(cs)
        by_day: dict[int, list[int]] = defaultdict(list)
        for i, c in enumerate(cs):
            if t0 <= c.open_time < t1 and A[i] and i + HORIZON + 1 < len(cs):
                by_day[c.open_time // DAY].append(i)
        for typ, ver in TYYPIT.items():
            for i, side, reason, A_bot in signals_for(sym, cs, ver):
                if not (t0 <= cs[i].open_time < t1) or i + HORIZON + 1 >= len(cs):
                    continue
                if A[i] is None or abs(A[i] - A_bot) > 1e-9 * max(1.0, A_bot):
                    raise SystemExit(f"A-ristiriita {sym} {cs[i].open_time}: {A[i]} vs botti {A_bot}")
                row = {"tyyppi": typ, "markkina": sym, "suunta": side, "peruste": reason,
                       "signaali_utc": datetime.fromtimestamp(cs[i].open_time / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M"),
                       "paiva": cs[i].open_time // DAY, "A": A[i], "avaus": cs[i + 1].open}
                for k, tag in ((K_PRIMARY, "k1"), (K_SECONDARY, "k2")):
                    o = outcome(cs, i, side, A[i], k)
                    ctr = controls(cs, A, i, side, k, rnd, by_day)
                    row[f"{tag}_tulos"] = o["tulos"]
                    row[f"{tag}_pisteet"] = o["pisteet"]
                    row[f"{tag}_vertailu_ka"] = st.mean(c["pisteet"] for c in ctr) if ctr else None
                    row[f"{tag}_vertailu_tavoite_osuus"] = (sum(c["tulos"] == "tavoite" for c in ctr) / len(ctr)) if ctr else None
                    row[f"{tag}_vertailu_epaselva_osuus"] = (sum(c["tulos"] == "epäselvä" for c in ctr) / len(ctr)) if ctr else None
                    if tag == "k1":
                        for f in ("mfe", "mae", "r1", "r5", "r15"):
                            row[f] = o[f]
                            row[f"{f}_vertailu"] = st.mean(c[f] for c in ctr) if ctr else None
                rows.append(row)

    # ---- CSV
    if rows:
        with open(a.tulos + "_signaalit.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    # ---- analyysi
    def diff_stat(sel, key, ctrl_key, rnd_):
        byc = defaultdict(list)
        for r in sel:
            if r[ctrl_key] is not None:
                byc[r["paiva"]].append(r[key] - r[ctrl_key])
        return cluster_boot(byc, rnd_), sum(len(v) for v in byc.values()), len(byc)

    rb = random.Random(SEED + 1)
    L = []
    L.append(f"# Vaihe 1 – ajoitustutkimus ({a.aineisto}-aineisto)\n")
    L.append(f"Aineisto {a.alku} – {a.loppu} UTC · suunnitelma docs/VAIHE1_AJOITUSTUTKIMUS.md · ei kuluja · siemen {SEED}\n")
    L.append("## Markkinat ja kattavuus\n\n| Markkina | Kauppaminuutteja | Minuutteja | Mukana |\n|---|---|---|---|")
    for s, (cv, n, f0, f1) in sorted(cover.items()):
        ok = cv >= MIN_COVERAGE and f0 is not None and f0 <= t0 - DAY
        L.append(f"| {s} | {cv:.1%} | {n} | {'kyllä' if ok else 'EI (kattavuus tai historia)'} |")
    prim, prim_p = {}, {}
    L.append("\n## Ensisijainen mittari\n\nSignaalin pisteet − saman markkinan, suunnan ja UTC-päivän 50 satunnaisen hetken keskiarvo "
             "(±1,0·A, 15 min). Epävarmuus: päiväklusteribootstrap. Holm-korjaus kahdelle testille (K, J).\n")
    L.append("| Tyyppi | Signaaleja | Päiviä | Signaali ka | Vertailu ka | Ero | 95 % LV | p | p (Holm) |\n|---|---|---|---|---|---|---|---|---|")
    for typ in TYYPIT:
        sel = [r for r in rows if r["tyyppi"] == typ]
        (m, lo, hi, p), n, nd = diff_stat(sel, "k1_pisteet", "k1_vertailu_ka", rb)
        prim[typ] = (m, lo, hi, p, n, nd, sel)
        prim_p[typ] = p
    ph = holm(prim_p) if prim_p else {}
    for typ, (m, lo, hi, p, n, nd, sel) in prim.items():
        sm = st.mean(r["k1_pisteet"] for r in sel) if sel else float("nan")
        cm = st.mean(r["k1_vertailu_ka"] for r in sel if r["k1_vertailu_ka"] is not None) if sel else float("nan")
        L.append(f"| {typ} | {n} | {nd} | {sm:+.4f} | {cm:+.4f} | **{m:+.4f}** | {lo:+.4f} … {hi:+.4f} | {p:.4f} | {ph.get(typ, 1):.4f} |")

    # ---- päätössäännöt (lukittu)
    n_mukana = sum(1 for s, (cv, n_, f0, f1) in cover.items()
                   if cv >= MIN_COVERAGE and f0 is not None and f0 <= t0 - DAY)
    L.append("\n## Päätös (ennakkoon lukittu sääntö)\n")
    L.append(f"Kattavuusehdon täyttäviä markkinoita: **{n_mukana}/{len(cover)}** (vaaditaan ≥ {MIN_COINS}).\n")
    for typ, (m, lo, hi, p, n, nd, sel) in prim.items():
        days = sorted({r["paiva"] for r in sel})
        half = days[len(days) // 2] if days else 0
        h1 = [r["k1_pisteet"] - r["k1_vertailu_ka"] for r in sel if r["paiva"] < half and r["k1_vertailu_ka"] is not None]
        h2 = [r["k1_pisteet"] - r["k1_vertailu_ka"] for r in sel if r["paiva"] >= half and r["k1_vertailu_ka"] is not None]
        coins = defaultdict(list)
        for r in sel:
            if r["k1_vertailu_ka"] is not None:
                coins[r["markkina"]].append(r["k1_pisteet"] - r["k1_vertailu_ka"])
        pos_coins = sum(1 for v in coins.values() if v and st.mean(v) > 0)
        neg_coins = sum(1 for v in coins.values() if v and st.mean(v) < 0)
        verdict = paatos(n, nd, ph.get(typ, 1), m, st.mean(h1) if h1 else None, st.mean(h2) if h2 else None,
                         pos_coins, neg_coins, n_mukana)
        L.append(f"* **{typ}**: {verdict}. Puoliskot {st.mean(h1) if h1 else float('nan'):+.4f} / "
                 f"{st.mean(h2) if h2 else float('nan'):+.4f}; markkinoita, joissa ero > 0: {pos_coins}/{len(coins)}.")

    # ---- markkinakohtaiset tulokset (raportoidaan aina erikseen; eivät ole kokonaispäätös)
    L.append("\n## Markkinakohtaiset tulokset (ensisijainen mittari, erikseen – ei kokonaispäätös)\n")
    L.append("| Tyyppi | Markkina | Signaaleja | Päiviä | Ero | 95 % LV | p (korjaamaton) |\n|---|---|---|---|---|---|---|")
    rc = random.Random(SEED + 2)
    for typ, (_m, _lo, _hi, _p, _n, _nd, sel) in prim.items():
        for sym in sorted({r["markkina"] for r in sel}):
            (m, lo, hi, p), n, nd = diff_stat([r for r in sel if r["markkina"] == sym], "k1_pisteet", "k1_vertailu_ka", rc)
            L.append(f"| {typ} | {sym} | {n} | {nd} | {m:+.4f} | {lo:+.4f} … {hi:+.4f} | {p:.4f} |")

    # ---- täydentävät (eksploratiiviset, BH-korjaus)
    L.append("\n## Täydentävät mittarit (eksploratiivisia, Benjamini–Hochberg)\n")
    sec, secp = [], {}
    for typ in TYYPIT:
        sel = [r for r in rows if r["tyyppi"] == typ]
        cands = [
            (f"{typ} long", [r for r in sel if r["suunta"] == "long"], "k1_pisteet", "k1_vertailu_ka"),
            (f"{typ} short", [r for r in sel if r["suunta"] == "short"], "k1_pisteet", "k1_vertailu_ka"),
            (f"{typ} ±2·A", sel, "k2_pisteet", "k2_vertailu_ka"),
            (f"{typ} tuotto 1 min (A)", sel, "r1", "r1_vertailu"),
            (f"{typ} tuotto 5 min (A)", sel, "r5", "r5_vertailu"),
            (f"{typ} tuotto 15 min (A)", sel, "r15", "r15_vertailu"),
            (f"{typ} MFE (A)", sel, "mfe", "mfe_vertailu"),
            (f"{typ} MAE (A)", sel, "mae", "mae_vertailu"),
        ]
        for sym in sorted({r["markkina"] for r in sel}):
            cands.append((f"{typ} {sym}", [r for r in sel if r["markkina"] == sym], "k1_pisteet", "k1_vertailu_ka"))
        for name, s_, k_, c_ in cands:
            (m, lo, hi, p), n, nd = diff_stat(s_, k_, c_, rb)
            sec.append((name, n, nd, m, lo, hi, p))
            secp[name] = p
    q = bh(secp)
    L.append("| Mittari | n | Päiviä | Ero (signaali − vertailu) | 95 % LV | p | q (BH) |\n|---|---|---|---|---|---|---|")
    for name, n, nd, m, lo, hi, p in sec:
        L.append(f"| {name} | {n} | {nd} | {m:+.4f} | {lo:+.4f} … {hi:+.4f} | {p:.4f} | {q[name]:.4f} |")

    # ---- epäselvät ja herkkyys
    L.append("\n## Saman kynttilän osumat (epäselvä) ja herkkyys\n")
    L.append("| Tyyppi | Epäselviä (signaalit) | Vertailujen epäselvä-osuus | Ero, jos epäselvä = +1 | Ero, jos epäselvä = −1 |\n|---|---|---|---|---|")
    for typ in TYYPIT:
        sel = [r for r in rows if r["tyyppi"] == typ and r["k1_vertailu_ka"] is not None]
        if not sel:
            continue
        amb = sum(r["k1_tulos"] == "epäselvä" for r in sel)
        camb = st.mean(r["k1_vertailu_epaselva_osuus"] for r in sel)
        plus = st.mean((1.0 if r["k1_tulos"] == "epäselvä" else r["k1_pisteet"]) - (r["k1_vertailu_ka"] + r["k1_vertailu_epaselva_osuus"]) for r in sel)
        minus = st.mean((-1.0 if r["k1_tulos"] == "epäselvä" else r["k1_pisteet"]) - (r["k1_vertailu_ka"] - r["k1_vertailu_epaselva_osuus"]) for r in sel)
        L.append(f"| {typ} | {amb} ({amb / len(sel):.1%}) | {camb:.1%} | {plus:+.4f} | {minus:+.4f} |")
    L.append("\n## Lopputulosten jakauma (±1·A)\n\n| Tyyppi | tavoite | stop | aikaraja | epäselvä | vertailun tavoiteosuus |\n|---|---|---|---|---|---|")
    for typ in TYYPIT:
        sel = [r for r in rows if r["tyyppi"] == typ]
        if not sel:
            continue
        c = defaultdict(int)
        for r in sel:
            c[r["k1_tulos"]] += 1
        ct = st.mean(r["k1_vertailu_tavoite_osuus"] for r in sel if r["k1_vertailu_tavoite_osuus"] is not None)
        L.append(f"| {typ} | {c['tavoite']} | {c['stop']} | {c['aikaraja']} | {c['epäselvä']} | {ct:.1%} |")
    L.append("\nTulokset kertovat vain ajoituksesta ennen kuluja. Kannattavuus kulujen jälkeen arvioidaan erikseen (vaihe 2).")
    with open(a.tulos + "_raportti.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nTallennettu: {a.tulos}_raportti.md, {a.tulos}_signaalit.csv")


if __name__ == "__main__":
    main()
