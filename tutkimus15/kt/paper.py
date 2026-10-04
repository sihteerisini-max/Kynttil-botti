"""Paperikaupan moottori – sama koodi historiatestissä ja live-paperikaupassa.

Ajuri kutsuu jokaiselle minuutille ja markkinalle:
    engine.on_bar_open(symbol, open_time, open_price)   # heti kun kynttilä alkaa
    engine.on_bar_close(candle)                          # kun kynttilä on sulkeutunut
Moottori ei koskaan näe tulevia kynttilöitä: signaali syntyy sulkeutuneesta
kynttilästä ja avataan vasta seuraavan kynttilän avaushinnalla.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Callable

from .analyzer import SymbolAnalyzer
from .patterns import TUNNISTUS
from .models import Candle
from .patterns import build_context
from .strategy import DefaultSpec, Ruleset, Signal, estimate_costs, make_signal, size_position

DAY = 86_400_000
HOUR = 3_600_000


def ts(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


@dataclass
class Position:
    id: int
    symbol: str
    side: str
    entry_time: int
    entry_ref: float        # avauskynttilän avaushinta (ennen kuluja)
    entry_price: float      # toteutunut hinta (spread + liukuma mukana)
    qty: float
    stop: float
    target: float
    risk_r: float           # |avaushinta - stop| per yksikkö
    entry_fee: float
    entry_half_spread: float
    reason: str
    signal_time: int
    bars_held: int = 0
    risk_budget: float = 0.0   # USD: suunniteltu kokonaistappio stopissa (kulut mukana)
    margin: float = 0.0        # sidottu alkumarginaali USD
    signaalityyppi: str = "kääntyminen"
    cost_to_r: float = 0.0     # stop-skenaarion kustannusarvio / R avaushetkellä (vain tieto)


@dataclass
class Trade:
    id: int
    ruleset: str
    symbol: str
    side: str
    signal_time: str
    entry_time: str
    entry_price: float
    exit_time: str
    exit_price: float
    qty: float
    notional: float
    stop: float
    target: float
    open_reason: str
    close_reason: str
    bars_held: int
    gross_pnl: float
    fees: float
    funding: float
    spread_slippage_est: float
    net_pnl: float
    r_multiple: float
    equity_after: float
    risk_budget: float = 0.0          # suunniteltu kokonaistappio stopissa (USD)
    budget_multiple: float = 0.0      # nettotulos / riskibudjetti (−1 = täysi suunniteltu tappio)
    lopputulos: str = ""              # tavoite / stop / aikaraja / epäselvä / muu (ks. lopputulos())
    entry_ref: float = 0.0            # avauskynttilän avaushinta ennen spreadia ja liukumaa
    exit_ref: float = 0.0             # sulun viitehinta (tavoite, stop tai kynttilän avaus) ennen kuluja
    hintaliike_pnl: float = 0.0       # qty × hintaliike viitehinnasta viitehintaan = tulos ennen KAIKKIA kuluja
    risk_r_price: float = 0.0         # R hinnan yksiköissä (|toteutunut avaushinta − stop|)
    signaalityyppi: str = ""          # kääntyminen / jatkuminen
    cost_to_r: float = 0.0            # stop-skenaarion kustannusarvio / R avaushetkellä


def lopputulos(reason: str) -> str:
    """Sulkemissyy -> ajoituksen lopputulosluokka. Jos stop ja tavoite osuvat samaan kynttilään,
    järjestystä ei voi 1 min datasta tietää -> 'epäselvä' (kirjanpidossa stop ensin, varovainen)."""
    if "samassa kynttilässä" in reason:
        return "epäselvä"
    if reason.startswith("voittotavoite") or reason.startswith("tavoite"):
        return "tavoite"
    if reason.startswith("stop"):
        return "stop"
    if reason.startswith("aikaraja"):
        return "aikaraja"
    return "muu"


@dataclass
class EngineState:
    equity: float
    peak: float
    day: int = -1
    day_start_equity: float = 0.0
    day_pnl: float = 0.0
    day_blocked: bool = False
    consecutive_losses: int = 0
    pause_until: int = 0
    halted: bool = False
    next_id: int = 1
    max_drawdown_seen: float = 0.0


class PaperEngine:
    def __init__(self, rules: Ruleset,
                 half_spread_fn: Callable[[str, int], float],
                 funding_fn: Callable[[str, int], float | None],
                 log: Callable[[str], None] = print,
                 on_trade: Callable[[Trade], None] | None = None,
                 on_event: Callable[[dict], None] | None = None,
                 on_signal: Callable[[object, int], None] | None = None,
                 verbose_signals: bool = True,
                 specs: dict | None = None):
        self.r = rules
        self.specs = specs            # None = testit/demo (DefaultSpec)
        self.half_spread_fn = half_spread_fn
        self.funding_fn = funding_fn
        self.log = log
        self.on_trade = on_trade
        self.on_event = on_event
        self.verbose_signals = verbose_signals
        self.on_signal = on_signal        # vain havainnointiin (ajoitusseuranta), ei vaikuta kauppoihin
        self.state = EngineState(equity=rules.start_equity, peak=rules.start_equity)
        self.positions: dict[str, Position] = {}
        self.pending: dict[str, Signal] = {}
        self.analyzers: dict[str, SymbolAnalyzer] = {}
        self.trades: list[Trade] = []
        self.skipped: dict[str, int] = {}
        self.last_signal_open: dict[str, int] = {}   # markkina -> viimeisimmän avatun signaalikynttilän aika
        self.allow_entries = True         # False esim. uudelleenkäynnistyksen kiinniottovaiheessa

    # ------------------------------------------------------------------ apu
    def analyzer(self, symbol: str) -> SymbolAnalyzer:
        if symbol not in self.analyzers:
            self.analyzers[symbol] = SymbolAnalyzer(symbol, TUNNISTUS[self.r.tunnistus], max_history=100)
        return self.analyzers[symbol]

    def _event(self, kind: str, **kw):
        if self.on_event:
            self.on_event({"kind": kind, "ruleset": self.r.version, **kw})

    def _skip(self, sig: Signal, t: int, why: str):
        k = why.split(":")[0]
        self.skipped[k] = self.skipped.get(k, 0) + 1
        if self.verbose_signals:
            self.log(f"[{sig.symbol} {ts(t)}] signaali ohitettu ({sig.side}, {sig.reason()}): {why}")
        self._event("skipped", symbol=sig.symbol, time=t, side=sig.side, why=why, reason=sig.reason())

    def _roll_day(self, t: int):
        d = t // DAY
        if d != self.state.day:
            self.state.day = d
            self.state.day_start_equity = self.state.equity
            self.state.day_pnl = 0.0
            self.state.day_blocked = False

    def open_notional(self) -> float:
        return sum(p.qty * p.entry_price for p in self.positions.values())

    # ------------------------------------------------------------ tapahtumat
    def on_bar_open(self, symbol: str, t: int, price: float) -> None:
        self._roll_day(t)
        pos = self.positions.get(symbol)
        if pos:
            long = pos.side == "long"
            if pos.bars_held >= self.r.max_hold_bars:
                self._close(pos, t, price, "aikaraja (15 kynttilää)", stop_fill=False)
            elif (long and price <= pos.stop) or (not long and price >= pos.stop):
                self._close(pos, t, price, "stop (hintakuilu avauksessa)", stop_fill=True)
            elif (long and price >= pos.target) or (not long and price <= pos.target):
                self._close(pos, t, price, "tavoite (hintakuilu avauksessa)", stop_fill=False)
        sig = self.pending.pop(symbol, None)
        if sig:
            self._try_open(sig, t, price)

    def on_bar_close(self, c: Candle) -> None:
        if not c.closed:
            raise ValueError("on_bar_close vaatii suljetun kynttilän")
        t_close = c.open_time + 60_000
        self._roll_day(c.open_time)
        pos = self.positions.get(c.symbol)
        if pos and pos.entry_time <= c.open_time:
            long = pos.side == "long"
            hit_stop = c.low <= pos.stop if long else c.high >= pos.stop
            hit_tgt = c.high >= pos.target if long else c.low <= pos.target
            if hit_stop:     # jos molemmat, oletetaan stop ensin
                self._close(pos, t_close, pos.stop, "stop loss" + (" (myös tavoite samassa kynttilässä – oletettu stop ensin)" if hit_tgt else ""), stop_fill=True)
            elif hit_tgt:
                self._close(pos, t_close, pos.target, "voittotavoite", stop_fill=False)
            else:
                pos.bars_held += 1

        an = self.analyzer(c.symbol)
        ctx = build_context(list(an.history))
        events = an.update(c)
        obs = [o for e in events if e.kind == "confirmed" for o in e.observations]
        sig = make_signal(c, obs, ctx, self.r)
        if sig and self.on_signal:
            self.on_signal(sig, t_close)
        if sig and self.allow_entries:
            if c.symbol in self.positions:
                self._skip(sig, t_close, "markkinassa on jo avoin positio")
            else:
                self.pending[c.symbol] = sig
                if self.verbose_signals:
                    self.log(f"[{c.symbol} {ts(t_close)}] SIGNAALI {sig.side.upper()} vahvistui: "
                             f"{sig.reason()} – avataan seuraavan kynttilän avauksella")

    # ----------------------------------------------------------------- avaus
    def _try_open(self, sig: Signal, t: int, price: float) -> None:
        r, s = self.r, self.state
        if not self.allow_entries:
            return
        if s.halted:
            return self._skip(sig, t, f"kaupankäynti pysäytetty (pudotus ≥ {r.max_drawdown:.0%})")
        if s.day_blocked:
            return self._skip(sig, t, f"päivän tappioraja ({r.daily_loss_limit:.0%}) täynnä")
        if t < s.pause_until:
            return self._skip(sig, t, f"tauko {r.max_consecutive_losses} peräkkäisen tappion jälkeen")
        if sig.candle.open_time <= self.last_signal_open.get(sig.symbol, -1):
            return self._skip(sig, t, "sama signaali on jo avattu kerran")
        if sig.symbol in self.positions:
            return self._skip(sig, t, "markkinassa on jo avoin positio")
        if len(self.positions) >= r.max_positions:
            return self._skip(sig, t, f"avoimia positioita jo {r.max_positions}")

        hs = self.half_spread_fn(sig.symbol, t)
        long = sig.side == "long"
        eq = s.equity
        budget = eq * r.risk_per_trade
        if r.cost_model == "korjattu":
            ce = estimate_costs(r, sig.side, price, sig.stop, hs)
            entry, risk_r = ce.entry_fill, ce.price_risk_r
            if (long and entry <= sig.stop) or (not long and entry >= sig.stop):
                return self._skip(sig, t, "avaushinta jo stopin väärällä puolella")
            if risk_r < r.min_r_to_cost * ce.stop_cost_estimate:
                return self._skip(sig, t, f"kulusuodatin: R {risk_r / entry:.3%} < {r.min_r_to_cost:g} x "
                                          f"stop-skenaarion kustannusarvio {ce.stop_cost_estimate / entry:.3%}")
            spec = DefaultSpec() if self.specs is None else self.specs.get(sig.symbol)
            if spec is None:
                return self._skip(sig, t, "sopimustiedot puuttuvat (koko- ja marginaalirajoja ei voi tarkistaa)")
            sz = size_position(r, eq, ce.loss_at_stop, entry, spec, self.open_notional(),
                               sum(p.margin for p in self.positions.values()))
            if sz.qty <= 0:
                return self._skip(sig, t, f"koko alle pienimmän kaupattavan askeleen (raja: {sz.binding})")
            return self._open(sig, t, price, entry, sz.qty, risk_r, hs, sz.risk_budget, sz.margin,
                              f" | raja: {sz.binding}, marginaali {sz.margin:,.0f} USD ({sz.initial_margin_rate:.0%})"
                              f" | kulut {ce.stop_cost_estimate / risk_r:.2f} R",
                              cost_to_r=ce.stop_cost_estimate / risk_r)
        else:   # alkuperäinen v1 (säilytetään jakson A toistettavuuden vuoksi)
            entry = price * (1 + hs + r.slippage) if long else price * (1 - hs - r.slippage)
            if (long and entry <= sig.stop) or (not long and entry >= sig.stop):
                return self._skip(sig, t, "avaushinta jo stopin väärällä puolella")
            risk_r = abs(entry - sig.stop)
            cost_unit = entry * r.round_trip_cost(hs)
            if risk_r < r.min_r_to_cost * cost_unit:
                return self._skip(sig, t, f"kulusuodatin: riski {risk_r / entry:.3%} < {r.min_r_to_cost:g} x kulut {cost_unit / entry:.3%}")
            qty = budget / (risk_r + cost_unit)
        full_qty = qty
        qty = min(qty, r.max_notional_per_pos * eq / entry,
                  max(0.0, r.max_notional_total * eq - self.open_notional()) / entry)
        if qty <= 0:
            return self._skip(sig, t, "nimellisarvon katto täynnä")
        budget *= qty / full_qty
        return self._open(sig, t, price, entry, qty, risk_r, hs, budget, 0.0, "")

    def _open(self, sig: Signal, t: int, price: float, entry: float, qty: float, risk_r: float,
              hs: float, budget: float, margin: float, note: str, cost_to_r: float = 0.0) -> None:
        r, s = self.r, self.state
        long = sig.side == "long"
        target = entry + r.target_r * risk_r if long else entry - r.target_r * risk_r
        pos = Position(s.next_id, sig.symbol, sig.side, t, price, entry, qty, sig.stop, target,
                       risk_r, qty * entry * r.taker_fee, hs, sig.reason(), sig.candle.open_time,
                       risk_budget=budget, margin=margin, signaalityyppi=getattr(sig, "tyyppi", "kääntyminen"),
                       cost_to_r=round(cost_to_r, 4))
        s.next_id += 1
        self.last_signal_open[sig.symbol] = sig.candle.open_time
        self.positions[sig.symbol] = pos
        self.log(f"[{sig.symbol} {ts(t)}] AVAUS #{pos.id} {sig.side.upper()} @ {entry:.6g} "
                 f"(avaus {price:.6g} + spread/liukuma) | koko {qty:.6g} = {qty * entry:,.0f} USD | "
                 f"stop {sig.stop:.6g} | tavoite {target:.6g} | hintariski {qty * risk_r:,.2f} USD, "
                 f"riskibudjetti (sis. kulut) {budget:,.2f} USD{note}\n"
                 f"      peruste: {sig.reason()}")
        self._event("open", **asdict(pos))

    # ----------------------------------------------------------------- sulku
    def _close(self, pos: Position, t: int, ref: float, reason: str, stop_fill: bool) -> None:
        r, s = self.r, self.state
        hs = self.half_spread_fn(pos.symbol, t)
        slip = r.stop_slippage if stop_fill else r.slippage
        long = pos.side == "long"
        exit_price = ref * (1 - hs - slip) if long else ref * (1 + hs + slip)
        gross = pos.qty * ((exit_price - pos.entry_price) if long else (pos.entry_price - exit_price))
        fees = pos.entry_fee + pos.qty * exit_price * r.taker_fee
        notional = pos.qty * pos.entry_price
        hours = max(0.0, (t - pos.entry_time) / HOUR)
        rate = self.funding_fn(pos.symbol, pos.entry_time)
        if rate is None:
            funding = notional * r.fallback_funding_per_hour * hours          # aina vastaan
        else:
            funding = notional * rate * hours * (1 if long else -1)          # + = kulu
        net = gross - fees - funding
        spread_slip = (pos.qty * pos.entry_ref * (pos.entry_half_spread + r.slippage)
                       + pos.qty * ref * (hs + slip))
        s.equity += net
        s.day_pnl += net
        s.peak = max(s.peak, s.equity)
        dd = 1 - s.equity / s.peak
        s.max_drawdown_seen = max(s.max_drawdown_seen, dd)
        notes: list[str] = []
        if net < 0:
            s.consecutive_losses += 1
            if s.consecutive_losses >= r.max_consecutive_losses:
                s.pause_until = t + r.loss_streak_pause_min * 60_000
                s.consecutive_losses = 0
                notes.append(f"      ! {r.max_consecutive_losses} peräkkäistä tappiota – tauko {r.loss_streak_pause_min} min")
        else:
            s.consecutive_losses = 0
        if s.day_pnl <= -r.daily_loss_limit * s.day_start_equity and not s.day_blocked:
            s.day_blocked = True
            notes.append(f"      ! päivän tappioraja saavutettu ({s.day_pnl:,.2f} USD) – ei uusia kauppoja tänään (UTC)")
        if dd >= r.max_drawdown and not s.halted:
            s.halted = True
            notes.append(f"      !!! pudotus {dd:.1%} huipusta – kaupankäynti PYSÄYTETTY (vaatii käsin nollauksen)")
        del self.positions[pos.symbol]
        tr = Trade(pos.id, r.version, pos.symbol, pos.side, ts(pos.signal_time), ts(pos.entry_time),
                   round(pos.entry_price, 8), ts(t), round(exit_price, 8), pos.qty, round(notional, 2),
                   pos.stop, round(pos.target, 8), pos.reason, reason, pos.bars_held,
                   round(gross, 4), round(fees, 4), round(funding, 4), round(spread_slip, 4),
                   round(net, 4), round(net / (pos.qty * pos.risk_r), 3), round(s.equity, 2),
                   round(pos.risk_budget, 4), round(net / pos.risk_budget, 3) if pos.risk_budget else 0.0,
                   lopputulos(reason), pos.entry_ref, ref,
                   round(pos.qty * ((ref - pos.entry_ref) if long else (pos.entry_ref - ref)), 4),
                   round(pos.risk_r, 10), getattr(pos, "signaalityyppi", ""), getattr(pos, "cost_to_r", 0.0))
        self.trades.append(tr)
        sign = "+" if net >= 0 else ""
        self.log(f"[{pos.symbol} {ts(t)}] SULKU #{pos.id} {pos.side.upper()} @ {exit_price:.6g} – syy: {reason}\n"
                 f"      avausperuste: {pos.reason}\n"
                 f"      brutto {gross:+,.2f} | palkkiot −{fees:,.2f} | funding {-funding:+,.4f} | "
                 f"(spread+liukuma sisältyy hintoihin ≈ {spread_slip:,.2f}) | NETTO {sign}{net:,.2f} USD "
                 f"({tr.r_multiple:+.2f} R, {tr.budget_multiple:+.2f} x riskibudjetti) | pääoma {s.equity:,.2f}")
        for n_ in notes:
            self.log(n_)
        self._event("close", **asdict(tr))
        if self.on_trade:
            self.on_trade(tr)

    def close_all(self, t: int, prices: dict[str, float], reason: str = "ajon loppu") -> None:
        for sym, pos in list(self.positions.items()):
            if sym in prices:
                self._close(pos, t, prices[sym], reason, stop_fill=False)
        self.pending.clear()


# ---------------------------------------------------------------- yhteenveto
def summarize(trades: list[Trade], engine: PaperEngine) -> str:
    r = engine.r
    n = len(trades)
    lines = [f"Sääntöversio {r.version} | kauppoja {n} | alkupääoma {r.start_equity:,.0f} USD | "
             f"loppupääoma {engine.state.equity:,.2f} USD"]
    if n:
        wins = [t for t in trades if t.net_pnl > 0]
        gp = sum(t.net_pnl for t in wins)
        gl = -sum(t.net_pnl for t in trades if t.net_pnl <= 0)
        lines += [
            f"Voittoja {len(wins)}/{n} ({len(wins) / n:.0%}) | nettotulos {sum(t.net_pnl for t in trades):+,.2f} USD "
            f"| keskim. {sum(t.r_multiple for t in trades) / n:+.3f} R (hinta) / "
            f"{sum(t.budget_multiple for t in trades) / n:+.3f} x riskibudjetti per kauppa | profit factor "
            f"{(gp / gl) if gl else float('inf'):.2f}",
            f"Bruttotulos {sum(t.gross_pnl for t in trades):+,.2f} | palkkiot −{sum(t.fees for t in trades):,.2f} | "
            f"funding {-sum(t.funding for t in trades):+,.2f} | spread+liukuma (hinnoissa) ≈ "
            f"{sum(t.spread_slippage_est for t in trades):,.2f} USD",
            f"Suurin pudotus huipusta {engine.state.max_drawdown_seen:.2%}",
        ]
        for label, key in (("Sulkemissyyt", lambda t: t.close_reason.split(" (")[0]),
                           ("Suunta", lambda t: t.side),
                           ("Markkina", lambda t: t.symbol)):
            groups: dict[str, list[Trade]] = {}
            for t in trades:
                groups.setdefault(key(t), []).append(t)
            lines.append(label + ": " + " | ".join(
                f"{k} {len(v)} kpl {sum(x.net_pnl for x in v):+,.2f}" for k, v in sorted(groups.items())))
    if engine.skipped:
        lines.append("Ohitetut signaalit: " + " | ".join(
            f"{k.split(':')[0]} {v}" for k, v in sorted(engine.skipped.items(), key=lambda kv: -kv[1])))
    return "\n".join(lines)


def trades_to_jsonl(trades: list[Trade], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for t in trades:
            f.write(json.dumps(asdict(t), ensure_ascii=False) + "\n")
