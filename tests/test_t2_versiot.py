"""T2-testin versiot eroavat pohjaversioistaan vain tunnistuksen osalta."""
import unittest
from dataclasses import asdict

from kynttilatulkki.paper import PaperEngine
from kynttilatulkki.patterns import TUNNISTUS
from kynttilatulkki.strategy import RULESETS


class TestT2Versiot(unittest.TestCase):
    def test_ainoa_ero_tunnistus(self):
        for base in ("v1.1", "v2"):
            a, b = asdict(RULESETS[base]), asdict(RULESETS[base + "-T2"])
            diff = {k for k in a if a[k] != b[k]}
            self.assertEqual(diff, {"version", "tunnistus", "notes"}, base)
            self.assertEqual(b["tunnistus"], "T2")

    def test_lukitut_versiot_kayttavat_T1(self):
        for v in ("v1", "v1.1", "v2"):
            self.assertEqual(RULESETS[v].tunnistus, "T1")

    def test_moottori_kayttaa_version_tunnistusta(self):
        for v, t in (("v1.1", "T1"), ("v1.1-T2", "T2")):
            e = PaperEngine(RULESETS[v], lambda s, t: 0.0001, lambda s, t: None, log=lambda m: None)
            self.assertIs(e.analyzer("PF_X").params, TUNNISTUS[t])


if __name__ == "__main__":
    unittest.main()
