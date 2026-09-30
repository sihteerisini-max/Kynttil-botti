# Testijaksot

Jaksoa, jota on käytetty sääntöjen arviointiin tai muutosten suunnitteluun, ei
käytetä myöhempien versioiden hyvyyden todisteena.

| Jakso | Aika (UTC) | Markkinat | Käyttö |
|---|---|---|---|
| **A** | 2026-09-22 18:43 – 2026-09-29 18:43 | PF_XBTUSD, PF_ETHUSD, PF_SOLUSD, PF_ZECUSD, PF_XRPUSD | v1:n ensimmäinen historiatesti. **Katsottu** – ei enää puolueeton millekään versiolle. |
| **B** | ei käynnistetty (Jessen päätös 30.9.2026) | – | Suunniteltu v1.1 vs v2 live-paperivertailu. Versiot pysyvät lukittuina. |
| arviointidata | 2026-09-29 18:43 – 2026-09-30 14:23 | samat 5 | Tunnistuksen sokkoarvioinnit, sarjat B ja C. **Katsottu** – ei kannattavuustestiin. |
| **T2-testi** | **2026-09-30 15:21 UTC – 2026-10-28 15:21 UTC** (kiinteä 28 vrk; molemmat tilit samasta hetkestä, Railway-loki `TESTIJAKSO [...]`, commit 768194a) | PF_XBTUSD, PF_ETHUSD, PF_SOLUSD, PF_ZECUSD, PF_XRPUSD | Eteenpäin kerättävä paperitesti, lukittu 30.9.2026 (`docs/TESTI_T2.md`). Käynnistetty 30.9.2026 puhtaalta tilalta (Volume `/data`). Katkokset: 30.9. 15:26:57–15:27:00 UTC uudelleenkäynnistys, jonka aiheutti dokumenttimuutoksen push (commit de7cfdf, kaupankäyntikoodi identtinen); tila jatkui tallennuksesta. **Markkinavaihto 30.9. 17:10 UTC** (Jessen pyyntö): XBT, ETH, SOL, ZEC, XRP → SUI, ZEC, XRP, DOGE, SOL (`results/MARKKINAVAIHTO_2026-09-30.md`). Ennen vaihtoa 0 kauppaa. Tulokset raportoidaan erikseen ennen vaihtoa ja sen jälkeen, eikä niitä yhdistetä. Tämän jälkeen botti deployataan vain `kynttilatulkki/**`-, `railway.json`- tai `requirements.txt`-muutoksista (Railway watch paths). |

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
