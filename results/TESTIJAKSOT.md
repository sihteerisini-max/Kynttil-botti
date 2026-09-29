# Testijaksot

Jaksoa, jota on käytetty sääntöjen arviointiin tai muutosten suunnitteluun, ei
käytetä myöhempien versioiden hyvyyden todisteena.

| Jakso | Aika (UTC) | Markkinat | Käyttö |
|---|---|---|---|
| **A** | 2026-09-22 18:43 – 2026-09-29 18:43 | PF_XBTUSD, PF_ETHUSD, PF_SOLUSD, PF_ZECUSD, PF_XRPUSD | v1:n ensimmäinen historiatesti. **Katsottu** – ei enää puolueeton millekään versiolle. |
| **B** | alkaa v1.1- ja v2-tilien todellisesta käynnistyshetkestä (loki: `JAKSO B – tilien todellinen aloitushetki`) → 4 viikkoa | 5 vaihdetuinta PF-perpetualia käynnistyshetkellä | v1.1 vs v2 live-paperivertailu. Säännöt lukittu 29.9.2026 (`docs/SAANNOT_v2.md`). **Kirjaa alkuhetki tähän käynnistyksen jälkeen.** |

## Jakso A – v1 (ajettu 29.9.2026, Jessen koneella)

* 42 kauppaa, voittoja 7 (17 %), nettotulos −1 034 USD (−10,3 %), keskim. −0,72 R/kauppa,
  profit factor 0,13. Maksimipudotusraja laukesi 28.9. → kaupankäynti pysähtyi.
* Tulos ennen kaikkia kuluja ≈ −442 USD → **signaaleilla ei ollut tällä jaksolla etua
  edes ilman kuluja**. Kulut (palkkiot 313 + spread/liukuma ≈ 280) ≈ 592 USD lisäksi.
* Stopit 22 kpl, keskim. −1,38 R (kulut ja stop-liukuma tekevät tappiosta yli 1 R).
  Voittotavoite (1,5 R) saavutettiin vain 1 kerran. Aikarajalla suljetut 19 kpl olivat
  ennen kuluja +196 USD mutta kulujen jälkeen −42 USD.
* Kulusuodatin hylkäsi 932 signaalia: 1 min kynttilöiden liikkeet ovat useimmiten liian
  pieniä suhteessa taker-kuluihin.
* Havainto datasta: Krakenin 1 min volyymi on hyvin epätasainen (volyymisuhteita jopa
  600×), joten volyymiehto erottelee heikosti. Kauppattomia (täytettyjä) minuutteja
  0,6–3 % markkinasta riippuen.

Tiedostot: `v1_2026-09-22T1843_2026-09-29T1843/`
