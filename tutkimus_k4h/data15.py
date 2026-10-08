"""Tutkimus 15M: Krakenin julkisen datan haku ja tallennus (vain luku, ei toimeksiantoja).

Suunnitelma: docs/TUTKIMUS15_SUUNNITELMA.md. Aika on aina millisekunteina UTC.
"""
from __future__ import annotations

import csv
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from kt.models import Candle

BASE = "https://futures.kraken.com"
MIN = 60_000
STEP15 = 15 * MIN
DAY = 86_400_000
RES = {"1m": MIN, "15m": STEP15}


def ms(s: str) -> int:
    """'2025-01-01' tai '2025-01-01T06:00' (UTC) -> ms."""
    if "T" not in s:
        s += "T00:00"
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp() * 1000)


def iso(t: int) -> str:
    return datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M")


def http_json(url: str, tries: int = 6, pause: float = 0.12) -> dict:
    err = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kynttilabotti-tutkimus15/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                out = json.loads(r.read().decode())
            time.sleep(pause)
            return out
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError) as e:
            err = e
            time.sleep(min(30, 1.5 * 2 ** k))
    raise RuntimeError(f"haku epäonnistui {url}: {err}")


def charts(sym: str, res: str, frm: int, to: int, get=http_json) -> dict[int, dict]:
    """Kynttilät [frm, to) avainnettuna avausajalla. Sivutus more_candles-lipulla."""
    step = RES[res]
    out: dict[int, dict] = {}
    f = frm // 1000
    end = to // 1000
    while f < end:
        d = get(f"{BASE}/api/charts/v1/trade/{sym}/{res}?from={f}&to={end}")
        cs = d.get("candles") or []
        for c in cs:
            t = int(c["time"])
            if frm <= t < to:
                out[t] = {"open": float(c["open"]), "high": float(c["high"]), "low": float(c["low"]),
                          "close": float(c["close"]), "volume": float(c["volume"])}
        if not cs or not d.get("more_candles"):
            break
        nxt = int(cs[-1]["time"]) // 1000 + step // 1000
        if nxt <= f:
            break
        f = nxt
    return out


def to_candles(sym: str, raw: dict[int, dict], frm: int, to: int, step: int) -> tuple[list[Candle], list[int]]:
    """Säännöllinen sarja [frm, to). Puuttuvat rivit täytetään edellisellä päätöksellä (volyymi 0)
    ja palautetaan erikseen listana (puuttuva ≠ API:n palauttama kaupaton kynttilä)."""
    out: list[Candle] = []
    missing: list[int] = []
    prev = None
    t = frm
    while t < to:
        c = raw.get(t)
        if c is None:
            missing.append(t)
            if prev is not None:
                p = prev.close
                out.append(Candle(sym, t, p, p, p, p, 0.0, True, t + step - 1))
        else:
            out.append(Candle(sym, t, c["open"], c["high"], c["low"], c["close"], c["volume"], True, t + step - 1))
        if out:
            prev = out[-1]
        t += step
    return out, missing


def write_csv(path: str, raw: dict[int, dict]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["open_time", "open", "high", "low", "close", "volume"])
        for t in sorted(raw):
            c = raw[t]
            w.writerow([t, repr(c["open"]), repr(c["high"]), repr(c["low"]), repr(c["close"]), repr(c["volume"])])


def read_csv(path: str) -> dict[int, dict]:
    out = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[int(r["open_time"])] = {k: float(r[k]) for k in ("open", "high", "low", "close", "volume")}
    return out


def aggregate(minutes: list[dict]) -> dict | None:
    """1m-kynttilät (aikajärjestyksessä) -> yksi kynttilä."""
    if not minutes:
        return None
    return {"open": minutes[0]["open"], "high": max(m["high"] for m in minutes),
            "low": min(m["low"] for m in minutes), "close": minutes[-1]["close"],
            "volume": sum(m["volume"] for m in minutes)}


def same(a: dict, b: dict, rel_px: float = 1e-9, rel_vol: float = 1e-6) -> bool:
    for k in ("open", "high", "low", "close"):
        if abs(a[k] - b[k]) > rel_px * max(abs(a[k]), abs(b[k]), 1e-12):
            return False
    return abs(a["volume"] - b["volume"]) <= rel_vol * max(abs(a["volume"]), abs(b["volume"]), 1.0)
