"""
model/bm25_model
Modul untuk membangun dan menggunakan model BM25Okapi.

BM25 (Best Match 25) adalah algoritma ranking berbasis probabilistik yang
merupakan penyempurnaan dari TF-IDF dengan mempertimbangkan:
- Document length normalization
- Term saturation (IDF lebih halus)

Menggunakan library: rank-bm25 (BM25Okapi)
"""

import numpy as np
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi

MODEL_DIR = Path(__file__).parent
BM25_MODEL_PATH = MODEL_DIR / "saved" / "bm25_model.pkl"


class BM25Model:
    """
    Wrapper class untuk BM25Okapi.
    Usage:
        model = BM25Model()
        model.fit(tokenized_corpus)
        scores = model.get_scores(query_tokens)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Inisialisasi BM25Model.
        Args:
            k1: Parameter saturasi TF (default: 1.5)
                - Nilai lebih tinggi = lebih sensitif terhadap frekuensi term
            b: Parameter normalisasi panjang dokumen (default: 0.75)
                - 0 = tidak ada normalisasi, 1 = normalisasi penuh
        """
        self.k1 = k1
        self.b = b
        self.model = None
        self.is_fitted = False
        self._tokenized_corpus = None

    def fit(self, tokenized_corpus: list[list[str]]) -> None:
        """
        Fit BM25 model pada tokenized corpus.
        Args:
            tokenized_corpus: List of list of tokens
                Contoh: [["presiden", "resmikan", "jalan"], ["gempa", "bumi"]]
        """
        print(f"  [BM25] Fitting pada {len(tokenized_corpus)} dokumen...")
        self._tokenized_corpus = tokenized_corpus
        self.model = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)
        self.is_fitted = True

        avg_doc_len = np.mean([len(doc) for doc in tokenized_corpus]) if tokenized_corpus else 0
        print(f"  [BM25] Rata-rata panjang dokumen: {avg_doc_len:.1f} token")

    def get_scores(self, query_tokens: list[str]) -> np.ndarray:
        """
        Hitung BM25 score untuk semua dokumen terhadap query.
        Args:
            query_tokens: List token dari query yang sudah di-preprocess
        Returns:
            Array 1D BM25 scores untuk setiap dokumen
        """
        if not self.is_fitted:
            raise RuntimeError("Model belum di-fit. Panggil fit() terlebih dahulu.")

        if not query_tokens:
            return np.zeros(len(self._tokenized_corpus))

        scores = self.model.get_scores(query_tokens)
        return scores

    def normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Normalisasi BM25 scores ke range [0, 1] untuk dapat digabungkan dengan cosine similarity.
        Args:
            scores: Array BM25 scores mentah

        Returns:
            Array scores yang sudah dinormalisasi ke [0, 1]
        """
        max_score = np.max(scores)
        if max_score == 0:
            return scores
        return scores / max_score

    def get_normalized_scores(self, query_tokens: list[str]) -> np.ndarray:
        """
        Hitung dan normalisasi BM25 scores.
        Args:
            query_tokens: List token query
        Returns:
            Normalized scores dalam range [0, 1]
        """
        raw_scores = self.get_scores(query_tokens)
        return self.normalize_scores(raw_scores)

    def save(self) -> None:
        """Simpan model ke disk."""
        BM25_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(BM25_MODEL_PATH, "wb") as f:
            pickle.dump(self, f)
        print(f"  [BM25] Model disimpan ke {BM25_MODEL_PATH}")

    @classmethod
    def load(cls) -> "BM25Model | None":
        """
        Load model dari disk.
        Returns:
            BM25Model instance atau None jika file tidak ditemukan
        """
        if BM25_MODEL_PATH.exists():
            with open(BM25_MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            print(f"  [BM25] Model di-load dari disk.")
            return model
        return None


def build_bm25_model(tokenized_corpus: list[list[str]], force_rebuild: bool = False) -> BM25Model:
    """
    Build atau load BM25 model.
    Args:
        tokenized_corpus: List of list of tokens
        force_rebuild: Paksa rebuild meskipun model sudah tersimpan
    Returns:
        BM25Model yang sudah di-fit
    """
    if not force_rebuild:
        loaded = BM25Model.load()
        if loaded is not None:
            return loaded

    model = BM25Model()
    model.fit(tokenized_corpus)
    model.save()
    return model


# ===== TESTING =====
if __name__ == "__main__":
    tokenized_sample = [
        ["presiden", "indonesia", "resmikan", "jalan", "tol"],
        ["timnas", "indonesia", "kalahkan", "thailand"],
        ["gempa", "bumi", "guncang", "sulawesi", "bmkg"],
        ["bank", "indonesia", "pertahan", "suku", "bunga"],
        ["banjir", "bandang", "melanda", "jakarta", "ribuan", "rumah"],
    ]

    model = BM25Model()
    model.fit(tokenized_sample)

    query_tokens = ["gempa", "bumi", "indonesia"]
    raw_scores = model.get_scores(query_tokens)
    norm_scores = model.normalize_scores(raw_scores)

    sample_corpus = [
        "presiden indonesia resmikan jalan tol",
        "timnas indonesia kalahkan thailand",
        "gempa bumi guncang sulawesi bmkg",
        "bank indonesia pertahan suku bunga",
        "banjir bandang melanda jakarta ribuan rumah",
    ]

    print("\nBM25 Raw Scores vs Normalized Scores:")
    for doc, raw, norm in zip(sample_corpus, raw_scores, norm_scores):
        print(f"  Raw: {raw:.4f} | Norm: {norm:.4f} | {doc}")
