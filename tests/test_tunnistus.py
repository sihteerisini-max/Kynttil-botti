import unittest

from kynttilatulkki.analyzer import SymbolAnalyzer
from kynttilatulkki.models import Candle
from kynttilatulkki.patterns import build_context, detect
from kynttilatulkki.replay import synthetic_ticks

T0 = 1_767_225_600_000
M = 60_000


def history(trend: str, n: int = 20, start: float = 100.0, vol: float = 100.0):
    """n suljettua kynttilää, vaihteluväli ~1.0, runko 0.5."""
    step = {"nousu": 0.5, "lasku": -0.5, "sivuttain": 0.0}[trend]
    out, p = [], start
    for i in range(n):
        o = p
        c = p + (step if step else (0.25 if i % 2 else -0.25))
        out.append(Candle("TEST", T0 + i * M, o, max(o, c) + 0.25, min(o, c) - 0.25, c, vol))
        p = c
    return out


def nxt(prev, o, h, l, c, vol=100.0, closed=True):
    return Candle("TEST", prev[-1].open_time + M, o, h, l, c, vol, closed=closed)


def keys(obs):
    return {o.key for o in obs}


class TestKonteksti(unittest.TestCase):
    def test_trendit(self):
        self.assertEqual(build_context(history("nousu")).trend, "nousu")
        self.assertEqual(build_context(history("lasku")).trend, "lasku")
        self.assertEqual(build_context(history("sivuttain")).trend, "sivuttain")

    def test_liian_vahan_historiaa(self):
        h = history("lasku", n=10)
        self.assertEqual(detect(h, nxt(h, 95, 95.1, 94, 95)), [])


class TestYksittaiset(unittest.TestCase):
    def test_vasara_laskun_jalkeen(self):
        h = history("lasku")
        p = h[-1].close
        # runko 0.2 ylhäällä, pitkä alavarjo 1.0, yläsvarjo 0.02
        c = nxt(h, p, p + 0.22, p - 1.0, p + 0.2, vol=200)
        obs = detect(h, c)
        self.assertIn("hammer", keys(obs))
        o = [o for o in obs if o.key == "hammer"][0]
        self.assertEqual(o.bias, "nousuun viittaava")
        self.assertEqual(o.strength, "selvempi")   # konteksti + uusi pohja + volyymi

    def test_sama_muoto_nousussa_on_hirttaytyja(self):
        h = history("nousu")
        p = h[-1].close
        c = nxt(h, p, p + 0.22, p - 1.0, p + 0.2)
        self.assertIn("hanging_man", keys(detect(h, c)))
        self.assertNotIn("hammer", keys(detect(h, c)))

    def test_sama_muoto_sivuttain_neutraali(self):
        h = history("sivuttain")
        p = h[-1].close
        c = nxt(h, p, p + 0.22, p - 1.0, p + 0.2)
        self.assertIn("hammer_shape", keys(detect(h, c)))

    def test_tahdenlento_nousun_jalkeen(self):
        h = history("nousu")
        p = h[-1].close
        c = nxt(h, p, p + 1.0, p - 0.22, p - 0.2)
        self.assertIn("shooting_star", keys(detect(h, c)))

    def test_kaanteinen_vasara_laskussa(self):
        h = history("lasku")
        p = h[-1].close
        c = nxt(h, p, p + 1.0, p - 0.02, p + 0.2)
        self.assertIn("inverted_hammer", keys(detect(h, c)))

    def test_doji_ja_alatyypit(self):
        h = history("nousu")
        p = h[-1].close
        self.assertIn("long_legged_doji", keys(detect(h, nxt(h, p, p + 0.6, p - 0.6, p + 0.02))))
        self.assertIn("gravestone_doji", keys(detect(h, nxt(h, p, p + 1.0, p - 0.02, p))))
        self.assertIn("dragonfly_doji", keys(detect(h, nxt(h, p, p + 0.02, p - 1.0, p))))

    def test_pieni_kynttila_ei_tulkita(self):
        h = history("nousu")
        p = h[-1].close
        self.assertEqual(detect(h, nxt(h, p, p + 0.1, p - 0.1, p)), [])

    def test_ei_vasaraa_jos_ylavarjo_pitka(self):
        h = history("lasku")
        p = h[-1].close
        c = nxt(h, p, p + 0.6, p - 1.0, p + 0.2)
        self.assertNotIn("hammer", keys(detect(h, c)))


class TestPeittava(unittest.TestCase):
    def test_nouseva_peittava(self):
        h = history("lasku")   # viimeinen kynttilä laskeva, runko 0.5
        pc = h[-1]
        c = nxt(h, pc.close, pc.open + 0.5, pc.close - 0.1, pc.open + 0.4)
        self.assertIn("bullish_engulfing", keys(detect(h, c)))

    def test_laskeva_peittava(self):
        h = history("nousu")
        pc = h[-1]
        c = nxt(h, pc.close, pc.close + 0.1, pc.open - 0.5, pc.open - 0.4)
        self.assertIn("bearish_engulfing", keys(detect(h, c)))

    def test_ei_peita_jos_runko_pienempi(self):
        h = history("lasku")
        pc = h[-1]
        c = nxt(h, pc.close, pc.close + 0.5, pc.close - 0.1, pc.close + 0.3)
        self.assertNotIn("bullish_engulfing", keys(detect(h, c)))


class TestKeskeneräinenVsVahvistettu(unittest.TestCase):
    def test_keskenerainen_ei_vahvistu(self):
        h = history("lasku")
        an = SymbolAnalyzer("TEST")
        an.warmup(h)
        p = h[-1].close
        t = h[-1].open_time + M
        # 30 s kohdalla vasaran muoto
        ev = an.update(Candle("TEST", t, p, p + 0.22, p - 1.0, p + 0.2, 60, closed=False), now_ms=t + 30_000)
        self.assertEqual(ev[0].kind, "provisional")
        self.assertEqual(ev[0].observations[0].status, "KESKENERÄINEN")
        # suljettaessa hinta nousi selvästi -> ei enää vasara
        ev = an.update(Candle("TEST", t, p, p + 1.2, p - 1.0, p + 1.1, 120, closed=True), now_ms=t + M)
        kinds = [e.kind for e in ev]
        self.assertIn("not_confirmed", kinds)
        self.assertNotIn("hammer", {o.key for e in ev for o in e.observations})

    def test_vahvistettu_merkitaan(self):
        h = history("lasku")
        an = SymbolAnalyzer("TEST")
        an.warmup(h)
        p = h[-1].close
        ev = an.update(nxt(h, p, p + 0.22, p - 1.0, p + 0.2))
        conf = [e for e in ev if e.kind == "confirmed"]
        self.assertTrue(conf and conf[0].observations[0].status == "VAHVISTETTU")

    def test_sama_keskenerainen_ei_toistu(self):
        h = history("lasku")
        an = SymbolAnalyzer("TEST")
        an.warmup(h)
        p = h[-1].close
        t = h[-1].open_time + M
        c = Candle("TEST", t, p, p + 0.22, p - 1.0, p + 0.2, 60, closed=False)
        self.assertTrue(an.update(c, now_ms=t + 20_000))
        self.assertEqual(an.update(c, now_ms=t + 25_000), [])


class TestEiTulevaisuustietoa(unittest.TestCase):
    def test_detect_hylkaa_tulevan_historian(self):
        h = history("lasku")
        with self.assertRaises(ValueError):
            detect(h, h[5])

    def test_katkaistu_data_antaa_samat_havainnot(self):
        """Havainto kynttilästä i on sama riippumatta siitä, onko dataa
        olemassa i:n jälkeen."""
        closed = [c for c, _ in synthetic_ticks(minutes=200, seed=3) if c.closed]
        full = SymbolAnalyzer("DEMOUSDT")
        full_obs = {}
        for c in closed:
            for ev in full.update(c):
                if ev.kind == "confirmed":
                    full_obs[c.open_time] = [o.to_dict() for o in ev.observations]
        self.assertGreater(len(full_obs), 5)
        for cut in (40, 77, 120, 199):
            part = SymbolAnalyzer("DEMOUSDT")
            got = []
            for c in closed[:cut + 1]:
                for ev in part.update(c):
                    if ev.kind == "confirmed" and c.open_time == closed[cut].open_time:
                        got = [o.to_dict() for o in ev.observations]
            self.assertEqual(got, full_obs.get(closed[cut].open_time, []))

    def test_tulevaisuuden_muutos_ei_vaikuta_menneeseen(self):
        closed = [c for c, _ in synthetic_ticks(minutes=120, seed=11) if c.closed]
        tampered = closed[:80] + [Candle(c.symbol, c.open_time, c.open * 3, c.high * 3,
                                         c.low * 3, c.close * 3, c.volume * 50) for c in closed[80:]]

        def run(cs):
            an, res = SymbolAnalyzer("X"), []
            for c in cs[:80]:
                res += [o.to_dict() for ev in an.update(c) for o in ev.observations]
            return res
        self.assertEqual(run(closed), run(tampered))


if __name__ == "__main__":
    unittest.main()
