"""Rakentaa näkymän validointi/nakyma.html tiedostosta validointi/tulokset.json."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "tulokset.json"), encoding="utf-8") as f:
    data = json.load(f)
tpl = open(os.path.join(HERE, "nakyma_pohja.html"), encoding="utf-8").read()
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
with open(os.path.join(HERE, "nakyma.html"), "w", encoding="utf-8") as f:
    f.write(tpl.replace("__DATA__", blob))
print("validointi/nakyma.html", os.path.getsize(os.path.join(HERE, "nakyma.html")), "tavua")
