from bs4 import BeautifulSoup

from .common import clean_text, raise_empty_page, scrape_paged

NAME = "smyk_html"
SOURCE = "Smyk"

LIST_URL = ("https://smyk.ro/jocuri-si-jucarii/masinute-si-vehicule/masinute,030802.html"
            "?mark=Hot%20Wheels&p={page}")


def get_total_pages(scraper):
    r = scraper.get(LIST_URL.format(page=1))
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    pages = soup.select("ul.pagination li a.pagination__number")
    if pages:
        try:
            return int(pages[-1].get_text(strip=True))
        except ValueError:
            return 1
    return 1


def fetch_page(scraper, page=1):
    r = scraper.get(LIST_URL.format(page=page))
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    products = []
    for item in soup.select("div.complex-product"):
        title_el = item.select_one("div.complex-product__name")
        price_el = item.select_one("span.price--new")
        # unele carduri au un link promo (ex. Black Friday) înaintea celui de produs;
        # luăm doar linkuri spre pagina produsului (/p/...)
        link_el = (item.select_one("a[data-testid='link-wrapper'][href*='/p/']")
                   or item.select_one("a[href*='/p/']"))
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
            "title": clean_text(title_el),
            "price": price,
            "link": link,
            "source": SOURCE,
            "image_url": image_url
        })
    if not products:
        raise_empty_page(r, soup, len(soup.select("div.complex-product")))
    return products


def scrape(max_pages=None):
    return scrape_paged(get_total_pages, fetch_page, max_pages)
