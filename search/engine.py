"""
Core Search Engine yang mengintegrasikan semua komponen:
- Data loading
- Preprocessing
- TF-IDF model
- BM25 model
- Score fusion
- Result ranking & pagination
"""

import time
import math
import numpy as np
import pandas as pd
from pathlib import Path
from preprocessing.cleaning import preprocess, preprocess_batch
from model.tfidf_model import TFIDFModel, build_tfidf_model
from model.bm25_model import BM25Model, build_bm25_model
from data.fetcher import fetch_and_save

DATA_PATH = Path(__file__).parent.parent / "data" / "news.csv"

# Bobot untuk combined scoring
TFIDF_WEIGHT = 0.5
BM25_WEIGHT = 0.5


class SearchEngine:
    """
    Mesin pencari utama yang mengintegrasikan TF-IDF dan BM25.

    Attributes:
        df: DataFrame berita mentah
        preprocessed_corpus: List teks yang sudah di-preprocess
        tokenized_corpus: List list token untuk BM25
        tfidf_model: Instance TFIDFModel
        bm25_model: Instance BM25Model
    """

    def __init__(self):
        self.df: pd.DataFrame | None = None
        self.preprocessed_corpus: list[str] = []
        self.tokenized_corpus: list[list[str]] = []
        self.tfidf_model: TFIDFModel | None = None
        self.bm25_model: BM25Model | None = None
        self.is_ready = False

    def load_data(self, force_refresh: bool = False) -> None:
        """Load dataset dari CSV atau ambil dari internet."""
        print("\n[1/4] Memuat dataset...")
        self.df = fetch_and_save(force_refresh=force_refresh)
        
        for col in ["title", "content", "source", "date", "url"]:
            if col not in self.df.columns:
                self.df[col] = ""
        self.df = self.df.fillna("")
        print(f"  Dataset dimuat: {len(self.df)} dokumen dari {self.df['source'].nunique()} sumber")

    def preprocess_corpus(self) -> None:
        """Preprocessing semua dokumen dalam corpus."""
        print("\n[2/4] Preprocessing corpus...")

        # Gabungkan judul + konten untuk representasi dokumen yang lebih kaya
        combined_texts = []
        for _, row in self.df.iterrows():
            title = str(row.get("title", ""))
            content = str(row.get("content", ""))
            # Judul diberi bobot lebih dengan mengulang 2x
            combined = f"{title} {title} {content[:300]}"
            combined_texts.append(combined)

        self.preprocessed_corpus = preprocess_batch(
            combined_texts, do_stem=True, verbose=True
        )
        self.tokenized_corpus = [text.split() for text in self.preprocessed_corpus]
        print(f"  Preprocessing selesai: {len(self.preprocessed_corpus)} dokumen")

    def build_models(self, force_rebuild: bool = False) -> None:
        """Build atau load TF-IDF dan BM25 model."""
        print("\n[3/4] Membangun model...")
        self.tfidf_model = build_tfidf_model(self.preprocessed_corpus, force_rebuild=force_rebuild)
        self.bm25_model = build_bm25_model(self.tokenized_corpus, force_rebuild=force_rebuild)
        print("  Model TF-IDF dan BM25 siap.")

    def initialize(self, force_refresh: bool = False, force_rebuild: bool = False) -> None:
        """
        Inisialisasi penuh search engine.
        Args:
            force_refresh: Ambil ulang data dari internet
            force_rebuild: Rebuild model meskipun sudah tersimpan
        """
        print("\n" + "=" * 60)
        print("  INISIALISASI SEARCH ENGINE ")
        print("=" * 60)

        self.load_data(force_refresh=force_refresh)
        self.preprocess_corpus()
        self.build_models(force_rebuild=force_rebuild or force_refresh)

        self.is_ready = True
        print("\n[4/4] Search engine siap digunakan!")
        print("=" * 60)

    def rebuild(self, force_refresh: bool = True) -> None:
        """Rebuild seluruh pipeline (data + model)."""
        self.initialize(force_refresh=force_refresh, force_rebuild=True)

    def _compute_scores(
        self, query: str, method: str = "combined"
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Hitung skor semua dokumen untuk query.

        Returns:
            tuple: (tfidf_scores, bm25_scores, final_scores)
        """
        # Preprocessing query
        processed_query = preprocess(query, do_stem=True)
        query_tokens = processed_query.split()

        # Hitung TF-IDF cosine similarity
        tfidf_scores = self.tfidf_model.get_scores(processed_query)

        # Hitung BM25 scores (normalized)
        bm25_scores = self.bm25_model.get_normalized_scores(query_tokens)

        # Pilih metode scoring
        if method == "tfidf":
            final_scores = tfidf_scores
        elif method == "bm25":
            final_scores = bm25_scores
        else:  # combined (default)
            final_scores = (TFIDF_WEIGHT * tfidf_scores) + (BM25_WEIGHT * bm25_scores)

        return tfidf_scores, bm25_scores, final_scores

    def search(
        self,
        query: str,
        top_n: int = 10,
        page: int = 1,
        method: str = "combined",
    ) -> tuple[list[dict], dict]:
        """
        Cari dokumen yang relevan dengan query.

        Args:
            query: String query dari user
            top_n: Jumlah hasil per halaman
            page: Nomor halaman
            method: Metode scoring ("combined", "tfidf", "bm25")

        Returns:
            Tuple (results_list, metadata_dict)
        """
        if not self.is_ready:
            raise RuntimeError("Search engine belum diinisialisasi.")

        start_time = time.time()

        tfidf_scores, bm25_scores, final_scores = self._compute_scores(query, method)

        # Sort berdasarkan final score
        sorted_indices = np.argsort(final_scores)[::-1]

        # Filter hanya yang memiliki score > 0
        relevant_indices = [i for i in sorted_indices if final_scores[i] > 0]

        total_results = len(relevant_indices)
        total_pages = max(1, math.ceil(total_results / top_n))
        page = min(page, total_pages)

        # Paginasi
        start_idx = (page - 1) * top_n
        end_idx = start_idx + top_n
        page_indices = relevant_indices[start_idx:end_idx]

        # Format hasil
        results = []
        for rank, idx in enumerate(page_indices, start=start_idx + 1):
            row = self.df.iloc[idx]
            results.append({
                "rank": rank,
                "title": str(row.get("title", "")),
                "content": str(row.get("content", ""))[:200] + "..."
                           if len(str(row.get("content", ""))) > 200
                           else str(row.get("content", "")),
                "source": str(row.get("source", "")),
                "date": str(row.get("date", "")),
                "url": str(row.get("url", "")),
                "score": round(float(final_scores[idx]), 4),
                "tfidf_score": round(float(tfidf_scores[idx]), 4),
                "bm25_score": round(float(bm25_scores[idx]), 4),
            })

        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        meta = {
            "total": total_results,
            "page": page,
            "per_page": top_n,
            "total_pages": total_pages,
            "method": method,
            "processing_time_ms": elapsed_ms,
        }

        return results, meta

    def get_stats(self) -> dict:
        """Kembalikan statistik dataset dan model."""
        if not self.is_ready or self.df is None:
            return {"error": "Engine belum siap."}

        return {
            "total_documents": len(self.df),
            "sources": self.df["source"].value_counts().to_dict(),
            "date_range": {
                "min": str(self.df["date"].min()),
                "max": str(self.df["date"].max()),
            },
            "avg_doc_length": round(
                float(np.mean([len(t) for t in self.tokenized_corpus])), 1
            ),
        }
