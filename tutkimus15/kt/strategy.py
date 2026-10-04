"""Versioidut kaupankäyntisäännöt (vain paperikauppa).

Sääntösarjaa EI muuteta tulosten perusteella. Muutos = uusi versio uudella
avaimella RULESETS-sanakirjaan + oma dokumentti docs/SAANNOT_vN.md.
"""
from __future__ import annotations

import math
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
    # --- marginaali (vain korjattu malli) ---
    max_leverage_cap: float = 10.0      # Kraken EEA: enintään 10x -> alkumarginaali vähintään 10 %
    margin_limit: float = 0.5           # käytetty alkumarginaali yhteensä ≤ 50 % pääomasta
    cost_model: str = "v1"              # "v1" = alkuperäinen arvio, "korjattu" = estimate_costs()
    tunnistus: str = "T1"               # patterns.TUNNISTUS-avain (T1 = alkuperäinen, T2 = koon alaraja 0,6)
    signaalit: str = "kaanto"           # "kaanto" = kääntymiskuviot, "jatko" = jatkumissignaali (jatkuminen.py)
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
    funding_reserve: float   # funding-VARAUS koko maksimipitoajalle (arvio, ei toteutunut funding)
    stop_cost_estimate: float  # C = stop-skenaarion kustannusarvio = entry + exit + palkkiot + funding-varaus
    loss_at_stop: float      # L = kokonaistappio stopissa mallin oletuksilla = R + exit + palkkiot + varaus


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


@dataclass(frozen=True)
class DefaultSpec:
    """Käytetään vain testeissä/demossa, kun oikeita sopimustietoja ei anneta."""
    qty_step: float = 1e-8
    max_position: float = 1e18

    def initial_margin(self, notional: float) -> float:
        return 0.10


@dataclass(frozen=True)
class Sizing:
    qty: float
    notional: float
    initial_margin_rate: float
    margin: float
    risk_budget: float          # q × L (≤ tavoitebudjetti pyöristyksen ja rajojen vuoksi)
    binding: str                # mikä raja määräsi koon


def size_position(r: "Ruleset", equity: float, loss_at_stop: float, entry: float, spec,
                  open_notional: float, open_margin: float) -> Sizing:
    """Positiokoko korjatussa mallissa. Järjestys:
    1) q = 0,5 % pääomasta / L
    2) rajat: nimellisarvo/positio ≤ 3 × pääoma, avoin nimellisarvo yhteensä ≤ 5 × pääoma,
       käytetty alkumarginaali yhteensä ≤ 50 % pääomasta, Krakenin maxPositionSize
    3) pyöristys ALASPÄIN sallittuun kokoaskeleeseen; jos alle yhden askeleen -> 0
    Alkumarginaali = max(Krakenin porrastettu alkumarginaali, 1 / 10x)."""
    cands = {
        "riskibudjetti": equity * r.risk_per_trade / loss_at_stop,
        "nimellisarvo/positio": r.max_notional_per_pos * equity / entry,
        "nimellisarvo yhteensä": max(0.0, r.max_notional_total * equity - open_notional) / entry,
        "Krakenin maksimikoko": spec.max_position,
    }
    q0 = min(cands.values())
    im = max(spec.initial_margin(q0 * entry), 1 / r.max_leverage_cap)
    cands["marginaali"] = max(0.0, r.margin_limit * equity - open_margin) / (entry * im)
    binding = min(cands, key=cands.get)
    q = cands[binding]
    step = spec.qty_step
    digits = max(0, -int(math.floor(math.log10(step)))) if step < 1 else 0
    q = round(math.floor(q / step + 1e-9) * step, digits)
    if q < step:
        q = 0.0
    return Sizing(q, q * entry, im, q * entry * im, q * loss_at_stop, binding)


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
# Lukittu 30.9.2026 – T2-testi (docs/TESTI_T2.md). Ainoa ero pohjaversioon: tunnistus T2.
RULESETS["v1.1-T2"] = replace(RULESETS["v1.1"], version="v1.1-T2", tunnistus="T2",
                              notes="v1.1 + tunnistus T2 (koon alaraja 0,6). docs/TESTI_T2.md")
RULESETS["v2-T2"] = replace(RULESETS["v2"], version="v2-T2", tunnistus="T2",
                            notes="v2 + tunnistus T2 (koon alaraja 0,6). docs/TESTI_T2.md")
# Lukittu 30.9.2026 – AJOITUSTESTI 1 (docs/AJOITUSTESTI_1.md). Pohja v1.1-T2; muutokset:
# kulusuodatin pois avausten esteenä (kulut lasketaan ja kirjataan), tavoite 1 R (stop 1 R, aikaraja 15 min).
# Kaksi erillistä paperitiliä: kääntymissignaalit (T2) ja jatkumissignaalit.
_AJ = replace(RULESETS["v1.1-T2"], min_r_to_cost=0.0, target_r=1.0)
RULESETS["aj1-kaanto"] = replace(_AJ, version="aj1-kaanto", signaalit="kaanto",
                                 notes="Ajoitustesti 1: T2-kääntymissignaalit, ei kulusuodatinta, 1 R / 1 R / 15 min")
RULESETS["aj1-jatko"] = replace(_AJ, version="aj1-jatko", signaalit="jatko",
                                notes="Ajoitustesti 1: jatkumissignaali, ei kulusuodatinta, 1 R / 1 R / 15 min")
@dataclass
class Signal:
    symbol: str
    side: str                        # "long" | "short"
    candle: Candle                   # signaalikynttilä (suljettu)
    stop: float
    avg_range: float
    observations: list[Observation] = field(default_factory=list)
    tyyppi: str = "kääntyminen"      # "kääntyminen" | "jatkuminen"
    kuvaus: str = ""                 # jatkumissignaalin peruste

    def reason(self) -> str:
        if self.kuvaus:
            return self.kuvaus
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
    if r.signaalit == "jatko":
        from .jatkuminen import signaali as jatko
        hit = jatko(ctx, candle)
        if not hit:
            return None
        side, cs = hit
        buf = r.stop_buffer_atr * ctx.avg_range
        stop = candle.low - buf if side == "long" else candle.high + buf
        vol = next(x["arvo"] for x in cs if x["ehto"].startswith("volyymi"))
        size = next(x["arvo"] for x in cs if x["ehto"].startswith("vaihteluväli"))
        kuv = (f"Jatkuminen {'nousussa' if side == 'long' else 'laskussa'}: "
               f"{'nouseva' if side == 'long' else 'laskeva'} kynttilä {size:.1f}x keskikoko, päätös "
               f"{'uuteen 10 min huippuun' if side == 'long' else 'uuteen 10 min pohjaan'}, "
               f"trendi {ctx.trend_move_atr:+.1f}, volyymi {vol:.1f}x")
        return Signal(candle.symbol, side, candle, stop, ctx.avg_range, [], "jatkuminen", kuv)
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
