import json
import socket
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

NAME = socket.gethostname()

PAGE = """<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>NODE</title></head>
<body style="font-family:sans-serif;max-width:640px;margin:40px auto;padding:0 16px">
<h2>I am: NODE</h2>
<form id="f">
  <input id="ip" placeholder="peer IP or hostname, e.g. 10.0.1.5 or vm-b" style="width:70%" required>
  <button>Call peer</button>
</form>
<pre id="out" style="background:#eee;padding:12px"></pre>
<script>
document.getElementById('f').onsubmit = async function (e) {
  e.preventDefault();
  var ip = document.getElementById('ip').value;
  document.getElementById('out').textContent = 'calling ' + ip + ' ...';
  var r = await fetch('/api/call?ip=' + encodeURIComponent(ip));
  document.getElementById('out').textContent = JSON.stringify(await r.json(), null, 2);
};
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, body, ctype="application/json"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            self.reply(200, PAGE.replace("NODE", NAME), "text/html")
        elif url.path == "/api/hello":
            # What a peer sees when it calls this node
            self.reply(200, json.dumps({"hello_from": NAME, "caller_ip": self.client_address[0]}))
        elif url.path == "/api/call":
            # Backend makes the request, so private VNet IPs work
            ip = parse_qs(url.query).get("ip", [""])[0].strip()
            try:
                with urllib.request.urlopen(f"http://{ip}/api/hello", timeout=5) as r:
                    peer = json.loads(r.read())
                self.reply(200, json.dumps({"ok": True, "me": NAME, "peer_said": peer}))
            except Exception as e:
                self.reply(502, json.dumps({"ok": False, "me": NAME, "target": ip, "error": str(e)}))
        else:
            self.reply(404, json.dumps({"error": "not found"}))


print(f"{NAME} listening on :80", flush=True)
ThreadingHTTPServer(("0.0.0.0", 80), Handler).serve_forever()
