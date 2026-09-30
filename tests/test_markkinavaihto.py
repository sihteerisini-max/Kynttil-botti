"""Markkinalistan vaihto: tilit, aloitushetki ja säännöt säilyvät, vaihto kirjataan tapahtumaksi."""
import json
import os
import pickle
import tempfile
import unittest
from unittest import mock

from kynttilatulkki import kraken, paper_live
from kynttilatulkki.backtest import synthetic
from kynttilatulkki.models import Candle

T0 = 1_767_225_600_000
M = 60_000


def aja(d, symbols, data, clock, stop_at):
    def fetch_candles(sym, start, end, base=None, now_ms=None):
        now, out = clock[0], []
        for c in data[sym]:
            if start <= c.open_time < end and c.open_time <= now:
                out.append(c if c.open_time + M <= now else
                           Candle(sym, c.open_time, c.open, c.open, c.open, c.open, 1.0, False, c.close_time))
        return out

    def sleep(_):
        clock[0] += 20_000
        if clock[0] > stop_at:
            raise KeyboardInterrupt

    specs = {s: kraken.InstrumentSpec(s, 0.001, 1e9, ((0.0, 0.01),)) for s in data}
    tickers = {s: kraken.Ticker(s, 99.99, 100.01, 100, 0.00001, 1e6) for s in data}
    with mock.patch.object(kraken, "fetch_tickers", lambda base=None: tickers), \
            mock.patch.object(kraken, "fetch_instruments", lambda base=None: specs), \
            mock.patch.object(kraken, "fetch_candles", fetch_candles), \
            mock.patch.object(paper_live.time, "time", lambda: clock[0] / 1000), \
            mock.patch.object(paper_live.time, "sleep", sleep), \
            mock.patch("builtins.print"):
        paper_live.main(["--rules", "v1.1-T2,v2-T2", "--symbols", symbols, "--state-dir", d, "--log-dir", d])


class TestMarkkinavaihto(unittest.TestCase):
    def test_vaihto(self):
        data = {s: synthetic(s, T0, 500, seed=i + 1) for i, s in enumerate(["PF_A", "PF_B", "PF_C"])}
        clock = [T0 + 20 * M + 5_000]
        with tempfile.TemporaryDirectory() as d:
            aja(d, "PF_A,PF_B", data, clock, T0 + 200 * M)
            st1 = pickle.load(open(os.path.join(d, "paper_v1.1-T2.pkl"), "rb"))
            aja(d, "PF_B,PF_C", data, clock, T0 + 400 * M)
            st2 = pickle.load(open(os.path.join(d, "paper_v1.1-T2.pkl"), "rb"))
            ev = [json.loads(x) for x in open(os.path.join(d, "tapahtumat_v1.1-T2.jsonl"))]
        self.assertEqual(st1["symbols"], ["PF_A", "PF_B"])
        self.assertEqual(st2["symbols"], ["PF_B", "PF_C"])
        self.assertEqual(st1["started_at"], st2["started_at"])          # testijakson alku ei muutu
        ch = [e for e in ev if e["kind"] == "markkinat_vaihdettu"]
        self.assertEqual(len(ch), 1)
        self.assertEqual((ch[0]["old"], ch[0]["new"]), (["PF_A", "PF_B"], ["PF_B", "PF_C"]))
        self.assertEqual(len(st2["symbol_changes"]), 1)
        # vaihdon jälkeen ei avata kauppoja poistuneella markkinalla
        opens_a = [e for e in ev if e["kind"] == "open" and e["symbol"] == "PF_A" and e["entry_time"] > ch[0]["time"]]
        self.assertEqual(opens_a, [])


if __name__ == "__main__":
    unittest.main()
