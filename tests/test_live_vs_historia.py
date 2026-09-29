"""Live-paperikauppasilmukka simuloidulla Kraken-rajapinnalla tuottaa samat
kaupat kuin historiatesti samalla datalla (= samat säännöt, sama moottori)."""
import json
import os
import tempfile
import unittest
from dataclasses import asdict
from unittest import mock

from kynttilatulkki import kraken, paper_live
from kynttilatulkki.backtest import run, synthetic
from kynttilatulkki.models import Candle

T0 = 1_767_225_600_000
M = 60_000


class TestLiveVastaaHistoriaa(unittest.TestCase):
    def test_samat_kaupat(self):
        data = {s: synthetic(s, T0, 700, seed=i + 1) for i, s in enumerate(["PF_A", "PF_B"])}
        stop_at = T0 + 600 * M
        clock = [T0 + 20 * M + 5_000]

        def fetch_candles(sym, start, end, base=None, now_ms=None):
            now, out = clock[0], []
            for c in data[sym]:
                if start <= c.open_time < end and c.open_time <= now:
                    if c.open_time + M <= now:
                        out.append(c)
                    else:
                        out.append(Candle(sym, c.open_time, c.open, c.open, c.open, c.open, 1.0, False, c.close_time))
            return out

        def sleep(_):
            clock[0] += 20_000
            if clock[0] > stop_at:
                raise KeyboardInterrupt

        tickers = {s: kraken.Ticker(s, 99.99, 100.01, 100, 0.00001, 1e6) for s in data}
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(kraken, "fetch_tickers", lambda base=None: tickers), \
                mock.patch.object(kraken, "top_perpetuals", lambda n, base=None: list(data)), \
                mock.patch.object(kraken, "fetch_candles", fetch_candles), \
                mock.patch.object(paper_live.time, "time", lambda: clock[0] / 1000), \
                mock.patch.object(paper_live.time, "sleep", sleep), \
                mock.patch("builtins.print"):
            paper_live.main(["--rules", "v1,v2", "--state-dir", d, "--log-dir", d])
            live = {}
            for v in ("v1", "v2"):
                with open(os.path.join(d, f"kaupat_{v}.jsonl")) as f:
                    live[v] = [json.loads(x) for x in f]

        cut = {s: [c for c in cs if c.open_time < stop_at - M] for s, cs in data.items()}
        fund = {s: {T0 + h * 3_600_000: 0.00001 for h in range(24)} for s in data}
        key = lambda t: (t["symbol"], t["side"], t["entry_time"], round(t["entry_price"], 6),
                         t["exit_time"], round(t["exit_price"], 6), t["close_reason"], round(t["net_pnl"], 3))
        for v in ("v1", "v2"):      # kaksi rinnakkaista tiliä, kumpikin = oma historiatestinsä
            bt = run(cut, v, {s: 0.0001 for s in data}, fund, log=lambda m: None)
            b = [key(asdict(t)) for t in bt.trades if t.close_reason != "testijakson loppu"]
            self.assertGreater(len(b), 0 if v == "v2" else 2)
            self.assertEqual(b, [key(t) for t in live[v]], v)


if __name__ == "__main__":
    unittest.main()
