"""Tutkimus 15M: koodikopion samuus, lopputuloslogiikka, tulevan tiedon esto, vertailut, puuttuvat
rivit, eheystarkistus, markkinavalinta, päätössääntö ja vaiheen 2 kululaskenta."""
import filecmp
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tutkimus15"))

import analyysi as an  # noqa: E402
import data15  # noqa: E402
import valinta  # noqa: E402
from kt.models import Candle  # noqa: E402

S = data15.STEP15
T0 = data15.ms("2025-01-01")


def c(t, o, h, l, cl, v=10.0):
    return Candle("X", t, o, h, l, cl, v, True, t + S - 1)


def flat(n, p=100.0, start=T0):
    return [c(start + k * S, p, p + 0.5, p - 0.5, p) for k in range(n)]


def synth15(n, seed, start):
    """Satunnaiskulku 15m-aikaleimoin (vain koneiston testaamiseen)."""
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
            a = os.path.join(ROOT, "kynttilatulkki", m + ".py")
            b = os.path.join(ROOT, "tutkimus15", "kt", m + ".py")
            self.assertTrue(filecmp.cmp(a, b, shallow=False), f"{m}.py eroaa – aja python tutkimus15/synkronoi.py")


class TestLopputulos(unittest.TestCase):
    def test_tavoite_ja_stop(self):
        cs = flat(40)
        cs[11] = c(cs[11].open_time, 100, 102.1, 99.9, 101)      # long-tavoite 100 + 2
        o = an.outcome(cs, 9, "long", 2.0, 1.0)
        self.assertEqual((o["tulos"], o["pisteet"], o["j"]), ("tavoite", 1.0, 11))
        o = an.outcome(cs, 9, "short", 2.0, 1.0)
        self.assertEqual(o["tulos"], "stop")

    def test_sama_kynttila_epaselva(self):
        cs = flat(40)
        cs[12] = c(cs[12].open_time, 100, 103, 97, 100)
        o = an.outcome(cs, 9, "long", 2.0, 1.0)
        self.assertEqual((o["tulos"], o["pisteet"], o["px"], o["px_alt"]), ("epäselvä", 0.0, 98.0, 102.0))

    def test_hintakuilu(self):
        cs = flat(40)
        cs[13] = c(cs[13].open_time, 95, 95.5, 94.5, 95)
        o = an.outcome(cs, 9, "long", 2.0, 1.0)
        self.assertEqual((o["tulos"], o["px"]), ("stop", 95))

    def test_aikaraja_16_kynttilaa(self):
        cs = flat(40)
        cs[9 + 1 + 16] = c(cs[26].open_time, 101, 101.2, 100.8, 101)
        o = an.outcome(cs, 9, "long", 2.0, 1.0)
        self.assertEqual((o["tulos"], o["j"]), ("aikaraja", 26))
        self.assertAlmostEqual(o["pisteet"], 0.5)

    def test_liian_lahella_loppua(self):
        self.assertIsNone(an.outcome(flat(20), 5, "long", 1.0, 1.0))


class TestEiTulevaaTietoa(unittest.TestCase):
    def test_signaalit_ja_A_eivat_muutu_katkaisussa(self):
        cs = synth15(1500, 3, T0)
        for typ, ver in an.TYYPIT.items():
            full = an.signals_for(cs, ver)
            self.assertTrue(full, f"ei signaaleja ({typ})")
            cut = 900
            part = an.signals_for(cs[:cut], ver)
            self.assertEqual(part, [x for x in full if x[0] < cut])
        A_full = an.avg_range_before(cs)
        A_cut = an.avg_range_before(cs[:700])
        self.assertEqual(A_full[:700], A_cut)

    def test_A_vain_edeltavista(self):
        cs = synth15(100, 4, T0)
        A = an.avg_range_before(cs)
        self.assertAlmostEqual(A[50], sum(x.range for x in cs[30:50]) / 20)


class TestVertailu(unittest.TestCase):
    def test_sama_paiva_ja_etaisyys(self):
        cs = synth15(96 * 4, 5, T0)
        A = an.avg_range_before(cs)
        by_day = {}
        for i, x in enumerate(cs):
            if A[i] and i + an.H + 1 < len(cs):
                by_day.setdefault(x.open_time // data15.DAY, []).append(i)
        i = 96 + 40
        seen = []
        orig = an.outcome
        an.outcome = lambda cs_, j, side, a, k: (seen.append(j), orig(cs_, j, side, a, k))[1]
        try:
            ctr = an.controls(cs, A, i, "long", 1.0, random.Random(1), by_day)
        finally:
            an.outcome = orig
        self.assertEqual(len(ctr), an.CONTROLS)
        for j in seen:
            self.assertEqual(cs[j].open_time // data15.DAY, cs[i].open_time // data15.DAY)
            self.assertGreaterEqual(abs(j - i), an.EXCLUDE)


class TestData(unittest.TestCase):
    def test_puuttuva_rivi_erotetaan(self):
        raw = {T0: dict(open=1, high=2, low=0.5, close=1.5, volume=3), T0 + 2 * S: dict(open=1.5, high=1.6, low=1.4, close=1.5, volume=0.0)}
        cs, miss = data15.to_candles("X", raw, T0, T0 + 3 * S, S)
        self.assertEqual(miss, [T0 + S])
        self.assertEqual(len(cs), 3)
        self.assertEqual((cs[1].open, cs[1].volume), (1.5, 0.0))

    def test_kokoaminen(self):
        m = [dict(open=1, high=2, low=0.9, close=1.5, volume=1), dict(open=1.5, high=1.7, low=0.8, close=1.6, volume=2)]
        a = data15.aggregate(m)
        self.assertEqual(a, dict(open=1, high=2, low=0.8, close=1.6, volume=3))
        self.assertTrue(data15.same(a, dict(a)))
        self.assertFalse(data15.same(a, dict(a, close=1.61)))


class TestValinta(unittest.TestCase):
    def test_ehdokkaat(self):
        inst = [dict(symbol="PF_XBTUSD", type="flexible_futures", tradeable=True, tradfi=False, openingDate="2022-03-22T13:15:36Z"),
                dict(symbol="PF_NEWUSD", type="flexible_futures", tradeable=True, tradfi=False, openingDate="2025-03-22T13:15:36Z"),
                dict(symbol="PF_SPYUSD", type="flexible_futures", tradeable=True, tradfi=True, openingDate="2022-03-22T13:15:36Z"),
                dict(symbol="FI_XBTUSD_250101", type="futures_inverse", tradeable=True, openingDate="2022-03-22T13:15:36Z")]
        self.assertEqual([x["symbol"] for x in valinta.ehdokkaat(inst)], ["PF_XBTUSD"])

    def test_valitse(self):
        rows = [dict(symbol=f"S{k}", mediaani=100 - k, data_ok=True, kauppakynttilat=0.995 if k % 3 else 0.98) for k in range(12)]
        rows.append(dict(symbol="EI", mediaani=1000, data_ok=False, kauppakynttilat=None))
        chosen, why = valinta.valitse(rows)
        self.assertEqual(why, "ok")
        self.assertEqual(chosen, ["S1", "S2", "S4", "S5", "S7", "S8"])
        rows = [dict(symbol=f"S{k}", mediaani=100 - k, data_ok=True, kauppakynttilat=0.5) for k in range(10)]
        self.assertNotEqual(valinta.valitse(rows)[1], "ok")


class TestPaatos(unittest.TestCase):
    def test_saanto(self):
        self.assertEqual(an.vaadittu(6), 4)
        self.assertEqual(an.vaadittu(5), 4)
        self.assertEqual(an.vaadittu(4), 3)
        self.assertTrue(an.paatos(5000, 500, 0.001, 0.1, 0.1, 0.1, 6, 0, 3).startswith("KOKONAISPÄÄTÖS AVOIN"))
        self.assertTrue(an.paatos(200, 500, 0.001, 0.1, 0.1, 0.1, 6, 0, 6).startswith("AINEISTO EI RIITÄ"))
        self.assertEqual(an.paatos(5000, 500, 0.001, 0.1, 0.1, 0.1, 4, 2, 6), "AJOITUSETU OSOITETTU (ennen kuluja)")
        self.assertTrue(an.paatos(5000, 500, 0.001, 0.1, 0.1, 0.1, 3, 3, 6).startswith("TILASTOLLINEN ERO"))
        self.assertTrue(an.paatos(5000, 500, 0.001, 0.1, -0.02, 0.1, 6, 0, 6).startswith("TILASTOLLINEN ERO"))
        self.assertEqual(an.paatos(5000, 500, 0.001, -0.1, -0.1, -0.1, 0, 5, 6), "SIGNAALIT SATTUMAA HUONOMPIA")
        self.assertEqual(an.paatos(5000, 500, 0.2, 0.1, 0.1, 0.1, 6, 0, 6), "EI NÄYTTÖÄ AJOITUSEDUSTA")
        self.assertTrue(an.kannattavuus_paatos(0.001, 0.0001, 0.001, 0.001, 4, 4).startswith("KANNATTAVA"))
        self.assertEqual(an.kannattavuus_paatos(0.001, -0.0001, 0.001, 0.001, 4, 4), "EI KANNATTAVA")


class TestVaihe2(unittest.TestCase):
    def test_kulut(self):
        o = {"tulos": "tavoite", "e": 100.0, "px": 102.0, "px_alt": 102.0}
        x = an.net_trade(o, "long", 0.0001, T0, T0 + 3_600_000, {T0: 0.0001})
        entry = 100 * (1 + 0.0003)
        exit_ = 102 * (1 - 0.0003)
        self.assertAlmostEqual(x["brutto"], (exit_ - entry) / entry)
        self.assertAlmostEqual(x["palkkiot"], 0.0005 * (entry + exit_) / entry)
        self.assertAlmostEqual(x["funding"], 0.0001)
        self.assertAlmostEqual(x["netto"], x["brutto"] - x["palkkiot"] - x["funding"])
        o = {"tulos": "epäselvä", "e": 100.0, "px": 102.0, "px_alt": 98.0}     # short: stop 102, tavoite 98
        s = an.net_trade(o, "short", 0.0001, T0, T0 + S, {})
        t = an.net_trade(o, "short", 0.0001, T0, T0 + S, {}, ambiguous_as_target=True)
        self.assertLess(s["netto"], 0)
        self.assertGreater(t["netto"], 0)


if __name__ == "__main__":
    unittest.main()


class TestKaupatonJakso(unittest.TestCase):
    def test_A_nolla_tasaisella_jaksolla(self):
        cs = synth15(60, 7, T0)
        p = cs[29].close
        cs = cs[:30] + [c(T0 + (30 + k) * S, p, p, p, p, 0.0) for k in range(25)] + cs[55:]
        A = an.avg_range_before(cs)
        self.assertEqual(A[50], 0.0)
        self.assertIsNone(an.outcome(cs, 50, "long", A[50], 1.0))
