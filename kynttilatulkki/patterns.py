"""Kynttilöiden tulkinta ja kuvioiden tunnistus.

Kaikki funktiot ovat puhtaita: ne saavat vain edeltävät SULJETUT kynttilät
(`prev`) ja tarkasteltavan kynttilän (`cur`). Tulevaisuuden kynttilöitä ei
ole mahdollista antaa, joten tunnistus ei voi käyttää tulevaisuustietoa.

Tunnistusehdot (R = vaihteluväli, B = runko, U = yläsvarjo, L = alavarjo,
kaikki mitattu yhdestä kynttilästä):

  doji              B <= 0.10 R
    - sudenkorento  lisäksi U <= 0.10 R ja L >= 0.60 R
    - hautakivi     lisäksi L <= 0.10 R ja U >= 0.60 R
    - pitkäjalkainen lisäksi U >= 0.30 R, L >= 0.30 R ja R >= 1.0 x keskim. R
  vasaran muoto     B > 0.10 R, L >= 2 B, L >= 0.60 R, U <= 0.15 R
    - edeltävä lasku  -> vasara (nousuun viittaava)
    - edeltävä nousu  -> hirttäytyjä (laskuun viittaava)
  käänteinen muoto  B > 0.10 R, U >= 2 B, U >= 0.60 R, L <= 0.15 R
    - edeltävä nousu  -> tähdenlento (laskuun viittaava)
    - edeltävä lasku  -> käänteinen vasara (nousuun viittaava)
  peittävä kuvio    edellinen kynttilä suljettu ja B_ed > 0.10 R_ed,
                    suunnat vastakkaiset, nykyinen runko peittää edellisen
                    rungon (avaus <= ed. päätös & päätös > ed. avaus nousevalla;
                    peilikuvana laskevalla) ja B > B_ed.
                    Krypto käy tauotta, joten avaus = ed. päätös on sallittu.
  marubozu          B >= 0.90 R ja R >= 1.2 x keskim. R

Muotoa ei tulkita lainkaan, jos R < 0.30 x keskim. R (liian pieni liike
tulkittavaksi) tai jos historiaa on alle MIN_HISTORY kynttilää.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from .models import Candle, Context, Observation


@dataclass(frozen=True)
class Params:
    min_history: int = 20          # suljettuja kynttilöitä ennen tulkintaa
    avg_window: int = 20           # keskiarvojen ikkuna
    trend_window: int = 10         # edeltävän liikkeen ikkuna
    trend_threshold_atr: float = 1.5   # liike keskim. vaihteluväleinä, jotta trendi
    extreme_window: int = 10       # "uusi paikallinen pohja/huippu" -ikkuna
    min_range_rel: float = 0.30    # tätä pienempiä ei muototulkita
    doji_body: float = 0.10
    long_shadow_min: float = 0.60
    short_shadow_max: float = 0.15
    shadow_to_body: float = 2.0
    marubozu_body: float = 0.90
    marubozu_range_rel: float = 1.2
    vol_high: float = 1.5          # volyymi / keskiarvo -> "selvästi suuri"
    vol_low: float = 0.7           # volyymi / keskiarvo -> "pieni"


DEFAULT = Params()

# Tunnistusmääritelmän versiot. T1 = käytössä kaupankäyntiversioissa v1, v1.1 ja v2 (lukittu).
# T2 = sokkoarvioinnin (sarja A) perusteella ehdotettu: suhteellisen koon alaraja 0,3 -> 0,6.
# T2:ta käytetään vain tunnistuksen arviointiin; kaupankäyntisäännöt käyttävät T1:tä.
TUNNISTUS = {"T1": DEFAULT, "T2": replace(DEFAULT, min_range_rel=0.60)}


# ---------------------------------------------------------------------------
# Tausta (konteksti)
# ---------------------------------------------------------------------------
def build_context(prev: Sequence[Candle], p: Params = DEFAULT) -> Context | None:
    """Laskee taustan pelkästään edeltävistä suljetuista kynttilöistä."""
    closed = [c for c in prev if c.closed]
    if len(closed) < p.min_history:
        return None
    win = closed[-p.avg_window:]
    avg_range = sum(c.range for c in win) / len(win)
    avg_body = sum(c.body for c in win) / len(win)
    avg_volume = sum(c.volume for c in win) / len(win)

    tw = closed[-p.trend_window:]
    # Pienimmän neliösumman kulmakerroin päätöshinnoista -> liike koko ikkunalla
    n = len(tw)
    xs = range(n)
    mx = (n - 1) / 2
    my = sum(c.close for c in tw) / n
    num = sum((x - mx) * (c.close - my) for x, c in zip(xs, tw))
    den = sum((x - mx) ** 2 for x in xs) or 1.0
    move = num / den * (n - 1)
    move_atr = move / avg_range if avg_range > 0 else 0.0
    if move_atr >= p.trend_threshold_atr:
        trend = "nousu"
    elif move_atr <= -p.trend_threshold_atr:
        trend = "lasku"
    else:
        trend = "sivuttain"

    ew = closed[-p.extreme_window:]
    return Context(
        n_history=len(closed), avg_range=avg_range, avg_body=avg_body,
        avg_volume=avg_volume, trend=trend, trend_move_atr=move_atr,
        recent_low=min(c.low for c in ew), recent_high=max(c.high for c in ew),
    )


# ---------------------------------------------------------------------------
# Yhden kynttilän kuvaus
# ---------------------------------------------------------------------------
def size_label(rel: float) -> str:
    if rel < 0.5:
        return "pieni"
    if rel < 1.5:
        return "tavallinen"
    if rel < 2.5:
        return "suuri"
    return "poikkeuksellisen suuri"


def volume_ratio(cur: Candle, ctx: Context, elapsed_frac: float = 1.0) -> float:
    """Volyymi suhteessa keskiarvoon. Keskeneräiselle kynttilälle volyymi
    suhteutetaan kuluneeseen aikaan (arvio, ei lopullinen)."""
    if ctx.avg_volume <= 0:
        return 0.0
    frac = max(min(elapsed_frac, 1.0), 0.15)
    return (cur.volume / frac) / ctx.avg_volume


def describe_candle(cur: Candle, ctx: Context, elapsed_frac: float = 1.0) -> str:
    """Selkokielinen kuvaus kynttilän anatomiasta."""
    dir_txt = {1: "nouseva", -1: "laskeva", 0: "tasainen"}[cur.direction]
    rel = cur.range / ctx.avg_range if ctx.avg_range > 0 else 0.0
    vr = volume_ratio(cur, ctx, elapsed_frac)
    return (
        f"{dir_txt}, koko {size_label(rel)} ({rel:.1f}x keskim.), "
        f"runko {cur.ratio(cur.body):.0%}, yläsvarjo {cur.ratio(cur.upper_wick):.0%}, "
        f"alavarjo {cur.ratio(cur.lower_wick):.0%} vaihteluvälistä, "
        f"volyymi {vr:.1f}x keskim.{' (arvio)' if elapsed_frac < 1 else ''}, "
        f"edeltävä liike: {ctx.trend} ({ctx.trend_move_atr:+.1f})"
    )


# ---------------------------------------------------------------------------
# Kuvioiden tunnistus
# ---------------------------------------------------------------------------
def _cond(text: str, value, limit: str, ok: bool) -> dict:
    return {"ehto": text, "arvo": round(value, 4) if isinstance(value, float) else value,
            "raja": limit, "ok": ok}


def _strength(score: int) -> str:
    return "selvempi" if score >= 3 else "kohtalainen" if score == 2 else "heikko"


def _volume_notes(vr: float, p: Params, provisional: bool) -> tuple[int, str]:
    tag = " (arvio keskeneräisestä)" if provisional else ""
    if vr >= p.vol_high:
        return 1, f"volyymi {vr:.1f}x keskiarvo – selvästi tavallista suurempi, tukee havaintoa{tag}"
    if vr < p.vol_low:
        return -1, f"volyymi {vr:.1f}x keskiarvo – pieni, heikentää havaintoa{tag}"
    return 0, f"volyymi {vr:.1f}x keskiarvo – tavanomainen{tag}"


def detect(prev: Sequence[Candle], cur: Candle, p: Params = DEFAULT,
           elapsed_frac: float = 1.0) -> list[Observation]:
    """Tunnistaa kuviot kynttilästä `cur` käyttäen vain `prev`-historiaa.

    `prev` saa sisältää vain `cur`-kynttilää edeltäviä suljettuja kynttilöitä.
    """
    if prev and prev[-1].open_time >= cur.open_time:
        raise ValueError("prev sisältää kynttilän, joka ei ole cur-kynttilää aiempi")
    ctx = build_context(prev, p)
    if ctx is None or ctx.avg_range <= 0:
        return []
    status = "VAHVISTETTU" if cur.closed else "KESKENERÄINEN"
    provisional = not cur.closed
    R, B, U, L = cur.range, cur.body, cur.upper_wick, cur.lower_wick
    rel = R / ctx.avg_range
    if R <= 0 or rel < p.min_range_rel:
        return []

    vr = volume_ratio(cur, ctx, elapsed_frac)
    v_score, v_note = _volume_notes(vr, p, provisional)
    trend_note = f"edeltävä {p.trend_window} min liike: {ctx.trend} ({ctx.trend_move_atr:+.1f} keskim. vaihteluväliä)"
    out: list[Observation] = []
    closed_prev = [c for c in prev if c.closed]
    measures = {
        "R": R, "B": B, "U": U, "L": L,
        "B/R": cur.ratio(B), "U/R": cur.ratio(U), "L/R": cur.ratio(L),
        "R/keskim.R": rel, "keskim.R": ctx.avg_range, "keskim.B": ctx.avg_body,
        "volyymi/keskim.": vr, "trendi": ctx.trend, "liike_keskim.R": ctx.trend_move_atr,
        "ikkunan_alin": ctx.recent_low, "ikkunan_ylin": ctx.recent_high,
    }
    base_conds = [
        _cond(f"historiaa ≥ {p.min_history} suljettua kynttilää", len(closed_prev), f"≥ {p.min_history}", True),
        _cond("vaihteluväli / keskim. vaihteluväli", rel, f"≥ {p.min_range_rel}", True),
    ]
    used_base = {
        "kynttila": cur.open_time,
        "keskiarvot_alkaen": closed_prev[-p.avg_window:][0].open_time,
        "trendi_alkaen": closed_prev[-p.trend_window:][0].open_time,
        "ikkuna_loppuu": closed_prev[-1].open_time,
    }
    trend_cond = _cond(f"edeltävä {p.trend_window} min liike (keskim. vaihteluväleinä)", ctx.trend_move_atr,
                       f"lasku ≤ −{p.trend_threshold_atr}, nousu ≥ +{p.trend_threshold_atr}", True)

    def add(key, name, bias, score, reasons, context_ok, conds, extra_used=None):
        used = dict(used_base)
        if extra_used:
            used.update(extra_used)
        out.append(Observation(cur.symbol, cur.open_time, status, key, name, bias,
                               _strength(score), reasons, score=score, volume_ratio=vr,
                               context_ok=context_ok, conditions=base_conds + conds + [trend_cond],
                               measures=dict(measures), candles_used=used))

    # --- Doji ---------------------------------------------------------------
    is_doji = B <= p.doji_body * R
    if is_doji:
        reasons = [f"runko vain {cur.ratio(B):.0%} vaihteluvälistä (raja {p.doji_body:.0%})"]
        if U <= 0.10 * R and L >= p.long_shadow_min * R:
            key, name = "dragonfly_doji", "Sudenkorento-doji"
            reasons.append(f"pitkä alavarjo {cur.ratio(L):.0%}, lähes ei yläsvarjoa: myynti painoi hintaa alas, mutta se palautui")
            bias = "nousuun viittaava" if ctx.trend == "lasku" else "epäröinti"
        elif L <= 0.10 * R and U >= p.long_shadow_min * R:
            key, name = "gravestone_doji", "Hautakivi-doji"
            reasons.append(f"pitkä yläsvarjo {cur.ratio(U):.0%}, lähes ei alavarjoa: nousu torjuttiin")
            bias = "laskuun viittaava" if ctx.trend == "nousu" else "epäröinti"
        elif U >= 0.30 * R and L >= 0.30 * R and rel >= 1.0:
            key, name = "long_legged_doji", "Pitkäjalkainen doji"
            reasons.append("pitkät varjot molempiin suuntiin: voimakasta edestakaista liikettä ilman voittajaa")
            bias = "epäröinti"
        else:
            key, name, bias = "doji", "Doji", "epäröinti"
            reasons.append("avaus ja päätös lähes samat: ostajat ja myyjät tasapainossa")
        reasons.append(trend_note)
        score = 1
        if ctx.trend != "sivuttain":
            score += 1
            reasons.append(f"epäröinti {ctx.trend}liikkeen jälkeen voi kertoa liikkeen hiipumisesta")
        else:
            reasons.append("sivuttaisliikkeessä doji on tavallinen eikä kerro paljoa")
        score += v_score
        reasons.append(v_note)
        ctx_ok = ((key == "dragonfly_doji" and ctx.trend == "lasku")
                  or (key == "gravestone_doji" and ctx.trend == "nousu"))
        conds = [_cond("runko / vaihteluväli", cur.ratio(B), f"≤ {p.doji_body}", True)]
        if key == "dragonfly_doji":
            conds += [_cond("yläsvarjo / vaihteluväli", cur.ratio(U), "≤ 0.10", True),
                      _cond("alavarjo / vaihteluväli", cur.ratio(L), f"≥ {p.long_shadow_min}", True)]
        elif key == "gravestone_doji":
            conds += [_cond("alavarjo / vaihteluväli", cur.ratio(L), "≤ 0.10", True),
                      _cond("yläsvarjo / vaihteluväli", cur.ratio(U), f"≥ {p.long_shadow_min}", True)]
        elif key == "long_legged_doji":
            conds += [_cond("yläsvarjo / vaihteluväli", cur.ratio(U), "≥ 0.30", True),
                      _cond("alavarjo / vaihteluväli", cur.ratio(L), "≥ 0.30", True),
                      _cond("vaihteluväli / keskim.", rel, "≥ 1.0", True)]
        add(key, name, bias, score, reasons, ctx_ok, conds)

    # --- Vasara / hirttäytyjä ----------------------------------------------
    if (not is_doji and L >= p.shadow_to_body * B and L >= p.long_shadow_min * R
            and U <= p.short_shadow_max * R):
        reasons = [
            f"alavarjo {cur.ratio(L):.0%} vaihteluvälistä ja {L / B:.1f}x runko (raja 2x)",
            f"yläsvarjo vain {cur.ratio(U):.0%} (raja {p.short_shadow_max:.0%})",
            trend_note,
        ]
        score = 1
        if ctx.trend == "lasku":
            key, name, bias = "hammer", "Vasara", "nousuun viittaava"
            score += 1
            reasons.append("laskun jälkeen: myyjät painoivat hintaa, mutta ostajat nostivat sen takaisin")
            if cur.low <= ctx.recent_low:
                score += 1
                reasons.append(f"alavarjo kävi uudessa {p.extreme_window} min pohjassa ja hylättiin")
        elif ctx.trend == "nousu":
            key, name, bias = "hanging_man", "Hirttäytyjä", "laskuun viittaava"
            score += 1
            reasons.append("nousun jälkeen sama muoto kertoo, että myyntipainetta ilmeni kesken nousun")
        else:
            key, name, bias = "hammer_shape", "Vasaran muotoinen (ei trendiä)", "epäröinti"
            reasons.append("ei selvää edeltävää trendiä, joten muodolla on vähän merkitystä")
        score += v_score
        reasons.append(v_note)
        conds = [_cond("runko / vaihteluväli", cur.ratio(B), f"> {p.doji_body} (ei doji)", True),
                 _cond("alavarjo / runko", L / B, f"≥ {p.shadow_to_body}", True),
                 _cond("alavarjo / vaihteluväli", cur.ratio(L), f"≥ {p.long_shadow_min}", True),
                 _cond("yläsvarjo / vaihteluväli", cur.ratio(U), f"≤ {p.short_shadow_max}", True)]
        add(key, name, bias, score, reasons, ctx.trend != "sivuttain", conds)

    # --- Tähdenlento / käänteinen vasara ------------------------------------
    if (not is_doji and U >= p.shadow_to_body * B and U >= p.long_shadow_min * R
            and L <= p.short_shadow_max * R):
        reasons = [
            f"yläsvarjo {cur.ratio(U):.0%} vaihteluvälistä ja {U / B:.1f}x runko (raja 2x)",
            f"alavarjo vain {cur.ratio(L):.0%} (raja {p.short_shadow_max:.0%})",
            trend_note,
        ]
        score = 1
        if ctx.trend == "nousu":
            key, name, bias = "shooting_star", "Tähdenlento", "laskuun viittaava"
            score += 1
            reasons.append("nousun jälkeen: ostajat nostivat hintaa, mutta myyjät painoivat sen takaisin")
            if cur.high >= ctx.recent_high:
                score += 1
                reasons.append(f"yläsvarjo kävi uudessa {p.extreme_window} min huipussa ja hylättiin")
        elif ctx.trend == "lasku":
            key, name, bias = "inverted_hammer", "Käänteinen vasara", "nousuun viittaava"
            score += 1
            reasons.append("laskun jälkeen ostajat yrittivät nousua – ensimmäinen merkki ostohalukkuudesta")
        else:
            key, name, bias = "inverted_shape", "Käänteisen vasaran muotoinen (ei trendiä)", "epäröinti"
            reasons.append("ei selvää edeltävää trendiä, joten muodolla on vähän merkitystä")
        score += v_score
        reasons.append(v_note)
        conds = [_cond("runko / vaihteluväli", cur.ratio(B), f"> {p.doji_body} (ei doji)", True),
                 _cond("yläsvarjo / runko", U / B, f"≥ {p.shadow_to_body}", True),
                 _cond("yläsvarjo / vaihteluväli", cur.ratio(U), f"≥ {p.long_shadow_min}", True),
                 _cond("alavarjo / vaihteluväli", cur.ratio(L), f"≤ {p.short_shadow_max}", True)]
        add(key, name, bias, score, reasons, ctx.trend != "sivuttain", conds)

    # --- Peittävä kuvio (2 kynttilää) ---------------------------------------
    pc = prev[-1] if prev else None
    if (pc is not None and pc.closed and pc.range > 0 and pc.body > p.doji_body * pc.range
            and cur.direction != 0 and pc.direction == -cur.direction and B > pc.body):
        if cur.direction == 1 and cur.open <= pc.close and cur.close > pc.open:
            key, name, bias, want = "bullish_engulfing", "Nouseva peittävä kuvio", "nousuun viittaava", "lasku"
        elif cur.direction == -1 and cur.open >= pc.close and cur.close < pc.open:
            key, name, bias, want = "bearish_engulfing", "Laskeva peittävä kuvio", "laskuun viittaava", "nousu"
        else:
            key = None
        if key:
            reasons = [
                f"runko ({B / pc.body:.1f}x edellisen) peittää kokonaan edellisen vastakkaissuuntaisen rungon",
                trend_note,
            ]
            score = 1
            if ctx.trend == want:
                score += 1
                reasons.append(f"tulee {want}liikkeen jälkeen, jolloin se voi viitata suunnan kääntymiseen")
            else:
                reasons.append(f"ei edeltävää {want}liikettä, joten kääntymismerkitys on heikko")
            if B >= 1.5 * ctx.avg_body:
                score += 1
                reasons.append(f"runko {B / ctx.avg_body:.1f}x keskimääräinen runko")
            score += v_score
            reasons.append(v_note)
            up = cur.direction == 1
            conds = [_cond("edellisen runko / vaihteluväli", pc.body / pc.range, f"> {p.doji_body}", True),
                     _cond("suunnat vastakkaiset", 1.0, "edellinen " + ("laskeva" if up else "nouseva"), True),
                     _cond("avaus vs. edellinen päätös", cur.open - pc.close, "≤ 0" if up else "≥ 0", True),
                     _cond("päätös vs. edellinen avaus", cur.close - pc.open, "> 0" if up else "< 0", True),
                     _cond("runko / edellinen runko", B / pc.body, "> 1", True)]
            add(key, name, bias, score, reasons, ctx.trend == want, conds, {"edellinen": pc.open_time})

    # --- Marubozu ----------------------------------------------------------
    if B >= p.marubozu_body * R and rel >= p.marubozu_range_rel:
        up = cur.direction == 1
        reasons = [
            f"runko {cur.ratio(B):.0%} vaihteluvälistä – varjot lähes puuttuvat",
            f"koko {rel:.1f}x keskimääräinen",
            ("ostajat hallitsivat koko minuutin" if up else "myyjät hallitsivat koko minuutin"),
            trend_note,
        ]
        score = 1 + (1 if rel >= 2.0 else 0) + v_score
        reasons.append(v_note)
        add("bullish_marubozu" if up else "bearish_marubozu",
            "Nouseva marubozu" if up else "Laskeva marubozu",
            "jatkuvuus", score, reasons, False,
            [_cond("runko / vaihteluväli", cur.ratio(B), f"≥ {p.marubozu_body}", True),
             _cond("vaihteluväli / keskim.", rel, f"≥ {p.marubozu_range_rel}", True)])

    return out
