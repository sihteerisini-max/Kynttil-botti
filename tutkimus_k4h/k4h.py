"""Tutkimus K4H: 15m K-signaalit (aj1-kaanto) ja kiinteä 4 h pitoaika.
Suunnitelma: docs/TUTKIMUS_K4H_SUUNNITELMA.md (lukittu ennen laskelmia). Vain tutkimus ja paperilaskenta.
"""
from __future__ import annotations

import csv
import json
import math
import os
import random
import statistics as st
import time
from collections import defaultdict

from data15 import (BASE, DAY, STEP15, aggregate, charts, http_json, iso, ms, read_csv, same, to_candles,
                    write_csv)
from kt.paper import PaperEngine
from kt.strategy import RULESETS

# ---------------------------------------------------------------- LUKITUT ASETUKSET
VERSIO = "aj1-kaanto"
MARKKINAT = ["PF_XBTUSD", "PF_ETHUSD", "PF_SOLUSD", "PF_DOGEUSD", "PF_XRPUSD", "PF_PEPEUSD"]
H = 16                    # pitoaika 16 kynttilää = 4 h; sulku kynttilän i+17 avauksessa
AVG = 20
CONTROLS = 50
EXCLUDE = 16
BOOT = 10_000
SEED = 20261008
ALPHA = 0.05
MIN_MARKETS, MIN_N, MIN_DAYS = 4, 300, 60
FEE, SLIP, HS_MIN = 0.0005, 0.0002, 0.00005
FUNDING_VAROVAINEN = 0.0001        # 0,01 % per kauppa, kun funding-historiaa ei ole
HOUR = 3_600_000
N_USD = 1000.0
JAKSOT = {
    "KEHITYS": {"alku": ms("2025-01-01"), "loppu": ms("2026-07-01"), "puoli": ms("2025-10-01"),
                "lataus_alku": ms("2024-12-29"), "lataus_loppu": ms("2026-07-01T06:00")},
    "VAHVISTUS": {"alku": ms("2024-01-01"), "loppu": ms("2024-10-01"), "puoli": ms("2024-05-17"),
                  "lataus_alku": ms("2023-12-29"), "lataus_loppu": ms("2024-10-01T06:00")},
}
# datan laatu (kuten Tutkimus 15M)
MIN_KAUPALLISET, MAX_PUUTTUVAT, MIN_TASMAYS, OTOS, NOLLA_MAX = 0.98, 0.005, 0.99, 200, 300


def vaadittu(m: int) -> int:
    return math.ceil(2 * m / 3)


# ---------------------------------------------------------------- signaalit ja mittarit
def avg_range_before(cs) -> list:
    out = [None] * len(cs)
    for i in range(AVG, len(cs)):
        out[i] = sum(cs[k].range for k in range(i - AVG, i)) / AVG
    return out


def signals_for(cs, version: str = VERSIO) -> list[tuple[int, str, float]]:
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


def move(cs, i: int, side: str, A: float | None) -> float | None:
    """Suunnattu muutos avauksesta (i+1 avaus) sulkuun (i+17 avaus) A-yksiköissä."""
    if A is None or A <= 0 or i + H + 1 >= len(cs):
        return None
    sg = 1 if side == "long" else -1
    return sg * (cs[i + H + 1].open - cs[i + 1].open) / A


def controls(cs, A, i: int, side: str, rnd: random.Random, by_day: dict) -> list[float]:
    cand = [j for j in by_day.get(cs[i].open_time // DAY, []) if abs(j - i) >= EXCLUDE]
    out = []
    tries = 0
    while cand and len(out) < CONTROLS and tries < 20 * CONTROLS:
        tries += 1
        j = cand[rnd.randrange(len(cand))]
        v = move(cs, j, side, A[j])
        if v is not None:
            out.append(v)
    return out


def select_trades(signals: list[tuple[int, str]]) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """Yksi positio per markkina. signals: [(i, side)] aikajärjestyksessä yhdeltä markkinalta.
    Positio avautuu i+1:ssä ja sulkeutuu i+17:n avauksessa; uusi voi avautua aikaisintaan i+17:ssä."""
    taken, skipped = [], []
    free_from = -1
    for i, side in sorted(signals):
        if i + 1 >= free_from:
            taken.append((i, side))
            free_from = i + 1 + H
        else:
            skipped.append((i, side))
    return taken, skipped


def funding_cost(side: str, t_entry: int, fund: dict[int, float]) -> tuple[float, bool]:
    """Pitoajan funding suhteessa nimellisarvoon (+ = kulu). Long maksaa positiivisella korolla."""
    h0 = t_entry - t_entry % HOUR
    rates = [fund.get(h0 + k * HOUR) for k in range(1, 5)]
    if any(r is None for r in rates):
        return FUNDING_VAROVAINEN, False
    sg = 1 if side == "long" else -1
    return sg * sum(rates), True


def trade_net(cs, i: int, side: str, hs: float, fund: dict[int, float], funding_zero: bool = False) -> dict:
    sg = 1 if side == "long" else -1
    e, x = cs[i + 1].open, cs[i + H + 1].open
    ef = e * (1 + sg * (hs + SLIP))
    xf = x * (1 - sg * (hs + SLIP))
    gross_mid = sg * (x - e) / e
    gross_fill = sg * (xf - ef) / ef
    fees = FEE * (ef + xf) / ef
    fcost, actual = (0.0, True) if funding_zero else funding_cost(side, cs[i + 1].open_time, fund)
    return {"brutto": gross_mid, "spread_liukuma": gross_mid - gross_fill, "palkkiot": fees, "funding": fcost,
            "netto": gross_fill - fees - fcost, "funding_todellinen": actual,
            "puuttuvia_pidossa": sum(1 for k in range(i + 1, i + H + 1) if cs[k].volume == 0 and cs[k].high == cs[k].low)}


# ---------------------------------------------------------------- tilastot
def cluster_boot(by_cluster: dict, rnd: random.Random, boot: int = BOOT):
    keys = list(by_cluster)
    allv = [v for k in keys for v in by_cluster[k]]
    if len(keys) < 2 or not allv:
        return (st.mean(allv) if allv else float("nan"), float("-inf"), float("inf"), 1.0, 1.0)
    m = st.mean(allv)
    S = [sum(by_cluster[k]) for k in keys]
    N = [len(by_cluster[k]) for k in keys]
    rng = range(len(keys))
    bs = []
    for _ in range(boot):
        idx = rnd.choices(rng, k=len(keys))
        n = sum(map(N.__getitem__, idx))
        bs.append(sum(map(S.__getitem__, idx)) / n if n else 0.0)
    bs.sort()
    lo, hi = bs[int(0.025 * boot)], bs[int(0.975 * boot) - 1]
    le = sum(1 for x in bs if x <= 0) / boot
    ge = sum(1 for x in bs if x >= 0) / boot
    return m, lo, hi, min(1.0, 2 * min(le, ge)), le      # (ka, ala, ylä, p kaksisuunt., p yksisuunt. H0: ≤ 0)


def holm(ps: dict) -> dict:
    items = sorted(ps.items(), key=lambda x: x[1])
    m, out, prev = len(items), {}, 0.0
    for r, (k, p) in enumerate(items):
        adj = min(1.0, max(prev, (m - r) * p))
        out[k], prev = adj, adj
    return out


def ehto(p_holm, m, lo_ok, h1, h2, pos, need) -> bool:
    return (p_holm < ALPHA and m > 0 and lo_ok and h1 is not None and h2 is not None and h1 > 0 and h2 > 0
            and pos >= need)


def paatos(n_mukana: int, n_trades: int, n_days: int, h1_ok: bool, h2_ok: bool) -> str:
    if n_mukana < MIN_MARKETS:
        return f"AVOIN (mukana {n_mukana} < {MIN_MARKETS} markkinaa)"
    if n_trades < MIN_N or n_days < MIN_DAYS:
        return f"AINEISTO EI RIITÄ (kauppoja {n_trades}, päiviä {n_days}; vaaditaan ≥ {MIN_N} ja ≥ {MIN_DAYS})"
    if h1_ok and h2_ok:
        return "JATKOON ETEENPÄIN KERÄTTÄVÄÄN PAPERITESTIIN (ei lupa oikeaan kaupankäyntiin)"
    if h1_ok:
        return "SUUNTAVAIKUTUS SÄILYI, MUTTA EI KATA KULUJA – hylätään kaupankäyntistrategiana"
    return "EI NÄYTTÖÄ – hylätään"


# ---------------------------------------------------------------- data ja eheys
def lataa(out_dir: str, jakso: str, symbols: list[str], get=http_json, log=print) -> dict:
    J = JAKSOT[jakso]
    d_dir = os.path.join(out_dir, jakso.lower())
    os.makedirs(d_dir, exist_ok=True)
    res = {"jakso": jakso, "markkinat": {}}
    for s in symbols:
        raw = charts(s, "15m", J["lataus_alku"], J["lataus_loppu"], get)
        _, missing = to_candles(s, raw, J["lataus_alku"], J["lataus_loppu"], STEP15)
        for d in sorted({t - t % DAY for t in missing}):
            for t, c in charts(s, "15m", d, min(d + DAY, J["lataus_loppu"]), get).items():
                raw.setdefault(t, c)
        _, missing = to_candles(s, raw, J["lataus_alku"], J["lataus_loppu"], STEP15)
        write_csv(os.path.join(d_dir, f"{s}_15m.csv"), raw)
        slots = list(range(J["alku"], J["loppu"], STEP15))
        traded = sum(1 for t in slots if t in raw and raw[t]["volume"] > 0)
        miss = [t for t in missing if J["alku"] <= t < J["loppu"]]
        zeros = [t for t in slots if t in raw and raw[t]["volume"] == 0]
        rnd = random.Random(f"{SEED}-{jakso}-{s}")
        pool = [t for t in slots if t in raw]
        ok, bad = 0, []
        sample = rnd.sample(pool, min(OTOS, len(pool)))
        for t in sample:
            m = charts(s, "1m", t, t + STEP15, get)
            agg = aggregate([m[k] for k in sorted(m)])
            if agg is not None and len(m) == 15 and same(agg, raw[t]):
                ok += 1
            else:
                bad.append(iso(t))
        zsel = zeros if len(zeros) <= NOLLA_MAX else rnd.sample(zeros, NOLLA_MAX)
        z_ok = sum(1 for t in zsel if all(c["volume"] == 0 for c in charts(s, "1m", t, t + STEP15, get).values()))
        m_ = {"kaupalliset": traded / len(slots), "puuttuvat": len(miss), "puuttuvat_osuus": len(miss) / len(slots),
              "nollia": len(zeros), "tasmaa": ok, "otos": len(sample), "poikkeamat": bad[:10],
              "nollia_tarkistettu": len(zsel), "nollia_aitoja": z_ok}
        m_["mukana"] = (m_["kaupalliset"] >= MIN_KAUPALLISET and m_["puuttuvat_osuus"] <= MAX_PUUTTUVAT
                        and (ok / len(sample) if sample else 0) >= MIN_TASMAYS)
        res["markkinat"][s] = m_
        log(f"{jakso} lataus {s}: kaupallisia {m_['kaupalliset']:.4f}, puuttuvia {len(miss)}, täsmäys {ok}/{len(sample)}, "
            f"nollat {z_ok}/{len(zsel)}, mukana={m_['mukana']}")
    # funding-historia (saatavilla vain viimeiseltä noin vuodelta)
    for s in symbols:
        from datetime import datetime
        rows = get(f"{BASE}/derivatives/api/v4/historicalfundingrates?symbol={s}").get("rates", [])
        f = {}
        for r in rows:
            t = int(datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")).timestamp() * 1000)
            if J["lataus_alku"] <= t < J["lataus_loppu"] + DAY:
                f[t] = float(r.get("relativeFundingRate") or 0.0)
        with open(os.path.join(d_dir, f"{s}_funding.json"), "w") as fh:
            json.dump(f, fh)
        res["markkinat"][s]["funding_tunteja"] = len(f)
    # spreadit nyt
    obs = {s: [] for s in symbols}
    for k in range(20):
        for x in get(f"{BASE}/derivatives/api/v3/tickers").get("tickers", []):
            if x.get("symbol") in obs and x.get("bid") and x.get("ask"):
                b, a = float(x["bid"]), float(x["ask"])
                if a > b > 0:
                    obs[x["symbol"]].append((a - b) / 2 / ((a + b) / 2))
        if k < 19:
            time.sleep(15)
    res["spread"] = {s: (st.median(v) if v else None) for s, v in obs.items()}
    res["spread_mitattu"] = iso(int(time.time() * 1000))
    res["mukana"] = [s for s in symbols if res["markkinat"][s]["mukana"]]
    with open(os.path.join(d_dir, "eheys.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    return res


# ---------------------------------------------------------------- analyysi
def analysoi(out_dir: str, jakso: str, log=print) -> dict:
    J = JAKSOT[jakso]
    d_dir = os.path.join(out_dir, jakso.lower())
    with open(os.path.join(d_dir, "eheys.json"), encoding="utf-8") as f:
        eh = json.load(f)
    mukana = eh["mukana"]
    n_m = len(mukana)
    hs = {s: max(eh["spread"].get(s) or 0.0, HS_MIN) for s in eh["markkinat"]}
    rnd = random.Random(SEED)
    sig_rows, trades, skips = [], [], 0
    for s in mukana:
        cs, _ = to_candles(s, read_csv(os.path.join(d_dir, f"{s}_15m.csv")), J["lataus_alku"], J["lataus_loppu"], STEP15)
        with open(os.path.join(d_dir, f"{s}_funding.json")) as fh:
            fund = {int(k): v for k, v in json.load(fh).items()}
        A = avg_range_before(cs)
        by_day = defaultdict(list)
        for i, c in enumerate(cs):
            if J["alku"] <= c.open_time < J["loppu"] and A[i] and i + H + 1 < len(cs):
                by_day[c.open_time // DAY].append(i)
        sigs = []
        for i, side, A_bot in signals_for(cs):
            if not (J["alku"] <= cs[i].open_time < J["loppu"]) or i + H + 1 >= len(cs):
                continue
            if A[i] is None or abs(A[i] - A_bot) > 1e-9 * max(1.0, abs(A_bot)):
                raise SystemExit(f"A-ristiriita {s} {iso(cs[i].open_time)}")
            v = move(cs, i, side, A[i])
            ctr = controls(cs, A, i, side, rnd, by_day)
            sig_rows.append({"markkina": s, "suunta": side, "t": cs[i].open_time, "paiva": cs[i].open_time // DAY,
                             "d16": v, "vertailu": st.mean(ctr) if ctr else None})
            sigs.append((i, side))
        taken, skipped = select_trades(sigs)
        skips += len(skipped)
        for i, side in taken:
            x = trade_net(cs, i, side, hs[s], fund)
            x0 = trade_net(cs, i, side, hs[s], fund, funding_zero=True)
            trades.append({"markkina": s, "suunta": side, "avaus_utc": iso(cs[i + 1].open_time), "t": cs[i].open_time,
                           "paiva": cs[i].open_time // DAY, "sulku_t": cs[i + H + 1].open_time,
                           "avaushinta": cs[i + 1].open, "sulkuhinta": cs[i + H + 1].open, **x, "netto_f0": x0["netto"]})
        log(f"{jakso} {s}: signaaleja {len(sigs)}, kauppoja {len(taken)}, ohitettu {len(skipped)}")
    # tallenna kaupat
    if trades:
        with open(os.path.join(d_dir, "kaupat.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(trades[0].keys()))
            w.writeheader()
            w.writerows(trades)
    rb = random.Random(SEED + 1)
    res, p1, p2 = {}, {}, {}
    for side in ("long", "short"):
        S = [r for r in sig_rows if r["suunta"] == side and r["vertailu"] is not None]
        byc = defaultdict(list)
        for r in S:
            byc[r["paiva"]].append(r["d16"] - r["vertailu"])
        m1, lo1, hi1, pt1, _ = cluster_boot(byc, rb)
        T = [t for t in trades if t["suunta"] == side]
        byt = defaultdict(list)
        for t in T:
            byt[t["paiva"]].append(t["netto"])
        m2, lo2, hi2, _, pone = cluster_boot(byt, rb)
        res[side] = {"S": S, "T": T, "d16": (m1, lo1, hi1, pt1), "netto": (m2, lo2, hi2, pone), "n_sig": len(S),
                     "n_trades": len(T), "days_sig": len(byc), "days_trades": len(byt)}
        p1[side], p2[side] = pt1, pone
    h1p, h2p = holm(p1), holm(p2)
    need = vaadittu(n_m)
    L = [f"# Tutkimus K4H – {jakso}\n",
         f"Suunnitelma `docs/TUTKIMUS_K4H_SUUNNITELMA.md` (lukittu ennen laskelmia). Jakso {iso(J['alku'])} – {iso(J['loppu'])} UTC, "
         f"15m K-signaalit (aj1-kaanto), pitoaika 16 kynttilää (4 h), ei stoppia/tavoitetta, yksi positio per markkina, siemen {SEED}.\n"]
    if jakso == "KEHITYS":
        L.append("> **KEHITYSANALYYSI – ei näyttöä.** Data on jo käytetty Tutkimus 15M:ssä, jossa 4 h -havainto tehtiin. "
                 "Päätössääntöjen tulokset alla ovat vain kuvaus siitä, miltä lukittu sääntö näyttää kehitysdatalla.\n")
    L.append(f"Mukana: **{', '.join(mukana)}** ({n_m}/{len(eh['markkinat'])}). Spreadit mitattu {eh.get('spread_mitattu')} UTC.\n")
    L.append("## Ensisijaiset testit\n")
    L.append("| Ryhmä | Signaaleja | D16 (A) | 95 % LV | Holm-p | Puoliskot | Markkinoita > 0 | H1 | Kauppoja | Netto/kauppa | 95 % LV | Holm-p (yksisuunt.) | Puoliskot | Markkinoita > 0 | H2 | **Päätös** |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    out = {}
    for side in ("long", "short"):
        r = res[side]
        m1, lo1, hi1, _ = r["d16"]
        m2, lo2, hi2, _ = r["netto"]
        hv1 = [st.mean([x["d16"] - x["vertailu"] for x in r["S"] if (x["t"] < J["puoli"]) == first] or [float("nan")]) for first in (True, False)]
        hv2 = [st.mean([x["netto"] for x in r["T"] if (x["t"] < J["puoli"]) == first] or [float("nan")]) for first in (True, False)]
        bm1, bm2 = defaultdict(list), defaultdict(list)
        for x in r["S"]:
            bm1[x["markkina"]].append(x["d16"] - x["vertailu"])
        for x in r["T"]:
            bm2[x["markkina"]].append(x["netto"])
        pos1 = sum(1 for v in bm1.values() if st.mean(v) > 0)
        pos2 = sum(1 for v in bm2.values() if st.mean(v) > 0)
        ok1 = ehto(h1p[side], m1, True, hv1[0], hv1[1], pos1, need)
        ok2 = ehto(h2p[side], m2, lo2 > 0, hv2[0], hv2[1], pos2, need)
        dec = paatos(n_m, r["n_trades"], r["days_trades"], ok1, ok2)
        out[side] = {"d16": r["d16"], "netto": r["netto"], "h1": ok1, "h2": ok2, "paatos": dec, "n_sig": r["n_sig"], "n_trades": r["n_trades"]}
        L.append(f"| K {side} | {r['n_sig']} | {m1:+.4f} | {lo1:+.4f} … {hi1:+.4f} | {h1p[side]:.4f} | {hv1[0]:+.3f} / {hv1[1]:+.3f} | {pos1}/{len(bm1)} | "
                 f"{'kyllä' if ok1 else 'ei'} | {r['n_trades']} | {m2:+.4%} | {lo2:+.4%} … {hi2:+.4%} | {h2p[side]:.4f} | "
                 f"{hv2[0]:+.4%} / {hv2[1]:+.4%} | {pos2}/{len(bm2)} | {'kyllä' if ok2 else 'ei'} | **{dec}** |")
    L.append(f"\nVaadittu markkinamäärä ⌈2m/3⌉ = {need}. D16 = signaalin suunnattu 4 h muutos − 50 satunnaisen hetken keskiarvo (A-yksiköissä, ei kuluja). "
             "Netto = tuotto % nimellisarvosta kaikkien kulujen jälkeen (toteutetut kaupat).\n")
    # kulut ja kuvaus
    L.append("## Kulut ja bruttotuotto (kuvaileva)\n")
    L.append("| Ryhmä | Kauppoja | Brutto ka (ennen kuluja) | Spread + liukuma | Palkkiot | Funding | Netto ka | Netto, funding = 0 | Osuma (netto > 0) | Funding todellinen / varovainen |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for side in ("long", "short"):
        T = res[side]["T"]
        if not T:
            continue
        mean = lambda k: st.mean(t[k] for t in T)
        fa = sum(1 for t in T if t["funding_todellinen"])
        L.append(f"| K {side} | {len(T)} | {mean('brutto'):+.4%} | {mean('spread_liukuma'):.4%} | {mean('palkkiot'):.4%} | {mean('funding'):+.4%} | "
                 f"{mean('netto'):+.4%} | {mean('netto_f0'):+.4%} | {sum(t['netto'] > 0 for t in T) / len(T):.1%} | {fa} / {len(T) - fa} |")
    L.append("\n| Markkina | ½ spread | Kauppoja | Brutto ka | Netto ka |\n|---|---|---|---|---|")
    for s in mukana:
        T = [t for t in trades if t["markkina"] == s]
        if T:
            L.append(f"| {s} | {hs[s]:.4%} | {len(T)} | {st.mean(t['brutto'] for t in T):+.4%} | {st.mean(t['netto'] for t in T):+.4%} |")
    # salkku
    ev = sorted(trades, key=lambda t: t["sulku_t"])
    eq, pk, dd, dd_t = 0.0, 0.0, 0.0, None
    for t in ev:
        eq += t["netto"] * N_USD
        pk = max(pk, eq)
        if pk - eq > dd:
            dd, dd_t = pk - eq, t["sulku_t"]
    gross_usd = sum(t["brutto"] for t in trades) * N_USD
    cost_usd = sum(t["spread_liukuma"] + t["palkkiot"] + t["funding"] for t in trades) * N_USD
    L.append(f"\n## Salkku (N = {N_USD:,.0f} $ per kauppa, vertailupääoma 6 × N = {6 * N_USD:,.0f} $)\n")
    L.append(f"* Kauppoja {len(trades)} (long {res['long']['n_trades']}, short {res['short']['n_trades']}); päällekkäisyyden vuoksi ohitettuja signaaleja {skips}.")
    L.append(f"* Brutto {gross_usd:+,.2f} $, kulut {cost_usd:,.2f} $, **netto {eq:+,.2f} $**.")
    L.append(f"* Suurin pudotus {dd:,.2f} $ ({dd / (6 * N_USD):.2%} vertailupääomasta){' – ' + iso(dd_t) if dd_t else ''}.")
    L.append(f"* Kauppoja, joiden pidossa kaupattomia/puuttuvia 15m-kynttilöitä: {sum(1 for t in trades if t['puuttuvia_pidossa'])}.")
    L.append("\nKaikki luvut ovat paperilaskentaa historiadatalla. Toimeksiantoja ei lähetetty.")
    with open(os.path.join(d_dir, "raportti.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    summary = {"jakso": jakso, "mukana": mukana, "ryhmat": out, "salkku": {"netto_usd": eq, "brutto_usd": gross_usd,
               "kulut_usd": cost_usd, "max_dd_usd": dd, "kauppoja": len(trades), "ohitettu": skips}}
    with open(os.path.join(d_dir, "tulos.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, default=str)
    log(f"{jakso} analyysi valmis")
    return summary
