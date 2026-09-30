"""Seurannan kopio tunnistus- ja signaalikoodista on identtinen botin koodin kanssa."""
import filecmp
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestSeurantaKopio(unittest.TestCase):
    def test_identtinen(self):
        for m in ["models", "patterns", "komponentit", "strategy"]:
            a = os.path.join(ROOT, "kynttilatulkki", m + ".py")
            b = os.path.join(ROOT, "seuranta", "kynttilatulkki", m + ".py")
            self.assertTrue(filecmp.cmp(a, b, shallow=False), f"{m}.py eroaa – aja python -m seuranta.synkronoi")


if __name__ == "__main__":
    unittest.main()
