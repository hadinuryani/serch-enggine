"""
data/fetcher
Modul untuk mengambil data berita dari berbagai sumber:
1. NewsAPI (jika API key tersedia)
2. RSS Feed: Kompas, Detik, CNN Indonesia, Tribun, Liputan6

Hasil disimpan ke data/news.csv
"""

import os
import feedparser
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === KONFIGURASI ===
TARGET_ARTICLES = int(os.getenv("TARGET_ARTICLES", 700))
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
DATA_DIR = Path(__file__).parent
OUTPUT_PATH = DATA_DIR / "news.csv"

# RSS Feed sources (Bahasa Indonesia)
RSS_FEEDS = {
    # Kompas.com: RSS langsung sudah tidak aktif, gunakan Google News RSS sebagai pengganti
    "Kompas.com": [
        "https://news.google.com/rss/search?q=site:kompas.com+nasional&hl=id&gl=ID&ceid=ID:id",
        "https://news.google.com/rss/search?q=site:kompas.com+ekonomi&hl=id&gl=ID&ceid=ID:id",
        "https://news.google.com/rss/search?q=site:kompas.com+teknologi&hl=id&gl=ID&ceid=ID:id",
        "https://news.google.com/rss/search?q=site:kompas.com+olahraga&hl=id&gl=ID&ceid=ID:id",
        "https://news.google.com/rss/search?q=site:kompas.com+tren&hl=id&gl=ID&ceid=ID:id",
    ],
    "CNN Indonesia": [
        "https://www.cnnindonesia.com/rss",
        "https://www.cnnindonesia.com/nasional/rss",
        "https://www.cnnindonesia.com/ekonomi/rss",
        "https://www.cnnindonesia.com/teknologi/rss",
        "https://www.cnnindonesia.com/olahraga/rss",
        "https://www.cnnindonesia.com/hiburan/rss",
        "https://www.cnnindonesia.com/internasional/rss",
        "https://www.cnnindonesia.com/gaya-hidup/rss",
    ],
    # Antara News: ekstensi berubah dari .rss menjadi .xml
    "Antara News": [
        "https://www.antaranews.com/rss/terkini.xml",
        "https://www.antaranews.com/rss/top-news.xml",
        "https://www.antaranews.com/rss/politik.xml",
        "https://www.antaranews.com/rss/ekonomi.xml",
        "https://www.antaranews.com/rss/metro.xml",
        "https://www.antaranews.com/rss/olahraga.xml",
        "https://www.antaranews.com/rss/humaniora.xml",
        "https://www.antaranews.com/rss/tekno.xml",
    ],
    # Tribun News: hanya main feed yang aktif, kategori individual sudah 404
    "Tribun News": [
        "https://www.tribunnews.com/rss",
    ],
    "Okezone": [
        "https://sindikasi.okezone.com/index.php/rss/0/RSS2.0",
        "https://sindikasi.okezone.com/index.php/rss/1/RSS2.0",
        "https://sindikasi.okezone.com/index.php/rss/2/RSS2.0",
        "https://sindikasi.okezone.com/index.php/rss/3/RSS2.0",
        "https://sindikasi.okezone.com/index.php/rss/4/RSS2.0",
    ],
    "Tempo": [
        "https://rss.tempo.co/nasional",
        "https://rss.tempo.co/bisnis",
        "https://rss.tempo.co/dunia",
        "https://rss.tempo.co/olahraga",
        "https://rss.tempo.co/gaya-hidup",  # Diperbaiki: gaya_hidup -> gaya-hidup
        "https://rss.tempo.co/otomotif",
    ],
}


def parse_date(entry) -> str:
    """Parse tanggal dari entry RSS, kembalikan string format ISO."""
    for field in ["published_parsed", "updated_parsed"]:
        val = getattr(entry, field, None)
        if val:
            try:
                dt = datetime(*val[:6], tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_content(entry) -> str:
    """Ambil konten/summary dari entry RSS jika tersedia."""
    if hasattr(entry, "content") and entry.content:
        return entry.content[0].get("value", "")
    if hasattr(entry, "summary"):
        return entry.summary or ""
    return ""

# Browser-like headers agar server tidak memblokir request
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.9",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Referer": "https://www.google.com/",
}


def fetch_rss_feed(source_name: str, feed_url: str) -> list[dict]:
    """Ambil artikel dari satu RSS feed URL menggunakan requests + feedparser."""
    articles = []
    try:
        # Gunakan requests dengan browser headers terlebih dahulu
        resp = requests.get(feed_url, headers=_HEADERS, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        # Parse konten XML yang didapat langsung dari response
        feed = feedparser.parse(resp.content)

        if not feed.entries:
            # Fallback: coba parse langsung dengan feedparser
            feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "").strip()
            content = get_content(entry).strip()
            date = parse_date(entry)

            if not title or len(title) < 10:
                continue

            articles.append({
                "title": title,
                "content": content[:1000] if content else title,
                "url": link,
                "date": date,
                "source": source_name,
            })
    except Exception as e:
        print(f"  [WARN] Gagal fetch {feed_url}: {e}")
    return articles

def fetch_all_rss() -> list[dict]:
    """Ambil semua artikel dari seluruh RSS feed."""
    all_articles = []
    for source, urls in RSS_FEEDS.items():
        print(f"  Fetching dari {source}...")
        for url in urls:
            articles = fetch_rss_feed(source, url)
            all_articles.extend(articles)
            print(f"    -> {url}: {len(articles)} artikel")
    return all_articles

def fetch_newsapi(keyword: str = "indonesia", page_size: int = 100, max_pages: int = 5) -> list[dict]:
    """Ambil berita dari NewsAPI jika API key tersedia."""
    if not NEWS_API_KEY or NEWS_API_KEY == "your_newsapi_key_here":
        print("  [INFO] NewsAPI key tidak ditemukan, skip NewsAPI.")
        return []

    articles = []
    for page in range(1, max_pages + 1):
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": keyword,
                "language": "id",
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "page": page,
                "apiKey": NEWS_API_KEY,
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get("status") != "ok":
                print(f"  [WARN] NewsAPI error: {data.get('message', 'Unknown error')}")
                break

            for item in data.get("articles", []):
                title = (item.get("title") or "").strip()
                if not title or title == "[Removed]" or len(title) < 10:
                    continue
                articles.append({
                    "title": title,
                    "content": (item.get("content") or item.get("description") or title)[:1000],
                    "url": item.get("url", ""),
                    "date": item.get("publishedAt", datetime.now().isoformat()),
                    "source": item.get("source", {}).get("name", "NewsAPI"),
                })

            if len(data.get("articles", [])) < page_size:
                break
        except Exception as e:
            print(f"  [WARN] NewsAPI page {page} error: {e}")
            break

    print(f"  NewsAPI: {len(articles)} artikel ditemukan")
    return articles

def deduplicate(articles: list[dict]) -> list[dict]:
    """Hapus artikel duplikat berdasarkan judul."""
    seen_titles = set()
    unique = []
    for art in articles:
        title_key = art["title"].lower().strip()
        if title_key not in seen_titles and len(title_key) >= 10:
            seen_titles.add(title_key)
            unique.append(art)
    return unique

def save_to_csv(articles: list[dict], output_path: Path) -> pd.DataFrame:
    """Simpan daftar artikel ke file CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(articles, columns=["title", "content", "url", "date", "source"])
    df = df.fillna("")
    df.index = range(1, len(df) + 1)
    df.index.name = "id"
    df.to_csv(output_path)
    return df

def fetch_and_save(force_refresh: bool = False) -> pd.DataFrame:
    """
    Pipeline lengkap: fetch data → deduplikasi → simpan ke CSV.
    Args:
        force_refresh: Jika True, akan selalu fetch ulang data meskipun CSV sudah ada.
    Returns:
        DataFrame berisi data berita.
    """
    if not force_refresh and OUTPUT_PATH.exists():
        df = pd.read_csv(OUTPUT_PATH, index_col="id")
        print(f"[INFO] Dataset sudah ada: {len(df)} artikel. Gunakan --refresh untuk update.")
        return df

    print("=" * 60)
    print("  MEMULAI PENGAMBILAN DATA BERITA")
    print("=" * 60)

    # 1. Ambil dari NewsAPI (opsional)
    print("\n[1] Mengambil dari NewsAPI...")
    newsapi_articles = fetch_newsapi(keyword="berita indonesia terbaru", max_pages=5)

    # 2. Ambil dari RSS Feed
    print("\n[2] Mengambil dari RSS Feed...")
    rss_articles = fetch_all_rss()

    # Gabungkan semua artikel
    all_articles = newsapi_articles + rss_articles

    # Deduplikasi
    print(f"\n[3] Total sebelum deduplikasi: {len(all_articles)} artikel")
    unique_articles = deduplicate(all_articles)
    print(f"[4] Total setelah deduplikasi: {len(unique_articles)} artikel")

    if len(unique_articles) < 100:
        print("[WARN] Terlalu sedikit artikel. Coba cek koneksi internet atau RSS feed.")

    # Simpan ke CSV
    df = save_to_csv(unique_articles, OUTPUT_PATH)
    print(f"\n[OK] Dataset disimpan ke: {OUTPUT_PATH}")
    print(f"[OK] Total: {len(df)} artikel dari {df['source'].nunique()} sumber")
    print("=" * 60)

    return df

if __name__ == "__main__":
    import sys
    force = "--refresh" in sys.argv
    df = fetch_and_save(force_refresh=force)
    print(df[["title", "source", "date"]].head(10).to_string())
