"""Registrul scraperelor.

Fiecare modul expune NAME, SOURCE și scrape(max_pages=None) -> listă de produse
({"title", "link", "price", "source", "image_url"}).

`enabled` = dacă rulează implicit (în GitHub Actions). Cele dezactivate se pot
rula oricând manual cu --site <nume> sau cu variabila SCRAPERS=nume1,nume2.
"""

from . import noriel, smyk_html

# ordinea contează: rulează de sus în jos
REGISTRY = [
    # blocat pe GitHub Actions de WAF-ul Smyk (pagina "WAF")
    {"module": smyk_html, "enabled": False},
    # blocat pe GitHub Actions de Cloudflare ("Just a moment...")
    {"module": noriel, "enabled": False},
]

ALL = {entry["module"].NAME: entry["module"] for entry in REGISTRY}
DEFAULT = [entry["module"].NAME for entry in REGISTRY if entry["enabled"]]
