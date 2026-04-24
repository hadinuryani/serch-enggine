"""
preprocessing/cleaning
Pipeline preprocessing teks Bahasa Indonesia:
1. Case Folding
2. Cleaning (hapus karakter non-alfabet, URL, angka)
3. Tokenization
4. Stopword Removal (PySastrawi)
5. Stemming (PySastrawi)
6. Penggabungan kembali menjadi string bersih

Digunakan untuk memproses corpus dokumen maupun query user.
"""

import re
import string
from functools import lru_cache
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# init sastrawi
_stemmer_factory = StemmerFactory()
STEMMER = _stemmer_factory.create_stemmer()

_stopword_factory = StopWordRemoverFactory()
STOPWORD_REMOVER = _stopword_factory.create_stop_word_remover()
STOPWORDS = set(_stopword_factory.get_stop_words())

# Tambahan stopword custom
CUSTOM_STOPWORDS = {
    "com", "www", "http", "https", "net", "org", "html", "php",
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "untuk",
    "pada", "dengan", "dalam", "oleh", "juga", "ada", "akan",
    "sudah", "tidak", "bisa", "telah", "saat", "bagi",
    "karena", "lebih", "hingga", "seperti", "antara",
}
STOPWORDS.update(CUSTOM_STOPWORDS)

# Pola regex yang sering digunakan
_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
_NON_ALPHA = re.compile(r"[^a-z\s]")
_MULTI_SPACE = re.compile(r"\s+")

# individual function

def case_fold(text: str) -> str:
    """Ubah semua huruf menjadi lowercase."""
    return text.lower()

def remove_noise(text: str) -> str:
    """Hapus URL, angka, tanda baca, karakter khusus."""
    text = _URL_PATTERN.sub(" ", text)       # Hapus URL
    text = _NON_ALPHA.sub(" ", text)         # Hapus non-alfabet
    text = _MULTI_SPACE.sub(" ", text)       # Normalisasi spasi
    return text.strip()

def tokenize(text: str) -> list[str]:
    """Pisahkan teks menjadi daftar token."""
    return text.split()

def remove_stopwords(tokens: list[str]) -> list[str]:
    """Hapus stopword dari daftar token menggunakan Sastrawi + custom stopwords."""
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

def stem(tokens: list[str]) -> list[str]:
    """Lakukan stemming pada setiap token menggunakan PySastrawi."""
    return [STEMMER.stem(t) for t in tokens]

# main pipeline

def preprocess(text: str, do_stem: bool = True) -> str:
    """
    Full preprocessing pipeline untuk satu string teks.

    Args:
        text: Teks mentah (judul atau konten berita)
        do_stem: Apakah perlu dilakukan stemming (default: True)

    Returns:
        String teks yang sudah bersih dan siap untuk vectorization.

    Pipeline:
        raw text
          → case folding
          → remove noise (URL, angka, special chars)
          → tokenize
          → remove stopwords
          → stemming (opsional)
          → join kembali jadi string
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    text = case_fold(text)
    text = remove_noise(text)
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens)

    if do_stem:
        tokens = stem(tokens)

    return " ".join(tokens)


def preprocess_batch(texts: list[str], do_stem: bool = True, verbose: bool = False) -> list[str]:
    """
    Preprocessing untuk sekumpulan teks (batch processing).

    Args:
        texts: List string teks mentah
        do_stem: Apakah perlu stemming
        verbose: Cetak progress setiap 100 dokumen

    Returns:
        List string teks yang sudah bersih
    """
    results = []
    total = len(texts)
    for i, text in enumerate(texts):
        results.append(preprocess(text, do_stem=do_stem))
        if verbose and (i + 1) % 100 == 0:
            print(f"  Preprocessing: {i + 1}/{total} dokumen selesai...")
    return results


# ===== UNTUK TESTING MANDIRI =====

if __name__ == "__main__":
    contoh_teks = [
        "Presiden Jokowi Resmikan Jalan Tol Baru di Sumatera Utara Senilai Rp 5 Triliun",
        "Tim Nasional Indonesia Berhasil Kalahkan Thailand 2-1 di Kualifikasi Piala Asia",
        "Gempa Bumi 6,5 SR Guncang Sulawesi, BMKG Pastikan Tidak Ada Tsunami",
        "Bank Indonesia Pertahankan Suku Bunga Acuan di Level 6 Persen",
    ]

    print("=" * 60)
    print("DEMO PREPROCESSING PIPELINE")
    print("=" * 60)

    for teks in contoh_teks:
        hasil = preprocess(teks)
        print(f"\nInput  : {teks}")
        print(f"Output : {hasil}")

    print("\n[OK] Preprocessing berhasil!")
