# Kynttiläbotti – vaihe 1: kynttilöiden tulkinta

Havainnoi kryptovaluuttojen 1 minuutin kynttilöitä reaaliajassa useammalta
kolikolta, tunnistaa kynttiläkuvioita ja selittää selkokielellä, mitä
tunnistettiin ja miksi. **Ei käy kauppaa eikä ennusta** – kaupankäyntisäännöt
tulevat myöhemmässä vaiheessa.

Vaatii vain Python 3.10+ (ei ulkoisia kirjastoja). Data: Binancen julkinen
markkinadata (`data-api.binance.vision`), ei API-avainta.

## Käyttö

```bash
# reaaliaikainen seuranta
python -m kynttilatulkki.live --symbols BTCUSDT,ETHUSDT,SOLUSDT
python -m kynttilatulkki.live --top 8 --quiet      # 8 vaihdetuinta, vain kuviot

# historian läpikäynti ilman tulevaisuustietoa
python -m kynttilatulkki.replay --binance BTCUSDT --minutes 600 --quiet
python -m kynttilatulkki.replay --csv data.csv --symbol ETHUSDT
python -m kynttilatulkki.replay --demo              # synteettinen, ei verkkoa

# testit
python -m unittest discover -s tests -v
```

Havainnot tallentuvat myös tiedostoon `logs/havainnot.jsonl` (live-tila).

## Rakenne

| Tiedosto | Tehtävä |
|---|---|
| `kynttilatulkki/models.py` | Kynttilä (runko, varjot, suunta), konteksti, havainto |
| `kynttilatulkki/patterns.py` | Tunnistusehdot, trendi- ja volyymikonteksti – kaikki raja-arvot `Params`-luokassa |
| `kynttilatulkki/analyzer.py` | Symbolikohtainen tila, keskeneräinen vs. vahvistettu, selkokielinen tulostus |
| `kynttilatulkki/feed.py` | Binancen julkinen REST-data |
| `kynttilatulkki/live.py` | Reaaliaikainen ajo |
| `kynttilatulkki/replay.py` | Historia-/demoajo kynttilä kerrallaan |
| `docs/KUVIOT.md` | Tunnistusehdot ja vaiheen 2 kuviotausta |

## Keskeneräinen vs. vahvistettu

* **KESKENERÄINEN** – kynttilä on vielä auki. Muoto voi muuttua täysin ennen
  minuutin loppua. Tulkitaan vasta kun ≥ 25 % minuutista on kulunut; volyymi
  suhteutetaan kuluneeseen aikaan (arvio). Tulostetaan vain kun havaittu
  kuviojoukko muuttuu.
* **VAHVISTETTU** – kynttilä on sulkeutunut, arvot ovat lopulliset.
* **✗ ei vahvistunut** – keskeneräisenä nähty kuvio katosi sulkeutuessa.

## Tulevaisuustiedon estäminen

`detect(prev, cur)` saa vain `cur`-kynttilää edeltävät suljetut kynttilät ja
hylkää (ValueError) historian, jossa on myöhempiä kynttilöitä. Testit
varmistavat lisäksi, että (1) katkaistu data antaa täsmälleen samat havainnot
kuin koko data ja (2) tulevien kynttilöiden muuttaminen ei muuta aiempia
havaintoja.

## Ajo Railwayssä (GitHubin kautta)

1. Pushaa repo GitHubiin ja luo Railwayssä *New Project → Deploy from GitHub repo*.
2. **Settings → Region: EU West (Amsterdam).** Binance estää Yhdysvalloista
   tulevat yhteydet, ja Railwayn oletusalue voi olla USA:ssa.
3. **Variables** (kaikki valinnaisia):

| Muuttuja | Esimerkki | Merkitys |
|---|---|---|
| `SYMBOLS` | `BTCUSDT,ETHUSDT,SOLUSDT` | seurattavat parit (ohittaa TOP:n) |
| `TOP` | `8` | N vaihdetuinta USDT-paria (oletus 5) |
| `INTERVAL` | `3` | kyselyväli sekunteina |
| `QUIET` | `1` | vain kuviot, ei jokaista kynttilää |
| `BRIEF` | `1` | ei perusteluja |
| `LOG_PATH` | `/data/havainnot.jsonl` | JSONL-loki; pysyvä vain jos `/data` on Railway Volume |

Havainnot näkyvät Railwayn *Deploy Logs* -näkymässä. Palvelu ei tarvitse
porttia eikä julkista osoitetta (worker). `railway.json` määrittää
käynnistyskomennon ja uudelleenkäynnistyksen kaatumisen jälkeen.

---

# Vaihe 2: paperikauppa (Kraken Derivatives -perpetualit)

**Vain paperikauppaa – koodi ei lähetä toimeksiantoja eikä käytä API-avaimia.**
Säännöt: [`docs/SAANNOT_v1.md`](docs/SAANNOT_v1.md), [`docs/SAANNOT_v2.md`](docs/SAANNOT_v2.md) (v1.1 ja v2, korjattu kulumalli).
Arviointi: `python -m kynttilatulkki.evaluate` (ks. SAANNOT_v2.md kohta 6).

```bash
# historiatesti oikealla Kraken-datalla (viimeiset 7 päivää, 5 vaihdetuinta perpetualia)
python -m kynttilatulkki.backtest --rules v1 --top 5 --days 7 --quiet
# tietty jakso ja markkinat
python -m kynttilatulkki.backtest --rules v1 --symbols PF_XBTUSD,PF_ETHUSD --start 2026-09-20 --end 2026-09-27
# live-paperikauppa
python -m kynttilatulkki.paper_live --rules v1.1,v2 --top 5   # kaksi rinnakkaista paperitiliä
```

Historiatesti tallentaa datan kansioon `data/` ja tulokset kansioon
`results/<versio>_<alku>_<loppu>/` (`yhteenveto.md`, `kaupat.jsonl`, `loki.txt`, `meta.json`).

| Tiedosto | Tehtävä |
|---|---|
| `kynttilatulkki/strategy.py` | Versioidut säännöt (`RULESETS`), signaaliehdot |
| `kynttilatulkki/paper.py` | Yhteinen paperikauppamoottori: avaus, stop/tavoite/aikaraja, kulut, tappiorajat |
| `kynttilatulkki/backtest.py` | Historiatesti |
| `kynttilatulkki/paper_live.py` | Live-paperikauppa, tila säilyy uudelleenkäynnistysten yli |
| `kynttilatulkki/kraken.py` | Krakenin julkinen data (kynttilät, bid/ask, funding) |
| `kynttilatulkki/start.py` | Railwayn käynnistys (MODE / BACKTEST_DAYS) |

### Railway

| Muuttuja | Arvo | Merkitys |
|---|---|---|
| `MODE` | `observe` (oletus) / `paper` | havainnointi (Binance) tai paperikauppa (Kraken) |
| `BACKTEST_DAYS` | esim. `7` | aja ensin historiatesti, tulos Deploy Logsiin |
| `RULES` | `v1.1,v2` | sääntöversiot – useampi = rinnakkaiset paperitilit |
| `SYMBOLS` | esim. `PF_XBTUSD,PF_ETHUSD` | paperikaupan markkinat (muuten `TOP`) |
| `STATE_DIR` | `/data/state` | paperitilien tila (`paper_<versio>.pkl`) – pysyvä vain Railway Volumella |
| `LOG_DIR` | `/data/logs` | kauppa- ja tapahtumaloki |
| `RESET_STATE` | `1` | aloita alusta (esim. maksimipudotuksen pysäytyksen jälkeen), poista sitten |

Paperikaupassa kannattaa liittää palveluun Railway Volume polkuun `/data`, jotta
pääoma, avoimet positiot ja tappiorajat eivät nollaudu uuden julkaisun yhteydessä.

### Uusi sääntöversio

1. Lisää `RULESETS["v2"]` tiedostoon `strategy.py` (v1:tä ei muokata).
2. Kirjoita `docs/SAANNOT_v2.md`: mitä muutettiin ja miksi – ennen testiä.
3. Arvioi v2 ja v1 rinnakkain jaksolla, joka alkaa v1-testijakson jälkeen.
