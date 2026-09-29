"""Paperikauppaversioiden arviointi epävarmuuksineen.

Lähteet (yksi tai useampi):
    --trades logs/kaupat_v1.1.jsonl logs/kaupat_v2.jsonl   # live-paperitilien kauppalokit
    --railway-log railway_logs.txt                         # Railwayn lokivienti (rivit KAUPPA_JSON …)
    --backtest-start 2026-09-29T19:30 --days 28 --rules v1.1,v2 [--symbols …]
                                                           # sama jakso historiatestinä (ristiintarkistus)
    --start / --end                                        # arviointijakso (UTC); muuten kaupoista

Epävarmuus (ks. docs/SAANNOT_v2.md kohta 6):
  * Kaupat eivät ole toisistaan riippumattomia: saman päivän / saman markkinatilan kaupat
    korreloivat, ja tappiorajat kytkevät peräkkäiset kaupat toisiinsa. Siksi luottamusvälit
    lasketaan LOHKOBOOTSTRAPILLA:
      - ensisijainen: päivälohkot (kalenteripäivät, myös kauppattomat, peräkkäisinä 3 päivän
        lohkoina, kehämäinen). Keskiarvo per kauppa = Σ tulos / Σ kauppoja otospäivistä.
      - toissijainen: kauppajono aikajärjestyksessä, lohkon pituus ⌈n^(1/3)⌉.
    Tulkinnassa käytetään näistä VAROVAISEMPAA (leveämpää) väliä.
  * Versioiden ero lasketaan PARITETTUNA päivälohkobootstrapilla (sama jakso, samat päivät).

Tulkinta – n ≥ 30 on vain alaraja tulkinnalle, ei riittävä näyttö:
  * n < 30 tai kauppapäiviä < 10              -> KESKENERÄINEN NÄYTTÖ
  * varovaisen välin yläraja < 0              -> NÄYTTÖ TAPPIOLLISUUDESTA
  * varovaisen välin alaraja > 0 JA molemmat jakson puoliskot positiivisia JA yksikään päivä ei
    tuota yli 50 % nettovoitosta              -> ALUSTAVA NÄYTTÖ VOITOLLISUUDESTA (ei hyväksyntä;
                                                 vaatii toiston uudella, lukitsemattomalla jaksolla)
  * muuten                                    -> EI NÄYTTÖÄ SUUNTAAN TAI TOISEEN
Mittari: nettotulos / riskibudjetti per kauppa (kaikki toteutuneet kulut mukana).
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics as st
from collections import defaultdict
from datetime import datetime, timezone

MIN_N = 30
MIN_DAYS = 10
DAY_BLOCK = 3
BOOT = 10_000
DAY = 86_400_000


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def ms(s: str) -> int:
    return int(datetime.strptime(s, "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc).timestamp() * 1000)


def day_table(trades: list[dict], d0: int, d1: int) -> list[tuple[float, int]]:
    """[(tulos-summa, kauppamäärä)] jokaiselle päivälle d0..d1 (sulkupäivän mukaan)."""
    t = [[0.0, 0] for _ in range(d1 - d0 + 1)]
    for x in trades:
        d = ms(x["exit_time"]) // DAY - d0
        if 0 <= d < len(t):
            t[d][0] += x.get("budget_multiple", 0.0)
            t[d][1] += 1
    return [(a, b) for a, b in t]


def _block_idx(n: int, b: int, rnd: random.Random) -> list[int]:
    out = []
    while len(out) < n:
        s = rnd.randrange(n)
        out += [(s + k) % n for k in range(b)]
    return out[:n]


def day_block_ci(days: list[tuple[float, int]], seed: int = 1) -> tuple[float, float]:
    n = len(days)
    if n < 2 or sum(c for _, c in days) < 2:
        return (float("-inf"), float("inf"))
    rnd = random.Random(seed)
    vals = []
    for _ in range(BOOT):
        idx = _block_idx(n, min(DAY_BLOCK, n), rnd)
        s = sum(days[i][0] for i in idx)
        c = sum(days[i][1] for i in idx)
        if c:
            vals.append(s / c)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1])


def trade_block_ci(xs: list[float], seed: int = 3) -> tuple[float, float]:
    n = len(xs)
    if n < 2:
        return (float("-inf"), float("inf"))
    b = max(2, math.ceil(n ** (1 / 3)))
    rnd = random.Random(seed)
    vals = sorted(sum(xs[i] for i in _block_idx(n, b, rnd)) / n for _ in range(BOOT))
    return (vals[int(0.025 * BOOT)], vals[int(0.975 * BOOT) - 1])


def paired_day_diff_ci(da: list[tuple[float, int]], db: list[tuple[float, int]], seed: int = 5):
    n = len(da)
    rnd = random.Random(seed)
    vals = []
    for _ in range(BOOT):
        idx = _block_idx(n, min(DAY_BLOCK, n), rnd)
        ca, cb = sum(da[i][1] for i in idx), sum(db[i][1] for i in idx)
        if ca and cb:
            vals.append(sum(db[i][0] for i in idx) / cb - sum(da[i][0] for i in idx) / ca)
    if len(vals) < 100:
        return (float("-inf"), float("inf"))
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1])


def lag1(xs: list[float]) -> float:
    if len(xs) < 3:
        return float("nan")
    m = st.mean(xs)
    num = sum((xs[i] - m) * (xs[i - 1] - m) for i in range(1, len(xs)))
    den = sum((x - m) ** 2 for x in xs)
    return num / den if den else float("nan")


def analyse(name: str, trades: list[dict], d0: int, d1: int, start_equity: float = 10_000.0) -> dict:
    trades = sorted(trades, key=lambda t: t["exit_time"])
    n = len(trades)
    xs = [t.get("budget_multiple", 0.0) for t in trades]
    net = [t["net_pnl"] for t in trades]
    days = day_table(trades, d0, d1)
    active = sum(1 for _, c in days if c)
    lo_d, hi_d = day_block_ci(days)
    lo_t, hi_t = trade_block_ci(xs)
    lo, hi = min(lo_d, lo_t), max(hi_d, hi_t)
    wins = sum(1 for x in net if x > 0)
    wl, wh = wilson(wins, n)
    eq = peak = start_equity
    mdd = 0.0
    for x in net:
        eq += x
        peak = max(peak, eq)
        mdd = max(mdd, 1 - eq / peak)
    half = len(days) // 2
    h1 = [d for d in days[:half]]
    h2 = [d for d in days[half:]]
    m1 = sum(a for a, _ in h1) / max(1, sum(c for _, c in h1))
    m2 = sum(a for a, _ in h2) / max(1, sum(c for _, c in h2))
    pos_total = sum(a for a, _ in days if a > 0)
    top_day = max((a for a, _ in days), default=0.0)
    top_share = top_day / sum(a for a, _ in days) if sum(a for a, _ in days) > 0 else float("nan")

    if n < MIN_N or active < MIN_DAYS:
        v = f"KESKENERÄINEN NÄYTTÖ (n = {n}, kauppapäiviä {active}; vaaditaan ≥ {MIN_N} ja ≥ {MIN_DAYS})"
    elif hi < 0:
        v = "NÄYTTÖ TAPPIOLLISUUDESTA"
    elif lo > 0 and m1 > 0 and m2 > 0 and top_share <= 0.5:
        v = "ALUSTAVA NÄYTTÖ VOITOLLISUUDESTA – ei hyväksyntä; vaatii toiston uudella jaksolla"
    else:
        v = "EI NÄYTTÖÄ SUUNTAAN TAI TOISEEN"

    print(f"\n=== {name} ===")
    print(f"Kauppoja {n}, kauppapäiviä {active}/{len(days)} | voittoja {wins} "
          f"({(wins / n if n else 0):.0%}, Wilson 95 % {wl:.0%}–{wh:.0%}; olettaa riippumattomuuden)")
    print(f"Nettotulos {sum(net):+,.2f} USD ({sum(net) / start_equity:+.2%}) | suurin pudotus {mdd:.2%}")
    if n:
        costs = sum(t["fees"] + t["spread_slippage_est"] + t["funding"] for t in trades)
        pre = sum(t["gross_pnl"] + t["spread_slippage_est"] for t in trades)
        print(f"Ennen kuluja {pre:+,.2f} USD | toteutuneet kulut {costs:,.2f} USD "
              f"(palkkiot + spread/liukuma + toteutunut funding)")
        print(f"Keskim. {st.mean(xs):+.3f} x riskibudjetti per kauppa")
        print(f"  95 % LV päivälohkobootstrap ({DAY_BLOCK} pv):  {lo_d:+.3f} … {hi_d:+.3f}")
        print(f"  95 % LV kauppalohkobootstrap (b={max(2, math.ceil(n ** (1 / 3)))}): {lo_t:+.3f} … {hi_t:+.3f}")
        print(f"  varovaisempi väli tulkintaan:        {lo:+.3f} … {hi:+.3f}")
        print(f"Peräkkäisten kauppojen autokorrelaatio (viive 1): {lag1(xs):+.2f}")
        print(f"Jakson puoliskot: 1. {m1:+.3f}, 2. {m2:+.3f} x budjetti/kauppa | "
              f"suurimman päivän osuus nettotuloksesta: "
              f"{'–' if math.isnan(top_share) else f'{top_share:.0%}'}")
        by = defaultdict(list)
        for t in trades:
            by[t["close_reason"].split(" (")[0]].append(t["net_pnl"])
        print("Sulkemissyyt: " + " | ".join(f"{k} {len(v_)} kpl {sum(v_):+,.2f}" for k, v_ in sorted(by.items())))
    print(f"Tulkinta: {v}")
    return {"days": days, "n": n}


def load_jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def load_railway(path: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    seen = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            i = line.find("KAUPPA_JSON ")
            if i < 0:
                continue
            t = json.loads(line[i + len("KAUPPA_JSON "):])
            k = (t["ruleset"], t["id"], t["symbol"])
            if k not in seen:
                seen.add(k)
                out[t["ruleset"]].append(t)
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Paperikauppaversioiden arviointi")
    ap.add_argument("--trades", nargs="*", default=[])
    ap.add_argument("--railway-log")
    ap.add_argument("--backtest-start")
    ap.add_argument("--days", type=float, default=28)
    ap.add_argument("--rules", default="v1.1,v2")
    ap.add_argument("--symbols")
    ap.add_argument("--start", help="arviointijakson alku UTC (oletus: ensimmäinen kauppa)")
    ap.add_argument("--end", help="arviointijakson loppu UTC (oletus: viimeinen kauppa)")
    a = ap.parse_args(argv)

    sets: dict[str, list[dict]] = {}
    for p in a.trades:
        ts_ = load_jsonl(p)
        if ts_:
            sets[f"{ts_[0]['ruleset']} (kauppaloki {p})"] = ts_
    if a.railway_log:
        for v, ts_ in load_railway(a.railway_log).items():
            sets[f"{v} (live, Railway-loki)"] = ts_
    if a.backtest_start:
        from dataclasses import asdict
        from . import backtest
        for v in a.rules.split(","):
            args = ["--rules", v, "--start", a.backtest_start, "--days", str(a.days), "--quiet"]
            if a.symbols:
                args += ["--symbols", a.symbols]
            eng = backtest.main(args)
            sets[f"{v} (historiatesti samalta jaksolta)"] = [asdict(t) for t in eng.trades]
        a.start = a.start or a.backtest_start

    all_t = [t for ts_ in sets.values() for t in ts_]
    if not all_t:
        print("Ei kauppoja arvioitavaksi.")
        return
    from .backtest import parse_date
    d0 = (parse_date(a.start) if a.start else min(ms(t["exit_time"]) for t in all_t)) // DAY
    d1 = (parse_date(a.end) - 1 if a.end else max(ms(t["exit_time"]) for t in all_t)) // DAY

    print("Mittari: nettotulos / riskibudjetti per kauppa, kaikki toteutuneet kulut mukana.")
    print(f"Epävarmuus: lohkobootstrap (päivät {DAY_BLOCK} pv lohkoina + kauppajono), {BOOT} otosta. "
          f"n ≥ {MIN_N} on vain tulkinnan alaraja, ei riittävä näyttö.")
    res = {name: analyse(name, ts_, d0, d1) for name, ts_ in sets.items()}
    names = list(res)
    if len(names) >= 2:
        a_, b_ = names[0], names[1]
        lo, hi = paired_day_diff_ci(res[a_]["days"], res[b_]["days"])
        print(f"\nEro ({b_} − {a_}) per kauppa, paritettu päivälohkobootstrap: 95 % LV {lo:+.3f} … {hi:+.3f}")
        if min(res[a_]["n"], res[b_]["n"]) < MIN_N or lo <= 0 <= hi:
            print("Versioiden välillä ei voi todeta eroa.")


if __name__ == "__main__":
    main()
