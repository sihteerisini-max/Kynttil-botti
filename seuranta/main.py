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
              max_positions=3, min_volume_ratio=1.2, max_hold_min=15),
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
                "funding_rel": (float(r.get("fundingRate") or 0) / float(r.get("markPrice") or 1)
                                if r.get("markPrice") else None),
                "last_time": (int(datetime.fromisoformat(lt.replace("Z", "+00:00")).timestamp() * 1000)
                              if lt else None)}
    return out


def switches(events: list[dict]) -> list[dict]:
    return sorted(({"time": e["time"], "old": e["old"], "new": e["new"]} for e in events
                   if e.get("kind") == "markkinat_vaihdettu"), key=lambda x: x["time"])


def segment_stats(rows: list[dict], t_from: int, t_to: int) -> dict:
    """Suljetut kaupat, jotka AVATTIIN välillä [t_from, t_to)."""
    xs = [x for x in rows if t_from <= x["entry_time"] < t_to]
    w = sum(1 for x in xs if x["net"] > 0)
    return {"trades": len(xs), "wins": w, "win_rate": w / len(xs) if xs else None,
            "net": round(sum(x["net"] for x in xs), 2), "gross": round(sum(x["gross"] for x in xs), 2),
            "long": sum(1 for x in xs if x["side"] == "long"), "short": sum(1 for x in xs if x["side"] == "short")}


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
            "gross": round(float(t["gross_pnl"]) + float(t["spread_slippage_est"]), 2), "net": net, "reason": t["close_reason"], "open_reason": t["open_reason"],
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
        "switches": switches(events),
        "segments": ([{"label": "Ennen markkinavaihtoa", "from": ms(TEST_START), "to": sw[-1]["time"],
                       "symbols": sw[-1]["old"], **segment_stats(rows, 0, sw[-1]["time"])},
                      {"label": "Markkinavaihdon jälkeen", "from": sw[-1]["time"], "to": None,
                       "symbols": sw[-1]["new"], **segment_stats(rows, sw[-1]["time"], 1 << 62)}]
                     if (sw := switches(events)) else []),
    }


_cache: dict = {"t": 0, "data": None}
_lock = threading.Lock()

# ---------------------------------------------------------------- kynttiläkaaviot
SYMBOLS = [x.strip() for x in os.environ.get(
    "SYMBOLS", "PF_XBTUSD,PF_ETHUSD,PF_SOLUSD,PF_ZECUSD,PF_XRPUSD").split(",") if x.strip()]
CHARTS_URL = "https://futures.kraken.com/api/charts/v1/trade/{sym}/1m?from={frm}&to={to}"
MAX_H = 24
_candles: dict[str, dict[int, list]] = {}      # symboli -> {avausaika ms: [t, o, h, l, c]}
_cstate = {"t": 0.0, "ok_at": 0, "error": None, "loaded": set()}
_logs = {"t": 0.0, "data": None}
_tick = {"t": 0.0, "data": {}, "at": 0}


def tickers_cached() -> dict:
    if time.time() - _tick["t"] > 8:
        _tick["t"] = time.time()
        try:
            _tick["data"], _tick["at"] = fetch_tickers(), int(time.time() * 1000)
        except Exception:
            pass
    return _tick["data"]


def open_estimate(e: dict, v: str, tk: dict, now: int) -> dict:
    """Avoimen paperiposition arvio nykyhinnalla samoilla kulusäännöillä kuin moottorin sulussa:
    ennen kuluja = qty × (keskihinta − avauskynttilän avaus); kulujen jälkeen = sulku bid/ask-hintaan
    + liukuma, molemmat palkkiot ja funding tähän asti. Ei vaikuta botin kauppoihin."""
    r = rules(v)
    long = e["side"] == "long"
    sg = 1 if long else -1
    out = {"time_limit": ms(e["entry_time"]) + r.get("max_hold_min", 15) * 60_000}
    if not (tk and tk.get("bid") and tk.get("ask")):
        return out
    mid = (tk["bid"] + tk["ask"]) / 2
    ref = e.get("entry_ref") or e["entry_price"]
    exit_fill = tk["bid"] * (1 - r["slippage"]) if long else tk["ask"] * (1 + r["slippage"])
    notional = e["qty"] * e["entry_price"]
    hours = max(0.0, (now - ms(e["entry_time"])) / 3_600_000)
    rate = tk.get("funding_rel")
    funding = notional * (rate * sg if rate is not None else 0.0000125) * hours
    entry_fee = e.get("entry_fee", r["taker_fee"] * notional)
    exit_fee = r["taker_fee"] * exit_fill * e["qty"]
    gross = e["qty"] * (mid - ref) * sg
    net = e["qty"] * (exit_fill - e["entry_price"]) * sg - entry_fee - exit_fee - funding
    out.update(price=mid, gross_now=round(gross, 2), net_now=round(net, 2), costs_now=round(gross - net, 2),
               price_time=tk.get("last_time"))
    return out
_clock = threading.Lock()


def _fetch_range(sym: str, start_ms: int, end_ms: int) -> None:
    frm, to = start_ms // 1000, end_ms // 1000
    store = _candles.setdefault(sym, {})
    while frm < to:
        d = json.loads(http_get(CHARTS_URL.format(sym=sym, frm=frm, to=to)))
        cs = d.get("candles") or []
        for c in cs:
            t = int(c["time"])
            store[t] = [t, float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"])]
        if not cs or not d.get("more_candles"):
            break
        nxt = int(cs[-1]["time"]) // 1000 + 60
        if nxt <= frm:
            break
        frm = nxt


def refresh_candles() -> None:
    now = int(time.time() * 1000)
    if time.time() - _cstate["t"] < 8:
        return
    _cstate["t"] = time.time()
    try:
        for sym in SYMBOLS:
            if sym not in _cstate["loaded"]:
                _fetch_range(sym, now - MAX_H * 3_600_000, now + 60_000)
                _cstate["loaded"].add(sym)
            else:
                _fetch_range(sym, now - 5 * 60_000, now + 60_000)   # viimeiset minuutit + muodostuva
            store = _candles[sym]
            for t in [t for t in store if t < now - (MAX_H + 1) * 3_600_000]:
                del store[t]
        _cstate["ok_at"], _cstate["error"] = now, None
    except Exception as e:
        _cstate["error"] = f"Krakenin kynttilädataa ei saatu: {e}"


def bot_logs() -> tuple[dict, list]:
    """{versio: (kaupat, tapahtumat)} – välimuisti 20 s, koska tiedostot haetaan kokonaan."""
    if _logs["data"] is None or time.time() - _logs["t"] > 20:
        out, errs = {}, []
        for v in VERSIONS:
            try:
                out[v] = (fetch_log(f"kaupat_{v}.jsonl"), fetch_log(f"tapahtumat_{v}.jsonl"))
            except Exception as e:
                errs.append(f"[{v}] botin lokeja ei saatu: {e}")
                out[v] = _logs["data"][0].get(v, ([], [])) if _logs["data"] else ([], [])
        _logs["data"], _logs["t"] = (out, errs), time.time()
    return _logs["data"]


def outcome(reason: str) -> str:
    if "samassa kynttilässä" in reason:
        return "epäselvä"
    if reason.startswith("voittotavoite") or reason.startswith("tavoite"):
        return "tavoite"
    if reason.startswith("stop"):
        return "stop"
    if reason.startswith("aikaraja"):
        return "aikaraja"
    return "muu"


def exit_bar(t_exit: int, reason: str) -> int:
    """Kynttilä, jonka aikana sulku tapahtui. Stop/tavoite todetaan kynttilän sulkeutuessa
    (kirjattu aika = seuraavan kynttilän avaus); aikaraja ja hintakuilut avauksessa."""
    if reason.startswith("stop loss") or reason.startswith("voittotavoite"):
        return t_exit - 60_000
    return t_exit


def build_charts(hours: float) -> dict:
    now = int(time.time() * 1000)
    with _clock:
        refresh_candles()
        logs, log_errs = bot_logs()
        w0 = now - int(hours * 3_600_000)
        candles = {s: [c for t, c in sorted(_candles.get(s, {}).items()) if t >= w0 - 60_000] for s in SYMBOLS}
        ticks = tickers_cached()
    trades, opens, skips, summary = [], [], [], {}
    seg_summary, switch_info = {}, None
    for bi, v in enumerate(VERSIONS, start=1):
        tr, ev = logs.get(v, ([], []))
        closed = {t["id"]: t for t in tr}
        summ = {side: {"kauppoja": 0, "tavoite": 0, "stop": 0, "aikaraja": 0, "epäselvä": 0, "muu": 0, "avoinna": 0}
                for side in ("long", "short")}
        open_ev = {e["id"]: e for e in ev if e.get("kind") == "open"}
        for t in closed.values():
            o = outcome(t["close_reason"])
            summ[t["side"]]["kauppoja"] += 1
            summ[t["side"]][o] += 1
            te = ms(t["exit_time"])
            oe = open_ev.get(t["id"], {})
            trades.append({
                "bot": bi, "version": v, "id": t["id"], "symbol": t["symbol"], "side": t["side"],
                "signal_time": ms(t["signal_time"]), "entry_time": ms(t["entry_time"]),
                "entry_price": t["entry_price"], "entry_ref": oe.get("entry_ref"),
                "stop": t["stop"], "target": t["target"], "qty": t["qty"],
                "exit_time": te, "exit_bar": exit_bar(te, t["close_reason"]), "exit_price": t["exit_price"],
                "reason": t["close_reason"], "outcome": o, "open_reason": t["open_reason"],
                "gross_move": round(float(t["gross_pnl"]) + float(t["spread_slippage_est"]), 2),
                "fees": t["fees"], "spread_slippage": t["spread_slippage_est"], "funding": t["funding"],
                "costs": round(float(t["fees"]) + float(t["spread_slippage_est"]) + float(t["funding"]), 2),
                "net": t["net_pnl"]})
        for pid, e in open_ev.items():
            if pid in closed:
                continue
            summ[e["side"]]["avoinna"] += 1
            opens.append({"bot": bi, "version": v, "id": pid, "symbol": e["symbol"], "side": e["side"],
                          "signal_time": e.get("signal_time"),
                          "entry_time": ms(e["entry_time"]), "entry_price": e["entry_price"],
                          "entry_ref": e.get("entry_ref"), "stop": e["stop"], "target": e["target"],
                          "qty": e["qty"], "open_reason": e.get("reason", ""),
                          **open_estimate(e, v, ticks.get(e["symbol"], {}), now)})
        for e in ev:
            if e.get("kind") == "skipped" and e["time"] >= w0 - 60_000:
                skips.append({"bot": bi, "version": v, "symbol": e["symbol"], "side": e["side"],
                              "time": e["time"], "why": e["why"], "reason": e.get("reason", "")})
        summary[v] = summ
        sw = switches(ev)
        if sw:
            t_sw = sw[-1]["time"]
            seg = {}
            for name, cond in (("ennen", lambda x: ms(x["entry_time"]) < t_sw), ("jälkeen", lambda x: ms(x["entry_time"]) >= t_sw)):
                sm = {side: {"kauppoja": 0, "tavoite": 0, "stop": 0, "aikaraja": 0, "epäselvä": 0, "muu": 0, "avoinna": 0}
                      for side in ("long", "short")}
                for t in closed.values():
                    if cond(t):
                        sm[t["side"]]["kauppoja"] += 1
                        sm[t["side"]][outcome(t["close_reason"])] += 1
                for pid, e in open_ev.items():
                    if pid not in closed and cond(e):
                        sm[e["side"]]["avoinna"] += 1
                seg[name] = sm
            seg_summary[v] = seg
            switch_info = sw[-1]
    errors = list(log_errs) + ([_cstate["error"]] if _cstate["error"] else [])
    last = {s: (candles[s][-1][0] if candles[s] else None) for s in SYMBOLS}
    return {"generated": now, "hours": hours, "symbols": SYMBOLS, "candles": candles, "last_candle": last,
            "kraken_ok_at": _cstate["ok_at"], "versions": VERSIONS, "trades": trades, "opens": opens,
            "skips": skips, "summary": summary, "seg_summary": seg_summary, "switch": switch_info,
            "errors": errors}


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
    syms = sorted({p["symbol"] for a in accts for p in a["open"]} | set(SYMBOLS))
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
        if u.path == "/kaaviot.js":
            with open(os.path.join(HERE, "kaaviot.js"), "rb") as f:
                return self._send(200, f.read(), "text/javascript; charset=utf-8")
        if u.path == "/api/kaaviot":
            try:
                h = float(parse_qs(u.query).get("tunnit", ["3"])[0])
                data = build_charts(min(max(h, 0.5), MAX_H))
            except Exception as e:
                return self._send(500, json.dumps({"error": str(e)}).encode(), "application/json")
            return self._send(200, json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8")
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
