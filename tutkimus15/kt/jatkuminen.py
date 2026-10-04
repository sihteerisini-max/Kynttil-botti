"""Jatkumissignaali (lukittu 30.9.2026, docs/AJOITUSTESTI_1.md).

Liike jatkuu samaan suuntaan: edeltävä trendi + voimakas samansuuntainen kynttilä, joka päättyy
lähelle ääripäätään ja murtaa edeltävän 10 minuutin ääripään, sekä tavallista suurempi volyymi.
Kaikki ehdot lasketaan SULJETUSTA kynttilästä ja sitä edeltävästä suljetusta historiasta
(Context = build_context(edeltävät)). Pelkkä kynttilän väri ei riitä.

Rajat valittiin etukäteen yleisinä pyöreinä arvoina ja käyttäen jo olemassa olevia rajoja
(trendi 1,5 ja volyymi 1,2 kuten kääntymissignaaleissa). Niitä ei sovitettu mihinkään
yksittäiseen hintaliikkeeseen.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import Candle, Context


@dataclass(frozen=True)
class JatkoParams:
    trend_threshold_atr: float = 1.5   # = patterns.Params.trend_threshold_atr (Context.trend)
    body_min: float = 0.50             # runko ≥ 50 % vaihteluvälistä (ei doji / hyrrä)
    range_min: float = 1.00            # vaihteluväli ≥ 1,0 × 20 edeltävän keskiarvo
    close_zone: float = 0.25           # päätös vaihteluvälin uloimmassa neljänneksessä liikkeen suuntaan
    volume_min: float = 1.20           # volyymi ≥ 1,2 × 20 edeltävän keskiarvo (= kääntymissignaalit)
    # murto: päätös alittaa (short) / ylittää (long) edeltävien 10 kynttilän alimman / ylimmän hinnan


JATKO = JatkoParams()


def _c(ehto: str, arvo: float, raja: str, ok: bool) -> dict:
    return {"ehto": ehto, "arvo": round(float(arvo), 4), "raja": raja, "ok": bool(ok)}


def ehdot(ctx: Context, cur: Candle, side: str, jp: JatkoParams = JATKO) -> list[dict]:
    """Jatkumissignaalin ehdot yhdelle suunnalle. Kaikkien pitää täyttyä."""
    short = side == "short"
    R, B = cur.range, cur.body
    rel = R / ctx.avg_range if ctx.avg_range > 0 else 0.0
    vr = cur.volume / ctx.avg_volume if ctx.avg_volume > 0 else 0.0
    pos = ((cur.close - cur.low) / R if short else (cur.high - cur.close) / R) if R > 0 else 1.0
    brk = (cur.close - ctx.recent_low) if short else (cur.close - ctx.recent_high)
    return [
        _c("edeltävä 10 min liike / keskim. vaihteluväli", ctx.trend_move_atr,
           f"≤ −{jp.trend_threshold_atr} (lasku)" if short else f"≥ +{jp.trend_threshold_atr} (nousu)",
           ctx.trend == ("lasku" if short else "nousu")),
        _c("kynttilän suunta", cur.direction, "laskeva (−1)" if short else "nouseva (+1)",
           cur.direction == (-1 if short else 1)),
        _c("runko / vaihteluväli", B / R if R > 0 else 0.0, f"≥ {jp.body_min}", R > 0 and B >= jp.body_min * R),
        _c("vaihteluväli / keskim. vaihteluväli (20 ed.)", rel, f"≥ {jp.range_min}", rel >= jp.range_min),
        _c("päätöksen etäisyys " + ("alimmasta" if short else "ylimmästä") + " / vaihteluväli", pos,
           f"≤ {jp.close_zone}", pos <= jp.close_zone),
        _c("päätös − edeltävän 10 min " + ("alin" if short else "ylin"), brk, "< 0" if short else "> 0",
           brk < 0 if short else brk > 0),
        _c("volyymi / keskim. volyymi (20 ed.)", vr, f"≥ {jp.volume_min}", vr >= jp.volume_min),
    ]


def signaali(ctx: Context | None, cur: Candle, jp: JatkoParams = JATKO) -> tuple[str, list[dict]] | None:
    """('long'|'short', ehdot), jos jatkumissignaali täyttyy; muuten None."""
    if ctx is None or not cur.closed:
        return None
    for side in ("long", "short"):
        cs = ehdot(ctx, cur, side, jp)
        if all(x["ok"] for x in cs):
            return side, cs
    return None
