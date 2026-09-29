"""Luokitellut esimerkit kynttiläkuvioiden tunnistuksen tarkistamiseen.

TÄMÄ TIEDOSTO EI KÄYTÄ TUNNISTUSKOODIA. Oikeat vastaukset on kirjattu käsin:
  * `maaritelma` = mitä kirjallisten ehtojen (docs/KUVIOT.md) mukaan pitäisi tunnistaa.
    Kynttilät on rakennettu suoraan mittasuhteista (runko-, varjo- ja kokoosuudet), joten
    vastaus seuraa rakenteesta eikä koodin ajamisesta.
  * `kirjallisuus` = mitä kuviokirjallisuuden tavallinen lukija kutsuisi kuvioksi. Poikkeaa
    määritelmästä vain luokan G tapauksissa (tunnetut aukot: botti jättää huomaamatta).

Luokat:
  P = oikea kuvio, pitäisi hyväksyä
  N = samannäköinen tapaus, ei pitäisi hyväksyä
  B = rajatapaus (juuri rajan kummallakin puolella)
  G = tunnettu aukko: kuvio kirjallisuuden mukaan, mutta määritelmä / toteutus ei tunnista
  K = keskeneräinen kynttilä (tikki kerrallaan), tarkistetaan keskeneräinen vs. vahvistettu

Historia: 20 suljettua 1 min kynttilää, jokaisen vaihteluväli täsmälleen 1,0 (keskim. R = 1,0),
volyymi 100. Trendi: 'lasku' = päätös −0,5/kynttilä (liike −4,5 R 10 min aikana), 'nousu' =
+0,5/kynttilä, 'sivuttain' = vuorotellen ±0,25 (viimeinen nouseva), 'loiva_lasku' = −0,13/kynttilä
(liike ≈ −1,2 R, alle 1,5 R:n trendirajan).
"""
from __future__ import annotations

T0 = 1_767_225_600_000
M = 60_000

STEPS = {"lasku": -0.5, "nousu": 0.5, "loiva_lasku": -0.13}


def history(trend: str, n: int = 20, start: float = 100.0):
    """[(open, high, low, close, volume)] – vaihteluväli aina 1,0."""
    out, p = [], start
    for i in range(n):
        step = STEPS.get(trend, 0.25 if i % 2 else -0.25)
        o, c = p, p + step
        w = (1.0 - abs(step)) / 2
        out.append((o, max(o, c) + w, min(o, c) - w, c, 100.0))
        p = c
    return out


def shape(anchor: float, direction: int, R: float, body: float, upper: float, vol: float = 100.0):
    """Kynttilä mittasuhteista: R = vaihteluväli, body/upper = osuus R:stä, alavarjo = loput."""
    lower = 1.0 - body - upper
    low = anchor - lower * R - (body * R if direction < 0 else 0.0)
    if direction >= 0:
        o = low + lower * R
        c = o + body * R
    else:
        c = low + lower * R
        o = c + body * R
    return (o, low + R, low, c, vol)


def case(cid, luokka, kuvaus, hist, target, maaritelma, kirjallisuus=None, ticks=None, n_hist=20,
         prev_override=None, korjaus=""):
    return {"id": cid, "korjaus": korjaus, "luokka": luokka, "kuvaus": kuvaus, "historia": hist, "n_hist": n_hist,
            "prev_override": prev_override, "target": target, "ticks": ticks,
            "maaritelma": set(maaritelma),
            "kirjallisuus": set(kirjallisuus if kirjallisuus is not None else maaritelma)}


def build():
    C = []
    last = lambda h: history(h)[-1][3]          # historian viimeinen päätöshinta
    # ---------------- DOJI ----------------
    C.append(case("D1", "P", "Doji sivuttaisliikkeessä: runko 5 %, varjot 45/50 %, koko 0,8 × keskim.",
                  "sivuttain", shape(last("sivuttain"), 1, 0.8, 0.05, 0.45), {"doji"}))
    C.append(case("D2", "P", "Pitkäjalkainen doji: runko 4 %, varjot 48/48 %, koko 1,5 × keskim.",
                  "sivuttain", shape(last("sivuttain"), 1, 1.5, 0.04, 0.48), {"long_legged_doji"}))
    C.append(case("D3", "P", "Sudenkorento-doji laskun jälkeen: runko 5 %, yläsvarjo 2 %, alavarjo 93 %",
                  "lasku", shape(last("lasku"), 1, 1.0, 0.05, 0.02), {"dragonfly_doji"}))
    C.append(case("D4", "P", "Hautakivi-doji nousun jälkeen: runko 5 %, yläsvarjo 93 %, alavarjo 2 %",
                  "nousu", shape(last("nousu"), -1, 1.0, 0.05, 0.93), {"gravestone_doji"}))
    C.append(case("D5", "N", "Hyrrä (spinning top): runko 15 % – liian suuri dojiksi, varjot 40/45 %",
                  "sivuttain", shape(last("sivuttain"), 1, 1.0, 0.15, 0.40), set()))
    C.append(case("D6a", "B", "Runko 9,9 % (juuri doji-rajan alla), varjot 45/45,1 %, koko 0,8 ×",
                  "sivuttain", shape(last("sivuttain"), 1, 0.8, 0.099, 0.45), {"doji"}))
    C.append(case("D6b", "B", "Runko 10,1 % (juuri doji-rajan yli), varjot 45/44,9 %, koko 0,8 ×",
                  "sivuttain", shape(last("sivuttain"), 1, 0.8, 0.101, 0.45), set()))
    C.append(case("D7", "N", "Pikkuruinen kynttilä: koko 0,2 × keskim. (alle 0,3 × tulkintarajan), runko 2 %",
                  "sivuttain", shape(last("sivuttain"), 1, 0.2, 0.02, 0.49), set()))
    C.append(case("D8", "B", "Sudenkorennon näköinen, mutta yläsvarjo 12 % (> 10 %) -> tavallinen doji",
                  "lasku", shape(last("lasku"), 1, 1.0, 0.05, 0.12), {"doji"},
                  kirjallisuus={"dragonfly_doji"}))
    C.append(case("D9", "G", "Doji, mutta historiaa vain 15 kynttilää (lämmittely kesken)",
                  "sivuttain", shape(last("sivuttain"), 1, 0.8, 0.05, 0.45), set(),
                  kirjallisuus={"doji"}, n_hist=15))
    # ---------------- VASARA / HIRTTÄYTYJÄ ----------------
    C.append(case("H1", "P", "Vasara laskun jälkeen: nouseva, runko 20 %, yläsvarjo 5 %, alavarjo 75 %, koko 1,2 ×",
                  "lasku", shape(last("lasku"), 1, 1.2, 0.20, 0.05), {"hammer"}))
    C.append(case("H2", "P", "Vasara laskun jälkeen, laskeva runko: runko 20 %, yläsvarjo 5 %, alavarjo 75 %",
                  "lasku", shape(last("lasku"), -1, 1.2, 0.20, 0.05), {"hammer"}))
    C.append(case("H3", "P", "Hirttäytyjä nousun jälkeen: sama muoto kuin H1",
                  "nousu", shape(last("nousu"), 1, 1.2, 0.20, 0.05), {"hanging_man"}))
    C.append(case("H4", "P", "Vasaran muoto sivuttaisliikkeessä (ei trendiä)",
                  "sivuttain", shape(last("sivuttain"), 1, 1.2, 0.20, 0.05), {"hammer_shape"}))
    C.append(case("H5", "N", "Liian lyhyt alavarjo: runko 30 %, yläsvarjo 15 %, alavarjo 55 % (< 60 %)",
                  "lasku", shape(last("lasku"), 1, 1.2, 0.30, 0.15), set()))
    C.append(case("H6", "N", "Liian pitkä yläsvarjo: runko 15 %, yläsvarjo 25 % (> 15 %), alavarjo 60 %",
                  "lasku", shape(last("lasku"), 1, 1.2, 0.15, 0.25), set()))
    C.append(case("H7a", "B", "Yläsvarjo 14,9 % (juuri rajan alla), runko 20 %, alavarjo 65,1 %",
                  "lasku", shape(last("lasku"), 1, 1.2, 0.20, 0.149), {"hammer"}))
    C.append(case("H7b", "B", "Yläsvarjo 15,1 % (juuri rajan yli), runko 20 %, alavarjo 64,9 %",
                  "lasku", shape(last("lasku"), 1, 1.2, 0.20, 0.151), set()))
    C.append(case("H8a", "B", "Alavarjo 2,03 × runko (juuri rajan yli): runko 30 %, yläsvarjo 9 %, alavarjo 61 %",
                  "lasku", shape(last("lasku"), 1, 1.2, 0.30, 0.09), {"hammer"}))
    C.append(case("H8b", "B", "Alavarjo 1,94 × runko (juuri rajan alla): runko 31 %, yläsvarjo 9 %, alavarjo 60 %",
                  "lasku", shape(last("lasku"), 1, 1.2, 0.31, 0.09), set()))
    C.append(case("H9", "G", "Vasara loivan laskun jälkeen (liike ≈ −1,2 R < 1,5 R:n trendiraja)",
                  "loiva_lasku", shape(last("loiva_lasku"), 1, 1.2, 0.20, 0.05),
                  {"hammer_shape", "bullish_engulfing"}, kirjallisuus={"hammer", "bullish_engulfing"},
                  korjaus="Alkuperäinen käsin kirjattu vastaus oli {hammer_shape}. Ajon jälkeen botti tunnisti "
                          "myös nousevan peittävän. Tarkistettu määritelmää vasten: loivan laskun viimeisen "
                          "kynttilän runko on 0,13 (13 % vaihteluvälistä > 10 %), vasaran nouseva runko 0,24 > 0,13, "
                          "avaus = edellinen päätös ja päätös > edellinen avaus -> peittävä kuvio täyttyy. "
                          "Virhe oli luokittelijan, ei botin."))
    C.append(case("H10", "G", "Pieni vasara: täydellinen muoto, mutta koko 0,25 × keskim. (< 0,3 ×)",
                  "lasku", shape(last("lasku"), 1, 0.25, 0.20, 0.05), set(), kirjallisuus={"hammer"}))
    # ---------------- TÄHDENLENTO / KÄÄNTEINEN VASARA ----------------
    C.append(case("I1", "P", "Tähdenlento nousun jälkeen: laskeva, runko 20 %, yläsvarjo 75 %, alavarjo 5 %",
                  "nousu", shape(last("nousu"), -1, 1.2, 0.20, 0.75), {"shooting_star"}))
    C.append(case("I2", "P", "Käänteinen vasara laskun jälkeen: nouseva, runko 20 %, yläsvarjo 75 %, alavarjo 5 %",
                  "lasku", shape(last("lasku"), 1, 1.2, 0.20, 0.75), {"inverted_hammer"}))
    C.append(case("I3", "N", "Liian lyhyt yläsvarjo nousun jälkeen: runko 30 %, yläsvarjo 55 %, alavarjo 15 %",
                  "nousu", shape(last("nousu"), -1, 1.2, 0.30, 0.55), set()))
    C.append(case("I4a", "B", "Tähdenlento, alavarjo 14,9 % (juuri rajan alla)",
                  "nousu", shape(last("nousu"), -1, 1.2, 0.20, 0.651), {"shooting_star"}))
    C.append(case("I4b", "B", "Tähdenlennon näköinen, alavarjo 15,1 % (juuri rajan yli)",
                  "nousu", shape(last("nousu"), -1, 1.2, 0.20, 0.649), set()))
    C.append(case("I5", "P", "Käänteisen vasaran muoto sivuttaisliikkeessä",
                  "sivuttain", shape(last("sivuttain"), -1, 1.2, 0.20, 0.75), {"inverted_shape"}))
    # ---------------- PEITTÄVÄ KUVIO ----------------
    # Edellinen kynttilä korvataan: laskeva o=100,5 c=100,0 h=100,75 l=99,75 (runko 0,5, R 1,0)
    down_prev = (100.5, 100.75, 99.75, 100.0, 100.0)
    up_prev = (100.0, 100.75, 99.75, 100.5, 100.0)
    doji_prev = (100.05, 100.5, 99.5, 100.0, 100.0)
    C.append(case("E1", "P", "Nouseva peittävä laskun jälkeen: runko 0,7 peittää edellisen 0,5 rungon",
                  "lasku", (100.0, 100.8, 99.95, 100.7, 100.0), {"bullish_engulfing"}, prev_override=down_prev))
    C.append(case("E2", "P", "Laskeva peittävä nousun jälkeen: runko 0,7 peittää edellisen 0,5 rungon",
                  "nousu", (100.5, 100.55, 99.7, 99.8, 100.0), {"bearish_engulfing"}, prev_override=up_prev))
    C.append(case("E3", "N", "Runko ei yllä edellisen avaukseen (100,45 < 100,5)",
                  "lasku", (100.0, 100.5, 99.95, 100.45, 100.0), set(), prev_override=down_prev))
    C.append(case("E4", "N", "Edellinen kynttilä on doji (runko 5 %), ei peitettävää runkoa",
                  "lasku", (100.0, 100.75, 99.95, 100.7, 100.0), set(), prev_override=doji_prev))
    C.append(case("E5", "N", "Sama suunta kuin edellisellä (molemmat nousevia)",
                  "lasku", (100.5, 101.25, 100.45, 101.2, 100.0), set(), prev_override=up_prev))
    C.append(case("E6", "B", "Päätös täsmälleen edellisen avauksen tasolla (100,5 = 100,5)",
                  "lasku", (99.9, 100.55, 99.85, 100.5, 100.0), set(), prev_override=down_prev,
                  kirjallisuus={"bullish_engulfing"}))
    C.append(case("E7", "P", "Iso nouseva peittävä, joka on myös marubozu (runko 94 %, koko 1,38 ×)",
                  "lasku", (100.0, 101.35, 99.97, 101.3, 100.0), {"bullish_engulfing", "bullish_marubozu"},
                  prev_override=down_prev))
    C.append(case("E8", "P", "Nouseva peittävä ilman edeltävää laskua (tunnistetaan, konteksti heikko)",
                  "sivuttain", (100.0, 100.8, 99.95, 100.7, 100.0), {"bullish_engulfing"}, prev_override=down_prev))
    # ---------------- MARUBOZU ----------------
    C.append(case("M1", "P", "Nouseva marubozu: runko 95 %, koko 1,5 × (edellinen nouseva -> ei peittävää)",
                  "sivuttain", shape(last("sivuttain"), 1, 1.5, 0.95, 0.03), {"bullish_marubozu"}))
    C.append(case("M2", "P", "Laskeva marubozu, joka peittää edellisen nousevan rungon",
                  "sivuttain", shape(last("sivuttain"), -1, 1.5, 0.95, 0.02),
                  {"bearish_marubozu", "bearish_engulfing"}))
    C.append(case("M3", "N", "Runko 85 % (< 90 %) – vahva kynttilä muttei marubozu",
                  "sivuttain", shape(last("sivuttain"), 1, 1.5, 0.85, 0.08), set()))
    C.append(case("M4a", "B", "Runko 95 %, koko 1,19 × (juuri alle 1,2 ×)",
                  "sivuttain", shape(last("sivuttain"), 1, 1.19, 0.95, 0.03), set()))
    C.append(case("M4b", "B", "Runko 95 %, koko 1,21 × (juuri yli 1,2 ×)",
                  "sivuttain", shape(last("sivuttain"), 1, 1.21, 0.95, 0.03), {"bullish_marubozu"}))
    # ---------------- EI TOTEUTETTUJA KUVIOITA (G) ----------------
    C.append(case("G1", "G", "Nouseva harami laskun jälkeen: pieni nouseva runko edellisen laskevan rungon sisällä",
                  "lasku", (100.1, 100.35, 100.05, 100.3, 100.0), set(), kirjallisuus={"bullish_harami"},
                  prev_override=(100.6, 100.75, 99.85, 99.9, 100.0)))
    # ---------------- KESKENERÄINEN (K) ----------------
    # tikit: (sekuntia kynttilän alusta, kynttilä siihen asti) – viimeinen = suljettu
    a = last("lasku")
    C.append(case("K1", "K", "Vasaraksi muodostuva kynttilä, joka 30 s kohdalla on vasara mutta sulkeutuu marubozuna",
                  "lasku", None, set(), ticks=[
                      (10, (a, a + 0.05, a - 0.20, a + 0.02), {"~alle 25 %": set()}),
                      (30, (a, a + 0.26, a - 0.90, a + 0.24), {"hammer"}),
                      # sulkeutuu: runko 1,6 / R 1,68 = 95 %, koko 1,68 × -> marubozu; nouseva runko 1,6
                      # peittää edellisen laskevan 0,5 rungon (avaus = ed. päätös, päätös > ed. avaus)
                      (60, (a, a + 1.62, a - 0.06, a + 1.60), {"bullish_marubozu", "bullish_engulfing"}),
                  ]))
    C.append(case("K2", "K", "Tähdenlento, joka näkyy keskeneräisenä ja vahvistuu sellaisenaan",
                  "nousu", None, set(), ticks=[
                      # 40 s: R 1,15, runko 0,2 (17 %), yläsvarjo 0,9 (78 %), alavarjo 0,05 (4 %)
                      (40, (last("nousu"), last("nousu") + 0.9, last("nousu") - 0.25, last("nousu") - 0.2),
                       {"shooting_star"}),
                      # suljettu: R 1,24, runko 0,24 (19 %), yläsvarjo 0,95 (77 %), alavarjo 0,05 (4 %)
                      (60, (last("nousu"), last("nousu") + 0.95, last("nousu") - 0.29, last("nousu") - 0.24),
                       {"shooting_star"}),
                  ]))
    return C
