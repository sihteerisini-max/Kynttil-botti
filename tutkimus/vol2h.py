"""Kehitystesti VOL2H: tavoite ja stop kahden tunnin hintavaihtelun mukaan vs. nykyinen malli (aj1).
Suunnitelma: docs/KEHITYSTESTI_VOL2H_SUUNNITELMA.md (lukittu ennen laskentaa). Vain kehitysdata, paperilaskenta.

    python -m tutkimus.vol2h --data-glob "data/PF_*_2026-07-14T0000_2026-09-15T0000.csv" \
        --spread spread.json --funding funding_paiva.json --tulos tutkimus/tulokset/vol2h
"""
from __future__ import annotations

import argparse
import glob
import json
import random
import statistics as st
from collections import defaultdict, deque
from dataclasses import replace

from kynttilatulkki.backtest import parse_date
from kynttilatulkki.paper import PaperEngine
from kynttilatulkki.strategy import RULESETS
from tutkimus.ajoitus import load

DAY = 86_400_000
W = 120                  # 2 h suljettuja 1m-kynttilöitä (signaalikynttilä mukaan lukien)
HMOVE = 15               # pitoaika (= aikaraja 15 kynttilää) -> tyypillinen 15 min liike
COST_MULT = 2.0          # tavoite ≥ 2 × arvioidut kulut
MALLIT = {"NYKYINEN": None, "V1": (1.0, 1.0), "V2": (0.5, 1.0)}   # (tavoite × M, stop × M)
SEED = 20261008
BOOT = 10_000
REF_RISK_USD = 50.0      # 0,5 % × 10 000 $ (vakiopääomavastine)


def ilman_tappiorajoja(version: str):
    """Sama sääntöversio, mutta tilikohtaiset tappiorajat pois (vertailu koko jaksolta)."""
    return replace(RULESETS[version], daily_loss_limit=1e9, max_consecutive_losses=10 ** 9, max_drawdown=1e9)


def vol_mittarit(hist) -> tuple[float, float] | None:
    """(M, R2) viimeisistä W suljetusta kynttilästä. M = 15 min päätösmuutosten itseisarvojen mediaani."""
    if len(hist) < W:
        return None
    w = hist[-W:]
    m = st.median(abs(w[k].close - w[k - HMOVE].close) for k in range(HMOVE, W))
    r2 = max(c.high for c in w) - min(c.low for c in w)
    return m, r2


class VolEngine(PaperEngine):
    """Botin paperimoottori; vain stop, tavoite ja kulusuodatin lasketaan 2 h vaihtelusta."""

    def __init__(self, rules, hs_fn, funding_fn, k_target: float, k_stop: float, **kw):
        super().__init__(rules, hs_fn, funding_fn, **kw)
        self.k_target, self.k_stop = k_target, k_stop
        self.meta: dict[int, dict] = {}
        self.buf: dict = defaultdict(lambda: deque(maxlen=W))   # oma 2 h puskuri (analysaattori pitää vain 100)

    def on_bar_close(self, c) -> None:
        self.buf[c.symbol].append(c)          # vain suljetut kynttilät; käytetään vasta seuraavan avauksessa
        super().on_bar_close(c)

    def _try_open(self, sig, t: int, price: float) -> None:
        if not self.allow_entries:
            return
        vm = vol_mittarit(list(self.buf[sig.symbol]))
        if vm is None or vm[0] <= 0:
            return self._skip(sig, t, "VOL2H: historia < 2 h tai M = 0")
        m, r2 = vm
        sg = 1 if sig.side == "long" else -1
        d_t = min(self.k_target * m, 0.5 * r2)
        d_s = self.k_stop * m
        hs = self.half_spread_fn(sig.symbol, t)
        r = self.r
        cost = price * (2 * r.taker_fee + 2 * (hs + r.slippage))
        if d_t < COST_MULT * cost:
            return self._skip(sig, t, f"VOL2H kulusuodatin: tavoite {d_t / price:.3%} < {COST_MULT:g} × kulut {cost / price:.3%}")
        before = self.state.next_id
        super()._try_open(replace(sig, stop=price - sg * d_s), t, price)
        pos = self.positions.get(sig.symbol)
        if pos is not None and pos.id == before:
            pos.target = price + sg * d_t
            self.meta[pos.id] = {"M": m, "R2": r2, "d_t": d_t, "d_s": d_s, "cost": cost}


def aja_malli(data: dict, version: str, malli: str, hs: dict, fund_day: dict, t0: int, t1: int) -> dict:
    trades, events = [], []
    r = ilman_tappiorajoja(version)
    hs_fn = lambda s, t: max(hs.get(s, 0.0), r.min_half_spread_backtest)
    f_fn = lambda s, t: fund_day.get(s, {}).get(str(t // DAY))
    kw = dict(log=lambda m: None, on_trade=trades.append, on_event=events.append, verbose_signals=False)
    if MALLIT[malli] is None:
        eng = PaperEngine(r, hs_fn, f_fn, **kw)
    else:
        eng = VolEngine(r, hs_fn, f_fn, *MALLIT[malli], **kw)
    by_time = defaultdict(list)
    for cs in data.values():
        for c in cs:
            if c.open_time < t1 + 60 * 60_000:
                by_time[c.open_time].append(c)
    for t in sorted(by_time):
        bar = sorted(by_time[t], key=lambda c: c.symbol)
        eng.allow_entries = t0 <= t < t1        # signaalit vain jaksolta; lämmittely ilman kauppoja
        for c in bar:
            eng.on_bar_open(c.symbol, t, c.open)
        for c in bar:
            eng.on_bar_close(c)
    return {"trades": trades, "events": events, "meta": getattr(eng, "meta", {})}


def boot(by_day: dict, rnd: random.Random):
    keys = list(by_day)
    allv = [v for k in keys for v in by_day[k]]
    if len(keys) < 2:
        return (st.mean(allv) if allv else float("nan"), float("-inf"), float("inf"))
    S = [sum(by_day[k]) for k in keys]
    N = [len(by_day[k]) for k in keys]
    rng = range(len(keys))
    bs = []
    for _ in range(BOOT):
        idx = rnd.choices(rng, k=len(keys))
        n = sum(map(N.__getitem__, idx))
        bs.append(sum(map(S.__getitem__, idx)) / n if n else 0.0)
    bs.sort()
    return st.mean(allv), bs[int(0.025 * BOOT)], bs[int(0.975 * BOOT) - 1]


def boot_diff(days: list[int], a: dict, b: dict, rnd: random.Random):
    """Päiväkohtainen erotus Σa − Σb, keskiarvo päivää kohden ja 95 % LV."""
    d = [sum(a.get(k, [])) - sum(b.get(k, [])) for k in days]
    bs = sorted(st.mean(rnd.choices(d, k=len(d))) for _ in range(BOOT))
    return st.mean(d), bs[int(0.025 * BOOT)], bs[int(0.975 * BOOT) - 1]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-glob", required=True)
    ap.add_argument("--spread", required=True)
    ap.add_argument("--funding", required=True)
    ap.add_argument("--alku", default="2026-07-15T00:00")
    ap.add_argument("--loppu", default="2026-09-15T00:00")
    ap.add_argument("--puoli", default="2026-08-15T00:00")
    ap.add_argument("--tulos", default="tutkimus/tulokset/vol2h")
    a = ap.parse_args(argv)
    t0, t1, tp = parse_date(a.alku), parse_date(a.loppu), parse_date(a.puoli)
    data = load(glob.glob(a.data_glob))
    hs = json.load(open(a.spread))
    fund = json.load(open(a.funding))
    days_all = list(range(t0 // DAY, t1 // DAY))
    n_days = len(days_all)
    rnd = random.Random(SEED)
    res = {}
    for tili, ver in (("K", "aj1-kaanto"), ("J", "aj1-jatko")):
        for malli in MALLIT:
            out = aja_malli(data, ver, malli, hs, fund, t0, t1)
            res[(tili, malli)] = out
            print(f"{tili} {malli}: kauppoja {len(out['trades'])}", flush=True)
    L = ["# Kehitystesti VOL2H – tulokset (KEHITYSDATA, ei näyttöä)\n",
         f"Suunnitelma `docs/KEHITYSTESTI_VOL2H_SUUNNITELMA.md` (lukittu ennen laskentaa). Jakso {a.alku} – {a.loppu} UTC ({n_days} vrk), "
         f"1m-kynttilät, markkinat {', '.join(sorted(data))}. Tilikohtaiset tappiorajat pois kaikista malleista. "
         "½ spread: " + ", ".join(f"{k[3:-3]} {max(v, 0.0001):.4%}" for k, v in sorted(hs.items())) + ".\n"]
    summary = {}
    for tili in ("K", "J"):
        L.append(f"\n## Tili {tili} ({'aj1-kaanto, kääntymissignaalit' if tili == 'K' else 'aj1-jatko, jatkumissignaalit'})\n")
        L.append("| Malli | Suunta | Kauppoja | Kauppoja/pv | Osuma (netto > 0) | Tavoite / stop / aika / epäselvä | Keskim. voitto | Keskim. tappio | Kulut/kauppa | Netto/kauppa | Netto/kauppa (riskiyks.) | Netto yht. | Netto yht. vakiopääoma | Suurin pudotus (vakiopääoma) |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        base_byday = None
        for malli in MALLIT:
            tr = [x for x in res[(tili, malli)]["trades"] if t0 <= _ms(x.entry_time) < t1]
            for side in ("kaikki", "long", "short"):
                T = tr if side == "kaikki" else [x for x in tr if x.side == side]
                if not T:
                    L.append(f"| {malli} | {side} | 0 | – | – | – | – | – | – | – | – | – | – | – |")
                    continue
                wins = [x.net_pnl for x in T if x.net_pnl > 0]
                loss = [x.net_pnl for x in T if x.net_pnl <= 0]
                oc = defaultdict(int)
                for x in T:
                    oc[x.lopputulos or "muu"] += 1
                costs = [x.fees + x.spread_slippage_est + x.funding for x in T]
                bm = [x.budget_multiple for x in T]
                cum, pk, dd = 0.0, 0.0, 0.0
                for x in sorted(T, key=lambda x: x.exit_time):
                    cum += x.budget_multiple * REF_RISK_USD
                    pk = max(pk, cum)
                    dd = max(dd, pk - cum)
                L.append(f"| {malli} | {side} | {len(T)} | {len(T) / n_days:.1f} | {len(wins) / len(T):.1%} | "
                         f"{oc['tavoite']} / {oc['stop']} / {oc['aikaraja']} / {oc['epäselvä']} | "
                         f"{(st.mean(wins) if wins else 0):+.2f} $ | {(st.mean(loss) if loss else 0):+.2f} $ | {st.mean(costs):.2f} $ | "
                         f"{st.mean(x.net_pnl for x in T):+.2f} $ | {st.mean(bm):+.3f} | {sum(x.net_pnl for x in T):+,.0f} $ | "
                         f"{sum(bm) * REF_RISK_USD:+,.0f} $ | {dd:,.0f} $ ({dd / 10_000:.1%}) |")
            byday = defaultdict(list)
            for x in tr:
                byday[_ms(x.entry_time) // DAY].append(x.budget_multiple)
            if malli == "NYKYINEN":
                base_byday = byday
            m, lo, hi = boot(byday, rnd)
            h = [st.mean([x.budget_multiple for x in tr if (_ms(x.entry_time) < tp) == first] or [float("nan")]) for first in (True, False)]
            k2 = "TUKEE" if (m > 0 and lo > 0 and h[0] > 0 and h[1] > 0) else "EI TUE"
            entry = {"n": len(tr), "per_day": len(tr) / n_days, "bm_mean": m, "bm_lo": lo, "bm_hi": hi, "halves": h, "K2": k2}
            if malli != "NYKYINEN":
                dm, dlo, dhi = boot_diff(days_all, byday, base_byday, rnd)
                entry.update({"diff_day": dm, "diff_lo": dlo, "diff_hi": dhi,
                              "K1": "PARANTAA" if (dm > 0 and dlo > 0) else "EI OSOITETTU PARANNUSTA"})
            summary[(tili, malli)] = entry
        # tilaisuudet
        L.append(f"\n**Tilaisuudet ja ohitukset ({tili}):**\n")
        L.append("| Malli | Signaaleja/pv | Avattu/pv | Ohitettu: kulusuodatin | Ohitettu: markkinassa jo positio | Ohitettu: 3 positiota auki | Muut ohitukset |")
        L.append("|---|---|---|---|---|---|---|")
        for malli in MALLIT:
            ev = [e for e in res[(tili, malli)]["events"] if e.get("kind") in ("open", "skipped")
                  and t0 <= (e.get("entry_time") if e["kind"] == "open" else e.get("time", 0)) < t1 + 60_000]
            sk = defaultdict(int)
            for e in ev:
                if e["kind"] == "skipped":
                    w = e["why"]
                    k = "kulu" if "kulusuodatin" in w else "pos" if "jo avoin positio" in w else "max" if "avoimia positioita" in w else "muu"
                    sk[k] += 1
            n_sig = len(ev)
            n_open = sum(1 for e in ev if e["kind"] == "open")
            L.append(f"| {malli} | {n_sig / n_days:.1f} | {n_open / n_days:.1f} | {sk['kulu']} | {sk['pos']} | {sk['max']} | {sk['muu']} |")
        L.append(f"\n**Arviointi ({tili}):**\n")
        L.append("| Malli | Netto/kauppa riskiyksikköinä, 95 % LV | Puoliskot | K2: tukeeko suurempaa kauppamäärää | Päiväero vs NYKYINEN (riskiyks./pv), 95 % LV | K1: parantaako nettotulosta |")
        L.append("|---|---|---|---|---|---|")
        for malli in MALLIT:
            e = summary[(tili, malli)]
            d = f"{e['diff_day']:+.2f} ({e['diff_lo']:+.2f} … {e['diff_hi']:+.2f})" if "diff_day" in e else "–"
            L.append(f"| {malli} | {e['bm_mean']:+.3f} ({e['bm_lo']:+.3f} … {e['bm_hi']:+.3f}) | {e['halves'][0]:+.3f} / {e['halves'][1]:+.3f} | "
                     f"**{e['K2']}** | {d} | **{e.get('K1', '–')}** |")
    # V-mallien tavoite- ja stop-etäisyydet
    L.append("\n## V-mallien tavoite- ja stopetäisyydet (avatut kaupat, % hinnasta)\n")
    L.append("| Tili | Malli | M mediaani | Tavoite mediaani | Stop mediaani | Arvioidut kulut mediaani | Tavoite / kulut mediaani |")
    L.append("|---|---|---|---|---|---|---|")
    for tili in ("K", "J"):
        for malli in ("V1", "V2"):
            out = res[(tili, malli)]
            px = {x.id: x.entry_price for x in out["trades"]}
            rows = [(v, px[k]) for k, v in out["meta"].items() if k in px]
            if rows:
                L.append(f"| {tili} | {malli} | {st.median(v['M'] / p for v, p in rows):.3%} | {st.median(v['d_t'] / p for v, p in rows):.3%} | "
                         f"{st.median(v['d_s'] / p for v, p in rows):.3%} | {st.median(v['cost'] / p for v, p in rows):.3%} | "
                         f"{st.median(v['d_t'] / v['cost'] for v, p in rows):.2f} |")
    L.append("\nRiskiyksikkö = nettotulos / kaupan riskibudjetti (−1 = suunniteltu täysi tappio). Vakiopääomavastine = riskiyksiköt × 50 $ "
             "(0,5 % × 10 000 $), jolloin korkoa korolle ei vääristä vertailua. Kaikki luvut ovat paperilaskentaa jo käytetyllä kehitysdatalla.")
    with open(a.tulos + "_raportti.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(a.tulos + "_yhteenveto.json", "w", encoding="utf-8") as f:
        json.dump({f"{k[0]} {k[1]}": v for k, v in summary.items()}, f, ensure_ascii=False, indent=1)
    print("\n".join(L))


def _ms(s) -> int:
    return parse_date(s.replace(" UTC", "")) if isinstance(s, str) else int(s)


if __name__ == "__main__":
    main()
