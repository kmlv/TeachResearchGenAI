#!/usr/bin/env python3
"""Checks that the literature-review packet is structurally ready to teach."""
from pathlib import Path
import re
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
SITE_ROOT = PROJECT / "_site" / "course" / "exercises" / "literature_review"
REQUIRED = {
    "README.md", "sources.md", "worksheet.md", "prompt.md", "answer-key.md",
    "fallback-matrix.md", "facilitator-runbook.md", "participant-packet.qmd",
    "workflow-guide.qmd", "starter_workspace.zip",
    "discovery-screening-clip.html", "clip-data.js", "validate_clip.js",
}
ENUMS = {"supported", "contradicted", "partially_supported", "insufficient"}
SLIDE_PARTIAL = PROJECT / "course" / "slides" / "partials" / "literature-review.qmd"

def urls(text):
    return re.findall(r"https?://[^)\]\s]+", text)

def main():
    missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit("Faltan: " + ", ".join(missing))
    source_text = (ROOT / "sources.md").read_text(encoding="utf-8")
    quotes = re.findall(r"> “([^”]+)”", source_text)
    if not quotes or any(len(q.split()) > 25 for q in quotes):
        raise SystemExit("Cada extracto textual debe existir y tener <=25 palabras.")
    answer = (ROOT / "answer-key.md").read_text(encoding="utf-8")
    absent = [enum for enum in ENUMS if f"`{enum}`" not in answer]
    if absent:
        raise SystemExit("Faltan enums: " + ", ".join(absent))
    if "NO ENCONTRADO" not in (ROOT / "prompt.md").read_text(encoding="utf-8"):
        raise SystemExit("El prompt debe obligar NO ENCONTRADO.")
    worksheet = (ROOT / "worksheet.md").read_text(encoding="utf-8")
    if "S1–S4" not in worksheet:
        raise SystemExit("La hoja debe entregar los cuatro pasajes S1–S4.")
    if re.search(r"_{20,}", worksheet):
        raise SystemExit("La hoja contiene líneas no responsivas de guiones bajos.")
    guide = (ROOT / "workflow-guide.qmd").read_text(encoding="utf-8")
    slide_text = SLIDE_PARTIAL.read_text(encoding="utf-8")
    if "PROJECT-INSTRUCTIONS.md" not in guide:
        raise SystemExit("La ruta de chat debe cargar instrucciones portátiles.")
    with ZipFile(ROOT / "starter_workspace.zip") as archive:
        archived = set(archive.namelist())
    if "starter_workspace/PROJECT-INSTRUCTIONS.md" not in archived:
        raise SystemExit("El ZIP no contiene PROJECT-INSTRUCTIONS.md.")
    if "Panamá" not in source_text or "Juntos" not in source_text or "ENAHO" not in source_text:
        raise SystemExit("Falta el control de país/programa.")
    source_urls = urls(source_text)
    if len(source_urls) != 4:
        raise SystemExit("Se esperaban exactamente cuatro enlaces de fuente.")
    platform_urls = sorted(set(urls(guide) + urls(slide_text)) - set(source_urls))
    if "--check-render" in sys.argv:
        rendered = {
            "participant-packet.html",
            "workflow-guide.html",
            "discovery-screening-clip.html",
            "starter_workspace.zip",
        }
        missing_render = [name for name in sorted(rendered) if not (SITE_ROOT / name).is_file()]
        if missing_render:
            raise SystemExit("Faltan en _site: " + ", ".join(missing_render))
        packet_html = (SITE_ROOT / "participant-packet.html").read_text(encoding="utf-8")
        for bad_href in ('href="sources.md"', 'href="prompt.md"'):
            if bad_href in packet_html:
                raise SystemExit(f"Enlace interno no publicable: {bad_href}")
        for anchor in (
            'id="corpus-congelado-cuatro-pasajes-para-auditar"',
            'id="prompt-común-extracción-no-síntesis"',
        ):
            if anchor not in packet_html:
                raise SystemExit(f"Falta ancla interna en la práctica: {anchor}")
        site_zip = SITE_ROOT / "starter_workspace.zip"
        if site_zip.read_bytes() != (ROOT / "starter_workspace.zip").read_bytes():
            raise SystemExit("El ZIP publicado no coincide con el workspace actual.")
    if "--check-links" in sys.argv:
        for url in sorted(set(source_urls + platform_urls)):
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")
            try:
                with urlopen(request, timeout=20) as response:
                    if response.status >= 400:
                        raise RuntimeError(f"HTTP {response.status}")
                print("OK", url)
            except HTTPError as error:
                # DOI and publisher landing pages commonly reject automated HEAD
                # requests while remaining valid, stable links for a browser.
                if error.code in {401, 403, 405, 429}:
                    print("RESTRINGIDO PERO ALCANZABLE", error.code, url)
                else:
                    raise SystemExit(f"No se pudo verificar {url}: {error}")
            except Exception as error:
                raise SystemExit(f"No se pudo verificar {url}: {error}")
    print(
        f"OK: {len(REQUIRED)} archivos fuente, {len(quotes)} extractos <=25 "
        f"palabras, 4 enums, 4 fuentes y {len(platform_urls)} enlaces de plataforma."
    )

if __name__ == "__main__":
    main()
