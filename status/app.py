import json, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SITES = [
    ("Axolotl (nginx)", "http://web/"),
    ("Google", "https://www.google.com"),
    ("GitHub", "https://github.com"),
    ("Wikipedia", "https://www.wikipedia.org"),
]
state = {n: (None, None) for n, _ in SITES}
lock = threading.Lock()
sim_until = 0
last_click = 0

def check():
    while True:
        for name, url in SITES:
            t = time.time()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "AxolotlStatus/1.0"})
                urllib.request.urlopen(req, timeout=5)
                res = (True, int((time.time() - t) * 1000))
            except Exception:
                res = (False, None)
            with lock:
                state[name] = res
        time.sleep(30)

def view():
    now = time.time()
    out = []
    for i, (name, _) in enumerate(SITES):
        ok, ms = state[name]
        if i == 0 and now < sim_until:
            if sim_until - now > 10:
                out.append({"name": name, "cls": "ko", "label": "Guasto simulato"})
            else:
                out.append({"name": name, "cls": "wait", "label": "Riparazione automatica..."})
        elif ok is None:
            out.append({"name": name, "cls": "wait", "label": "In controllo"})
        elif ok:
            out.append({"name": name, "cls": "ok", "label": "Online (%d ms)" % ms})
        else:
            out.append({"name": name, "cls": "ko", "label": "Offline"})
    return {"sites": out}

PAGE = """<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Axolotl Status</title>
<style>body{font-family:system-ui;background:#0f172a;color:#e2e8f0;max-width:560px;margin:2rem auto;padding:0 1rem}
.row{display:flex;justify-content:space-between;padding:.8rem 1rem;margin:.5rem 0;border-radius:10px;background:#1e293b}
.ok{color:#4ade80}.ko{color:#f87171}.wait{color:#fbbf24}
button{padding:.8rem 1.2rem;border:0;border-radius:10px;background:#f59e0b;font-weight:700;cursor:pointer}
small{color:#94a3b8}</style></head><body>
<h1>Axolotl Status</h1>
<p><small>Piattaforma auto-riparante: controlli ogni 30 secondi, deploy automatico con GitHub Actions.</small></p>
<div id="list"></div>
<p><button onclick="fail()">Simula un guasto</button></p>
<p><small id="msg">Il pulsante e una simulazione: mostra come il sistema rileva e ripara un guasto.</small></p>
<script>
async function load(){const r=await fetch('/api/status');const d=await r.json();
document.getElementById('list').innerHTML=d.sites.map(s=>'<div class="row"><span>'+s.name+'</span><span class="'+s.cls+'">'+s.label+'</span></div>').join('');}
async function fail(){const r=await fetch('/api/fail',{method:'POST'});
document.getElementById('msg').textContent=r.ok?'Guasto simulato: guarda il sistema ripararsi...':'Attendi un minuto prima di riprovare.';load();}
load();setInterval(load,3000);
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def send(self, code, body, ctype):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/status":
            with lock:
                self.send(200, json.dumps(view()), "application/json")
        else:
            self.send(200, PAGE, "text/html; charset=utf-8")

    def do_POST(self):
        global sim_until, last_click
        now = time.time()
        if self.path == "/api/fail" and now - last_click > 60:
            last_click = now
            sim_until = now + 20
            self.send(200, "{}", "application/json")
        else:
            self.send(429, "{}", "application/json")

    def log_message(self, *a):
        pass

threading.Thread(target=check, daemon=True).start()
ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
