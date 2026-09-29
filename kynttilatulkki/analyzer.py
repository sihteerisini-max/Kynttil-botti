"""Symbolikohtainen tila: pitää kirjaa suljetuista kynttilöistä ja erottaa
keskeneräiset havainnot vahvistetuista."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .models import Candle, Observation
from .patterns import DEFAULT, Params, build_context, describe_candle, detect

DISCLAIMER = "Havainto kuvaa mennyttä hintaliikettä – se ei ole ennuste eikä kaupankäyntisuositus."


@dataclass
class Event:
    """Mitä analysaattori haluaa kertoa tästä päivityksestä."""
    kind: str                    # "provisional" | "confirmed" | "not_confirmed" | "candle"
    candle: Candle
    observations: list[Observation] = field(default_factory=list)
    text: str = ""


class SymbolAnalyzer:
    def __init__(self, symbol: str, params: Params = DEFAULT, max_history: int = 300,
                 min_elapsed: float = 0.25):
        self.symbol = symbol
        self.min_elapsed = min_elapsed   # keskeneräistä ei tulkita ennen kuin 25 % minuutista kulunut
        self.params = params
        self.history: deque[Candle] = deque(maxlen=max_history)
        self._provisional_keys: dict[int, set[str]] = {}   # open_time -> avainjoukko
        self._printed: dict[int, set[frozenset]] = {}       # jo tulostetut joukot per kynttilä

    def warmup(self, candles: list[Candle]) -> None:
        """Lisää historiaa havainnoimatta (vain suljetut kynttilät)."""
        for c in candles:
            if c.closed and (not self.history or c.open_time > self.history[-1].open_time):
                self.history.append(c)

    def update(self, candle: Candle, now_ms: int | None = None) -> list[Event]:
        """Käsittelee uuden tiedon kynttilästä. Palauttaa tapahtumat, jotka
        kannattaa näyttää käyttäjälle."""
        if self.history and candle.open_time <= self.history[-1].open_time:
            return []   # vanha tai jo suljettu kynttilä – ohitetaan
        prev = list(self.history)
        events: list[Event] = []

        if not candle.closed:
            elapsed = 1.0
            if now_ms is not None:
                elapsed = (now_ms - candle.open_time) / 60_000
            if elapsed < self.min_elapsed:
                return []   # minuutin alussa muoto on vielä pelkkää kohinaa
            obs = detect(prev, candle, self.params, elapsed_frac=elapsed)
            for o in obs:
                o.detected_at = now_ms if now_ms is not None else 0
            keys = {o.key for o in obs}
            if keys != self._provisional_keys.get(candle.open_time, set()):
                self._provisional_keys[candle.open_time] = keys
                printed = self._printed.setdefault(candle.open_time, set())
                if obs and frozenset(keys) not in printed:
                    printed.add(frozenset(keys))
                    events.append(Event("provisional", candle, obs))
            return events

        # Suljettu kynttilä -> vahvistettu havainto
        obs = detect(prev, candle, self.params)
        for o in obs:   # vahvistus syntyy aikaisintaan kynttilän sulkeutuessa
            o.detected_at = max(now_ms or 0, candle.open_time + 60_000)
        ctx = build_context(prev, self.params)
        text = describe_candle(candle, ctx) if ctx else f"lämmittely: {len(prev)}/{self.params.min_history} kynttilää historiaa"
        events.append(Event("candle", candle, [], text))
        if obs:
            events.append(Event("confirmed", candle, obs))
        seen = self._provisional_keys.pop(candle.open_time, set())
        lost = seen - {o.key for o in obs}
        if lost:
            events.append(Event("not_confirmed", candle, [], ", ".join(sorted(lost))))
        self.history.append(candle)
        # siivotaan vanhat keskeneräiset
        for k in [k for k in self._provisional_keys if k < candle.open_time]:
            del self._provisional_keys[k]
        for k in [k for k in self._printed if k <= candle.open_time]:
            del self._printed[k]
        return events


# ---------------------------------------------------------------------------
# Tulostus selkokielellä
# ---------------------------------------------------------------------------
def format_event(ev: Event, verbose: bool = True) -> str:
    c = ev.candle
    head = f"[{c.symbol} {c.time_str}]"
    if ev.kind == "candle":
        return f"{head} suljettu kynttilä: {ev.text}"
    if ev.kind == "not_confirmed":
        return f"{head} ✗ keskeneräinen havainto ei vahvistunut kynttilän sulkeutuessa ({ev.text})"
    lines = []
    for o in ev.observations:
        if ev.kind == "provisional":
            tag = "… KESKENERÄINEN (voi vielä muuttua)"
        else:
            tag = "✓ VAHVISTETTU (kynttilä sulkeutui)"
        lines.append(f"{head} {tag}: {o.name} – {o.bias}, signaalin selkeys: {o.strength}")
        if verbose:
            for r in o.reasons:
                lines.append(f"      · {r}")
    if ev.kind == "confirmed" and verbose:
        lines.append(f"      ! {DISCLAIMER}")
    return "\n".join(lines)
