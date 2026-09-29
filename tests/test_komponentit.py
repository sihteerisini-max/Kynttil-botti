"""Muoto- ja taustaehtojen erittely vastaa täsmälleen detect()-tulosta."""
import glob
import os
import unittest

from kynttilatulkki.analyzer import SymbolAnalyzer
from kynttilatulkki.komponentit import PATTERNS, components, detected_patterns
from kynttilatulkki.patterns import detect
from kynttilatulkki.replay import synthetic_ticks

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check(tc, candles):
    hist, n = [], 0
    for c in candles:
        comp = components(hist, c)
        if comp is not None:
            keys = {o.key for o in detect(hist, c)}
            size_ok = comp["doji"]["tausta"]
            expect = {k for k in PATTERNS if "engulfing" not in k and comp[k]["muoto"] and comp[k]["tausta"]}
            tc.assertEqual(detected_patterns(keys), expect, c.open_time)
            for k in ("bullish_engulfing", "bearish_engulfing"):
                tc.assertEqual(k in keys, comp[k]["muoto"] and size_ok, (c.open_time, k))
            n += 1
        hist.append(c)
        hist = hist[-100:]
    return n


class TestKomponentit(unittest.TestCase):
    def test_synteettinen(self):
        cs = [c for c, _ in synthetic_ticks(minutes=600, seed=5) if c.closed]
        self.assertGreater(check(self, cs), 500)

    def test_jakso_a_jos_saatavilla(self):
        files = glob.glob(os.path.join(ROOT, "data", "PF_*_2026-09-22T1843_*.csv"))
        if not files:
            self.skipTest("jakson A dataa ei ole tässä ympäristössä")
        from kynttilatulkki.backtest import load_csv
        n = sum(check(self, load_csv(f, "X")) for f in files)
        self.assertGreater(n, 40_000)
