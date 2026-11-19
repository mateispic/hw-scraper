import cloudscraper


def new_scraper():
    """Sesiune HTTP nouă; fiecare scraper o primește pe a lui."""
    return cloudscraper.create_scraper(browser={
        "browser": "chrome",
        "platform": "windows",
        "mobile": False
    })


def clean_text(el):
    """Text dintr-un element HTML, cu spațiile și rândurile noi strânse."""
    return " ".join(el.get_text(" ", strip=True).split())


def raise_empty_page(r, soup, cards_found):
    """Pagina a venit cu 200 dar fără produse: probabil blocare, redirect sau HTML schimbat."""
    title = soup.title.get_text(strip=True) if soup.title else None
    print(f"  0 produse | status: {r.status_code} | url final: {r.url}")
    print(f"  titlu pagină: {title!r} | carduri găsite: {cards_found} | server: {r.headers.get('server')}")
    if r.history:
        print(f"  redirecturi: {' -> '.join(h.headers.get('location', '?') for h in r.history)}")
    print(f"  început HTML: {r.text[:300]!r}")
    raise RuntimeError("0 produse pe pagină (vezi detaliile de mai sus)")


def scrape_paged(get_total_pages, fetch_page, max_pages=None):
    """Pentru scraperele HTML cu paginare: află nr. de pagini, apoi le ia pe rând."""
    scraper = new_scraper()
    total_pages = get_total_pages(scraper)
    print(f"Pagini găsite: {total_pages}")
    if max_pages:
        total_pages = min(total_pages, max_pages)

    products = []
    for page in range(1, total_pages + 1):
        print(f"Pagina {page}...")
        products.extend(fetch_page(scraper, page))
    return products
