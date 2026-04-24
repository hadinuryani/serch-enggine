/**
 * app.js — NewsSearch.id Frontend Logic
 * ======================================
 * Mengelola interaksi UI, fetch ke Flask API, dan render hasil pencarian.
 * Fitur:
 *  - Search form submit & suggestion chips
 *  - Fetch POST /search ke backend
 *  - Keyword highlighting di judul & snippet
 *  - Animasi score bars
 *  - Paginasi dinamis
 *  - Transisi halaman hero ↔ hasil
 */

"use strict";

// ===== ELEMENT REFERENCES =====
const heroSection    = document.getElementById("hero-section");
const resultsSection = document.getElementById("results-section");
const statsSection   = document.getElementById("stats-section");
const howSection     = document.querySelector(".how-section");

const searchForm    = document.getElementById("search-form");
const searchInput   = document.getElementById("search-input");
const searchBtn     = document.getElementById("search-btn");
const methodSelect  = document.getElementById("method-select");
const topNSelect    = document.getElementById("topn-select");

const resultsList   = document.getElementById("results-list");
const resultsTitle  = document.getElementById("results-title");
const resultsTime   = document.getElementById("results-time");
const methodBadges  = document.getElementById("method-badges");
const errorState    = document.getElementById("error-state");
const emptyState    = document.getElementById("empty-state");
const paginationEl  = document.getElementById("pagination");
const btnBack       = document.getElementById("btn-back");
const resultCardTpl = document.getElementById("result-card-template");

// ===== STATE =====
let currentQuery  = "";
let currentPage   = 1;
let currentMethod = "combined";
let currentTopN   = 10;
let isLoading     = false;

// ===== UTILS =====

/**
 * Format angka float menjadi string dengan 4 desimal
 */
function fmt(n) {
  return typeof n === "number" ? n.toFixed(4) : "0.0000";
}

/**
 * Escape karakter regex dalam string
 */
function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Highlight query keywords dalam teks
 */
function highlightKeywords(text, query) {
  if (!query || !text) return text;
  const words = query.trim().split(/\s+/).filter(w => w.length > 2);
  if (!words.length) return text;
  const pattern = new RegExp(`(${words.map(escapeRegex).join("|")})`, "gi");
  return text.replace(pattern, "<mark>$1</mark>");
}

/**
 * Format tanggal menjadi lebih mudah dibaca
 */
function formatDate(dateStr) {
  if (!dateStr || dateStr === "None" || dateStr === "") return "";
  try {
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    return d.toLocaleDateString("id-ID", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}

/**
 * Set loading state tombol search
 */
function setLoading(state) {
  isLoading = state;
  searchBtn.classList.toggle("loading", state);
  searchBtn.disabled = state;
  searchInput.disabled = state;
}

// ===== VIEW TRANSITIONS =====

function showResults() {
  heroSection.hidden    = true;
  statsSection.hidden   = true;
  howSection.hidden     = true;
  resultsSection.hidden = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showHero() {
  heroSection.hidden    = false;
  statsSection.hidden   = false;
  howSection.hidden     = false;
  resultsSection.hidden = true;
  searchInput.value     = "";
  currentQuery = "";
  currentPage  = 1;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ===== CARD BUILDER =====

/**
 * Buat elemen kartu hasil pencarian dari template
 */
function buildResultCard(item, query) {
  const tpl  = resultCardTpl.content.cloneNode(true);
  const card = tpl.querySelector(".result-card");

  // Rank
  card.querySelector(".rank-number").textContent = `#${item.rank}`;

  // Meta
  card.querySelector(".result-source").textContent = item.source || "Tidak diketahui";
  card.querySelector(".result-date").textContent   = formatDate(item.date);

  // Title dengan highlight & link
  const titleEl = card.querySelector(".result-title");
  const linkEl  = card.querySelector(".result-link");
  const highlightedTitle = highlightKeywords(item.title, query);
  linkEl.innerHTML = highlightedTitle;
  if (item.url && item.url !== "" && item.url !== "None") {
    linkEl.href = item.url;
  } else {
    linkEl.removeAttribute("href");
    linkEl.style.cursor = "default";
  }

  // Snippet dengan highlight
  const snippetEl = card.querySelector(".result-snippet");
  const rawSnippet = item.content || item.title;
  snippetEl.innerHTML = highlightKeywords(rawSnippet, query);

  // Scores
  card.querySelector(".score-final-val").textContent = fmt(item.score);
  card.querySelector(".score-tfidf-val").textContent  = fmt(item.tfidf_score);
  card.querySelector(".score-bm25-val").textContent   = fmt(item.bm25_score);

  // Animate score bars after DOM insert
  requestAnimationFrame(() => {
    setTimeout(() => {
      card.querySelector(".score-bar-final").style.width = `${(item.score * 100).toFixed(1)}%`;
      card.querySelector(".score-bar-tfidf").style.width  = `${(item.tfidf_score * 100).toFixed(1)}%`;
      card.querySelector(".score-bar-bm25").style.width   = `${(item.bm25_score * 100).toFixed(1)}%`;
    }, 50);
  });

  return card;
}

// ===== PAGINATION BUILDER =====

function buildPagination(meta) {
  paginationEl.innerHTML = "";
  if (meta.total_pages <= 1) return;

  const { page, total_pages } = meta;

  // Helper: create button
  function btn(label, targetPage, isActive = false, disabled = false, isEllipsis = false) {
    if (isEllipsis) {
      const span = document.createElement("span");
      span.className = "page-ellipsis";
      span.textContent = "…";
      paginationEl.appendChild(span);
      return;
    }
    const b = document.createElement("button");
    b.className = "page-btn" + (isActive ? " active" : "");
    b.textContent = label;
    b.disabled = disabled;
    if (!disabled && !isActive) {
      b.addEventListener("click", () => doSearch(currentQuery, targetPage));
    }
    paginationEl.appendChild(b);
  }

  btn("← Prev", page - 1, false, page <= 1);

  // Page number logic: show max 7 buttons
  const delta = 2;
  const left  = Math.max(2, page - delta);
  const right = Math.min(total_pages - 1, page + delta);

  btn(1, 1, page === 1);
  if (left > 2) btn("", 0, false, false, true);
  for (let i = left; i <= right; i++) btn(i, i, page === i);
  if (right < total_pages - 1) btn("", 0, false, false, true);
  if (total_pages > 1) btn(total_pages, total_pages, page === total_pages);

  btn("Next →", page + 1, false, page >= total_pages);
}

// ===== MAIN SEARCH FUNCTION =====

async function doSearch(query, page = 1) {
  if (!query.trim() || isLoading) return;

  currentQuery  = query.trim();
  currentPage   = page;
  currentMethod = methodSelect.value;
  currentTopN   = parseInt(topNSelect.value, 10);

  setLoading(true);

  try {
    const response = await fetch("/search", {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify({
        query:  currentQuery,
        top_n:  currentTopN,
        page:   currentPage,
        method: currentMethod,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Terjadi kesalahan pada server.");
    }

    renderResults(data);
    showResults();

  } catch (err) {
    console.error("Search error:", err);
    showResults();
    errorState.hidden = false;
    document.getElementById("error-message").textContent = err.message;
    emptyState.hidden   = true;
    resultsList.innerHTML = "";
    paginationEl.innerHTML = "";
  } finally {
    setLoading(false);
  }
}

// ===== RENDER RESULTS =====

function renderResults(data) {
  // Clear states
  errorState.hidden = true;
  emptyState.hidden = true;
  resultsList.innerHTML = "";
  paginationEl.innerHTML = "";

  const results = data.results || [];
  const meta    = {
    total:       data.total       || 0,
    page:        data.page        || 1,
    total_pages: data.total_pages || 1,
    processing_time_ms: data.processing_time_ms || 0,
    method:      data.method      || currentMethod,
  };

  // Update header
  resultsTitle.textContent = `Hasil pencarian: "${data.query}"`;
  resultsTime.textContent  = `${meta.total.toLocaleString("id-ID")} dokumen relevan · ${meta.processing_time_ms} ms · Halaman ${meta.page} dari ${meta.total_pages}`;

  // Method badge
  methodBadges.innerHTML = "";
  const badgeMap = {
    combined: "Gabungan (TF-IDF + BM25)",
    tfidf:    "TF-IDF Cosine",
    bm25:     "BM25 Okapi",
  };
  const badge = document.createElement("span");
  badge.className = `method-badge ${meta.method}`;
  badge.textContent = badgeMap[meta.method] || meta.method;
  methodBadges.appendChild(badge);

  // Empty
  if (results.length === 0) {
    emptyState.hidden = false;
    return;
  }

  // Render cards
  const fragment = document.createDocumentFragment();
  results.forEach(item => {
    fragment.appendChild(buildResultCard(item, data.query));
  });
  resultsList.appendChild(fragment);

  // Pagination
  buildPagination(meta);
}

// ===== EVENT LISTENERS =====

// Form submit
searchForm.addEventListener("submit", e => {
  e.preventDefault();
  const query = searchInput.value.trim();
  if (query) doSearch(query, 1);
});

// Suggestion chips
document.querySelectorAll(".suggestion-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const q = chip.dataset.query;
    searchInput.value = q;
    doSearch(q, 1);
  });
});

// Back button
btnBack.addEventListener("click", () => {
  showHero();
});

// Update search from URL param on load (deep link support)
(function initFromURL() {
  const params = new URLSearchParams(window.location.search);
  const q = params.get("q");
  if (q) {
    searchInput.value = q;
    doSearch(q, 1);
  }
})();

// ===== THEME TOGGLE =====
const themeToggle = document.getElementById("theme-toggle");

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}

function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    setTheme(savedTheme);
  } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
    setTheme('light');
  } else {
    setTheme('dark');
  }
}

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
    setTheme(currentTheme === "light" ? "dark" : "light");
  });
}

// Initialize theme immediately
initTheme();
