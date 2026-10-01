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


class TestYhteenveto(unittest.TestCase):
    def test_kattavuus_puuttuvat_ja_nollatarkistus(self):
        A = keruu.TOISTO_ALKU
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "kynttilat"))
            with open(os.path.join(d, "kynttilat", "PF_X.csv"), "w") as f:
                f.write("open_time,open,high,low,close,volume,haettu_ms\n")
                f.write(f"{A - 60000},1,1,1,1,5,0\n")              # lämmittely, ei lasketa
                for k, v in ((0, 5), (1, 0), (3, 2)):              # minuutti 2 puuttuu
                    f.write(f"{A + k * 60000},1,1,1,1,{v},0\n")
            with open(os.path.join(d, "nollaminuutit.csv"), "w") as f:
                f.write("symboli,open_time,kauppoja_minuutilla,historia_n,tarkistettu_ms\n")
                f.write(f"PF_X,{A + 60000},0,100,0\n")
            y = keruu.yhteenveto(d, ["PF_X", "PF_Y"], now_ms=A + 10 * 60000)
            x = y["markkinat"][0]
            self.assertEqual((x["minuutteja"], x["odotettu"], x["puuttuu"], x["kauppaminuutteja"]), (3, 4, 1, 2))
            self.assertAlmostEqual(x["kattavuus"], 2 / 3)
            self.assertEqual((x["nolla_tarkistettu"], x["nolla_kauppoja_loytyi"]), (1, 0))
            self.assertIsNone(y["markkinat"][1]["kattavuus"])
