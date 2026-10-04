"""Kopioi botin tunnistus- ja signaalikoodin tutkimuksen käyttöön (tutkimus15/kt/).
Tutkimus 15M on oma Railway-palvelunsa (juurihakemisto tutkimus15/), joten koodi kopioidaan.
Samuus tarkistetaan testillä tests/test_tutkimus15.py."""
import os
import shutil

MODULES = ["models", "patterns", "komponentit", "strategy", "jatkuminen", "analyzer", "paper"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    for m in MODULES:
        shutil.copy(os.path.join(ROOT, "kynttilatulkki", m + ".py"), os.path.join(ROOT, "tutkimus15", "kt", m + ".py"))
    print("kopioitu:", ", ".join(MODULES))
