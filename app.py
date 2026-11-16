#!/usr/bin/env python3
import os, sys, json, time, re, shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))
from generator import generate_fulltime, LOGOS_DIR, OUTPUT_DIR

WEB_DIR = Path(__file__).parent
UPLOAD_DIR = WEB_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
OUT_DIR = WEB_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)
PORT = int(os.environ.get("PORT", 8080))

LOGOS = [
    {"id": "BIRRAREAL", "name": "BIRRAREAL", "file": str(LOGOS_DIR / "BIRRAREAL.png")},
    {"id": "REPARACIONES HENRY", "name": "REPARACIONES HENRY", "file": str(LOGOS_DIR / "REPARACIONES HENRY.png")},
    {"id": "FRIMANG", "name": "FRIMANG", "file": str(LOGOS_DIR / "FRIMANG.png")}
]

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Erytheia FC – Generador</title>
<style>
  :root { --yellow: #FFCC00; --bg: #0f0f0f; --card: #1a1a1a; --text: #fff; --muted: #999; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; padding: 16px; max-width: 520px; margin: 0 auto; }
  h1 { text-align: center; font-size: 1.4rem; margin: 12px 0 24px; color: var(--yellow); }
  .card { background: var(--card); border-radius: 16px; padding: 20px; margin-bottom: 16px; }
  label { display: block; font-size: 0.85rem; color: var(--muted); margin-bottom: 8px; }
  .row { display: flex; gap: 10px; margin-bottom: 16px; }
  .row > * { flex: 1; }
  button, .btn { display: block; width: 100%; padding: 14px; border: none; border-radius: 12px; font-size: 1rem; font-weight: 700; cursor: pointer; }
  .btn-yellow { background: var(--yellow); color: #000; }
  .btn-outline { background: transparent; border: 2px solid #333; color: #fff; }
  .btn-outline.active { border-color: var(--yellow); color: var(--yellow); }
  input[type="number"], input[type="date"], textarea { width: 100%; padding: 12px; border-radius: 10px; border: 2px solid #333; background: #111; color: #fff; font-size: 0.95rem; margin-bottom: 12px; resize: vertical; }
  input[type="date"]::-webkit-calendar-picker-indicator { filter: invert(1); cursor: pointer; }
  .logos { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .logo-btn { padding: 12px; border-radius: 10px; border: 2px solid #333; background: #111; color: #fff; text-align: center; font-size: 0.85rem; cursor: pointer; }
  .logo-btn.active { border-color: var(--yellow); color: var(--yellow); }
  #preview { margin-top: 20px; text-align: center; display: none; }
  #preview img { max-width: 100%; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.5); }
  #status { text-align: center; color: var(--muted); margin: 12px 0; min-height: 24px; }
</style>
</head>
<body>
  <h1>⚽ Erytheia FC – Full Time</h1>
  <div class="card">
    <label>Condición</label>
    <div class="row">
      <button type="button" class="btn-outline active" id="btnLocal" onclick="setHome(true)">🏠 Local</button>
      <button type="button" class="btn-outline" id="btnAway" onclick="setHome(false)">✈️ Visitante</button>
    </div>
    <label>Resultado</label>
    <div class="row">
      <input type="number" id="scoreHome" value="0" min="0" max="20">
      <input type="number" id="scoreAway" value="0" min="0" max="20">
    </div>
    <label>Escudo del rival</label>
    <div class="logos" id="logoList" style="margin-bottom:16px">
      __LOGOS__
      <div class="logo-btn active" data-id="" onclick="selectLogo(this)">Sin logo</div>
    </div>
    <label>Goleadores (un nombre y minuto por línea)</label>
    <textarea id="scorers" rows="3" placeholder="Ej: JUANMA 12'&#10;MIGUEL 34'"></textarea>
    <label>Fecha del partido</label>
    <input type="date" id="datePicker">
    <label>Foto del partido</label>
    <input type="file" id="photo" accept="image/*" style="margin-bottom:16px; color:#ccc">
    <button type="button" class="btn-yellow" onclick="generate()">Generar Full Time</button>
    <div id="status"></div>
  </div>
  <div id="preview">
    <img id="resultImg" src="" alt="Full Time">
    <a id="downloadBtn" class="btn btn-yellow" style="margin-top:12px; text-decoration:none; text-align:center" download="fulltime.png">Descargar imagen</a>
  </div>
<script>
let isHome = true;
let selectedLogo = "";
const MONTHS_ES = ["ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO","JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"];

window.addEventListener('DOMContentLoaded', () => {
  const d = new Date();
  document.getElementById('datePicker').value = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
});

function formatSpanishDate(iso) {
  if (!iso) return "";
  const p = iso.split("-");
  return p.length === 3 ? `${parseInt(p[2], 10)} ${MONTHS_ES[parseInt(p[1], 10) - 1] || ""}`.trim() : iso;
}

function setHome(v) {
  isHome = v;
  document.getElementById('btnLocal').classList.toggle('active', v);
  document.getElementById('btnAway').classList.toggle('active', !v);
}

function selectLogo(el) {
  document.querySelectorAll('.logo-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  selectedLogo = el.dataset.id || "";
}

async function generate() {
  const status = document.getElementById('status');
  const preview = document.getElementById('preview');
  status.textContent = "⏳ Generando cartel...";
  preview.style.display = "none";

  const rawScorers = document.getElementById('scorers').value;
  const scorersLines = rawScorers.split("\n").map(l => l.trim()).filter(l => l.length > 0);

  const form = new FormData();
  form.append("is_home", isHome ? "1" : "0");
  form.append("score_home", document.getElementById("scoreHome").value);
  form.append("score_away", document.getElementById("scoreAway").value);
  form.append("rival_logo", selectedLogo);
  form.append("scorers", scorersLines.join("\n"));
  form.append("date", formatSpanishDate(document.getElementById("datePicker").value));
  
  const photo = document.getElementById("photo").files[0];
  if (photo) form.append("photo", photo);

  try {
    const res = await fetch("/generate", { method: "POST", body: form });
    const data = await res.json();
    if (data.ok) {
      status.textContent = "✅ ¡Cartel listo!";
      document.getElementById("resultImg").src = data.url + "?t=" + Date.now();
      document.getElementById("downloadBtn").href = data.url;
      preview.style.display = "block";
    } else {
      status.textContent = "❌ " + (data.error || "Error");
    }
  } catch (e) {
    status.textContent = "❌ Error de conexión";
  }
}
</script>
</body>
</html>
"""

def parse_multipart(body: bytes, boundary: bytes):
    fields, files = {}, {}
    for part in body.split(b"--" + boundary):
        if not part or part in (b"--\r\n", b"--", b"\r\n"): continue
        if part.startswith(b"\r\n"): part = part[2:]
        if part.endswith(b"\r\n"): part = part[:-2]
        if part.endswith(b"--"): part = part[:-2]
        he = part.find(b"\r\n\r\n")
        if he < 0: continue
        hr = part[:he].decode("utf-8", errors="replace")
        ct = part[he + 4:]
        if ct.endswith(b"\r\n"): ct = ct[:-2]
        nm = re.search(r'name="([^"]+)"', hr)
        if not nm: continue
        fn = re.search(r'filename="([^"]*)"', hr)
        if fn and fn.group(1):
            files[nm.group(1)] = {"filename": fn.group(1), "data": ct}
        else:
            fields[nm.group(1)] = ct.decode("utf-8", errors="replace")
    return fields, files

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            logos_html = "".join(f'<div class="logo-btn" data-id="{lg["id"]}" onclick="selectLogo(this)">{lg["name"]}</div>\n' for lg in LOGOS)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.replace("__LOGOS__", logos_html).encode("utf-8"))
            return
        if path.startswith("/output/"):
            fpath = OUT_DIR / Path(path.split("/output/")[-1]).name
            if fpath.exists() and fpath.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.end_headers()
                self.wfile.write(fpath.read_bytes())
                return
        self.send_error(404)

    def do_POST(self):
        if self.path != "/generate":
            self.send_error(404)
            return
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            content_type = self.headers.get("Content-Type", "")
            
            boundary_match = re.search(r"boundary=(.+)", content_type)
            if boundary_match:
                boundary = boundary_match.group(1).strip().encode()
                fields, files = parse_multipart(body, boundary)
            else:
                fields, files = {}, {}

            is_home = fields.get("is_home", "1") == "1"
            score_home = int(fields.get("score_home", 0))
            score_away = int(fields.get("score_away", 0))
            rival_id = fields.get("rival_logo", "") or ""
            scorers_raw = fields.get("scorers", "") or ""
            scorers = [l.strip() for l in scorers_raw.split("\n") if l.strip()]
            date_text = fields.get("date", "") or ""
            rival_path = next((lg["file"] for lg in LOGOS if lg["id"] == rival_id), None)
            
            photo_path = None
            if "photo" in files and files["photo"]["data"]:
                fileinfo = files["photo"]
                if fileinfo["filename"]:
                    ext = Path(fileinfo["filename"]).suffix or ".jpg"
                    photo_path = str(UPLOAD_DIR / f"photo_{int(time.time())}{ext}")
                    with open(photo_path, "wb") as f:
                        f.write(fileinfo["data"])

            out_name = f"ft_{int(time.time())}.png"
            dest = OUT_DIR / out_name
            result = generate_fulltime(
                photo_path=photo_path,
                score_home=score_home,
                score_away=score_away,
                scorers_erytheia=scorers,
                rival_logo_path=rival_path,
                date_text=date_text,
                is_home=is_home,
                output_name=out_name
            )
            if Path(result).resolve() != Path(dest).resolve():
                shutil.copy(result, dest)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "url": f"/output/{out_name}"}).encode())
        except Exception as e:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
