import argparse
from datetime import datetime, timezone
import os
import sys
import requests

import scrapers

# ------------------------------------
# Config din environment variables
# ------------------------------------

def load_dotenv(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
    """Citește KEY=valoare din .env de lângă script (ex. pe telefon, în Pydroid).

    Variabilele deja setate (ex. secretele din GitHub Actions) au prioritate.
    """
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

load_dotenv()

REQUIRED_ENV = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "RESEND_API_KEY", "NOTIFY_EMAIL"]

# acceptă și URL-ul copiat cu /rest/v1 la final; păstrăm doar baza proiectului
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
if SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL = SUPABASE_URL[: -len("/rest/v1")]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=ignore-duplicates"
}

# ------------------------------------
# Supabase
# ------------------------------------

PAGE_SIZE = 1000  # Supabase întoarce maxim 1000 de rânduri pe cerere

def get_existing_links():
    links = set()
    offset = 0
    while True:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/products?select=link&order=id",
            headers={**HEADERS, "Range": f"{offset}-{offset + PAGE_SIZE - 1}"}
        )
        r.raise_for_status()
        rows = r.json()
        links.update(row["link"] for row in rows)
        if len(rows) < PAGE_SIZE:
            return links
        offset += PAGE_SIZE

def upsert_products(products, chunk_size=500):
    """Inserează produsele noi și actualizează prețul/imaginea/last_seen la cele existente.

    first_seen nu e trimis, deci rămâne data la care produsul a apărut prima dată.
    last_seen primește aceeași oră pentru toată rularea; dashboard-ul o folosește ca să
    marcheze drept indisponibile produsele care n-au mai apărut pe site.
    """
    now = datetime.now(timezone.utc).isoformat()
    rows, seen = [], set()
    for p in products:
        if p["link"] in seen:
            continue
        seen.add(p["link"])
        rows.append({
            "title": p["title"],
            "link": p["link"],
            "price": p["price"],
            "source": p["source"],
            "image_url": p["image_url"],
            "last_seen": now,
        })

    headers = {**HEADERS, "Prefer": "resolution=merge-duplicates,return=minimal"}
    saved = 0
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/products?on_conflict=link",
            headers=headers,
            json=chunk
        )
        if r.status_code in (200, 201, 204):
            saved += len(chunk)
            continue
        print(f"Eroare la salvare în Supabase: {r.status_code} {r.text[:300]}")
        if "42P10" in r.text:
            print("  Coloana link nu are constrângere unique. Rulează o dată în Supabase SQL Editor:")
            print("  alter table products add constraint products_link_key unique (link);")
        r.raise_for_status()
    print(f"Salvate/actualizate în Supabase: {saved}")

# ------------------------------------
# Email
# ------------------------------------

def send_email(new_products):
    if not new_products:
        return

    cards = ""
    for p in new_products:
        source_color = "#0077cc" if p["source"] == "Noriel" else "#cc5500"

        cards += f"""
        <div style="background:#ffffff;border:1px solid #ebebeb;border-radius:12px;padding:16px;margin-bottom:12px;">

            <div style="margin-bottom:6px;">
                <span style="font-size:11px;font-weight:600;color:{source_color};text-transform:uppercase;letter-spacing:0.5px;">
                    {p['source']}
                </span>
            </div>

            <p style="margin:0 0 8px;font-size:14px;font-weight:500;color:#111;line-height:1.4;">
                {p['title']}
            </p>

            <p style="margin:0 0 12px;font-size:16px;font-weight:700;color:#111;">
                {p['price']}
            </p>

            <a href="{p['link']}"
            style="display:inline-block;padding:7px 16px;background:#111;color:#fff;text-decoration:none;border-radius:6px;font-size:12px;font-weight:500;">
                Vezi produs
            </a>

        </div>
        """

    subject_text = f"{len(new_products)} produse noi"
    if len(new_products) == 1:
        subject_text = "1 produs nou"

    html = f"""<!DOCTYPE html>
    <html lang="ro">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
    <body style="margin:0;padding:0;background:#f9f9f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
    <div style="max-width:560px;margin:40px auto;padding:0 16px 40px;">

        <!-- Header -->
        <div style="margin-bottom:24px;">
            <p style="margin:0 0 4px;font-size:12px;font-weight:600;color:#999;text-transform:uppercase;letter-spacing:1px;">Hot Wheels Scraper</p>
            <h1 style="margin:0;font-size:22px;font-weight:700;color:#111;">{subject_text} pe stoc</h1>
        </div>

        <!-- Cards -->
        {cards}

        <!-- Footer -->
        <p style="margin:8px 0 0;font-size:14px;color:#666;">
            Produse detectate automat din Noriel și Smyk
        </p>

    </div>
    </body>
    </html>"""

    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "from": "Hot Wheels Scraper <onboarding@resend.dev>",
            "to": NOTIFY_EMAIL,
            "subject": f"HW Alert • {subject_text}",
            "html": html
        }
    )

    if r.status_code == 200:
        print(f"Email trimis la {NOTIFY_EMAIL}")
    else:
        print(f"Eroare email: {r.text}")

# ------------------------------------
# Main
# ------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Hot Wheels scraper")
    parser.add_argument("--dry-run", action="store_true",
                        help="doar scrape + afișare; nu atinge Supabase și nu trimite email")
    parser.add_argument("--site", action="append", choices=list(scrapers.ALL),
                        help="rulează doar scraperul ăsta (se poate repeta); "
                             f"implicit: {', '.join(scrapers.DEFAULT) or 'niciunul'}")
    parser.add_argument("--max-pages", type=int,
                        help="limitează numărul de pagini per site")
    return parser.parse_args()

def main():
    args = parse_args()
    dry_run = args.dry_run or os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

    existing_links = None
    if dry_run:
        print("*** DRY RUN: nu scrie în Supabase, nu trimite email ***")
        if SUPABASE_URL and SUPABASE_KEY:
            # doar citire, ca să vedem ce produse AR FI noi
            existing_links = get_existing_links()
            print(f"Produse existente în DB: {len(existing_links)}")
    else:
        missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
        if missing:
            sys.exit(f"Lipsesc variabilele de mediu: {', '.join(missing)} (folosește --dry-run pentru test)")
        existing_links = get_existing_links()
        print(f"Produse existente în DB: {len(existing_links)}")

    # ordinea de prioritate: --site, apoi variabila SCRAPERS, apoi cele activate în registry
    env_sites = [s.strip() for s in os.environ.get("SCRAPERS", "").split(",") if s.strip()]
    selected = args.site or env_sites or scrapers.DEFAULT
    unknown = [s for s in selected if s not in scrapers.ALL]
    if unknown:
        sys.exit(f"Scrapere necunoscute: {', '.join(unknown)} (disponibile: {', '.join(scrapers.ALL)})")
    if not selected:
        print("Niciun scraper activat (vezi scrapers/__init__.py).")
        return
    print(f"Scrapere: {', '.join(selected)}")

    all_products = []
    failed_sites = []
    for site_name in selected:
        module = scrapers.ALL[site_name]
        print(f"\n=== {site_name} ===")
        try:
            products = module.scrape(args.max_pages)
            print(f"Total produse {site_name}: {len(products)}")
            all_products.extend(products)
        except Exception as e:
            failed_sites.append(site_name)
            print(f"::warning::{site_name} a eșuat, trec mai departe: {e}")
            resp = getattr(e, "response", None)
            if resp is not None:
                print(f"  server: {resp.headers.get('server')} | cf-ray: {resp.headers.get('cf-ray')}")
                print(f"  răspuns: {resp.text[:300]!r}")

    if dry_run:
        print(f"\nTotal produse găsite: {len(all_products)}")
        for p in all_products[:10]:
            print(f"  [{p['source']}] {p['title']} | {p['price']} | {p['link']}")
        if len(all_products) > 10:
            print(f"  ... și încă {len(all_products) - 10}")
        if existing_links is not None:
            would_be_new = [p for p in all_products if p["link"] not in existing_links]
            print(f"\nAR FI NOI (ar intra în DB și în email): {len(would_be_new)}")
            for p in would_be_new[:30]:
                print(f"  [{p['source']}] {p['title']} | {p['link']}")
            if len(would_be_new) > 30:
                print(f"  ... și încă {len(would_be_new) - 30}")
        if failed_sites:
            print(f"\nSite-uri eșuate: {', '.join(failed_sites)}")
            sys.exit(1)
        return

    new_products = [p for p in all_products if p["link"] not in existing_links]
    print(f"\nProduse noi găsite: {len(new_products)}")

    # toate produsele găsite: cele noi se adaugă, celor existente li se actualizează prețul
    upsert_products(all_products)

    if new_products:
        send_email(new_products)
    else:
        print("Nicio noutate.")

    if failed_sites:
        print(f"\nSite-uri eșuate: {', '.join(failed_sites)}")
        sys.exit(1)

if __name__ == "__main__":
    main()