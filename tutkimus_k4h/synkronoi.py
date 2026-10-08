"""Kopioi botin tunnistus- ja signaalikoodin tutkimuksen käyttöön (tutkimus_k4h/kt/).
Tutkimus K4H on oma Railway-palvelunsa (juurihakemisto tutkimus_k4h/), joten koodi kopioidaan.
Samuus tarkistetaan testillä tests/test_tutkimus_k4h.py."""
import os
import shutil

MODULES = ["models", "patterns", "komponentit", "strategy", "jatkuminen", "analyzer", "paper"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    for m in MODULES:
        shutil.copy(os.path.join(ROOT, "kynttilatulkki", m + ".py"), os.path.join(ROOT, "tutkimus_k4h", "kt", m + ".py"))
    print("kopioitu:", ", ".join(MODULES))
