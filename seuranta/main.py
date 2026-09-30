"""Paperikaupan seurantanäkymä: erillinen, VAIN LUKEVA palvelu.

Ei tuo mitään kaupankäyntikoodista eikä pääse bottien tilaan. Lukee:
  * botin kauppa- ja tapahtumalokit botin omasta token-suojatusta HTTP-päätepisteestä
  * Krakenin julkiset tickerit avointen positioiden nykyhintaa varten.
Tilin tila (pääoma, pudotus, tappiorajat) johdetaan lokeista samoilla säännöillä kuin
moottorissa (docs/SAANNOT_v2.md). Botin todellinen tila on sen omassa tallennuksessa.

Ympäristömuuttujat: LOG_TOKEN (sama kuin botilla), BOT_URL, PORT, VERSIONS, TEST_START, TEST_END.
Sivu: /?token=<LOG_TOKEN>, data: /api/tila?token=<LOG_TOKEN>
"""
from __future__ import annotations

import hmac
import json
import os
import threading
import time
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

TOKEN = os.environ.get("LOG_TOKEN", "")
BOT_URL = os.environ.get("BOT_URL", "https://kynttil-botti-production.up.railway.app").rstrip("/")
VERSIONS = [v.strip() for v in os.environ.get("VERSIONS", "v1.1-T2,v2-T2").split(",") if v.strip()]
TEST_START = os.environ.get("TEST_START", "2026-09-30 15:21 UTC")
TEST_END = os.environ.get("TEST_END", "2026-10-28 15:21 UTC")
KRAKEN = "https://futures.kraken.com/derivatives/api/v3/tickers"
CACHE_S = 30
DAY = 86_400_000

# Lukittujen versioiden parametrit (strategy.py / docs/SAANNOT_v2.md) – vain näyttöä varten.
RULES = {
    "_": dict(start_equity=10_000.0, taker_fee=0.0005, slippage=0.0002, daily_loss_limit=0.02,
              max_consecutive_losses=4, loss_streak_pause_min=60, max_drawdown=0.10,
              max_positions=3, min_volume_ratio=1.2),
    "v1.1-T2": dict(min_r_to_cost=2.0),
    "v2-T2": dict(min_r_to_cost=4.0),
}
HERE = os.path.dirname(os.path.abspath(__file__))


def rules(v: str) -> dict:
    return {**RULES["_"], **RULES.get(v, {})}


def ms(s) -> int:
    if isinstance(s, (int, float)):
        return int(s)
    return int(datetime.strptime(s, "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc).timestamp() * 1000)


def http_get(url: str, timeout: float = 15) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "kynttilabotti-seuranta/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def jsonl(b: bytes) -> list[dict]:
    out = []
    for line in b.decode("utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass          # kesken kirjoitettu viimeinen rivi
    return out


def fetch_log(name: str) -> list[dict]:
    return jsonl(http_get(f"{BOT_URL}/{name}?token={TOKEN}"))


def fetch_tickers() -> dict:
    rows = json.loads(http_get(KRAKEN))["tickers"]
    out = {}
    for r in rows:
        if str(r.get("symbol", "")).startswith("PF_"):
            lt = r.get("lastTime")
            out[r["symbol"]] = {
                "bid": float(r.get("bid") or 0), "ask": float(r.get("ask") or 0),
                "mark": float(r.get("markPrice") or r.get("last") or 0),
                "last_time": (int(datetime.fromisoformat(lt.replace("Z", "+00:00")).timestamp() * 1000)
                              if lt else None)}
    return out


def account(v: str, trades: list[dict], events: list[dict], tickers: dict, now: int) -> dict:
    r = rules(v)
    eq0 = r["start_equity"]
    by_id = {}
    for t in trades:
        by_id[t["id"]] = t
    closed = sorted(by_id.values(), key=lambda t: (ms(t["exit_time"]), t["id"]))

    # --- toteutunut tulos ja moottorin tappiorajat samalla logiikalla kuin paper.py ---
    eq = peak = eq0
    mdd = 0.0
    day, day_start, day_pnl, day_blocked = None, eq0, 0.0, False
    streak, pause_until, halted = 0, 0, False
    curve = [{"t": ms(TEST_START), "eq": eq0}]
    rows = []
    for t in closed:
        te = ms(t["exit_time"])
        d = te // DAY
        if d != day:
            day, day_start, day_pnl, day_blocked = d, eq, 0.0, False
        net = float(t["net_pnl"])
        eq += net
        day_pnl += net
        peak = max(peak, eq)
        mdd = max(mdd, 1 - eq / peak)
        if net < 0:
            streak += 1
            if streak >= r["max_consecutive_losses"]:
                pause_until, streak = te + r["loss_streak_pause_min"] * 60_000, 0
        else:
            streak = 0
        if day_pnl <= -r["daily_loss_limit"] * day_start:
            day_blocked = True
        if 1 - eq / peak >= r["max_drawdown"]:
            halted = True
        curve.append({"t": te, "eq": round(eq, 2)})
        rows.append({
            "id": t["id"], "symbol": t["symbol"], "side": t["side"],
            "entry_time": ms(t["entry_time"]), "exit_time": te,
            "entry_price": t["entry_price"], "exit_price": t["exit_price"], "qty": t["qty"],
            "costs": round(float(t["fees"]) + float(t["spread_slippage_est"]) + float(t["funding"]), 2),
            "fees": t["fees"], "spread_slippage": t["spread_slippage_est"], "funding": t["funding"],
            "gross": t["gross_pnl"], "net": net, "reason": t["close_reason"], "open_reason": t["open_reason"],
            "equity_after": round(eq, 2)})
    if day != now // DAY:
        day_blocked = False           # uusi UTC-päivä -> raja nollautuu moottorissa
    wins = sum(1 for x in rows if x["net"] > 0)

    # --- avoimet positiot: avaustapahtumat, joilla ei ole vielä sulkua ---
    opens = {e["id"]: e for e in events if e.get("kind") == "open"}
    open_rows, unreal = [], 0.0
    for pid, e in sorted(opens.items()):
        if pid in by_id:
            continue
        tk = tickers.get(e["symbol"], {})
        long = e["side"] == "long"
        px = tk.get("mark")
        est = None
        if tk.get("bid") and tk.get("ask"):
            exit_px = tk["bid"] * (1 - r["slippage"]) if long else tk["ask"] * (1 + r["slippage"])
            gross = (exit_px - e["entry_price"]) * e["qty"] * (1 if long else -1)
            est = gross - r["taker_fee"] * exit_px * e["qty"]
            unreal += est
        open_rows.append({
            "id": pid, "symbol": e["symbol"], "side": e["side"], "entry_time": ms(e["entry_time"]),
            "entry_price": e["entry_price"], "qty": e["qty"], "stop": e["stop"], "target": e["target"],
            "price": px, "est_pnl": None if est is None else round(est, 2), "reason": e.get("reason", ""),
            "bars_held": e.get("bars_held", 0)})

    # --- viimeisimmät ohitetut signaalit ja tapahtuma-aika ---
    skips = [e for e in events if e.get("kind") == "skipped"]
    last_skip = max(skips, key=lambda e: e["time"]) if skips else None
    today = now // DAY
    skip_today: dict[str, int] = {}
    for e in skips:
        if e["time"] // DAY == today:
            k = e["why"].split(":")[0]
            skip_today[k] = skip_today.get(k, 0) + 1
    ev_times = [e["time"] for e in skips] + [ms(e["entry_time"]) for e in opens.values()] + \
               [x["exit_time"] for x in rows]
    last_event = max(ev_times) if ev_times else None

    if halted:
        code, msg = "halted", (f"Pysäytetty: pudotus huipusta ≥ {r['max_drawdown']:.0%}. Uusia kauppoja ei "
                               "avata, eikä tiliä nollata testin aikana.")
    elif pause_until > now:
        code, msg = "paused", f"Tauko {r['max_consecutive_losses']} peräkkäisen tappion jälkeen."
    elif day_blocked:
        code, msg = "day_blocked", (f"Päivän tappioraja ({r['daily_loss_limit']:.0%}) täynnä. Uusia kauppoja "
                                    "vasta UTC-päivän vaihduttua.")
    elif len(open_rows) >= r["max_positions"]:
        code, msg = "full", f"Enimmäismäärä positioita ({r['max_positions']}) auki."
    elif open_rows:
        code, msg = "open", "Positio auki: sulkeutuu stopilla, tavoitteella tai 15 min aikarajalla."
    else:
        code, msg = "waiting", "Odottaa signaalia. Kaupankäyntiä estäviä rajoja ei ole voimassa."

    return {
        "version": v, "min_r_to_cost": r["min_r_to_cost"], "start_equity": eq0,
        "realized_equity": round(eq, 2), "realized_pnl": round(eq - eq0, 2),
        "realized_pct": (eq - eq0) / eq0, "unrealized_pnl": round(unreal, 2),
        "value_est": round(eq + unreal, 2), "trades": len(rows), "wins": wins,
        "win_rate": wins / len(rows) if rows else None, "max_dd": mdd,
        "open": open_rows, "closed": list(reversed(rows)), "curve": curve,
        "status": {"code": code, "text": msg, "pause_until": pause_until if pause_until > now else None},
        "last_skip": ({"time": last_skip["time"], "symbol": last_skip["symbol"], "side": last_skip["side"],
                       "why": last_skip["why"], "reason": last_skip.get("reason", "")} if last_skip else None),
        "skips_today": skip_today, "last_event": last_event,
    }


_cache: dict = {"t": 0, "data": None}
_lock = threading.Lock()


def build() -> dict:
    now = int(time.time() * 1000)
    errors, bot_ok = [], True
    try:
        tickers = fetch_tickers()
    except Exception as e:
        tickers, errors = {}, [f"Krakenin hintoja ei saatu: {e}"]
    accts = []
    for v in VERSIONS:
        try:
            tr, ev = fetch_log(f"kaupat_{v}.jsonl"), fetch_log(f"tapahtumat_{v}.jsonl")
        except Exception as e:
            bot_ok = False
            errors.append(f"[{v}] botin lokeja ei saatu: {e}")
            tr, ev = [], []
        accts.append(account(v, tr, ev, tickers, now))
    syms = sorted({p["symbol"] for a in accts for p in a["open"]} |
                  {"PF_XBTUSD", "PF_ETHUSD", "PF_SOLUSD", "PF_ZECUSD", "PF_XRPUSD"})
    return {
        "generated": now, "bot_ok": bot_ok, "errors": errors,
        "test_start": ms(TEST_START), "test_end": ms(TEST_END),
        "kraken_last": max((tickers[s]["last_time"] or 0 for s in syms if s in tickers), default=None),
        "prices": {s: tickers.get(s, {}).get("mark") for s in syms},
        "accounts": accts,
    }


def get_data() -> dict:
    with _lock:
        if _cache["data"] is None or time.time() - _cache["t"] > CACHE_S:
            _cache["data"], _cache["t"] = build(), time.time()
        return _cache["data"]


class H(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Robots-Tag", "noindex")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/health":
            return self._send(200, b"ok", "text/plain")
        tok = parse_qs(u.query).get("token", [""])[0]
        if not TOKEN or not hmac.compare_digest(tok, TOKEN):
            return self._send(403, "Pääsy estetty: token puuttuu tai on väärä.".encode(), "text/plain; charset=utf-8")
        if u.path == "/":
            with open(os.path.join(HERE, "sivu.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if u.path == "/api/tila":
            try:
                data = get_data()
            except Exception as e:
                return self._send(500, json.dumps({"error": str(e)}).encode(), "application/json")
            return self._send(200, json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8")
        return self._send(404, b"not found", "text/plain")

    def log_message(self, *a):
        pass


def main():
    port = int(os.environ.get("PORT", "8080"))
    print(f"Seuranta käynnissä portissa {port}; botti {BOT_URL}; versiot {', '.join(VERSIONS)}", flush=True)
    if not TOKEN:
        print("VAROITUS: LOG_TOKEN puuttuu – kaikki pyynnöt estetään.", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()


if __name__ == "__main__":
    main()
