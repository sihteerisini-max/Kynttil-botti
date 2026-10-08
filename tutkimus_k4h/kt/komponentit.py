"""Botin päätös jaettuna kahteen osaan kuvioittain:

  muoto  = täyttääkö kynttilä (tai kynttiläpari) kuvion muotoehdot
  tausta = täyttyvätkö erilliset taustaehdot: edeltävä liike ja suhteellinen koko

Käyttää samoja raja-arvoja (patterns.Params) kuin detect(). Testi
tests/test_komponentit.py varmistaa, että muoto ∧ tausta vastaa täsmälleen detect()-tulosta.
Tämä moduuli EI muuta tunnistusta – se vain erittelee sen.
"""
from __future__ import annotations

from typing import Sequence

from .models import Candle
from .patterns import DEFAULT, Params, build_context

PATTERNS = ["doji", "dragonfly_doji", "gravestone_doji", "hammer", "hanging_man", "inverted_hammer",
            "shooting_star", "bullish_engulfing", "bearish_engulfing", "bullish_marubozu", "bearish_marubozu"]


def _c(text, value, limit, ok):
    if isinstance(value, float):
        value = round(value, 4) if value == value and abs(value) != float("inf") else "∞"
    return {"ehto": text, "arvo": value, "raja": limit, "ok": bool(ok)}


def components(prev: Sequence[Candle], cur: Candle, p: Params = DEFAULT) -> dict | None:
    """{kuvio: {"muoto": bool, "tausta": bool, "muoto_ehdot": [...], "tausta_ehdot": [...]}}.
    None, jos historiaa ei ole tarpeeksi taustan laskemiseen."""
    ctx = build_context(prev, p)
    if ctx is None or ctx.avg_range <= 0:
        return None
    R, B, U, L = cur.range, cur.body, cur.upper_wick, cur.lower_wick
    r = (lambda x: x / R) if R > 0 else (lambda x: 0.0)
    rel = R / ctx.avg_range
    size_ok = R > 0 and rel >= p.min_range_rel
    size = _c(f"vaihteluväli / keskim. vaihteluväli ({p.avg_window} ed.)", rel, f"≥ {p.min_range_rel}", size_ok)
    trend = _c(f"edeltävä {p.trend_window} min liike / keskim. vaihteluväli", ctx.trend_move_atr,
               f"lasku ≤ −{p.trend_threshold_atr}, nousu ≥ +{p.trend_threshold_atr}", True)
    down = ctx.trend == "lasku"
    up = ctx.trend == "nousu"
    down_c = dict(trend, ok=down, raja=f"≤ −{p.trend_threshold_atr} (lasku)")
    up_c = dict(trend, ok=up, raja=f"≥ +{p.trend_threshold_atr} (nousu)")
    out = {}

    doji = R > 0 and B <= p.doji_body * R
    body_doji = _c("runko / vaihteluväli", r(B), f"≤ {p.doji_body}", doji)
    out["doji"] = {"muoto": doji, "muoto_ehdot": [body_doji], "tausta": size_ok, "tausta_ehdot": [size]}

    dfly = [body_doji, _c("yläsvarjo / vaihteluväli", r(U), "≤ 0.10", R > 0 and U <= 0.10 * R),
            _c("alavarjo / vaihteluväli", r(L), f"≥ {p.long_shadow_min}", R > 0 and L >= p.long_shadow_min * R)]
    out["dragonfly_doji"] = {"muoto": all(x["ok"] for x in dfly), "muoto_ehdot": dfly,
                             "tausta": size_ok, "tausta_ehdot": [size]}
    grav = [body_doji, _c("alavarjo / vaihteluväli", r(L), "≤ 0.10", R > 0 and L <= 0.10 * R),
            _c("yläsvarjo / vaihteluväli", r(U), f"≥ {p.long_shadow_min}", R > 0 and U >= p.long_shadow_min * R)]
    out["gravestone_doji"] = {"muoto": all(x["ok"] for x in grav), "muoto_ehdot": grav,
                              "tausta": size_ok, "tausta_ehdot": [size]}

    not_doji = _c("runko / vaihteluväli", r(B), f"> {p.doji_body} (ei doji)", R > 0 and not doji)
    ham = [not_doji,
           _c("alavarjo / runko", (L / B) if B else float("inf"), f"≥ {p.shadow_to_body}", L >= p.shadow_to_body * B),
           _c("alavarjo / vaihteluväli", r(L), f"≥ {p.long_shadow_min}", R > 0 and L >= p.long_shadow_min * R),
           _c("yläsvarjo / vaihteluväli", r(U), f"≤ {p.short_shadow_max}", R > 0 and U <= p.short_shadow_max * R)]
    ham_ok = all(x["ok"] for x in ham)
    out["hammer"] = {"muoto": ham_ok, "muoto_ehdot": ham, "tausta": size_ok and down, "tausta_ehdot": [down_c, size]}
    out["hanging_man"] = {"muoto": ham_ok, "muoto_ehdot": ham, "tausta": size_ok and up, "tausta_ehdot": [up_c, size]}

    inv = [not_doji,
           _c("yläsvarjo / runko", (U / B) if B else float("inf"), f"≥ {p.shadow_to_body}", U >= p.shadow_to_body * B),
           _c("yläsvarjo / vaihteluväli", r(U), f"≥ {p.long_shadow_min}", R > 0 and U >= p.long_shadow_min * R),
           _c("alavarjo / vaihteluväli", r(L), f"≤ {p.short_shadow_max}", R > 0 and L <= p.short_shadow_max * R)]
    inv_ok = all(x["ok"] for x in inv)
    out["inverted_hammer"] = {"muoto": inv_ok, "muoto_ehdot": inv, "tausta": size_ok and down, "tausta_ehdot": [down_c, size]}
    out["shooting_star"] = {"muoto": inv_ok, "muoto_ehdot": inv, "tausta": size_ok and up, "tausta_ehdot": [up_c, size]}

    pc = prev[-1] if prev else None
    for key, d, want_c, want in (("bullish_engulfing", 1, down_c, down), ("bearish_engulfing", -1, up_c, up)):
        if pc is None or not pc.closed or pc.range <= 0:
            ok_list = [_c("edellinen kynttilä saatavilla", 0, "suljettu, R > 0", False)]
        else:
            ok_list = [
                _c("edellisen runko / vaihteluväli", pc.body / pc.range, f"> {p.doji_body}", pc.body > p.doji_body * pc.range),
                _c("edellinen kynttilä " + ("laskeva" if d == 1 else "nouseva"), pc.direction, str(-d), pc.direction == -d),
                _c("tämä kynttilä " + ("nouseva" if d == 1 else "laskeva"), cur.direction, str(d), cur.direction == d),
                _c("avaus − edellinen päätös", cur.open - pc.close, "≤ 0" if d == 1 else "≥ 0",
                   cur.open <= pc.close if d == 1 else cur.open >= pc.close),
                _c("päätös − edellinen avaus", cur.close - pc.open, "> 0" if d == 1 else "< 0",
                   cur.close > pc.open if d == 1 else cur.close < pc.open),
                _c("runko / edellinen runko", (B / pc.body) if pc.body else float("inf"), "> 1", B > pc.body),
            ]
        out[key] = {"muoto": all(x["ok"] for x in ok_list), "muoto_ehdot": ok_list,
                    "tausta": size_ok and want, "tausta_ehdot": [want_c, size]}

    big = rel >= p.marubozu_range_rel
    big_c = _c("vaihteluväli / keskim. vaihteluväli", rel, f"≥ {p.marubozu_range_rel}", big)
    for key, d in (("bullish_marubozu", 1), ("bearish_marubozu", -1)):
        m = [_c("runko / vaihteluväli", r(B), f"≥ {p.marubozu_body}", R > 0 and B >= p.marubozu_body * R),
             _c("suunta " + ("nouseva" if d == 1 else "laskeva"), cur.direction, str(d), cur.direction == d)]
        out[key] = {"muoto": all(x["ok"] for x in m), "muoto_ehdot": m,
                    "tausta": size_ok and big, "tausta_ehdot": [big_c]}
    return out


# Miten detect()-avaimet vastaavat kuvioita (muoto ∧ tausta)
def detected_patterns(keys: set[str]) -> set[str]:
    out = set()
    if keys & {"doji", "dragonfly_doji", "gravestone_doji", "long_legged_doji"}:
        out.add("doji")
    for k in ("dragonfly_doji", "gravestone_doji", "hammer", "hanging_man", "inverted_hammer",
              "shooting_star", "bullish_marubozu", "bearish_marubozu"):
        if k in keys:
            out.add(k)
    return out
