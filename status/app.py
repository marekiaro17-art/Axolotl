import json, threading, time, urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SITES = [
    ("Axolotl", "Il mio sito (nginx in Docker)", "http://web/"),
    ("Google", "Servizio di riferimento", "https://www.google.com"),
    ("GitHub", "Dove vive il codice", "https://github.com"),
    ("Wikipedia", "Servizio di riferimento", "https://www.wikipedia.org"),
]
HIST = 30
state = {n: {"ok": None, "ms": None, "hist": deque(maxlen=HIST)} for n, _, _ in SITES}
lock = threading.Lock()
sim_until = 0
last_click = 0
last_check = 0


def check():
    global last_check
    while True:
        for name, _, url in SITES:
            t = time.time()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "AxolotlStatus/2.0"})
                urllib.request.urlopen(req, timeout=5)
                ok, ms = True, int((time.time() - t) * 1000)
            except Exception:
                ok, ms = False, None
            with lock:
                s = state[name]
                s["ok"], s["ms"] = ok, ms
                s["hist"].append(1 if ok else 0)
        with lock:
            last_check = time.time()
        time.sleep(30)


def view():
    now = time.time()
    sim = now < sim_until
    out = []
    for i, (name, desc, _) in enumerate(SITES):
        s = state[name]
        hist = list(s["hist"])
        up = round(100.0 * sum(hist) / len(hist), 1) if hist else None
        ms = None
        if i == 0 and sim:
            st = "ko" if sim_until - now > 10 else "fix"
        elif s["ok"] is None:
            st = "wait"
        elif s["ok"]:
            st, ms = "ok", s["ms"]
        else:
            st = "ko"
        out.append({"name": name, "desc": desc, "state": st, "ms": ms, "uptime": up, "hist": hist})
    states = [x["state"] for x in out]
    if "ko" in states:
        banner = ["ko", "Guasto rilevato"]
    elif "fix" in states:
        banner = ["fix", "Riparazione automatica in corso"]
    elif "wait" in states:
        banner = ["wait", "Controllo in corso"]
    else:
        banner = ["ok", "Tutti i sistemi operativi"]
    return {"sites": out, "banner": banner, "checked": last_check, "hist": HIST}


PAGE = """<!doctype html>
<html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Axolotl, piattaforma che si ripara da sola</title>
<style>
:root{--bg:#0d2326;--ink:#0d2326;--text:#e6efe9;--mute:#8fa9a3;--rule:#33565a;--line:#6f9a94;
--skin:#f1cdc4;--gill:#e0627f;--ok:#82d4b0;--ko:#ff7a70;--fix:#f0cd6a;--wait:#5f7d7c}
*{box-sizing:border-box}
html{background:var(--bg)}
body{margin:0;color:var(--text);background:var(--bg);line-height:1.5;
font-family:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif}
.page{max-width:940px;margin:0 auto;padding:2.5rem 1.25rem 3rem}
h1{font-size:clamp(2.8rem,9vw,4.6rem);line-height:1;margin:0;font-weight:600;letter-spacing:-.02em}
.latin{font-style:italic;color:var(--skin);font-size:1.15rem;margin:.7rem 0 0}
.lede{max-width:34rem;color:var(--mute);margin:.5rem 0 2.4rem;font-size:1.02rem}
.row{display:grid;grid-template-columns:60% 40%}
.lab{min-width:0;padding:.2rem .8rem .8rem 0}
.row.top .lab{border-bottom:1px solid var(--rule)}
.row.bot .lab{border-top:1px solid var(--rule);padding:.8rem .8rem .2rem 0}
.row .lab+.lab{padding-left:.9rem}
.row.bot .lab+.lab{padding-left:.9rem}
.nm{display:block;font-size:1.2rem;font-weight:600;line-height:1.25}
.ds{display:block;font-style:italic;color:var(--mute);font-size:.9rem}
.stl{display:flex;align-items:center;gap:.5rem;margin-top:.35rem;font-size:.95rem}
.dot{width:.6rem;height:.6rem;border-radius:50%;background:var(--wait);flex:none}
.stl.ok .dot{background:var(--ok)}.stl.ko .dot{background:var(--ko)}.stl.fix .dot{background:var(--fix)}
.tk{display:flex;gap:2px;height:9px;margin-top:.55rem}
.tk i{flex:1;background:#1b3a3e;border-radius:1px}
.tk i.u{background:var(--ok);opacity:.85}.tk i.d{background:var(--ko)}
.up{color:var(--mute);font-size:.8rem;margin-top:.25rem}
svg{display:block;width:100%;height:auto;overflow:visible}
.skin{fill:var(--skin)}
.bodyfill{fill:var(--skin);stroke:var(--ink);stroke-width:3;stroke-linejoin:round}
.ink{stroke:var(--ink);fill:none;stroke-linecap:round;stroke-linejoin:round}
.skS{stroke:var(--skin);fill:none;stroke-linecap:round;stroke-linejoin:round}
.gl{stroke:var(--gill);fill:none;stroke-linecap:round}
.spot{fill:rgba(13,35,38,.28)}
.tick{stroke:rgba(13,35,38,.35);stroke-width:2;stroke-linecap:round}
.gill{transform-origin:0 0;animation:sway 5s ease-in-out infinite alternate}
@keyframes sway{from{transform:rotate(-3deg)}to{transform:rotate(3deg)}}
.limb{transform-origin:0 0;transition:transform .35s ease-in}
.slot.ko .limb{transform:scale(.001)}
.slot.fix .limb{animation:regrow 9s cubic-bezier(.25,.6,.3,1) forwards}
@keyframes regrow{0%{transform:scale(.001)}25%{transform:scale(.2)}100%{transform:scale(1)}}
.lead{stroke:var(--line);stroke-width:1.5}
.tipdot{fill:var(--line)}
.slot.ko .lead{stroke:var(--ko);stroke-dasharray:5 5}
.slot.fix .lead{stroke:var(--fix);stroke-dasharray:5 5}
.slot.ko .tipdot{fill:var(--ko)}.slot.fix .tipdot{fill:var(--fix)}
.verdict{margin:2rem 0 0;max-width:36rem;font-size:clamp(1.35rem,3.6vw,1.85rem);line-height:1.25}
.when{color:var(--mute);font-size:.9rem;margin:.5rem 0 1.5rem;max-width:34rem}
button{font:inherit;color:var(--skin);background:transparent;border:1px solid var(--skin);border-radius:3px;
padding:.7rem 1.3rem;cursor:pointer;transition:background .2s,color .2s}
button:hover:not(:disabled){background:var(--skin);color:var(--ink)}
button:disabled{opacity:.55;cursor:default}
button:focus-visible{outline:2px solid var(--ok);outline-offset:3px}
.note{color:var(--mute);font-size:.88rem;margin:.8rem 0 0;max-width:34rem}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--rule);color:var(--mute);font-size:.88rem}
a{color:var(--skin)}
@media (max-width:600px){.ds{display:none}.nm{font-size:1.05rem}.stl{font-size:.85rem}.up{font-size:.72rem}}
@media (prefers-reduced-motion:reduce){.gill{animation:none}.slot.fix .limb{animation:none;transform:scale(.6)}.limb{transition:none}}

#monitor{margin-top:3rem;border-top:1px solid var(--rule);padding-top:1.6rem}
#monitor h2{font-size:1.5rem;margin:0 0 .4rem;font-weight:600}
.mon-lede{max-width:40rem;color:var(--mute);margin:0 0 1.2rem;font-size:1.02rem}
.mon-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:.6rem;margin-bottom:.6rem}
.mon-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.6rem}
.mon-stats iframe,.mon-grid iframe{width:100%;border:1px solid var(--rule);border-radius:6px;background:#111b25;display:block}
.mon-stats iframe{height:120px}
.mon-grid iframe{height:260px}
.mon-btn{display:inline-block;margin-top:1rem;padding:.55rem 1rem;border-radius:6px;background:#f2994a;color:#1a1005;text-decoration:none;font-weight:600}
.mon-note{color:var(--mute);font-size:.9rem;margin:.8rem 0 0}
@media(max-width:620px){.mon-stats{grid-template-columns:repeat(2,1fr)}.mon-grid{grid-template-columns:1fr}}
</style></head><body><div class="page">
<header>
<h1>Axolotl</h1>
<p class="latin">Ambystoma mexicanum, l'anfibio che rigenera gli arti perduti.</p>
<p class="lede">Questa pagina fa lo stesso con i servizi di un server: se uno smette di rispondere, lo rileva e lo riavvia da solo.</p>
</header>
<main>
<div class="row top" id="top"></div>
<svg id="plate" viewBox="0 0 900 460" role="img" aria-label="Un axolotl visto dall'alto: ogni zampa corrisponde a un servizio controllato"></svg>
<div class="row bot" id="bot"></div>
<p class="verdict" id="verdict">Primo controllo in corso.</p>
<p class="when" id="when">Ogni zampa è un servizio, controllato ogni 30 secondi.</p>
<button id="btn" type="button">Simula un guasto</button>
<p class="note" id="note">Il guasto è simulato e nessun server viene spento. I controlli sui servizi sono reali.</p>
</main>
<section id="monitor" aria-labelledby="monitor-t">
<h2 id="monitor-t">Monitoraggio in tempo reale</h2>
<p class="mon-lede">Questi grafici mostrano il mio server Oracle Cloud su cui gira Axolotl: CPU, memoria, disco e container. I dati sono raccolti da Prometheus e disegnati da Grafana, e si aggiornano ogni 30 secondi.</p>
<div class="mon-stats"><iframe src="https://monitor.speedrace.dpdns.org/d-solo/axolotl-overview/axolotl?orgId=1&amp;theme=dark&amp;refresh=30s&amp;from=now-6h&amp;to=now&amp;panelId=1" title="Container attivi" loading="lazy" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe><iframe src="https://monitor.speedrace.dpdns.org/d-solo/axolotl-overview/axolotl?orgId=1&amp;theme=dark&amp;refresh=30s&amp;from=now-6h&amp;to=now&amp;panelId=2" title="Uptime server" loading="lazy" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe><iframe src="https://monitor.speedrace.dpdns.org/d-solo/axolotl-overview/axolotl?orgId=1&amp;theme=dark&amp;refresh=30s&amp;from=now-6h&amp;to=now&amp;panelId=3" title="RAM usata" loading="lazy" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe><iframe src="https://monitor.speedrace.dpdns.org/d-solo/axolotl-overview/axolotl?orgId=1&amp;theme=dark&amp;refresh=30s&amp;from=now-6h&amp;to=now&amp;panelId=4" title="Disco usato" loading="lazy" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe></div>
<div class="mon-grid"><iframe src="https://monitor.speedrace.dpdns.org/d-solo/axolotl-overview/axolotl?orgId=1&amp;theme=dark&amp;refresh=30s&amp;from=now-6h&amp;to=now&amp;panelId=5" title="Uso CPU del server" loading="lazy" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe><iframe src="https://monitor.speedrace.dpdns.org/d-solo/axolotl-overview/axolotl?orgId=1&amp;theme=dark&amp;refresh=30s&amp;from=now-6h&amp;to=now&amp;panelId=6" title="Memoria per container" loading="lazy" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe><iframe src="https://monitor.speedrace.dpdns.org/d-solo/axolotl-overview/axolotl?orgId=1&amp;theme=dark&amp;refresh=30s&amp;from=now-6h&amp;to=now&amp;panelId=7" title="CPU per container" loading="lazy" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe><iframe src="https://monitor.speedrace.dpdns.org/d-solo/axolotl-overview/axolotl?orgId=1&amp;theme=dark&amp;refresh=30s&amp;from=now-6h&amp;to=now&amp;panelId=8" title="RAM del server" loading="lazy" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe><iframe src="https://monitor.speedrace.dpdns.org/d-solo/axolotl-overview/axolotl?orgId=1&amp;theme=dark&amp;refresh=30s&amp;from=now-6h&amp;to=now&amp;panelId=9" title="Disco usato nel tempo" loading="lazy" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe><iframe src="https://monitor.speedrace.dpdns.org/d-solo/axolotl-overview/axolotl?orgId=1&amp;theme=dark&amp;refresh=30s&amp;from=now-6h&amp;to=now&amp;panelId=10" title="Uptime per container" loading="lazy" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe></div>
<a class="mon-btn" href="https://monitor.speedrace.dpdns.org/d/axolotl-overview" target="_blank" rel="noopener">Apri la dashboard completa &rarr;</a>
<p class="mon-note">Dati in sola lettura.</p>
</section>
<footer>
<a href="https://github.com/marekiaro17-art/Axolotl" target="_blank" rel="noopener">Codice e documentazione su GitHub</a>.
Costruito con Docker, nginx, Python, GitHub Actions, autoheal e fail2ban.
</footer>
</div>
<script>
(function(){
var NS="http://www.w3.org/2000/svg";
function s(tag,attrs,parent){var e=document.createElementNS(NS,tag);for(var k in attrs)e.setAttribute(k,attrs[k]);if(parent)parent.appendChild(e);return e}
function h(tag,cls,txt,parent){var e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;if(parent)parent.appendChild(e);return e}
var svg=document.getElementById("plate");

function gill(parent,bx,by,tx,ty,flip,delay){
 var g=s("g",{transform:"translate("+bx+","+(flip?460-by:by)+")"+(flip?" scale(1,-1)":"")},parent);
 var a=s("g",{"class":"gill"},g);a.style.animationDelay=delay+"s";
 var dx=tx-bx,dy=ty-by,cx=dx*0.2-dy*0.18,cy=dy*0.55+dx*0.1;
 s("path",{"class":"gl","stroke-width":6,d:"M0 0 Q"+cx+" "+cy+" "+dx+" "+dy},a);
 for(var i=1;i<=8;i++){
  var t=0.22+i*0.095,u=1-t;
  var px=2*u*t*cx+t*t*dx,py=2*u*t*cy+t*t*dy;
  var tx2=2*u*cx+2*t*(dx-cx),ty2=2*u*cy+2*t*(dy-cy),n=Math.sqrt(tx2*tx2+ty2*ty2);
  tx2/=n;ty2/=n;
  var L=16*(1-Math.abs(t-0.62)*0.9);
  s("path",{"class":"gl","stroke-width":3,d:"M"+px+" "+py+" L"+(px-ty2*L+tx2*5)+" "+(py+tx2*L+ty2*5)},a);
  s("path",{"class":"gl","stroke-width":3,d:"M"+px+" "+py+" L"+(px+ty2*L+tx2*5)+" "+(py-tx2*L+ty2*5)},a);
 }
}
var gl=[[330,184,292,106],[356,178,340,90],[384,176,394,98]],gi,fl;
var gg=s("g",{},svg);
for(fl=0;fl<2;fl++)for(gi=0;gi<3;gi++)gill(gg,gl[gi][0],gl[gi][1],gl[gi][2],gl[gi][3],fl===1,(gi+fl*1.3)*0.7);

var LIMBS=[
 {x:443,y:170,flip:false,lx:471,l1:96},
 {x:584,y:195,flip:false,lx:612,l1:120},
 {x:443,y:290,flip:true,lx:471,l1:96},
 {x:584,y:265,flip:true,lx:612,l1:120}
];
var FING=[[19,-63],[27,-67],[36,-65],[43,-58]];
var limbG=[],leadG=[];
LIMBS.forEach(function(L,i){
 var g=s("g",{"class":"slot",transform:"translate("+L.x+","+L.y+")"+(L.flip?" scale(1,-1)":"")},svg);
 var l=s("g",{"class":"limb"},g);
 s("path",{"class":"ink","stroke-width":13,d:"M0 0 C4 -20 12 -36 28 -50"},l);
 FING.forEach(function(f){s("path",{"class":"ink","stroke-width":7,d:"M28 -50 L"+f[0]+" "+f[1]},l)});
 s("path",{"class":"skS","stroke-width":9,d:"M0 0 C4 -20 12 -36 28 -50"},l);
 FING.forEach(function(f){s("path",{"class":"skS","stroke-width":4,d:"M28 -50 L"+f[0]+" "+f[1]},l)});
 limbG.push(g);
});

s("path",{"class":"bodyfill",d:"M360 178 C430 164 500 168 560 188 C640 212 730 224 830 230 C730 236 640 248 560 272 C500 292 430 296 360 282 Z"},svg);
s("ellipse",{"class":"bodyfill",cx:318,cy:230,rx:72,ry:56},svg);
[[276,204],[276,256]].forEach(function(e){s("circle",{cx:e[0],cy:e[1],r:5,fill:"#0d2326"},svg)});
[[252,222],[252,238]].forEach(function(e){s("circle",{cx:e[0],cy:e[1],r:1.8,fill:"#0d2326"},svg)});
[[470,200,4],[520,214,5],[560,236,4],[500,258,3.5],[610,230,3],[430,214,3],[690,232,2.5],[430,250,4],[300,204,3.5],[322,254,3],[352,224,3]].forEach(function(p){
 s("circle",{"class":"spot",cx:p[0],cy:p[1],r:p[2]},svg)});
for(var x=400;x<=800;x+=22){var hh=6*(1-(x-400)/460)+1.5;s("line",{"class":"tick",x1:x,x2:x,y1:230-hh,y2:230+hh},svg)}
LIMBS.forEach(function(L){s("circle",{"class":"skin",cx:L.x,cy:L.y,r:7},svg)});
LIMBS.forEach(function(L){
 var g=s("g",{"class":"slot"},svg);
 var a=L.flip?460-L.l1:L.l1,b=L.flip?460:0;
 s("line",{"class":"lead",x1:L.lx,x2:L.lx,y1:a,y2:b},g);
 s("circle",{"class":"tipdot",cx:L.lx,cy:a,r:3.5},g);
 leadG.push(g);
});

var labs=[];
function mkLab(parent){
 var d=h("div","lab",undefined,parent),o={};
 o.nm=h("span","nm","",d);o.ds=h("span","ds","",d);
 o.stl=h("div","stl wait",undefined,d);h("span","dot","",o.stl);o.st=h("span","","",o.stl);
 o.tk=h("div","tk",undefined,d);o.up=h("div","up","",d);
 return o;
}
var top=document.getElementById("top"),bot=document.getElementById("bot");
labs.push(mkLab(top),mkLab(top),mkLab(bot),mkLab(bot));

var TXT={ok:"Operativo",ko:"Non risponde",fix:"Riavvio in corso",wait:"In controllo"};
var VERD={ok:"Tutti i servizi rispondono.",ko:"Un servizio non risponde: la zampa è caduta.",
 fix:"Riavvio automatico in corso: la zampa sta ricrescendo.",wait:"Primo controllo in corso."};
function render(d){
 var worst="ok";
 d.sites.forEach(function(st,i){
  var o=labs[i];
  o.nm.textContent=st.name;o.ds.textContent=st.desc;
  o.stl.className="stl "+st.state;
  o.st.textContent=TXT[st.state]+(st.state==="ok"&&st.ms!==null?", "+st.ms+" ms":"");
  o.tk.textContent="";
  var pad=d.hist-st.hist.length,k;
  for(k=0;k<pad;k++)h("i","",undefined,o.tk);
  st.hist.forEach(function(v){h("i",v?"u":"d",undefined,o.tk)});
  o.up.textContent=st.uptime===null?"Storico in raccolta":"Disponibile al "+String(st.uptime).replace(".",",")+"% negli ultimi 15 minuti";
  var cls="slot "+st.state;
  limbG[i].setAttribute("class",cls);leadG[i].setAttribute("class",cls);
  if(st.state==="ko")worst="ko";else if(st.state==="fix"&&worst!=="ko")worst="fix";else if(st.state==="wait"&&worst==="ok")worst="wait";
 });
 document.getElementById("verdict").textContent=VERD[worst];
 var t=d.checked?new Date(d.checked*1000).toLocaleTimeString("it-IT"):null;
 document.getElementById("when").textContent=(t?"Ultimo controllo alle "+t+". ":"")+"Ogni zampa è un servizio, controllato ogni 30 secondi.";
}
function load(){fetch("/api/status").then(function(r){return r.json()}).then(render).catch(function(){})}
var btn=document.getElementById("btn"),note=document.getElementById("note");
btn.addEventListener("click",function(){
 btn.disabled=true;
 fetch("/api/fail",{method:"POST"}).then(function(r){
  note.textContent=r.ok?"Guasto simulato: guarda la zampa. Cade, viene riavviata e ricresce.":"Attendi un minuto prima di riprovare.";
  load();setTimeout(function(){btn.disabled=false},r.ok?20000:3000);
 }).catch(function(){btn.disabled=false});
});
load();setInterval(load,2000);
})();
</script></body></html>"""

CSP = "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src 'self' data:; frame-src https://monitor.speedrace.dpdns.org"


class H(BaseHTTPRequestHandler):
    timeout = 10

    def send(self, code, body, ctype):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", CSP)
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
            sim_until = now + 18
            self.send(200, "{}", "application/json")
        else:
            self.send(429, "{}", "application/json")

    def log_message(self, *a):
        pass


threading.Thread(target=check, daemon=True).start()
ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
