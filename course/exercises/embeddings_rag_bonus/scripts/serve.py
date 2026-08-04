"""A browser front end for `answer.py`, bound to localhost and nothing else.

The terminal is the wrong surface for the part of this lab that matters. The
argument — retrieved, cited, verifiable, and silent when the corpus has nothing
— lands when a person types their own question and clicks through to the page.
So this serves a single page and one endpoint, and the interesting decisions
are all about what it refuses to do:

- **It binds to the loopback interface and rejects any other address.** A demo
  server holding an index of copyrighted books has no business listening on a
  conference wifi. `--host 0.0.0.0` is an error with an explanation, not an
  option.
- **It checks the `Host` header.** Binding to 127.0.0.1 is not enough on its
  own: a page open in the same browser can point a hostname that resolves to
  loopback at this port and read the answers back out. Only loopback names are
  served.
- **It never trusts the browser about consent.** The checkbox is a request to
  use the cloud generator; the server re-decides, and an unchecked box means
  the excerpts do not leave the laptop no matter what the payload says.
- **It has no dependencies and no CDN.** Standard library, inline assets. It
  works with the wifi off, which is the claim the lab is making.

Nothing is written to disk, and the page shows the same abstention rule, the
same citation check and the same warning as the command line, because it calls
the same `build_answer`.
"""

from __future__ import annotations

import argparse
import json
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from answer import CLAUDE_TIMEOUT_SECONDS, GENERATORS, build_answer, load_calibration
from common import CONSENT_WARNING
from search import SearchIndex

warnings.filterwarnings(
    "ignore", message=r"The model .* now uses mean pooling instead of CLS embedding.*"
)

# The only addresses this server is allowed to bind. Not a default that can be
# overridden: a list that `--host` has to be a member of.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})

# Host header values accepted once bound, before the port is stripped.
LOOPBACK_NAMES = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})

# A question longer than this is not a question, and the body that carries it
# is not one either. Both are bounded so a stray paste cannot occupy the model
# for minutes in front of a class.
MAX_QUESTION_CHARS = 500
MAX_BODY_BYTES = 8 * 1024

PAGE = """<!doctype html>
<html lang="es">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Respuestas con evidencia local</title>
<style>
 :root { color-scheme: light dark; }
 body { font: 16px/1.55 system-ui, sans-serif; max-width: 46rem; margin: 2rem auto;
        padding: 0 1rem; }
 h1 { font-size: 1.4rem; margin-bottom: .2rem; }
 .sub { color: #666; margin-top: 0; font-size: .9rem; }
 textarea { width: 100%; font: inherit; padding: .6rem; box-sizing: border-box; }
 .row { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; margin: .6rem 0; }
 button { font: inherit; padding: .5rem 1.1rem; cursor: pointer; }
 .warn { border-left: 4px solid #c47f00; background: #fff8e6; color: #4a3800;
         padding: .7rem .9rem; font-size: .88rem; margin: .8rem 0; }
 .answer { white-space: pre-wrap; border-left: 4px solid #3c78d8; padding: .2rem 0 .2rem .9rem;
           margin: 1rem 0; }
 .abstained { border-left-color: #999; color: #555; }
 ol.sources { padding-left: 1.2rem; }
 ol.sources li { margin: .35rem 0; font-size: .9rem; }
 .meta { font-size: .85rem; color: #555; border-top: 1px solid #ddd; padding-top: .7rem; }
 .bad { color: #b00; font-weight: 600; }
 .path { color: #777; }
 @media (prefers-color-scheme: dark) {
   .warn { background: #2a2415; color: #f0e2bf; }
   .sub, .meta, .path { color: #aaa; }
 }
</style>
<h1>Respuestas con evidencia local</h1>
<p class="sub">Recuperación sobre libros locales. Cada afirmación lleva
<code>[n]</code> y cada <code>[n]</code> apunta a una página que podés abrir.
Si el corpus no alcanza, el sistema se abstiene.</p>

<textarea id="q" rows="3" maxlength="500"
 placeholder="¿Cuáles son las diferencias entre el Sistema 1 y el Sistema 2?"></textarea>
<div class="row">
  <label>Fragmentos <input id="limit" type="number" value="3" min="1" max="8"></label>
  <label><input id="cloud" type="checkbox"> Redactar con Opus (envía los excerptos)</label>
  <button id="go">Responder</button>
</div>
<div class="warn" id="consent-warning"></div>
<div id="out"></div>

<script>
const $ = (id) => document.getElementById(id);
$("consent-warning").textContent = CONSENT_WARNING_TEXT;

async function ask() {
  const question = $("q").value.trim();
  if (!question) return;
  $("go").disabled = true;
  $("out").textContent = "Buscando en el índice local…";
  try {
    const response = await fetch("/api/answer", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        question,
        limit: Number($("limit").value) || 3,
        generator: $("cloud").checked ? "claude_cli" : "extractive",
        consent: $("cloud").checked,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "error del servidor");
    render(payload);
  } catch (error) {
    $("out").textContent = "Error: " + error.message;
  } finally {
    $("go").disabled = false;
  }
}

function render(payload) {
  const out = $("out");
  out.textContent = "";
  const answer = document.createElement("div");
  answer.className = "answer" + (payload.answered ? "" : " abstained");
  answer.textContent = payload.answer;
  out.append(answer);

  if (payload.sources.length) {
    const list = document.createElement("ol");
    list.className = "sources";
    for (const source of payload.sources) {
      const item = document.createElement("li");
      item.textContent = source.citation + " — " + source.pages + " ";
      const path = document.createElement("span");
      path.className = "path";
      path.textContent = source.relative_path;
      item.append(path);
      list.append(item);
    }
    out.append(list);
  }

  const meta = document.createElement("div");
  meta.className = "meta";
  const verdict = payload.verdict;
  const rule = document.createElement("div");
  rule.textContent =
    (verdict.answer ? "La recuperación pasa" : "La recuperación se abstiene") +
    ": similitud máxima " + verdict.statistic +
    (verdict.answer ? " ≥ " : " < ") + "umbral " + verdict.threshold +
    " (margen " + verdict.margin + ").";
  meta.append(rule);

  if (verdict.answer && !payload.answered) {
    const finalDecision = document.createElement("div");
    finalDecision.textContent =
      "Decisión final: Opus se abstuvo después de leer los fragmentos recuperados.";
    meta.append(finalDecision);
  }

  const check = document.createElement("div");
  check.textContent = "Generador: " + payload.generator + ". Citas verificadas: " +
    (payload.citation_check.ok ? "sí" : "NO");
  if (!payload.citation_check.ok) check.className = "bad";
  meta.append(check);

  for (const note of payload.notes) {
    const line = document.createElement("div");
    line.textContent = "Nota: " + note;
    meta.append(line);
  }
  out.append(meta);
}

$("go").addEventListener("click", ask);
$("q").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) ask();
});
</script>
</html>
"""


def render_page() -> bytes:
    """The page with the consent warning injected from its single definition.

    The warning the browser shows and the warning the terminal prints are the
    same string; embedding it as JSON keeps it that way and keeps quotes and
    accents from breaking the script.
    """
    warning = json.dumps(CONSENT_WARNING, ensure_ascii=False)
    return PAGE.replace("CONSENT_WARNING_TEXT", warning).encode("utf-8")


def host_is_loopback(header: str | None) -> bool:
    """Whether a `Host` header names this machine.

    Guards against a page in the same browser reaching this port through a
    hostname that resolves to 127.0.0.1. Without it, "bound to localhost" is a
    weaker claim than it sounds.
    """
    if not header:
        return False
    name = header.strip()
    if name.startswith("["):  # [::1]:8000
        closing = name.find("]")
        name = name[: closing + 1] if closing != -1 else name
    elif ":" in name:
        name = name.rsplit(":", 1)[0]
    return name.lower() in LOOPBACK_NAMES


def answer_request(state: dict, payload: dict) -> dict:
    """Validate one browser request and answer it, or explain the refusal.

    The consent flag is re-read here rather than trusted: the browser asks for
    the cloud generator, the server decides whether the excerpts may leave.
    """
    question = str(payload.get("question", "")).strip()
    if not question:
        raise ValueError("Falta la pregunta.")
    if len(question) > MAX_QUESTION_CHARS:
        raise ValueError(f"La pregunta supera {MAX_QUESTION_CHARS} caracteres.")
    generator = payload.get("generator", "extractive")
    if generator not in GENERATORS:
        raise ValueError(f"Generador desconocido: {generator!r}.")
    consent = payload.get("consent") is True
    downgraded = generator == "claude_cli" and not consent
    if downgraded:
        generator = "extractive"
    try:
        limit = max(1, min(8, int(payload.get("limit", 3))))
    except (TypeError, ValueError):
        limit = 3
    with state["lock"]:
        result = build_answer(
            state["index"],
            question,
            state["calibration"],
            mode=state["mode"],
            limit=limit,
            generator=generator,
            send_excerpts=consent,
            interactive=False,
            timeout=state["timeout"],
        )
    if downgraded:
        # The refusal is shown, not just performed: a request that asked for
        # the cloud generator without consent gets an answer that says why it
        # was answered locally.
        result["notes"].append(
            "Se pidió el generador claude_cli sin consentimiento: no se envió "
            "nada y se respondió en modo extractivo."
        )
    return result


class Handler(BaseHTTPRequestHandler):
    server_version = "embeddings-rag-bonus/1.0"
    state: dict = {}

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # No third-party assets are loaded, so the page can be locked down.
        self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def _guard(self) -> bool:
        if host_is_loopback(self.headers.get("Host")):
            return True
        self._json(403, {"error": "Este servidor solo responde en localhost."})
        return False

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        if not self._guard():
            return
        if self.path not in ("/", "/index.html"):
            self._json(404, {"error": "No existe."})
            return
        self._send(200, render_page(), "text/html; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802 (http.server API)
        if not self._guard():
            return
        if self.path != "/api/answer":
            self._json(404, {"error": "No existe."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"error": "Content-Length inválido."})
            return
        if length > MAX_BODY_BYTES:
            self._json(413, {"error": "Cuerpo demasiado grande."})
            return
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "JSON inválido."})
            return
        try:
            self._json(200, answer_request(self.state, payload))
        except ValueError as error:
            self._json(400, {"error": str(error)})

    def log_message(self, fmt: str, *args) -> None:
        """One quiet line per request; the console belongs to the class."""
        print(f"  {self.address_string()} {fmt % args}")


def parse_args() -> argparse.Namespace:
    root = Path(__file__).parents[1]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--index", type=Path, default=root / "local_index_full")
    parser.add_argument(
        "--calibration", type=Path, default=root / "answer-calibration.json"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--mode", choices=["lexical", "dense", "hybrid"], default="dense")
    parser.add_argument("--timeout", type=int, default=CLAUDE_TIMEOUT_SECONDS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.host not in LOOPBACK_HOSTS:
        raise SystemExit(
            f"--host {args.host} expondría el índice fuera de esta máquina. "
            f"Solo se permite {', '.join(sorted(LOOPBACK_HOSTS))}. Este servidor "
            "sirve una biblioteca local con derechos de autor: no se publica en "
            "una red."
        )
    index = SearchIndex.load(args.index)
    calibration = load_calibration(args.calibration, args.mode, index.config["model"])
    # Load the model before the first request instead of during it, so nobody
    # watches a blank page for eight seconds in front of a room.
    index.embed_query("calentamiento del modelo")
    Handler.state = {
        "index": index,
        "calibration": calibration,
        "mode": args.mode,
        "timeout": args.timeout,
        # fastembed sessions are not documented as thread-safe and the class
        # only ever asks one question at a time; serialise and stay boring.
        "lock": threading.Lock(),
    }
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Índice: {args.index} ({len(index.chunks)} fragmentos, modo {args.mode})")
    print(f"Umbral de abstención medido: {calibration['min_top_score']}")
    print(f"Abrí http://{args.host}:{args.port}/ — Ctrl-C para terminar.")
    print(CONSENT_WARNING)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
