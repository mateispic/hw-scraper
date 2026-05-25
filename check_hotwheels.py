import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
import os
import requests

# ------------------------------------
# Config din environment variables
# ------------------------------------

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
NOTIFY_EMAIL = os.environ["NOTIFY_EMAIL"]

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
# Noriel
# ------------------------------------

def get_total_pages_noriel(scraper):
    url = "https://noriel.ro/catalogsearch/result/index/?p=1&q=hot+wheels"
    r = scraper.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    el = soup.select_one("span.toolbar-number")
    if el:
        try:
            return int(el.get_text().split("/")[-1].strip())
        except:
            return 1
    return 1

def fetch_noriel(scraper, page=1):
    url = f"https://noriel.ro/catalogsearch/result/index/?p={page}&q=hot+wheels"
    r = scraper.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    products = []
    for item in soup.select("div.product-item"):
        title_el = item.select_one("h2.product-item-name")
        link_el = item.select_one("a[href]")
        price_el = item.select_one("span.price")
        img_el = item.select_one("img.product-image-photo")
        if title_el and link_el:
            products.append({
                "title": title_el.get_text(strip=True),
                "link": link_el["href"],
                "price": price_el.get_text(strip=True) if price_el else "N/A",
                "source": "Noriel",
                "image_url": img_el["src"] if img_el else None
            })
    return products

# ------------------------------------
# Smyk
# ------------------------------------

def get_total_pages_smyk(scraper):
    url = "https://smyk.ro/jocuri-si-jucarii/masinute-si-vehicule/masinute,030802.html?mark=Hot%20Wheels&p=1"
    r = scraper.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    pages = soup.select("ul.pagination li a.pagination__number")
    if pages:
        try:
            return int(pages[-1].get_text(strip=True))
        except:
            return 1
    return 1

def fetch_smyk(scraper, page=1):
    url = f"https://smyk.ro/jocuri-si-jucarii/masinute-si-vehicule/masinute,030802.html?mark=Hot%20Wheels&p={page}"
    r = scraper.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    products = []
    for item in soup.select("div.complex-product"):
        title_el = item.select_one("div.complex-product__name")
        price_el = item.select_one("span.price--new")
        link_el = item.select_one("a[data-testid='link-wrapper'][href]")
        img_el = item.select_one("img[data-src]") or item.select_one("img[src]")
        if not title_el or not link_el:
            continue
        link = link_el["href"]
        if link.startswith("/"):
            link = "https://smyk.ro" + link
        price = price_el.get_text(strip=True).replace("Lei", "").strip() if price_el else "N/A"
        image_url = None
        if img_el:
            image_url = img_el.get("data-src") or img_el.get("src")
        products.append({
            "title": title_el.get_text(strip=True),
            "price": price,
            "link": link,
            "source": "Smyk",
            "image_url": image_url
        })
    return products

# ------------------------------------
# Main
# ------------------------------------

def scrape_site(scraper, fetch_func, get_pages_func, site_name):
    print(f"\n=== {site_name} ===")
    total_pages = get_pages_func(scraper)
    print(f"Pagini găsite: {total_pages}")

    products = []
    for page in range(1, total_pages + 1):
        print(f"Pagina {page}...")
        products.extend(fetch_func(scraper, page))

    print(f"Total produse {site_name}: {len(products)}")
    return products

def main():
    scraper = cloudscraper.create_scraper(browser={
        "browser": "chrome",
        "platform": "windows",
        "mobile": False
    })

    existing_links = get_existing_links()
    print(f"Produse existente în DB: {len(existing_links)}")

    all_products = []
    all_products.extend(scrape_site(scraper, fetch_noriel, get_total_pages_noriel, "Noriel"))
    all_products.extend(scrape_site(scraper, fetch_smyk, get_total_pages_smyk, "Smyk"))

    new_products = [p for p in all_products if p["link"] not in existing_links]
    print(f"\nProduse noi găsite: {len(new_products)}")

    if new_products:
        insert_products(new_products)
        print(f"Salvate în Supabase: {len(new_products)}")
        send_email(new_products)
    else:
        print("Nicio noutate.")

if __name__ == "__main__":
    main()