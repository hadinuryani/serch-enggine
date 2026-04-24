# 📰 NewsSearch.id — Information Retrieval System

Sistem temu kembali informasi berbasis web untuk pencarian berita Indonesia menggunakan **TF-IDF**, **BM25 Okapi**, dan **Cosine Similarity**.

---

## 🏗️ Struktur Proyek

```
serch-enggine-v2/
├── data/
│   ├── __init__.py
│   ├── fetcher.py          # Ambil berita dari NewsAPI + RSS Feed
│   └── news.csv            # Dataset hasil scraping (auto-generated)
│
├── preprocessing/
│   ├── __init__.py
│   └── cleaning.py         # Pipeline preprocessing Bahasa Indonesia
│
├── model/
│   ├── __init__.py
│   ├── tfidf_model.py      # TF-IDF Vectorizer + Cosine Similarity
│   ├── bm25_model.py       # BM25Okapi model
│   └── saved/              # Model tersimpan (auto-generated)
│
├── routes/
│   ├── __init__.py
│   └── search.py           # Flask Blueprint endpoint /search
│
├── search/
│   ├── __init__.py
│   └── engine.py           # Core search engine (score fusion)
│
├── templates/
│   └── index.html          # Frontend HTML
│
├── static/
│   ├── style.css           # Dark theme CSS
│   └── app.js              # Frontend JavaScript
│
├── app.py                  # Entry point Flask
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Cara Install & Run

### 1. Clone / Masuk ke Direktori Proyek

```bash
cd "d:\kuliah\Matkul\semester_4\temu kembali informasi\serch-enggine-v2"
```

### 2. Buat Virtual Environment (Direkomendasikan)

```bash
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment (Opsional)

```bash
copy .env.example .env
# Edit .env dan isi NEWS_API_KEY jika Anda punya
```

> **Catatan**: Jika tidak ada NewsAPI key, sistem akan otomatis menggunakan RSS Feed dari:
> Kompas, CNN Indonesia, Detik, Liputan6, Tribun News, Antara News

### 5. Jalankan Aplikasi

```bash
# Run pertama kali (akan otomatis fetch data + build model)
python app.py

# Force refresh data dari internet
python app.py --refresh

# Force rebuild model setelah data diperbarui
python app.py --rebuild
```

### 6. Buka di Browser

```
http://localhost:5000
```

---

## 🔍 Cara Penggunaan

### Via Web UI

1. Buka `http://localhost:5000`
2. Ketik kata kunci di search box (contoh: `banjir jakarta`)
3. Pilih metode pencarian: **Gabungan**, **TF-IDF**, atau **BM25**
4. Pilih jumlah hasil per halaman
5. Klik **Cari** atau tekan Enter

### Via API (cURL)

```bash
# Search dengan metode gabungan
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "gempa bumi sulawesi", "top_n": 5, "method": "combined"}'

# Lihat statistik dataset
curl http://localhost:5000/stats

# Refresh data dari internet
curl -X POST http://localhost:5000/refresh
```

### Contoh Response JSON

```json
{
  "query": "gempa bumi sulawesi",
  "results": [
    {
      "rank": 1,
      "title": "Gempa 6.5 SR Guncang Sulawesi Tengah, Warga Panik...",
      "content": "Badan Meteorologi Klimatologi dan Geofisika (BMKG)...",
      "source": "Kompas.com",
      "date": "2024-04-20 08:30:00",
      "url": "https://kompas.com/...",
      "score": 0.8734,
      "tfidf_score": 0.7921,
      "bm25_score": 0.9546
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 10,
  "total_pages": 2,
  "method": "combined",
  "processing_time_ms": 43.2
}
```

---

## 📊 Pipeline Sistem

```
RSS Feed / NewsAPI
      ↓
  data/fetcher.py          → data/news.csv  (≥500 artikel)
      ↓
preprocessing/cleaning.py  → case fold → tokenize → stopword → stem
      ↓
model/tfidf_model.py       → TF-IDF Matrix + Cosine Similarity
model/bm25_model.py        → BM25Okapi scoring
      ↓
search/engine.py           → Score Fusion (0.5 × cosine + 0.5 × BM25)
      ↓
routes/search.py           → Flask API POST /search
      ↓
static/app.js              → Fetch API → Render hasil ke UI
```

---

## 🧠 Penjelasan Metode

### TF-IDF (Term Frequency–Inverse Document Frequency)
- **TF** = frekuensi term dalam dokumen / total term dokumen
- **IDF** = log(N / df(t)) — semakin jarang term, semakin tinggi bobot
- **Cosine Similarity** = dot product antara vektor query & dokumen yang dinormalisasi
- Implementasi: `sklearn.TfidfVectorizer` + `cosine_similarity`

### BM25 Okapi
- Penyempurnaan TF-IDF dengan penambahan:
  - **k1** (saturasi TF): term yang muncul 10x bukan 10× lebih penting dari term yang muncul 1x
  - **b** (normalisasi panjang dokumen): dokumen panjang tidak selalu lebih relevan
- Formula: `BM25(d,q) = Σ IDF(t) × [TF(t,d) × (k1+1)] / [TF(t,d) + k1×(1−b+b×|d|/avgdl)]`
- Implementasi: `rank_bm25.BM25Okapi`

### Score Fusion
```
final_score = (0.5 × cosine_similarity) + (0.5 × bm25_normalized)
```
BM25 dinormalisasi ke [0,1] sebelum digabungkan.

---

## 📦 Sumber Data

| Sumber | URL RSS |
|--------|---------|
| Kompas.com | rss.kompas.com |
| CNN Indonesia | cnnindonesia.com/rss |
| Detik.com | rss.detik.com |
| Liputan6 | liputan6.com/rss |
| Tribun News | tribunnews.com/rss |
| Antara News | antaranews.com/rss |

---

## 🚀 Fitur Bonus

- ✅ **Paginasi** — navigasi halaman hasil pencarian
- ✅ **Keyword Highlighting** — kata kunci di-highlight pada judul & snippet
- ✅ **Filter Metode** — pilih TF-IDF, BM25, atau Gabungan
- ✅ **Score Visualization** — progress bar untuk setiap skor
- ✅ **Stats Dashboard** — informasi dataset di halaman utama
- ✅ **Deep Link** — dukung `?q=query` di URL
- ✅ **Refresh Endpoint** — update data tanpa restart server

---

## 📋 Requirements

```
Flask==3.0.3
pandas==2.2.2
scikit-learn==1.5.0
PySastrawi==1.2.0
rank-bm25==0.2.2
requests==2.32.3
feedparser==6.0.11
python-dotenv==1.0.1
numpy==1.26.4
joblib (bundled dengan scikit-learn)
```
