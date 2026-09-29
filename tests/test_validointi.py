"""Luokitellut esimerkit (validointi/tapaukset.py): tunnistuksen on vastattava käsin
kirjattua määritelmän mukaista vastausta jokaisessa tapauksessa ja vaiheessa."""
import unittest

from validointi.aja import run_case
from validointi.tapaukset import build


class TestLuokitellutEsimerkit(unittest.TestCase):
    def test_maaritelman_mukaan(self):
        for cs in build():
            r = run_case(cs)
            with self.subTest(tapaus=cs["id"]):
                if r["vaiheet"]:
                    for s in r["vaiheet"]:
                        self.assertEqual(set(s["odotettu"]), set(s["tunnistettu"]), f"{cs['id']} {s['sekunti']} s")
                else:
                    self.assertEqual(set(r["maaritelma"]), set(r["tunnistettu"]))

    def test_keskenerainen_ennen_25_prosenttia_ei_tulkita(self):
        k1 = next(c for c in build() if c["id"] == "K1")
        r = run_case(k1)
        self.assertEqual(r["vaiheet"][0]["tunnistettu"], [])
        self.assertIn("hammer", r["vaiheet"][2]["ei_vahvistunut"][0])
