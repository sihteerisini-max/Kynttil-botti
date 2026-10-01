"""Toistojakson (vaihe 1) tiedonkeruu: 1 min kynttilät talteen jatkuvasti ja kauppattomien
minuuttien tarkistus Krakenin julkisesta kauppahistoriasta (vain luku, ei vaikuta bottiin).

* RECORD_DIR/kynttilat/<SYMBOLI>.csv  – open_time,open,high,low,close,volume,haettu_ms
  (kynttilä tallennetaan, kun se on ollut suljettuna ≥ 2 min; uudelleenkäynnistyksessä aukko täytetään)
* RECORD_DIR/nollaminuutit.csv        – symboli,open_time,kauppoja_minuutilla,historia_n,tarkistettu_ms
  (volyymi 0 -> haetaan kauppahistoria minuutin lopusta taaksepäin: 0 kauppaa = aito kauppaton minuutti)
* RECORD_DIR/keruu_tila.json          – viimeisin onnistunut kierros ja virheet

Ensisijainen analyysiaineisto ladataan jakson jälkeen Krakenilta (docs/VAIHE1_AJOITUSTUTKIMUS.md);
tämä keruu on varmuuskopio ja datan eheyden tarkistus.
"""
from __future__ import annotations

import csv
import json
import os
import threading
import time
import urllib.parse
from datetime import datetime, timezone

CHARTS = "https://futures.kraken.com/api/charts/v1/trade/{sym}/1m?from={frm}&to={to}"
HISTORY = "https://futures.kraken.com/derivatives/api/v3/history?symbol={sym}&lastTime={t}"
MIN = 60_000
SETTLE = 2 * MIN          # kynttilä tallennetaan vasta, kun se on ollut suljettuna 2 min
BACKFILL_MAX = 24 * 60 * MIN


class Keruu:
    def __init__(self, root: str, symbols: list[str], http_get, log=print):
        self.root, self.symbols, self.get, self.log = root, symbols, http_get, log
        self.cdir = os.path.join(root, "kynttilat")
        os.makedirs(self.cdir, exist_ok=True)
        self.last: dict[str, int] = {s: self._last_time(s) for s in symbols}
        self.state = {"kaynnistetty": int(time.time() * 1000), "kierroksia": 0, "viimeisin_ok": None,
                      "virheet": [], "nollaminuutteja": 0, "nolla_tarkistettu": 0, "nolla_kauppoja_loytyi": 0}

    def _path(self, s: str) -> str:
        return os.path.join(self.cdir, f"{s}.csv")

    def _last_time(self, s: str) -> int | None:
        p = self._path(s)
        if not os.path.exists(p):
            return None
        last = None
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line and line[0].isdigit():
                    last = int(line.split(",", 1)[0])
        return last

    def _candles(self, s: str, frm_ms: int, to_ms: int) -> list[dict]:
        out, frm, to = {}, frm_ms // 1000, to_ms // 1000
        while frm < to:
            d = json.loads(self.get(CHARTS.format(sym=s, frm=frm, to=to)))
            cs = d.get("candles") or []
            for c in cs:
                out[int(c["time"])] = c
            if not cs or not d.get("more_candles"):
                break
            nxt = int(cs[-1]["time"]) // 1000 + 60
            if nxt <= frm:
                break
            frm = nxt
        return [out[k] for k in sorted(out)]

    def _check_zero(self, s: str, t: int) -> tuple[int, int]:
        iso = datetime.fromtimestamp((t + MIN) / 1000, timezone.utc).isoformat().replace("+00:00", "Z")
        d = json.loads(self.get(HISTORY.format(sym=s, t=urllib.parse.quote(iso))))
        h = d.get("history") or []
        n = 0
        for x in h:
            try:
                tt = datetime.fromisoformat(x["time"].replace("Z", "+00:00")).timestamp() * 1000
            except Exception:
                continue
            if t <= tt < t + MIN:
                n += 1
        return n, len(h)

    def kierros(self) -> None:
        now = int(time.time() * 1000)
        upto = (now - SETTLE) // MIN * MIN          # tallennetaan kynttilät < upto
        errs = []
        for s in self.symbols:
            try:
                start = (self.last[s] + MIN) if self.last[s] else upto - BACKFILL_MAX
                start = max(start, upto - BACKFILL_MAX)
                if start >= upto:
                    continue
                cs = [c for c in self._candles(s, start, upto) if start <= int(c["time"]) < upto]
                new = []
                with open(self._path(s), "a", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    if f.tell() == 0:
                        w.writerow(["open_time", "open", "high", "low", "close", "volume", "haettu_ms"])
                    for c in cs:
                        w.writerow([int(c["time"]), c["open"], c["high"], c["low"], c["close"], c["volume"], now])
                        new.append(c)
                if new:
                    self.last[s] = int(new[-1]["time"])
                # kauppattomien minuuttien tarkistus (vain tuoreet: kauppahistoria kattaa vain viime ajan)
                for c in new:
                    if float(c["volume"]) == 0 and now - int(c["time"]) < 30 * MIN:
                        self.state["nollaminuutteja"] += 1
                        try:
                            n, hn = self._check_zero(s, int(c["time"]))
                            self.state["nolla_tarkistettu"] += 1
                            self.state["nolla_kauppoja_loytyi"] += 1 if n else 0
                            p = os.path.join(self.root, "nollaminuutit.csv")
                            with open(p, "a", newline="", encoding="utf-8") as f:
                                w = csv.writer(f)
                                if f.tell() == 0:
                                    w.writerow(["symboli", "open_time", "kauppoja_minuutilla", "historia_n", "tarkistettu_ms"])
                                w.writerow([s, int(c["time"]), n, hn, int(time.time() * 1000)])
                        except Exception as e:
                            errs.append(f"{s} nollatarkistus: {e}")
            except Exception as e:
                errs.append(f"{s}: {e}")
        self.state["kierroksia"] += 1
        if not errs:
            self.state["viimeisin_ok"] = now
        self.state["viimeiset"] = {s: self.last[s] for s in self.symbols}
        self.state["virheet"] = (self.state["virheet"] + [{"t": now, "e": e} for e in errs])[-50:]
        with open(os.path.join(self.root, "keruu_tila.json"), "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False)

    def kaynnista(self) -> None:
        def loop():
            while True:
                try:
                    self.kierros()
                except Exception as e:
                    self.log(f"keruu: {e!r}")
                time.sleep(60 - time.time() % 60 + 20)      # noin 20 s minuutin vaihteen jälkeen
        threading.Thread(target=loop, daemon=True).start()
        self.log(f"Tiedonkeruu käynnissä: {self.root} ({', '.join(self.symbols)})")


# ---------------------------------------------------------------- etenemisnäkymä (vain keruun laatu, ei tuloksia)
TOISTO_ALKU = 1_790_899_200_000   # 2.10.2026 00:00 UTC
TOISTO_LOPPU = 1_793_318_400_000  # 30.10.2026 00:00 UTC
TOISTO_MARKKINAT = ["PF_SUIUSD", "PF_ZECUSD", "PF_XRPUSD", "PF_DOGEUSD", "PF_SOLUSD"]   # lukittu tutkimussuunnitelmassa
_cache: dict = {}


def yhteenveto(root: str, symbols: list[str], alku: int = TOISTO_ALKU, loppu: int = TOISTO_LOPPU,
               now_ms: int | None = None) -> dict:
    """Toistojakson etenemisen yhteenveto. Ei laske signaaleja eikä lopputuloksia (testiä ei kurkita)."""
    now = now_ms or int(time.time() * 1000)
    key = (root, now // 60_000)
    if now_ms is None and key in _cache:
        return _cache[key]
    tila = {}
    try:
        with open(os.path.join(root, "keruu_tila.json"), encoding="utf-8") as f:
            tila = json.load(f)
    except Exception:
        pass
    zero = {}
    try:
        with open(os.path.join(root, "nollaminuutit.csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if alku <= int(r["open_time"]) < loppu:
                    z = zero.setdefault(r["symboli"], [0, 0])
                    z[0] += 1
                    z[1] += 1 if int(r["kauppoja_minuutilla"]) > 0 else 0
    except Exception:
        pass
    hi = min(now, loppu)
    expected = max(0, (hi - alku) // MIN) if now > alku else 0
    rows = []
    for s in symbols:
        n = traded = 0
        last = None
        seen = set()
        try:
            with open(os.path.join(root, "kynttilat", f"{s}.csv"), encoding="utf-8") as f:
                for line in f:
                    if not line[:1].isdigit():
                        continue
                    p = line.split(",")
                    t = int(p[0])
                    last = t if last is None or t > last else last
                    if alku <= t < loppu and t not in seen:
                        seen.add(t)
                        n += 1
                        traded += 1 if float(p[5]) > 0 else 0
        except FileNotFoundError:
            pass
        # odotetut minuutit tähän mennessä = jakson alusta viimeiseen tallennettuun asti
        upto = min((last + MIN) if last else alku, loppu)
        exp_s = max(0, (upto - alku) // MIN)
        z = zero.get(s, [0, 0])
        rows.append({"symboli": s, "minuutteja": n, "odotettu": exp_s, "puuttuu": max(0, exp_s - n),
                     "kauppaminuutteja": traded, "kattavuus": (traded / n) if n else None,
                     "viimeisin": last, "nolla_tarkistettu": z[0], "nolla_kauppoja_loytyi": z[1]})
    out = {"alku": alku, "loppu": loppu, "nyt": now, "jakson_minuutit": (loppu - alku) // MIN,
           "kulunut_min": expected, "kierroksia": tila.get("kierroksia"), "viimeisin_ok": tila.get("viimeisin_ok"),
           "kaynnistetty": tila.get("kaynnistetty"), "virheet": (tila.get("virheet") or [])[-5:],
           "markkinat": rows, "kattavuusraja": 0.95}
    if now_ms is None:
        _cache.clear()
        _cache[key] = out
    return out
