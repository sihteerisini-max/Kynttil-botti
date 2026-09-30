"""Vie arviointisarjan tekstimuotoon ChatGPT:lle (tai muulle arvioijalle) ja lukee vastaukset.

    python -m validointi.chatgpt_vienti vie B [--osia 6]
    python -m validointi.chatgpt_vienti tuo B vastaukset.txt      # -> validointi/arviot_B_chatgpt.json

Vientitiedostoissa on vain kirjallisuuden määritelmät, vertailujaksot ja hinnat arviointihetkeen asti.
Botin vastauksia, numeerisia raja-arvoja tai otosryhmää ei ole mukana.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

OHJE = """Olet kynttiläkuvioiden arvioija. Arvioi jokainen alla oleva tapaus kirjallisten määritelmien
perusteella. Älä arvaa tulevaa hintakehitystä: saat vain arvioitavan kynttilän ja sitä edeltävät kynttilät.

Jokaisesta tapauksesta vastataan erikseen kolmeen kysymykseen:
  MUOTO  = Täyttääkö arvioitava kynttilä (2 kynttilän kuviossa: arvioitava + edellinen) kuvion muotoehdot?
  LIIKE  = Onko edeltävä hintaliike vaaditun suuntainen? Vain kun määritelmä vaatii edeltävän liikkeen,
           muuten vastaa "-". Liikejakso = rivit, joiden jakso-sarakkeessa on L (10 edeltävää kynttilää).
  KOKO   = Täyttyykö suhteellisen koon ehto? Vaihteluväli = ylin − alin. Vertailujakso = rivit, joiden
           jakso-sarakkeessa on V (20 edeltävää kynttilää).
Vastausvaihtoehdot: on / ei / epaselva   (LIIKE lisäksi "-", kun ei vaatimusta)

Käytä omaa harkintaasi sanallisten määritelmien tulkinnassa ("pieni", "pitkä", "selvästi"). Arvioi jokainen
tapaus itsenäisesti, äläkä muuta aiempia vastauksia myöhempien perusteella.

VASTAUSMUOTO: palauta VAIN koodilohko, jossa yksi rivi per tapaus, samassa järjestyksessä:
  id;muoto;liike;koko;perustelu
esim.
  B001;on;-;ei;runko hyvin ohut, mutta vaihteluväli pieni vertailujaksoon nähden
Perustelu enintään 15 sanaa. Älä jätä yhtään tapausta pois.
"""


def fmt_time(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def vie(tag, osia):
    d = json.load(open(os.path.join(HERE, f"arviointi_{tag}.json"), encoding="utf-8"))
    defs, V, L = d["maaritelmat"], d["vertailu"]["koko"], d["vertailu"]["liike"]
    items = d["tapaukset"]
    out_dir = os.path.join(HERE, f"chatgpt_{tag}")
    os.makedirs(out_dir, exist_ok=True)
    per = -(-len(items) // osia)
    files = []
    for k in range(osia):
        part = items[k * per:(k + 1) * per]
        if not part:
            continue
        lines = [f"KYNTTILÄARVIOINTI, osa {k + 1}/{osia} (tapaukset {part[0]['id']}–{part[-1]['id']})", "", OHJE,
                 "Lähteet: [SC] StockCharts ChartSchool, Candlestick Pattern Dictionary; "
                 "[TB] Thomas N. Bulkowski, ThePatternSite.com.", "", "=" * 70]
        for it in part:
            df = dict(defs[it["kuvio"]])
            for key in ("liike", "koko"):
                if df[key]:
                    df[key] = (df[key].replace("(tummempi alue)", "(L-rivit)")
                             .replace("vertailujakson (20 edeltävää kynttilää, vaalea alue)", "vertailujakson (V-rivit)"))
            hist = it["historia"]
            n = len(hist)
            lines += ["", f"### {it['id']} – {it['symboli']} – arvioitava kynttilä {fmt_time(it['aika'])} UTC",
                      f"Kuvio: {df['nimi']} ({df['kynttiloita']} kynttilä{'ä' if df['kynttiloita'] > 1 else ''})",
                      f"Muoto: {df['muoto']}",
                      f"Edeltävä liike: {df['liike'] or 'Ei vaatimusta (vastaa LIIKE = -).'}",
                      f"Suhteellinen koko: {df['koko']}",
                      f"Lähde: {df['lahde']}",
                      "", "aika (UTC) | avaus | ylin | alin | päätös | jakso"]
            for i, c in enumerate(hist):
                tags = []
                if i >= n - V:
                    tags.append("V")
                if i >= n - L:
                    tags.append("L")
                if df["kynttiloita"] == 2 and i == n - 1:
                    tags.append("EDELLINEN")
                lines.append(f"{fmt_time(c['t'])[11:]} | {c['o']:g} | {c['h']:g} | {c['l']:g} | {c['c']:g} | {','.join(tags)}")
            c = it["kohde"]
            lines.append(f"{fmt_time(c['t'])[11:]} | {c['o']:g} | {c['h']:g} | {c['l']:g} | {c['c']:g} | ARVIOITAVA")
        lines += ["", "=" * 70, "Palauta nyt vastaukset ohjeen mukaisena koodilohkona "
                  f"({len(part)} riviä: {part[0]['id']}–{part[-1]['id']})."]
        path = os.path.join(out_dir, f"sarja_{tag}_osa{k + 1}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        files.append(path)
        print(path, len(part), "tapausta")
    return files


def tuo(tag, path):
    d = json.load(open(os.path.join(HERE, f"arviointi_{tag}.json"), encoding="utf-8"))
    need = {it["id"]: it for it in d["tapaukset"]}
    defs = d["maaritelmat"]
    got, errors = {}, []
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\s*(?i:(" + re.escape(tag) + r"\d{3}))\s*;\s*([^;]*)\s*;\s*([^;]*)\s*;\s*([^;]*)\s*;?(.*)$", line.strip())
        if not m:
            continue
        iid = m.group(1).upper()
        mu, li, ko = [x.strip().lower() for x in m.groups()[1:4]]
        norm = lambda v: {"on": "on", "ei": "ei", "epaselva": "epaselva", "epäselvä": "epaselva", "-": None, "": None}.get(v, "?")
        r = {"muoto": norm(mu), "liike": norm(li), "koko": norm(ko), "perustelu": m.group(5).strip()}
        if iid not in need:
            errors.append(f"{iid}: tuntematon id")
            continue
        needs_liike = bool(defs[need[iid]["kuvio"]]["liike"])
        for k in ("muoto", "koko") + (("liike",) if needs_liike else ()):
            if r[k] in (None, "?"):
                errors.append(f"{iid}: puuttuva tai tuntematon {k} ({m.group(2 if k == 'muoto' else 3 if k == 'liike' else 4)})")
        if not needs_liike:
            r["liike"] = None
        got[iid] = r
    missing = [i for i in need if i not in got]
    out = os.path.join(HERE, f"arviot_{tag}_chatgpt.json")
    json.dump({"_tapa": "tekoäly (ChatGPT), numeerinen tekstimuotoinen data", **got}, open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"Luettu {len(got)}/{len(need)} tapausta -> {out}")
    if missing:
        print("PUUTTUU:", ", ".join(missing))
    for e in errors:
        print("VIRHE:", e)
    return got, missing, errors


if __name__ == "__main__":
    cmd, tag = sys.argv[1], sys.argv[2]
    if cmd == "vie":
        osia = int(sys.argv[sys.argv.index("--osia") + 1]) if "--osia" in sys.argv else 6
        vie(tag, osia)
    else:
        tuo(tag, sys.argv[3])
