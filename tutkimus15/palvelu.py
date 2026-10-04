"""Tutkimus 15M – Railway-palvelu (vain tutkimus ja paperilaskenta, ei toimeksiantoja).

Vaiheet käynnistetään erikseen, jotta jokaisen vaiheen tulos voidaan kirjata repoon ennen seuraavaa:
  /aja?vaihe=valinta     markkinavalinta (vain valintajakson data)
  /aja?vaihe=lataus      testijakson data + eheystarkistus + spreadit + funding (vaatii valinnan)
  /aja?vaihe=analyysi    vaihe 1, kulusuhde ja ehdollinen vaihe 2 (vaatii latauksen)
Muut: /tila, /lista, /tiedosto/<polku>. Kaikki paitsi /health vaativat ?token=<LOG_TOKEN>.
"""
from __future__ import annotations

import hmac
import json
import os
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

OUT = os.environ.get("OUT_DIR", "/data/t15")
TOKEN = os.environ.get("LOG_TOKEN", "")
STATE = {"vaihe": None, "kaynnissa": False, "aloitettu": None, "valmis": {}, "virhe": None, "loki": []}
LOCK = threading.Lock()


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} {msg}"
    print(line, flush=True)
    STATE["loki"] = (STATE["loki"] + [line])[-200:]
    try:
        with open(os.path.join(OUT, "loki.txt"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _done(name: str) -> bool:
    return os.path.exists(os.path.join(OUT, {"valinta": "valinta.json", "lataus": "eheys.json", "analyysi": "raportti.md"}[name]))


def run_stage(name: str) -> None:
    try:
        if name == "valinta":
            import valinta
            valinta.aja(OUT, log=log)
        elif name == "lataus":
            import eheys
            with open(os.path.join(OUT, "valinta.json"), encoding="utf-8") as f:
                v = json.load(f)
            if v["perustelu"] != "ok":
                raise RuntimeError(f"valinta ei kelpaa: {v['perustelu']}")
            eheys.aja(OUT, v["valitut"], log=log)
        elif name == "analyysi":
            import analyysi
            analyysi.aja(OUT, log=log)
        STATE["valmis"][name] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        log(f"vaihe {name} valmis")
    except Exception as e:
        STATE["virhe"] = f"{name}: {e!r}"
        log(f"VIRHE vaiheessa {name}: {e!r}\n{traceback.format_exc()}")
    finally:
        STATE["kaynnissa"] = False


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/health":
            return self._send(200, "ok")
        q = parse_qs(u.query)
        if not TOKEN or not hmac.compare_digest(q.get("token", [""])[0], TOKEN):
            return self._send(403, "Pääsy estetty")
        if u.path == "/tila":
            st = dict(STATE)
            st["tiedostot_valmiina"] = {k: _done(k) for k in ("valinta", "lataus", "analyysi")}
            return self._send(200, json.dumps(st, ensure_ascii=False), "application/json; charset=utf-8")
        if u.path == "/aja":
            name = q.get("vaihe", [""])[0]
            if name not in ("valinta", "lataus", "analyysi"):
                return self._send(400, "tuntematon vaihe")
            need = {"valinta": None, "lataus": "valinta", "analyysi": "lataus"}[name]
            if need and not _done(need):
                return self._send(409, f"vaihe {need} puuttuu")
            if _done(name) and q.get("uudelleen", ["0"])[0] != "1":
                return self._send(409, f"vaihe {name} on jo ajettu (tulokset säilytetään; uudelleenajo vain uudelleen=1)")
            with LOCK:
                if STATE["kaynnissa"]:
                    return self._send(409, f"vaihe {STATE['vaihe']} on käynnissä")
                STATE.update(vaihe=name, kaynnissa=True, aloitettu=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), virhe=None)
            threading.Thread(target=run_stage, args=(name,), daemon=True).start()
            return self._send(202, f"vaihe {name} käynnistetty")
        if u.path == "/lista":
            lines = []
            for dp, _dn, fn in os.walk(OUT):
                for x in sorted(fn):
                    p = os.path.join(dp, x)
                    lines.append(f"{os.path.relpath(p, OUT)}\t{os.path.getsize(p)}")
            return self._send(200, "\n".join(sorted(lines)))
        if u.path.startswith("/tiedosto/"):
            root = os.path.realpath(OUT)
            p = os.path.realpath(os.path.join(root, u.path[len("/tiedosto/"):]))
            if not p.startswith(root) or not os.path.isfile(p):
                return self._send(404, "ei löydy")
            with open(p, "rb") as f:
                return self._send(200, f.read())
        return self._send(404, "ei löydy")

    def log_message(self, *a):
        pass


def main():
    os.makedirs(OUT, exist_ok=True)
    port = int(os.environ.get("PORT", "8080"))
    log(f"Tutkimus 15M -palvelu portissa {port}, tulokset {OUT}")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()


if __name__ == "__main__":
    main()
