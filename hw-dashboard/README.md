# hw-dashboard

Dashboard Next.js pentru Hot Wheels Tracker — afișează toate produsele din Supabase.

## Setup local

```bash
# 1. Instalează dependențele
npm install

# 2. Creează fișierul de env
cp .env.local.example .env.local
# Completează NEXT_PUBLIC_SUPABASE_URL și NEXT_PUBLIC_SUPABASE_ANON_KEY

# 3. Pornește dev server
npm run dev
# → http://localhost:3000
```

## Deploy pe Vercel

### Prima dată

1. Mergi pe [vercel.com](https://vercel.com) și creează cont cu GitHub
2. Click **Add New → Project**
3. Importă repo-ul cu `hw-dashboard` (sau monorepo-ul întreg dacă l-ai pus acolo)
4. La **Root Directory**, setează `hw-dashboard` dacă e în subfolder
5. La **Environment Variables**, adaugă:
   - `NEXT_PUBLIC_SUPABASE_URL` → URL-ul din Supabase
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` → Anon key din Supabase
6. Click **Deploy**

### Deploy-uri viitoare
Orice `git push` pe `main` → Vercel redeploy automat.

## Structură

```
hw-dashboard/
├── app/
│   ├── layout.js        # Root layout + fonturi
│   ├── page.js          # Pagina principală (Server Component)
│   ├── page.module.css  # Stiluri pagină
│   └── globals.css      # CSS global + variabile
├── components/
│   ├── ProductGrid.js         # Grid de carduri (Client Component)
│   └── ProductGrid.module.css
├── lib/
│   └── supabase.js      # Fetch direct la Supabase REST API
└── next.config.js       # Domenii imagini permise
```

## Funcționalități

- Filtrare după sursă (Noriel / Smyk)
- Căutare după titlu
- Sortare (cele mai noi / alfabetic / preț)
- Badge "nou" pentru produse adăugate în ultimele 24h
- Imagini cu fallback
- Responsive (2 coloane pe mobil)
- Cache de 5 minute (ISR)
