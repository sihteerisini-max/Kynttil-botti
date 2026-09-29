"""Versioidut kaupankäyntisäännöt (vain paperikauppa).

Sääntösarjaa EI muuteta tulosten perusteella. Muutos = uusi versio uudella
avaimella RULESETS-sanakirjaan + oma dokumentti docs/SAANNOT_vN.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .models import Candle, Context, Observation


@dataclass(frozen=True)
class Ruleset:
    version: str
    # --- signaali ---
    min_score: int                  # 2 = "kohtalainen"
    min_volume_ratio: float         # signaalikynttilän volyymi / 20 ed. keskiarvo
    require_context: bool
    long_bias: str = "nousuun viittaava"
    short_bias: str = "laskuun viittaava"
    # --- kulut ---
    taker_fee: float = 0.0005       # Kraken Derivatives, $0+ porras
    slippage: float = 0.0002
    stop_slippage: float = 0.0005
    min_half_spread_backtest: float = 0.0001
    fallback_funding_per_hour: float = 0.0000125   # aina omaa positiota vastaan
    # --- stop / tavoite / aika ---
    stop_buffer_atr: float = 0.10
    target_r: float = 1.5
    max_hold_bars: int = 15
    min_r_to_cost: float = 2.0
    # --- koko ---
    start_equity: float = 10_000.0
    risk_per_trade: float = 0.005
    max_notional_per_pos: float = 3.0   # x pääoma
    max_notional_total: float = 5.0     # x pääoma
    max_positions: int = 3
    # --- tappiorajat ---
    daily_loss_limit: float = 0.02
    max_consecutive_losses: int = 4
    loss_streak_pause_min: int = 60
    max_drawdown: float = 0.10
    notes: str = ""

    def round_trip_cost(self, half_spread: float) -> float:
        """Arvioitu kokonaiskulu suhteessa hintaan (avaus + sulku)."""
        return 2 * self.taker_fee + 2 * (half_spread + self.slippage)


RULESETS: dict[str, Ruleset] = {
    "v1": Ruleset(version="v1", min_score=2, min_volume_ratio=1.2, require_context=True,
                  notes="Ensimmäinen oletussääntösarja, lukittu 29.9.2026. Ks. docs/SAANNOT_v1.md"),
}


@dataclass
class Signal:
    symbol: str
    side: str                        # "long" | "short"
    candle: Candle                   # signaalikynttilä (suljettu)
    stop: float
    avg_range: float
    observations: list[Observation] = field(default_factory=list)

    def reason(self) -> str:
        parts = []
        for o in self.observations:
            parts.append(f"{o.name} (pisteet {o.score}/{o.strength}, volyymi {o.volume_ratio:.1f}x)")
        return "; ".join(parts)


def qualifies(o: Observation, r: Ruleset) -> str | None:
    """Palauttaa 'long'/'short', jos havainto täyttää signaaliehdot, muuten None."""
    if o.status != "VAHVISTETTU":
        return None
    if r.require_context and not o.context_ok:
        return None
    if o.score < r.min_score or o.volume_ratio < r.min_volume_ratio:
        return None
    if o.bias == r.long_bias:
        return "long"
    if o.bias == r.short_bias:
        return "short"
    return None


def make_signal(candle: Candle, obs: Sequence[Observation], ctx: Context | None,
                r: Ruleset) -> Signal | None:
    if ctx is None or not candle.closed:
        return None
    sides: dict[str, list[Observation]] = {"long": [], "short": []}
    for o in obs:
        s = qualifies(o, r)
        if s:
            sides[s].append(o)
    if sides["long"] and sides["short"]:
        return None                       # ristiriitainen kynttilä -> ei kauppaa
    for side in ("long", "short"):
        if sides[side]:
            buf = r.stop_buffer_atr * ctx.avg_range
            stop = candle.low - buf if side == "long" else candle.high + buf
            return Signal(candle.symbol, side, candle, stop, ctx.avg_range, sides[side])
    return None
