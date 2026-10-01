"""Vaihe 1 -analyysin perusominaisuudet: lopputulos, epäselvät, ei tulevaa tietoa, vertailuotanta."""
import random
import unittest

from kynttilatulkki.backtest import synthetic
from kynttilatulkki.models import Candle
from tutkimus import ajoitus as aj

T0 = 1_767_225_600_000
M = 60_000


def c(i, o, h, l, cl, v=1.0):
    return Candle("X", T0 + i * M, o, h, l, cl, v, True, T0 + i * M + M - 1)


def flat(n, p=100.0):
    return [c(i, p, p + 0.1, p - 0.1, p) for i in range(n)]


class TestLopputulos(unittest.TestCase):
    def test_tavoite_ensin(self):
        cs = flat(40)
        cs[21] = c(21, 100, 101.2, 99.95, 101)          # avauskynttilä 21 (signaali 20)
        o = aj.outcome(cs, 20, "long", 1.0, 1.0)
        self.assertEqual((o["tulos"], o["pisteet"]), ("tavoite", 1.0))

    def test_stop_ensin_short(self):
        cs = flat(40)
        cs[22] = c(22, 100, 101.5, 99.9, 101)
        o = aj.outcome(cs, 20, "short", 1.0, 1.0)
        self.assertEqual((o["tulos"], o["pisteet"]), ("stop", -1.0))

    def test_sama_kynttila_epaselva(self):
        cs = flat(40)
        cs[23] = c(23, 100, 101.5, 98.5, 100)
        o = aj.outcome(cs, 20, "long", 1.0, 1.0)
        self.assertEqual((o["tulos"], o["pisteet"]), ("epäselvä", 0.0))

    def test_hintakuilu(self):
        cs = flat(40)
        cs[24] = c(24, 98.0, 98.2, 97.5, 98)
        self.assertEqual(aj.outcome(cs, 20, "long", 1.0, 1.0)["tulos"], "stop")

    def test_aikaraja_rajattu(self):
        cs = flat(40)
        cs[36] = c(36, 100.5, 100.6, 100.4, 100.5)          # 16. kynttilän avaus = aikarajahinta
        o = aj.outcome(cs, 20, "long", 1.0, 1.0)
        self.assertEqual(o["tulos"], "aikaraja")
        self.assertAlmostEqual(o["pisteet"], 0.5)

    def test_liian_lahella_loppua(self):
        self.assertIsNone(aj.outcome(flat(30), 20, "long", 1.0, 1.0))


class TestEiTulevaaTietoa(unittest.TestCase):
    def test_signaalit_ja_A_eivat_muutu_katkaisussa(self):
        cs = synthetic("PF_A", T0, 1500, seed=7)
        cut = 900
        A_full, A_cut = aj.avg_range_before(cs), aj.avg_range_before(cs[:cut])
        self.assertEqual(A_full[:cut], A_cut)
        for ver in aj.TYYPIT.values():
            full = [s for s in aj.signals_for("PF_A", cs, ver) if s[0] < cut]
            part = aj.signals_for("PF_A", cs[:cut], ver)
            self.assertEqual(full, part, ver)
            for i, side, _r, A_bot in full:
                self.assertAlmostEqual(A_full[i], A_bot, places=12)

    def test_signaaleja_syntyy(self):
        cs = synthetic("PF_A", T0, 3000, seed=3)
        self.assertGreater(len(aj.signals_for("PF_A", cs, "aj1-kaanto")) + len(aj.signals_for("PF_A", cs, "aj1-jatko")), 0)


class TestVertailu(unittest.TestCase):
    def test_sama_paiva_ja_poissulku(self):
        cs = synthetic("PF_A", T0, 3000, seed=5)
        A = aj.avg_range_before(cs)
        by_day = {}
        for i, x in enumerate(cs):
            if A[i] and i + aj.HORIZON + 1 < len(cs):
                by_day.setdefault(x.open_time // aj.DAY, []).append(i)
        rnd = random.Random(1)
        picks = []
        orig = aj.outcome

        def spy(cs_, j, side, A_, k):
            picks.append(j)
            return orig(cs_, j, side, A_, k)
        aj.outcome = spy
        try:
            out = aj.controls(cs, A, 500, "long", 1.0, rnd, by_day)
        finally:
            aj.outcome = orig
        self.assertEqual(len(out), aj.CONTROLS)
        self.assertTrue(all(abs(j - 500) > aj.EXCLUDE for j in picks))
        self.assertTrue(all(cs[j].open_time // aj.DAY == cs[500].open_time // aj.DAY for j in picks))


class TestKorjaukset(unittest.TestCase):
    def test_holm_ja_bh(self):
        self.assertEqual(aj.holm({"a": 0.01, "b": 0.04}), {"a": 0.02, "b": 0.04})
        q = aj.bh({"a": 0.01, "b": 0.02, "c": 0.5})
        self.assertAlmostEqual(q["a"], 0.03)
        self.assertAlmostEqual(q["b"], 0.03)


if __name__ == "__main__":
    unittest.main()


class TestPaatossaanto(unittest.TestCase):
    def test_alle_kolme_markkinaa_avoin(self):
        # vahva ja johdonmukainen tulos, mutta vain 1 markkina täyttää kattavuuden -> avoin
        v = aj.paatos(900, 60, 0.001, 0.1, 0.1, 0.1, 1, 0, 1)
        self.assertTrue(v.startswith("KOKONAISPÄÄTÖS AVOIN"))
        self.assertTrue(aj.paatos(900, 60, 0.001, -0.1, -0.1, -0.1, 0, 2, 2).startswith("KOKONAISPÄÄTÖS AVOIN"))

    def test_kolme_markkinaa_normaali_saanto(self):
        self.assertEqual(aj.paatos(900, 60, 0.001, 0.1, 0.1, 0.1, 3, 0, 3), "AJOITUSETU OSOITETTU (ennen kuluja)")
        self.assertEqual(aj.paatos(900, 60, 0.001, -0.1, -0.1, -0.1, 0, 3, 5), "SIGNAALIT SATTUMAA HUONOMPIA")
        self.assertTrue(aj.paatos(900, 60, 0.001, 0.1, 0.1, 0.1, 2, 1, 5).startswith("TILASTOLLINEN ERO"))
        self.assertTrue(aj.paatos(100, 60, 0.001, 0.1, 0.1, 0.1, 3, 0, 5).startswith("AINEISTO EI RIITÄ"))
        self.assertEqual(aj.paatos(900, 60, 0.3, 0.1, 0.1, 0.1, 3, 0, 5), "EI NÄYTTÖÄ AJOITUSEDUSTA")
