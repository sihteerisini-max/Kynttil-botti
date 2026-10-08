"""Perustietorakenteet: kynttilä ja siitä lasketut mittasuhteet."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Candle:
    """Yksi 1 minuutin kynttilä.

    closed=False tarkoittaa, että kynttilä on vielä muodostumassa: sen
    ylä-/alahinta, päätöshinta ja volyymi voivat vielä muuttua.
    """
    symbol: str
    open_time: int          # millisekunteina (UTC)
    open: float
    high: float
    low: float
    close: float
    volume: float
    closed: bool = True
    close_time: int = 0     # millisekunteina; 0 = open_time + 60 000 - 1

    # --- perusmitat -------------------------------------------------------
    @property
    def range(self) -> float:          # koko vaihteluväli
        return self.high - self.low

    @property
    def body(self) -> float:           # rungon koko
        return abs(self.close - self.open)

    @property
    def upper_wick(self) -> float:     # yläpuolinen varjo
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:     # alapuolinen varjo
        return min(self.open, self.close) - self.low

    @property
    def direction(self) -> int:        # +1 nouseva, -1 laskeva, 0 tasan
        if self.close > self.open:
            return 1
        if self.close < self.open:
            return -1
        return 0

    def ratio(self, part: float) -> float:
        """Osuus vaihteluvälistä (0..1). Nollakokoisella kynttilällä 0."""
        return part / self.range if self.range > 0 else 0.0

    @property
    def time_str(self) -> str:
        return datetime.fromtimestamp(self.open_time / 1000, tz=timezone.utc).strftime("%H:%M UTC")


@dataclass
class Context:
    """Edeltävästä, jo SULJETUSTA historiasta laskettu tausta."""
    n_history: int
    avg_range: float        # edellisten kynttilöiden keskimääräinen vaihteluväli
    avg_body: float
    avg_volume: float
    trend: str              # "nousu" | "lasku" | "sivuttain"
    trend_move_atr: float   # edeltävä liike keskim. vaihteluväleinä (+ ylös, - alas)
    recent_low: float       # edeltävien kynttilöiden alin hinta
    recent_high: float      # edeltävien kynttilöiden ylin hinta


@dataclass
class Observation:
    """Yksi havainto (kuvio) yhdestä kynttilästä."""
    symbol: str
    open_time: int
    status: str             # "KESKENERÄINEN" | "VAHVISTETTU"
    key: str                # koneluettava tunniste, esim. "hammer"
    name: str               # suomenkielinen nimi
    bias: str               # "nousuun viittaava" | "laskuun viittaava" | "epäröinti" | "jatkuvuus"
    strength: str           # "heikko" | "kohtalainen" | "selvempi"
    reasons: list[str] = field(default_factory=list)
    score: int = 0              # selkeyspisteet (ks. docs/SAANNOT_v1.md)
    volume_ratio: float = 0.0   # volyymi / 20 edeltävän keskiarvo
    context_ok: bool = False    # edeltävä liike sopii kuvion tulkintaan
    # --- läpinäkyvyys (ei vaikuta tunnistukseen) ---
    conditions: list = field(default_factory=list)   # [{"ehto","arvo","raja","ok"}]
    measures: dict = field(default_factory=dict)      # mitatut suureet
    candles_used: dict = field(default_factory=dict)  # mihin kynttilöihin havainto perustuu
    detected_at: int = 0                              # milloin tunnistus syntyi (ms, UTC)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol, "open_time": self.open_time, "status": self.status,
            "key": self.key, "name": self.name, "bias": self.bias,
            "strength": self.strength, "reasons": self.reasons, "score": self.score,
            "volume_ratio": round(self.volume_ratio, 3), "context_ok": self.context_ok,
            "conditions": self.conditions, "measures": self.measures,
            "candles_used": self.candles_used, "detected_at": self.detected_at,
        }
