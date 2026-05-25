# 🚗 hw-scraper

Scraper automat pentru Hot Wheels pe noriel.ro și smyk.ro.  
Rulează prin GitHub Actions, salvează în Supabase, trimite notificări pe email.

## Stack
- **Python** — scraping cu cloudscraper + BeautifulSoup
- **GitHub Actions** — cron job la 6h + run manual
- **Supabase** — bază de date PostgreSQL
- **Resend** — email notificări

## Secrets necesare în GitHub

| Secret | Valoare |
|--------|---------|
| `SUPABASE_URL` | URL-ul proiectului Supabase |
| `SUPABASE_SERVICE_KEY` | Service role key |
| `RESEND_API_KEY` | Cheia API Resend |
| `NOTIFY_EMAIL` | Email-ul tău |

## Run manual
GitHub → Actions → Hot Wheels Scraper → Run workflow
