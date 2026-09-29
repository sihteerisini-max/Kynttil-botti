import unittest
from dataclasses import replace

from kynttilatulkki.backtest import run, synthetic
from kynttilatulkki.models import Candle, Observation
from kynttilatulkki.paper import PaperEngine
from kynttilatulkki.strategy import RULESETS, Signal, make_signal, qualifies
from kynttilatulkki.patterns import build_context

R1 = RULESETS["v1"]
M = 60_000
T0 = 1_767_225_600_000
HS = 0.0001


def engine(rules=R1, funding=None):
    return PaperEngine(rules, lambda s, t: HS, lambda s, t: funding, log=lambda m: None)


def c(t, o, h, l, cl, sym="PF_TST", v=100.0):
    return Candle(sym, t, o, h, l, cl, v, True, t + M - 1)


def sig(side="long", stop=99.0, sym="PF_TST"):
    return Signal(sym, side, c(T0 - M, 100, 100.5, 99.2, 100), stop, 0.5, [])


def open_long(e, price=100.0, stop=99.0, t=T0):
    e.pending["PF_TST"] = sig("long", stop)
    e.on_bar_open("PF_TST", t, price)
    return e.positions["PF_TST"]


class TestKulut(unittest.TestCase):
    def test_avaus_seuraavalla_avauksella_ja_kulut(self):
        e = engine()
        p = open_long(e)
        self.assertAlmostEqual(p.entry_price, 100 * (1 + HS + R1.slippage))
        self.assertAlmostEqual(p.target, p.entry_price + 1.5 * (p.entry_price - 99.0))
        # riski ≈ 0,5 % pääomasta sisältäen arvioidut kulut
        cost_unit = p.entry_price * R1.round_trip_cost(HS)
        self.assertAlmostEqual(p.qty * (p.risk_r + cost_unit), 50.0, places=6)

    def test_tavoite_netto(self):
        e = engine()
        p = open_long(e)
        e.on_bar_close(c(T0, 100, p.target + 0.1, 99.9, p.target))
        tr = e.trades[0]
        exit_px = p.target * (1 - HS - R1.slippage)
        gross = p.qty * (exit_px - p.entry_price)
        fees = p.qty * p.entry_price * R1.taker_fee + p.qty * exit_px * R1.taker_fee
        funding = p.qty * p.entry_price * R1.fallback_funding_per_hour * (1 / 60)
        self.assertEqual(tr.close_reason, "voittotavoite")
        self.assertAlmostEqual(tr.net_pnl, round(gross - fees - funding, 4), places=4)
        self.assertLess(tr.net_pnl, gross)      # kulut pienentävät tulosta

    def test_funding_short_saa_positiivisella_korolla(self):
        e = engine(funding=0.0001)
        e.pending["PF_TST"] = sig("short", stop=101.0)
        e.on_bar_open("PF_TST", T0, 100.0)
        for i in range(60):   # tunti ilman stoppia/tavoitetta
            if "PF_TST" not in e.positions:
                break
            e.on_bar_close(c(T0 + i * M, 100, 100.05, 99.95, 100))
        e.close_all(T0 + 60 * M, {"PF_TST": 100.0})
        self.assertLess(e.trades[0].funding, 0)   # negatiivinen kulu = tuotto shortille


class TestStopTavoiteAika(unittest.TestCase):
    def test_molemmat_samassa_kynttilassa_stop_ensin(self):
        e = engine()
        p = open_long(e)
        e.on_bar_close(c(T0, 100, p.target + 1, 98.0, 100))
        self.assertTrue(e.trades[0].close_reason.startswith("stop loss"))
        self.assertAlmostEqual(e.trades[0].exit_price, round(99.0 * (1 - HS - R1.stop_slippage), 8))

    def test_hintakuilu_stopin_yli(self):
        e = engine()
        open_long(e)
        e.on_bar_close(c(T0, 100, 100.2, 99.5, 99.6))
        e.on_bar_open("PF_TST", T0 + M, 98.0)
        tr = e.trades[0]
        self.assertIn("hintakuilu", tr.close_reason)
        self.assertAlmostEqual(tr.exit_price, round(98.0 * (1 - HS - R1.stop_slippage), 8))

    def test_aikaraja_15_kynttilaa(self):
        e = engine()
        open_long(e)
        for i in range(15):
            e.on_bar_close(c(T0 + i * M, 100, 100.1, 99.9, 100))
            e.on_bar_open("PF_TST", T0 + (i + 1) * M, 100)
        tr = e.trades[0]
        self.assertTrue(tr.close_reason.startswith("aikaraja"))
        self.assertEqual(tr.bars_held, 15)
        self.assertEqual(tr.exit_time, "2026-01-01 00:15 UTC")

    def test_kulusuodatin(self):
        e = engine()
        e.pending["PF_TST"] = sig("long", stop=99.9)   # riski ~0,13 % < 2 x ~0,16 %
        e.on_bar_open("PF_TST", T0, 100.0)
        self.assertEqual(e.positions, {})
        self.assertIn("kulusuodatin", e.skipped)

    def test_stopin_vaaralla_puolella(self):
        e = engine()
        e.pending["PF_TST"] = sig("long", stop=99.0)
        e.on_bar_open("PF_TST", T0, 98.5)
        self.assertEqual(e.positions, {})


class TestTappiorajat(unittest.TestCase):
    def _lose(self, e, t, sym="PF_TST"):
        e.pending[sym] = sig("long", 99.0, sym)
        e.on_bar_open(sym, t, 100.0)
        e.on_bar_close(c(t, 100, 100.1, 98.0, 98.5, sym=sym))

    def test_tappioputki_tauko(self):
        e = engine(R1.__class__(**{**R1.__dict__, "daily_loss_limit": 1.0}))
        for i in range(4):
            self._lose(e, T0 + i * 2 * M)
        self.assertGreater(e.state.pause_until, T0)
        self._lose(e, T0 + 10 * M)
        self.assertEqual(len(e.trades), 4)
        self.assertIn(f"tauko {R1.max_consecutive_losses} peräkkäisen tappion jälkeen", e.skipped)

    def test_paivaraja(self):
        e = engine(replace(R1, max_consecutive_losses=99))
        for i in range(6):
            self._lose(e, T0 + i * 2 * M)
        self.assertTrue(e.state.day_blocked)
        n = len(e.trades)
        self.assertLessEqual(n, 5)
        # seuraava UTC-päivä avaa rajan
        self._lose(e, T0 + 86_400_000)
        self.assertEqual(len(e.trades), n + 1)

    def test_maksimipudotus_pysayttaa(self):
        e = engine(replace(R1, max_consecutive_losses=999, daily_loss_limit=1.0, risk_per_trade=0.03))
        for i in range(10):
            self._lose(e, T0 + i * 2 * M)
        self.assertTrue(e.state.halted)
        n = len(e.trades)
        self._lose(e, T0 + 100 * M)
        self.assertEqual(len(e.trades), n)


class TestSignaaliehdot(unittest.TestCase):
    def obs(self, **kw):
        base = dict(symbol="X", open_time=T0, status="VAHVISTETTU", key="hammer", name="Vasara",
                    bias="nousuun viittaava", strength="kohtalainen", reasons=[], score=2,
                    volume_ratio=1.3, context_ok=True)
        base.update(kw)
        return Observation(**base)

    def test_ehdot(self):
        self.assertEqual(qualifies(self.obs(), R1), "long")
        self.assertIsNone(qualifies(self.obs(score=1), R1))
        self.assertIsNone(qualifies(self.obs(volume_ratio=1.19), R1))
        self.assertIsNone(qualifies(self.obs(context_ok=False), R1))
        self.assertIsNone(qualifies(self.obs(status="KESKENERÄINEN"), R1))
        self.assertIsNone(qualifies(self.obs(bias="epäröinti"), R1))
        self.assertEqual(qualifies(self.obs(bias="laskuun viittaava", key="shooting_star"), R1), "short")

    def test_ristiriita_ei_kauppaa(self):
        hist = [c(T0 + i * M, 100, 100.5, 99.5, 100) for i in range(25)]
        ctx = build_context(hist)
        cur = c(T0 + 25 * M, 100, 101, 99, 100)
        both = [self.obs(), self.obs(bias="laskuun viittaava", key="bearish_engulfing")]
        self.assertIsNone(make_signal(cur, both, ctx, R1))


class TestEiTulevaisuustietoa(unittest.TestCase):
    def data(self, days=2):
        return {f"PF_S{i}": synthetic(f"PF_S{i}", T0, int(days * 1440), seed=i + 1) for i in range(3)}

    def test_avaus_aina_signaalin_jalkeisella_kynttilalla(self):
        eng = run(self.data(), "v1", {}, {}, log=lambda m: None)
        self.assertGreater(len(eng.trades), 5)
        from datetime import datetime
        for tr in eng.trades:
            st = datetime.strptime(tr.signal_time, "%Y-%m-%d %H:%M UTC")
            et = datetime.strptime(tr.entry_time, "%Y-%m-%d %H:%M UTC")
            self.assertEqual((et - st).total_seconds(), 60)

    def test_katkaistu_data_samat_kaupat(self):
        full = self.data()
        e_full = run(full, "v1", {}, {}, log=lambda m: None)
        cut_t = T0 + 1500 * M
        part = {s: [x for x in cs if x.open_time < cut_t] for s, cs in full.items()}
        e_part = run(part, "v1", {}, {}, log=lambda m: None)
        done_full = [t for t in e_full.trades if t.close_reason != "testijakson loppu"
                     and t.exit_time < "2026-01-02 01:00 UTC"]
        done_part = [t for t in e_part.trades if t.close_reason != "testijakson loppu"
                     and t.exit_time < "2026-01-02 01:00 UTC"]
        self.assertGreater(len(done_full), 3)
        self.assertEqual(done_full, done_part)


if __name__ == "__main__":
    unittest.main()


class TestKorjattuKulumalli(unittest.TestCase):
    R11 = RULESETS["v1.1"]

    def test_kaava(self):
        from kynttilatulkki.strategy import estimate_costs
        ce = estimate_costs(self.R11, "long", 100.0, 99.0, HS)
        self.assertAlmostEqual(ce.entry_fill, 100 * (1 + HS + 0.0002))
        self.assertAlmostEqual(ce.stop_fill, 99 * (1 - HS - 0.0005))
        self.assertAlmostEqual(ce.price_risk_r, ce.entry_fill - 99.0)
        self.assertAlmostEqual(ce.fees, 0.0005 * (ce.entry_fill + ce.stop_fill))
        # avauksen spread/liukuma EI sisälly tappioon toista kertaa
        self.assertAlmostEqual(ce.loss_at_stop, ce.entry_fill - ce.stop_fill + ce.fees + ce.funding)
        self.assertAlmostEqual(ce.total_cost, ce.entry_friction + ce.exit_friction + ce.fees + ce.funding)

    def test_stop_tappio_on_riskibudjetti(self):
        e = engine(self.R11)
        e.pending["PF_TST"] = sig("long", 99.0)
        e.on_bar_open("PF_TST", T0, 100.0)
        p = e.positions["PF_TST"]
        self.assertAlmostEqual(p.risk_budget, 50.0)
        e.on_bar_close(c(T0, 100, 100.1, 98.0, 98.5))
        tr = e.trades[0]
        # ero vain siitä, että funding-arvio kattaa 15 min mutta positio oli auki 1 min
        unused_funding = p.qty * p.entry_price * self.R11.fallback_funding_per_hour * 14 / 60
        self.assertAlmostEqual(tr.net_pnl, -50.0 + unused_funding, places=3)
        self.assertAlmostEqual(tr.budget_multiple, -1.0, places=3)

    def test_v2_suodatin_tiukempi(self):
        from kynttilatulkki.strategy import estimate_costs
        ce = estimate_costs(RULESETS["v2"], "long", 100.0, 99.5, HS)
        ratio = ce.price_risk_r / ce.total_cost
        self.assertTrue(2 <= ratio < 4)      # v1.1 hyväksyy, v2 hylkää
        for key, opened in (("v1.1", True), ("v2", False)):
            e = engine(RULESETS[key])
            e.pending["PF_TST"] = sig("long", 99.5)
            e.on_bar_open("PF_TST", T0, 100.0)
            self.assertEqual("PF_TST" in e.positions, opened, key)
