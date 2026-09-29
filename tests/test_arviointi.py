import unittest

from kynttilatulkki import evaluate as ev

D0 = 1_767_225_600_000 // ev.DAY


def trade(day, x, hh=12):
    from datetime import datetime, timezone
    t = datetime.fromtimestamp((D0 + day) * 86400 + hh * 3600, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return {"exit_time": t, "budget_multiple": x, "net_pnl": 50 * x, "fees": 1, "spread_slippage_est": 1,
            "funding": 0, "gross_pnl": 50 * x + 1, "close_reason": "stop loss"}


class TestArviointi(unittest.TestCase):
    def verdict_of(self, trades, days=28):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ev.analyse("x", trades, D0, D0 + days - 1)
        return [l for l in buf.getvalue().splitlines() if l.startswith("Tulkinta")][0]

    def test_alle_30_keskenerainen(self):
        self.assertIn("KESKENERÄINEN", self.verdict_of([trade(d, 1.0) for d in range(20)]))

    def test_liian_vahan_paivia(self):
        ts = [trade(d % 5, 1.0, hh=d % 20) for d in range(40)]
        self.assertIn("KESKENERÄINEN", self.verdict_of(ts))

    def test_yhden_paivan_voitto_ei_riita(self):
        ts = [trade(d, -0.05) for d in range(28)] + [trade(3, 3.0, hh=h) for h in range(10)]
        self.assertNotIn("ALUSTAVA", self.verdict_of(ts))

    def test_tasainen_voitto(self):
        ts = [trade(d, x, hh=h) for d in range(28) for h, x in ((9, 0.6), (15, -0.2))]
        self.assertIn("ALUSTAVA NÄYTTÖ VOITOLLISUUDESTA", self.verdict_of(ts))

    def test_tappiollinen(self):
        ts = [trade(d, x, hh=h) for d in range(28) for h, x in ((9, -1.0), (15, 0.2))]
        self.assertIn("TAPPIOLLISUUDESTA", self.verdict_of(ts))

    def test_lohkovali_leveampi_kun_paivat_korreloivat(self):
        import random
        rnd = random.Random(0)
        ts = []
        for d in range(28):
            mood = rnd.choice([-1.0, 1.0])            # koko päivän kaupat samaan suuntaan
            ts += [trade(d, mood + rnd.gauss(0, 0.1), hh=h) for h in range(3)]
        days = ev.day_table(ts, D0, D0 + 27)
        lo_d, hi_d = ev.day_block_ci(days)
        xs = [t["budget_multiple"] for t in ts]
        import statistics as st
        naive = 1.96 * st.pstdev(xs) / len(xs) ** 0.5
        self.assertGreater(hi_d - lo_d, 2 * naive * 1.2)
