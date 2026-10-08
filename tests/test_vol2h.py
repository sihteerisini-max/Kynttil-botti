"""Kehitystesti VOL2H: M ja R2 vain menneestä, stop/tavoite, kulusuodatin, stop ensin samassa kynttilässä."""
import unittest

from kynttilatulkki.models import Candle
from kynttilatulkki.strategy import Signal
from tutkimus import vol2h

MIN = 60_000


def c(t, o, h, l, cl, v=10.0, s="X"):
    return Candle(s, t, o, h, l, cl, v, True, t + MIN - 1)


def hist(n=130, step=0.1):
    return [c(k * MIN, 100 + k * step, 100 + k * step + 0.05, 100 + k * step - 0.05, 100 + (k + 1) * step) for k in range(n)]


class TestMittarit(unittest.TestCase):
    def test_m_ja_r2(self):
        h = hist()
        m, r2 = vol2h.vol_mittarit(h)
        self.assertAlmostEqual(m, 1.5)                       # 15 × 0,1
        w = h[-120:]
        self.assertAlmostEqual(r2, max(x.high for x in w) - min(x.low for x in w))
        self.assertIsNone(vol2h.vol_mittarit(h[:119]))

    def test_ikkuna_on_viimeiset_120(self):
        h = hist(200)
        self.assertEqual(vol2h.vol_mittarit(h), vol2h.vol_mittarit(h[-120:]))


class TestMoottori(unittest.TestCase):
    def _eng(self, kt=1.0, ks=1.0, hs=0.0001):
        r = vol2h.ilman_tappiorajoja("aj1-kaanto")
        trades, events = [], []
        e = vol2h.VolEngine(r, lambda s, t: hs, lambda s, t: 0.0, kt, ks, log=lambda m: None,
                            on_trade=trades.append, on_event=events.append, verbose_signals=False)
        for x in hist():
            e.buf["X"].append(x)
        return e, trades, events

    def test_stop_ja_tavoite(self):
        e, trades, events = self._eng()
        h = list(e.buf["X"])
        sig = Signal("X", "long", h[-1], stop=0.0, avg_range=0.1)
        price = 113.1
        e._try_open(sig, 130 * MIN, price)
        pos = e.positions["X"]
        self.assertAlmostEqual(pos.stop, price - 1.5)
        self.assertAlmostEqual(pos.target, price + min(1.5, 0.5 * vol2h.vol_mittarit(h)[1]))

    def test_kulusuodatin(self):
        e, trades, events = self._eng(kt=0.001)
        h = list(e.buf["X"])
        e._try_open(Signal("X", "long", h[-1], stop=0.0, avg_range=0.1), 130 * MIN, 113.1)
        self.assertNotIn("X", e.positions)
        self.assertTrue(any("kulusuodatin" in ev.get("why", "") for ev in events))

    def test_puskurissa_vain_suljetut(self):
        e, trades, events = self._eng()
        x = c(130 * MIN, 113.0, 113.1, 112.9, 113.05)
        e.on_bar_close(x)
        self.assertIs(e.buf["X"][-1], x)          # signaalikynttilä viimeisenä, avauskynttilää ei ole vielä
        self.assertEqual(len(e.buf["X"]), 120)

    def test_sama_kynttila_stop_ensin(self):
        e, trades, events = self._eng()
        h = list(e.buf["X"])
        e._try_open(Signal("X", "long", h[-1], stop=0.0, avg_range=0.1), 130 * MIN, 113.1)
        e.on_bar_close(c(130 * MIN, 113.1, 120.0, 100.0, 113.0))
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].lopputulos, "epäselvä")
        self.assertLess(trades[0].net_pnl, 0)


if __name__ == "__main__":
    unittest.main()
