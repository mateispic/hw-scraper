import argparse
import os
import sys
import requests

import scrapers

# ------------------------------------
# Config din environment variables
# ------------------------------------

REQUIRED_ENV = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "RESEND_API_KEY", "NOTIFY_EMAIL"]

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
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

def get_existing_links():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/products?select=link",
        headers=HEADERS
    )
    r.raise_for_status()
    return {row["link"] for row in r.json()}

def insert_products(products):
    if not products:
        return
    inserted = 0
    seen_links = set()
    for p in products:
        if p["link"] in seen_links:
            continue
        seen_links.add(p["link"])
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/products",
            headers=HEADERS,
            json=p
        )
        if r.status_code in (200, 201):
            inserted += 1
        elif r.status_code == 409:
            pass  # link deja existent, ignorăm
        else:
            print(f"Eroare la inserare {p['link']}: {r.status_code}")
    print(f"Inserate în Supabase: {inserted}")

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

    if dry_run:
        print("*** DRY RUN: fără Supabase, fără email ***")
        existing_links = set()
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
        if failed_sites:
            print(f"\nSite-uri eșuate: {', '.join(failed_sites)}")
            sys.exit(1)
        return

    new_products = [p for p in all_products if p["link"] not in existing_links]
    print(f"\nProduse noi găsite: {len(new_products)}")

    if new_products:
        insert_products(new_products)
        print(f"Salvate în Supabase: {len(new_products)}")
        send_email(new_products)
    else:
        print("Nicio noutate.")

    if failed_sites:
        print(f"\nSite-uri eșuate: {', '.join(failed_sites)}")
        sys.exit(1)

if __name__ == "__main__":
    main()