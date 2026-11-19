from bs4 import BeautifulSoup

from .common import clean_text, raise_empty_page, scrape_paged

NAME = "noriel"
SOURCE = "Noriel"

SEARCH_URL = "https://noriel.ro/catalogsearch/result/index/?p={page}&q=hot+wheels"


def get_total_pages(scraper):
    r = scraper.get(SEARCH_URL.format(page=1))
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    el = soup.select_one("span.toolbar-number")
    if el:
        try:
            return int(el.get_text().split("/")[-1].strip())
        except ValueError:
            return 1
    return 1


def fetch_page(scraper, page=1):
    r = scraper.get(SEARCH_URL.format(page=page))
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
                "title": clean_text(title_el),
                "link": link_el["href"],
                "price": price_el.get_text(strip=True) if price_el else "N/A",
                "source": SOURCE,
                "image_url": img_el["src"] if img_el else None
            })
    if not products:
        raise_empty_page(r, soup, len(soup.select("div.product-item")))
    return products


def scrape(max_pages=None):
    return scrape_paged(get_total_pages, fetch_page, max_pages)
