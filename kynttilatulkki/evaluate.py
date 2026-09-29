"""Paperikauppaversioiden arviointi epävarmuuksineen.

Lähteet (yksi tai useampi):
    --trades logs/kaupat_v1.1.jsonl logs/kaupat_v2.jsonl   # live-paperitilien kauppalokit
    --railway-log railway_logs.txt                         # Railwayn lokivienti (rivit KAUPPA_JSON …)
    --backtest-start 2026-09-29T19:30 --days 28 --rules v1.1,v2 [--symbols …]
                                                           # sama jakso historiatestinä (ristiintarkistus)

Tulkintasäännöt (lukittu docs/SAANNOT_v2.md, kohta 6) – eivät riipu tuloksesta:
  * n < 30                                  -> KESKENERÄINEN NÄYTTÖ
  * n ≥ 30 ja 95 % luottamusvälin alaraja > 0 -> ALUSTAVA NÄYTTÖ VOITOLLISUUDESTA (ei hyväksyntä
                                               oikealle rahalle; vaatii uuden jakson toiston)
  * n ≥ 30 ja yläraja < 0                   -> NÄYTTÖ TAPPIOLLISUUDESTA
  * muuten                                  -> EI NÄYTTÖÄ SUUNTAAN TAI TOISEEN
Mittari: nettotulos / riskibudjetti per kauppa (kaikki kulut mukana).
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics as st
from collections import defaultdict

MIN_N = 30
BOOT = 10_000


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def boot_mean(xs: list[float], seed: int = 1) -> tuple[float, float]:
    if len(xs) < 2:
        return (float("-inf"), float("inf"))
    rnd = random.Random(seed)
    n = len(xs)
    ms = sorted(sum(rnd.choice(xs) for _ in range(n)) / n for _ in range(BOOT))
    return (ms[int(0.025 * BOOT)], ms[int(0.975 * BOOT)])


def boot_diff(a: list[float], b: list[float], seed: int = 2) -> tuple[float, float]:
    if len(a) < 2 or len(b) < 2:
        return (float("-inf"), float("inf"))
    rnd = random.Random(seed)
    ds = sorted(sum(rnd.choice(b) for _ in b) / len(b) - sum(rnd.choice(a) for _ in a) / len(a)
                for _ in range(BOOT))
    return (ds[int(0.025 * BOOT)], ds[int(0.975 * BOOT)])


def verdict(n: int, lo: float, hi: float) -> str:
    if n < MIN_N:
        return f"KESKENERÄINEN NÄYTTÖ (n = {n} < {MIN_N}) – ei johtopäätöksiä, ei hyväksyntää"
    if lo > 0:
        return "ALUSTAVA NÄYTTÖ VOITOLLISUUDESTA – ei vielä hyväksyntä, vaatii toiston uudella jaksolla"
    if hi < 0:
        return "NÄYTTÖ TAPPIOLLISUUDESTA"
    return "EI NÄYTTÖÄ SUUNTAAN TAI TOISEEN – luottamusväli sisältää nollan"


def report(version: str, trades: list[dict], start_equity: float = 10_000.0) -> list[float]:
    n = len(trades)
    xs = [t.get("budget_multiple", 0.0) for t in trades]
    net = [t["net_pnl"] for t in trades]
    wins = sum(1 for x in net if x > 0)
    eq, peak, mdd = start_equity, start_equity, 0.0
    for x in net:
        eq += x
        peak = max(peak, eq)
        mdd = max(mdd, 1 - eq / peak)
    lo, hi = boot_mean(xs)
    wl, wh = wilson(wins, n)
    gp = sum(x for x in net if x > 0)
    gl = -sum(x for x in net if x <= 0)
    print(f"\n=== {version} ===")
    print(f"Kauppoja {n} | voittoja {wins} ({(wins / n if n else 0):.0%}, 95 % LV {wl:.0%}–{wh:.0%})")
    print(f"Nettotulos {sum(net):+,.2f} USD ({sum(net) / start_equity:+.2%}) | suurin pudotus {mdd:.2%} | "
          f"profit factor {(gp / gl) if gl else float('inf'):.2f}")
    if n:
        print(f"Keskim. tulos per kauppa {st.mean(xs):+.3f} x riskibudjetti (95 % bootstrap-LV {lo:+.3f} … {hi:+.3f})")
        costs = sum(t["fees"] + t["spread_slippage_est"] + t["funding"] for t in trades)
        pre = sum(t["gross_pnl"] + t["spread_slippage_est"] for t in trades)
        print(f"Ennen kuluja {pre:+,.2f} USD | kulut {costs:,.2f} USD")
        by = defaultdict(list)
        for t in trades:
            by[t["close_reason"].split(" (")[0]].append(t["net_pnl"])
        print("Sulkemissyyt: " + " | ".join(f"{k} {len(v)} kpl {sum(v):+,.2f}" for k, v in sorted(by.items())))
    print(f"Tulkinta: {verdict(n, lo, hi)}")
    return xs


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
        from . import backtest
        from dataclasses import asdict
        for v in a.rules.split(","):
            args = ["--rules", v, "--start", a.backtest_start, "--days", str(a.days), "--quiet"]
            if a.symbols:
                args += ["--symbols", a.symbols]
            eng = backtest.main(args)
            sets[f"{v} (historiatesti samalta jaksolta)"] = [asdict(t) for t in eng.trades]

    print("Mittari: nettotulos / riskibudjetti per kauppa, kaikki kulut mukana. "
          f"Johtopäätöksiä vasta, kun n ≥ {MIN_N}.")
    xs = {name: report(name, ts_) for name, ts_ in sets.items()}
    names = list(xs)
    if len(names) >= 2:
        a_, b_ = names[0], names[1]
        lo, hi = boot_diff(xs[a_], xs[b_])
        print(f"\nEro ({b_} − {a_}) keskim. tulokseen per kauppa: "
              f"{(st.mean(xs[b_]) - st.mean(xs[a_])) if xs[a_] and xs[b_] else float('nan'):+.3f} "
              f"(95 % LV {lo:+.3f} … {hi:+.3f})")
        if min(len(xs[a_]), len(xs[b_])) < MIN_N or lo <= 0 <= hi:
            print("Versioiden välillä ei voi todeta eroa.")


if __name__ == "__main__":
    main()
