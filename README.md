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
