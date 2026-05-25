"use client";

import { useState } from "react";
import styles from "./ProductGrid.module.css";

const ONE_DAY = 24 * 60 * 60 * 1000;

export default function ProductGrid({ products }) {
  const [imgErrors, setImgErrors] = useState({});

  return (
    <>
      <p className={styles.count}>
        {products.length} {products.length === 1 ? "produs" : "produse"}
      </p>
      <div className={styles.grid}>
        {products.map((p) => {
          const isNew = new Date(p.created_at) > new Date(Date.now() - ONE_DAY);
          const isNoriel = p.source === "Noriel";
          const imgFailed = imgErrors[p.id || p.link];

          return (
            <a
              key={p.link}
              href={p.link}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.card}
            >
              {/* Image */}
              <div className={styles.imageWrap}>
                {p.image_url && !imgFailed ? (
                  <img
                    src={p.image_url}
                    alt={p.title}
                    className={styles.image}
                    onError={() =>
                      setImgErrors((prev) => ({ ...prev, [p.id || p.link]: true }))
                    }
                  />
                ) : (
                  <div className={styles.imagePlaceholder}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <rect x="2" y="6" width="20" height="12" rx="3"/>
                      <circle cx="7" cy="16" r="2"/>
                      <circle cx="17" cy="16" r="2"/>
                      <path d="M2 10h20"/>
                      <path d="M7 6l2-3h6l2 3"/>
                    </svg>
                  </div>
                )}
                {isNew && <span className={styles.badgeNew}>nou</span>}
              </div>

              {/* Content */}
              <div className={styles.content}>
                <div className={styles.sourceRow}>
                  <span
                    className={styles.source}
                    style={{
                      color: isNoriel ? "var(--accent-noriel)" : "var(--accent-smyk)",
                    }}
                  >
                    {p.source}
                  </span>
                  {p.created_at && (
                    <span className={styles.date}>
                      {new Date(p.created_at).toLocaleDateString("ro-RO", {
                        day: "numeric",
                        month: "short",
                      })}
                    </span>
                  )}
                </div>
                <p className={styles.title}>{p.title}</p>
                <p className={styles.price}>{p.price !== "N/A" ? p.price : "—"}</p>
              </div>

              {/* Arrow */}
              <div className={styles.arrow}>↗</div>
            </a>
          );
        })}
      </div>
    </>
  );
}
