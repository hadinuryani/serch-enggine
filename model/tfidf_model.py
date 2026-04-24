"""
model/tfidf_model
Modul untuk membangun dan menggunakan model TF-IDF.

Fitur:
- Fit TfidfVectorizer dari scikit-learn pada corpus
- Transform dokumen dan query menjadi TF-IDF vector
- Menghitung Cosine Similarity antara query vector dan document matrix
- Simpan dan load model menggunakan joblib
"""

import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_DIR = Path(__file__).parent
TFIDF_MODEL_PATH = MODEL_DIR / "saved" / "tfidf_vectorizer.pkl"
TFIDF_MATRIX_PATH = MODEL_DIR / "saved" / "tfidf_matrix.pkl"


class TFIDFModel:
    """
    Wrapper class untuk TF-IDF Vectorizer dan Cosine Similarity.
    
    Usage:
        model = TFIDFModel()
        model.fit(corpus_list)
        scores = model.get_scores(query_preprocessed)
    """

    def __init__(
        self,
        min_df: int = 1,
        max_df: float = 0.95,
        ngram_range: tuple = (1, 2),
        max_features: int = 50000,
    ):
        """
        Inisialisasi TF-IDF Vectorizer.

        Args:
            min_df: Minimum document frequency (abaikan term yang sangat jarang)
            max_df: Maximum document frequency (abaikan term yang terlalu umum)
            ngram_range: Gunakan unigram dan bigram
            max_features: Batas maksimum fitur/vocabulary
        """
        self.vectorizer = TfidfVectorizer(
            min_df=min_df,
            max_df=max_df,
            ngram_range=ngram_range,
            max_features=max_features,
            sublinear_tf=True,  # Gunakan log TF untuk mereduksi dominasi term frekuensi tinggi
        )
        self.tfidf_matrix = None
        self.is_fitted = False

    def fit(self, corpus: list[str]) -> None:
        """
        Fit vectorizer dan buat TF-IDF matrix dari corpus.
        Args:
            corpus: List string teks yang sudah di-preprocessing
        """
        print(f"  [TF-IDF] Fitting pada {len(corpus)} dokumen...")
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_fitted = True
        vocab_size = len(self.vectorizer.vocabulary_)
        print(f"  [TF-IDF] Vocabulary size: {vocab_size:,}")
        print(f"  [TF-IDF] Matrix shape: {self.tfidf_matrix.shape}")

    def transform_query(self, query_preprocessed: str) -> np.ndarray:
        """
        Ubah query (yang sudah di-preprocess) menjadi TF-IDF vector.
        Args:
            query_preprocessed: String query yang sudah bersih

        Returns:
            Sparse matrix representasi TF-IDF dari query
        """
        if not self.is_fitted:
            raise RuntimeError("Model belum di-fit. Panggil fit() terlebih dahulu.")
        return self.vectorizer.transform([query_preprocessed])

    def get_scores(self, query_preprocessed: str) -> np.ndarray:
        """
        Hitung cosine similarity antara query dan semua dokumen.
        Args:
            query_preprocessed: String query yang sudah bersih
        Returns:
            Array 1D cosine similarity scores untuk setiap dokumen
        """
        if not self.is_fitted:
            raise RuntimeError("Model belum di-fit. Panggil fit() terlebih dahulu.")

        query_vector = self.transform_query(query_preprocessed)
        scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        return scores

    def get_feature_names(self) -> list[str]:
        """Kembalikan daftar feature/term dari vocabulary."""
        return self.vectorizer.get_feature_names_out().tolist()

    def save(self) -> None:
        """Simpan model ke disk."""
        TFIDF_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.vectorizer, TFIDF_MODEL_PATH)
        joblib.dump(self.tfidf_matrix, TFIDF_MATRIX_PATH)
        print(f"  [TF-IDF] Model disimpan ke {TFIDF_MODEL_PATH.parent}/")

    def load(self) -> bool:
        """
        Load model dari disk.
        Returns:
            True jika berhasil, False jika file tidak ditemukan
        """
        if TFIDF_MODEL_PATH.exists() and TFIDF_MATRIX_PATH.exists():
            self.vectorizer = joblib.load(TFIDF_MODEL_PATH)
            self.tfidf_matrix = joblib.load(TFIDF_MATRIX_PATH)
            self.is_fitted = True
            print(f"  [TF-IDF] Model di-load dari disk. Shape: {self.tfidf_matrix.shape}")
            return True
        return False


def build_tfidf_model(corpus: list[str], force_rebuild: bool = False) -> TFIDFModel:
    """
    Build atau load TF-IDF model.
    Args:
        corpus: List teks corpus yang sudah di-preprocess
        force_rebuild: Paksa rebuild meskipun model sudah tersimpan
    Returns:
        TFIDFModel yang sudah di-fit
    """
    model = TFIDFModel()

    if not force_rebuild and model.load():
        return model

    model.fit(corpus)
    model.save()
    return model


# ===== TESTING =====
if __name__ == "__main__":
    sample_corpus = [
        "presiden indonesia resmikan jalan tol",
        "timnas indonesia kalahkan thailand dua satu",
        "gempa bumi guncang sulawesi bmkg pastik tsunami",
        "bank indonesia pertahan suku bunga enam persen",
        "banjir bandang melanda jakarta ribuan rumah terendam",
    ]

    model = TFIDFModel()
    model.fit(sample_corpus)

    query = "gempa bumi indonesia"
    scores = model.get_scores(query)

    print("\nCosine Similarity Scores:")
    for i, (doc, score) in enumerate(zip(sample_corpus, scores)):
        print(f"  [{score:.4f}] {doc}")
