import { getProducts } from "../lib/supabase";
import ProductGrid from "../components/ProductGrid";
import styles from "./page.module.css";

export const revalidate = 300;

export default async function Home({ searchParams }) {
  const source = searchParams?.source || "all";
  const search = searchParams?.search || "";
  const sort = searchParams?.sort || "created_at";

  let products = [];
  let error = null;

  try {
    products = await getProducts({ source, search, sort });
  } catch (e) {
    error = e.message;
  }

  const norielCount = products.filter((p) => p.source === "Noriel").length;
  const smykCount = products.filter((p) => p.source === "Smyk").length;

  const now = new Date();
  const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const newToday = products.filter(
    (p) => new Date(p.created_at) > oneDayAgo
  ).length;

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div>
            <h1 className={styles.title}>Hot Wheels Tracker</h1>
            <p className={styles.subtitle}>
              Noriel &amp; Smyk — actualizat la 6 ore
            </p>
          </div>
          <div className={styles.stats}>
            <div className={styles.stat}>
              <span className={styles.statValue}>{products.length}</span>
              <span className={styles.statLabel}>total</span>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.stat}>
              <span className={styles.statValue} style={{ color: "var(--accent-new)" }}>
                {newToday}
              </span>
              <span className={styles.statLabel}>azi</span>
            </div>
          </div>
        </div>
      </header>

      {/* Filters */}
      <div className={styles.filtersWrap}>
        <div className={styles.filters}>
          <form className={styles.filterRow} method="get" action="/">
            {/* Source tabs */}
            <div className={styles.tabs}>
              <FilterTab label="Toate" value="all" current={source} count={products.length} />
              <FilterTab label="Noriel" value="Noriel" current={source} count={norielCount} color="var(--accent-noriel)" />
              <FilterTab label="Smyk" value="Smyk" current={source} count={smykCount} color="var(--accent-smyk)" />
            </div>

            {/* Search */}
            <div className={styles.searchWrap}>
              <input
                className={styles.searchInput}
                type="text"
                name="search"
                defaultValue={search}
                placeholder="Caută produs..."
                autoComplete="off"
              />
              {search && (
                <a href={`/?source=${source}&sort=${sort}`} className={styles.clearSearch}>✕</a>
              )}
            </div>

            {/* Sort */}
            <select className={styles.select} name="sort" defaultValue={sort}>
              <option value="created_at">Cele mai noi</option>
              <option value="title">Alfabetic</option>
              <option value="price">Preț</option>
            </select>

            <button type="submit" className={styles.applyBtn}>Aplică</button>
          </form>
        </div>
      </div>

      {/* Content */}
      <main className={styles.main}>
        {error ? (
          <div className={styles.errorBox}>
            <p style={{ color: "#f87171", fontFamily: "var(--font-mono)", fontSize: 13 }}>
              Eroare la încărcare: {error}
            </p>
            <p style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 8 }}>
              Verifică variabilele de mediu NEXT_PUBLIC_SUPABASE_URL și NEXT_PUBLIC_SUPABASE_ANON_KEY.
            </p>
          </div>
        ) : products.length === 0 ? (
          <div className={styles.empty}>
            <p className={styles.emptyIcon}>○</p>
            <p className={styles.emptyText}>Niciun produs găsit</p>
          </div>
        ) : (
          <ProductGrid products={products} />
        )}
      </main>
    </div>
  );
}

function FilterTab({ label, value, current, count, color }) {
  const active = current === value;
  return (
    <a
      href={`/?source=${value}`}
      className={`${active ? "tab-active" : ""}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "6px 14px",
        borderRadius: 999,
        fontSize: 13,
        fontWeight: 500,
        background: active ? (color || "#fff") : "transparent",
        color: active ? (color ? "#fff" : "#0e0e0e") : "var(--text-muted)",
        border: `1px solid ${active ? (color || "#fff") : "var(--border)"}`,
        transition: "all 0.15s",
        whiteSpace: "nowrap",
      }}
    >
      {label}
      <span style={{
        fontSize: 11,
        fontFamily: "var(--font-mono)",
        opacity: 0.7,
      }}>{count}</span>
    </a>
  );
}
