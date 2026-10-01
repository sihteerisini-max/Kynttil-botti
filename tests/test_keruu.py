"""Seurannan tiedonkeruu: kynttilät talteen ilman aukkoja/tuplia, kauppattomien minuuttien tarkistus."""
import json
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "seuranta"))
import keruu  # noqa: E402

M = 60_000


class TestKeruu(unittest.TestCase):
    def test_tallennus_ja_nollatarkistus(self):
        now = [1_790_000_000_000 // M * M + 30_000]
        hist_calls = []

        def get(url):
            if "/charts/" in url:
                q = dict(x.split("=") for x in url.split("?")[1].split("&"))
                f, t = int(q["from"]) * 1000, int(q["to"]) * 1000
                cs = [{"time": x, "open": "1", "high": "1", "low": "1", "close": "1",
                       "volume": "0" if (x // M) % 7 == 0 else "5"} for x in range(f // M * M, t, M)]
                return json.dumps({"candles": cs, "more_candles": False}).encode()
            hist_calls.append(url)
            return json.dumps({"result": "success", "history": [{"time": "2020-01-01T00:00:00Z"}]}).encode()

        with tempfile.TemporaryDirectory() as d, mock.patch.object(keruu.time, "time", lambda: now[0] / 1000):
            k = keruu.Keruu(d, ["PF_A"], get, log=lambda m: None)
            k.kierros()
            now[0] += 5 * M
            k.kierros()
            k2 = keruu.Keruu(d, ["PF_A"], get, log=lambda m: None)      # uudelleenkäynnistys
            now[0] += 3 * M
            k2.kierros()
            rows = [l.split(",") for l in open(os.path.join(d, "kynttilat", "PF_A.csv")) if l[0].isdigit()]
            ts = [int(r[0]) for r in rows]
            self.assertEqual(ts, sorted(set(ts)))                         # ei tuplia
            self.assertTrue(all(b - a == M for a, b in zip(ts, ts[1:])))  # ei aukkoja
            self.assertLessEqual(ts[-1], now[0] - keruu.SETTLE)           # vain vakiintuneet
            z = open(os.path.join(d, "nollaminuutit.csv")).read().splitlines()[1:]
            self.assertTrue(z and all(r.split(",")[2] == "0" for r in z))
            self.assertTrue(hist_calls)


if __name__ == "__main__":
    unittest.main()
