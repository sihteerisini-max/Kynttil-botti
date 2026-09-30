"""Jatkumissignaali: täsmälliset ehdot, vain suljettu historia, ei pelkkä väri."""
import unittest

from kynttilatulkki.jatkuminen import JATKO, ehdot, signaali
from kynttilatulkki.models import Candle
from kynttilatulkki.patterns import build_context
from kynttilatulkki.strategy import RULESETS, make_signal

T0 = 1_767_225_600_000
M = 60_000


def c(i, o, h, l, cl, v=100.0, closed=True):
    return Candle("PF_X", T0 + i * M, o, h, l, cl, v, closed, T0 + i * M + M - 1)


def laskuhistoria(n=25):
    """Tasainen lasku: jokainen kynttilä 0,1 alempana, vaihteluväli 0,2."""
    out, p = [], 100.0
    for i in range(n):
        out.append(c(i, p, p + 0.05, p - 0.15, p - 0.1))
        p -= 0.1
    return out


class TestJatkuminen(unittest.TestCase):
    def setUp(self):
        self.prev = laskuhistoria()
        self.ctx = build_context(self.prev)
        self.p = self.prev[-1].close           # 97.5

    def test_short_signaali(self):
        cur = c(25, self.p, self.p + 0.02, self.p - 0.30, self.p - 0.28, v=200)
        self.assertEqual(self.ctx.trend, "lasku")
        hit = signaali(self.ctx, cur)
        self.assertIsNotNone(hit)
        self.assertEqual(hit[0], "short")
        sig = make_signal(cur, [], self.ctx, RULESETS["aj1-jatko"])
        self.assertEqual((sig.side, sig.tyyppi), ("short", "jatkuminen"))
        self.assertAlmostEqual(sig.stop, cur.high + 0.1 * self.ctx.avg_range)

    def test_pelkka_vari_ei_riita(self):
        cur = c(25, self.p, self.p + 0.02, self.p - 0.05, self.p - 0.01, v=200)   # pieni laskeva kynttilä
        self.assertIsNone(signaali(self.ctx, cur))
        fails = [x["ehto"] for x in ehdot(self.ctx, cur, "short") if not x["ok"]]
        self.assertTrue(any("runko" in f for f in fails))

    def test_volyymi_vaaditaan(self):
        cur = c(25, self.p, self.p + 0.02, self.p - 0.30, self.p - 0.28, v=100 * (JATKO.volume_min - 0.01))
        self.assertIsNone(signaali(self.ctx, cur))

    def test_murto_vaaditaan(self):
        # päättyy edellisen 10 min alimman yläpuolelle -> ei jatkumista
        low10 = min(x.low for x in self.prev[-10:])
        cur = c(25, low10 + 0.5, low10 + 0.52, low10 + 0.2, low10 + 0.22, v=200)
        self.assertIsNone(signaali(self.ctx, cur))

    def test_ei_trendia_ei_signaalia(self):
        flat = [c(i, 100, 100.1, 99.9, 100 + (0.01 if i % 2 else -0.01)) for i in range(25)]
        ctx = build_context(flat)
        cur = c(25, 100, 100.02, 99.6, 99.62, v=300)
        self.assertEqual(ctx.trend, "sivuttain")
        self.assertIsNone(signaali(ctx, cur))

    def test_long_peilikuva(self):
        up, p = [], 100.0
        for i in range(25):
            up.append(c(i, p, p + 0.15, p - 0.05, p + 0.1))
            p += 0.1
        ctx = build_context(up)
        cur = c(25, p, p + 0.30, p - 0.02, p + 0.28, v=200)
        self.assertEqual(signaali(ctx, cur)[0], "long")

    def test_keskenerainen_kynttila_ei_kelpaa(self):
        cur = c(25, self.p, self.p + 0.02, self.p - 0.30, self.p - 0.28, v=200, closed=False)
        self.assertIsNone(signaali(self.ctx, cur))

    def test_kaantymistili_ei_kayta_jatkumista(self):
        cur = c(25, self.p, self.p + 0.02, self.p - 0.30, self.p - 0.28, v=200)
        self.assertIsNone(make_signal(cur, [], self.ctx, RULESETS["aj1-kaanto"]))

    def test_saannot(self):
        for v in ("aj1-kaanto", "aj1-jatko"):
            r = RULESETS[v]
            self.assertEqual((r.target_r, r.min_r_to_cost, r.max_hold_bars, r.tunnistus), (1.0, 0.0, 15, "T2"))
            self.assertEqual((r.risk_per_trade, r.max_positions, r.daily_loss_limit, r.max_drawdown),
                             (RULESETS["v1.1-T2"].risk_per_trade, 3, 0.02, 0.10))


if __name__ == "__main__":
    unittest.main()
