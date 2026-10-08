"""Tutkimus K4H: kopion samuus, pitoaika, päällekkäisyyssääntö, kulut, funding, tulevan tiedon esto,
vertailut ja päätössääntö."""
import filecmp
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tutkimus_k4h"))
for m in [k for k in list(sys.modules) if k in ("data15", "kt") or k.startswith("kt.")]:
    del sys.modules[m]

import data15  # noqa: E402
import k4h  # noqa: E402
from kt.models import Candle  # noqa: E402

S = data15.STEP15
T0 = data15.ms("2025-01-01")


def c(t, o, h, l, cl, v=10.0):
    return Candle("X", t, o, h, l, cl, v, True, t + S - 1)


def synth15(n, seed, start=T0):
    rnd = random.Random(seed)
    p, out = 100.0, []
    for k in range(n):
        o = p
        path = [o]
        for _ in range(6):
            p *= 1 + rnd.gauss(0, 0.004)
            path.append(p)
        out.append(Candle("X", start + k * S, o, max(path), min(path), p, rnd.uniform(50, 150) * rnd.choice([1, 1, 1, 3]), True,
                          start + (k + 1) * S - 1))
    return out


class TestKopio(unittest.TestCase):
    def test_identtinen(self):
        for m in ["models", "patterns", "komponentit", "strategy", "jatkuminen", "analyzer", "paper"]:
            self.assertTrue(filecmp.cmp(os.path.join(ROOT, "kynttilatulkki", m + ".py"),
                                        os.path.join(ROOT, "tutkimus_k4h", "kt", m + ".py"), shallow=False), m)


class TestPito(unittest.TestCase):
    def test_avaus_ja_sulku(self):
        cs = [c(T0 + k * S, 100 + k, 101 + k, 99 + k, 100 + k) for k in range(40)]
        self.assertAlmostEqual(k4h.move(cs, 5, "long", 2.0), (cs[22].open - cs[6].open) / 2.0)
        self.assertAlmostEqual(k4h.move(cs, 5, "short", 2.0), -(cs[22].open - cs[6].open) / 2.0)
        self.assertIsNone(k4h.move(cs, 30, "long", 2.0))
        self.assertIsNone(k4h.move(cs, 5, "long", 0.0))

    def test_paallekkaisyys(self):
        taken, skipped = k4h.select_trades([(10, "long"), (12, "short"), (26, "long"), (27, "long"), (60, "short")])
        # 10 avaa 11, sulkeutuu 27:n avauksessa -> 26 (avaus 27) sallittu, 27 (avaus 28) ohitetaan
        self.assertEqual(taken, [(10, "long"), (26, "long"), (60, "short")])
        self.assertEqual(skipped, [(12, "short"), (27, "long")])


class TestKulut(unittest.TestCase):
    def test_netto(self):
        cs = [c(T0 + k * S, 100.0, 100.5, 99.5, 100.0) for k in range(40)]
        cs[22] = c(cs[22].open_time, 102.0, 102.5, 101.5, 102.0)
        hs = 0.0001
        x = k4h.trade_net(cs, 5, "long", hs, {})
        ef, xf = 100 * (1 + hs + k4h.SLIP), 102 * (1 - hs - k4h.SLIP)
        self.assertAlmostEqual(x["brutto"], 0.02)
        self.assertAlmostEqual(x["palkkiot"], k4h.FEE * (ef + xf) / ef)
        self.assertEqual((x["funding"], x["funding_todellinen"]), (k4h.FUNDING_VAROVAINEN, False))
        self.assertAlmostEqual(x["netto"], (xf - ef) / ef - x["palkkiot"] - k4h.FUNDING_VAROVAINEN)

    def test_funding_todellinen(self):
        t = T0 + 15 * 60_000          # avaus 00:15 -> tunnit 01, 02, 03, 04
        fund = {T0 + k * k4h.HOUR: 0.00001 for k in range(1, 5)}
        self.assertEqual(k4h.funding_cost("long", t, fund), (0.00004, True))
        self.assertEqual(k4h.funding_cost("short", t, fund)[0], -0.00004)
        del fund[T0 + 4 * k4h.HOUR]
        self.assertEqual(k4h.funding_cost("long", t, fund), (k4h.FUNDING_VAROVAINEN, False))


class TestEiTulevaaTietoa(unittest.TestCase):
    def test_signaalit_ja_A_katkaisussa(self):
        cs = synth15(1500, 3)
        full = k4h.signals_for(cs)
        self.assertTrue(full)
        self.assertEqual(k4h.signals_for(cs[:900]), [x for x in full if x[0] < 900])
        self.assertEqual(k4h.avg_range_before(cs)[:700], k4h.avg_range_before(cs[:700]))

    def test_vertailut_sama_paiva_ja_etaisyys(self):
        cs = synth15(96 * 4, 5)
        A = k4h.avg_range_before(cs)
        by_day = {}
        for i, x in enumerate(cs):
            if A[i] and i + k4h.H + 1 < len(cs):
                by_day.setdefault(x.open_time // data15.DAY, []).append(i)
        seen = []
        orig = k4h.move
        k4h.move = lambda cs_, j, side, a: (seen.append(j), orig(cs_, j, side, a))[1]
        try:
            v = k4h.controls(cs, A, 96 + 40, "long", random.Random(1), by_day)
        finally:
            k4h.move = orig
        self.assertEqual(len(v), k4h.CONTROLS)
        for j in seen:
            self.assertEqual(cs[j].open_time // data15.DAY, cs[96 + 40].open_time // data15.DAY)
            self.assertGreaterEqual(abs(j - 96 - 40), k4h.EXCLUDE)


class TestPaatos(unittest.TestCase):
    def test_saanto(self):
        self.assertTrue(k4h.ehto(0.01, 0.1, True, 0.1, 0.1, 4, 4))
        self.assertFalse(k4h.ehto(0.01, 0.1, False, 0.1, 0.1, 4, 4))
        self.assertFalse(k4h.ehto(0.01, 0.1, True, -0.1, 0.1, 4, 4))
        self.assertFalse(k4h.ehto(0.01, 0.1, True, 0.1, 0.1, 3, 4))
        self.assertFalse(k4h.ehto(0.2, 0.1, True, 0.1, 0.1, 4, 4))
        self.assertTrue(k4h.paatos(6, 1000, 200, True, True).startswith("JATKOON"))
        self.assertTrue(k4h.paatos(6, 1000, 200, True, False).startswith("SUUNTAVAIKUTUS SÄILYI"))
        self.assertTrue(k4h.paatos(6, 1000, 200, False, True).startswith("EI NÄYTTÖÄ"))
        self.assertTrue(k4h.paatos(3, 1000, 200, True, True).startswith("AVOIN"))
        self.assertTrue(k4h.paatos(6, 100, 200, True, True).startswith("AINEISTO EI RIITÄ"))

    def test_bootstrap_yksisuuntainen(self):
        by = {d: [0.01, 0.02] for d in range(30)}
        m, lo, hi, p2, p1 = k4h.cluster_boot(by, random.Random(1), boot=500)
        self.assertGreater(lo, 0)
        self.assertEqual(p1, 0.0)


if __name__ == "__main__":
    unittest.main()
