"""Versioidut kaupankäyntisäännöt (vain paperikauppa).

Sääntösarjaa EI muuteta tulosten perusteella. Muutos = uusi versio uudella
avaimella RULESETS-sanakirjaan + oma dokumentti docs/SAANNOT_vN.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
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
    cost_model: str = "v1"              # "v1" = alkuperäinen arvio, "korjattu" = estimate_costs()
    notes: str = ""

    def round_trip_cost(self, half_spread: float) -> float:
        """Arvioitu kokonaiskulu suhteessa hintaan (avaus + sulku)."""
        return 2 * self.taker_fee + 2 * (half_spread + self.slippage)


@dataclass(frozen=True)
class CostEstimate:
    """Kulut ja riski YHTÄ yksikköä kohden (hinnan yksiköissä). Ks. docs/SAANNOT_v2.md."""
    entry_fill: float        # toteutunut avaushinta = viite ± (½spread + liukuma)
    stop_fill: float         # toteutuva hinta, jos stop laukeaa = stop ∓ (½spread + stop-liukuma)
    price_risk_r: float      # R = |avaushinta − stop| (hintariski, ei kuluja)
    entry_friction: float    # avauksen spread + liukuma (sisältyy jo entry_fill-hintaan)
    exit_friction: float     # stop-sulun spread + stop-liukuma
    fees: float              # taker-palkkio avauksesta ja stop-sulusta
    funding: float           # varovainen arvio koko maksimipitoajalle
    total_cost: float        # kaikki kulut = entry + exit + palkkiot + funding
    loss_at_stop: float      # kokonaistappio stopissa = R + exit_friction + fees + funding


def estimate_costs(r: "Ruleset", side: str, ref_price: float, stop: float, half_spread: float) -> CostEstimate:
    long = side == "long"
    ef = ref_price * (half_spread + r.slippage)
    entry = ref_price + ef if long else ref_price - ef
    xf = stop * (half_spread + r.stop_slippage)
    stop_fill = stop - xf if long else stop + xf
    fees = r.taker_fee * (entry + stop_fill)
    funding = entry * r.fallback_funding_per_hour * r.max_hold_bars / 60
    R = abs(entry - stop)
    return CostEstimate(entry, stop_fill, R, ef, xf, fees, funding,
                        ef + xf + fees + funding, R + xf + fees + funding)


_V1 = Ruleset(version="v1", min_score=2, min_volume_ratio=1.2, require_context=True,
              notes="Ensimmäinen oletussääntösarja, lukittu 29.9.2026. Ks. docs/SAANNOT_v1.md")

RULESETS: dict[str, Ruleset] = {
    "v1": _V1,
    # Lukittu 29.9.2026 – korjattu kulumalli, muuten = v1. Ks. docs/SAANNOT_v2.md
    "v1.1": replace(_V1, version="v1.1", cost_model="korjattu",
                    notes="v1 + korjattu kulumalli (R ≥ 2 × kulut). docs/SAANNOT_v2.md"),
    # Lukittu 29.9.2026 – ainoa ero v1.1:een: kulusuodatin 4 ×
    "v2": replace(_V1, version="v2", cost_model="korjattu", min_r_to_cost=4.0,
                  notes="v1.1 + kulusuodatin R ≥ 4 × kulut. docs/SAANNOT_v2.md"),
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
