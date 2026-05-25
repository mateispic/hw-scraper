// lib/supabase.js
// Fetch-uri directe către Supabase REST API — fără SDK, zero dependențe extra.

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export async function getProducts({ source, search, sort = "created_at", order = "desc" } = {}) {
  const params = new URLSearchParams();
  params.set("select", "*");
  params.set("order", `${sort}.${order}`);

  if (source && source !== "all") {
    params.set("source", `eq.${source}`);
  }
  if (search) {
    params.set("title", `ilike.*${search}*`);
  }

  const res = await fetch(
    `${SUPABASE_URL}/rest/v1/products?${params.toString()}`,
    {
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`,
      },
      next: { revalidate: 300 }, // cache 5 minute
    }
  );

  if (!res.ok) throw new Error(`Supabase error: ${res.status}`);
  return res.json();
}
