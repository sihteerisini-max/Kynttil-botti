"""Kopioi botin tunnistus- ja signaalikoodin seurannan käyttöön (seuranta/kynttilatulkki/).
Seuranta on oma Railway-palvelunsa, jonka juurihakemisto on seuranta/, joten koodi kopioidaan."""
import os
import shutil

MODULES = ["models", "patterns", "komponentit", "strategy", "jatkuminen"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    for m in MODULES:
        shutil.copy(os.path.join(ROOT, "kynttilatulkki", m + ".py"), os.path.join(ROOT, "seuranta", "kynttilatulkki", m + ".py"))
    print("kopioitu:", ", ".join(MODULES))
