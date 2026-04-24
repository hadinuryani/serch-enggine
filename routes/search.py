"""
Endpoint:
- POST /search  → menerima query, kembalikan hasil ranking
- GET  /stats   → informasi tentang dataset dan model
"""

from flask import Blueprint, request, jsonify
from search.engine import SearchEngine

search_bp = Blueprint("search", __name__)

# Engine di-inject dari app.py saat inisialisasi
_engine: SearchEngine | None = None


def init_engine(engine: "SearchEngine") -> None:
    """Set search engine instance yang akan digunakan blueprint."""
    global _engine
    _engine = engine


@search_bp.route("/search", methods=["POST"])
def search():
    """
    POST /search
    
    Request body (JSON):
        {
            "query": "kata kunci pencarian",
            "top_n": 10,           // opsional, default 10
            "page": 1,             // opsional, default 1
            "method": "combined"   // opsional: "combined"|"tfidf"|"bm25"
        }
    
    Response (JSON):
        {
            "query": "...",
            "results": [
                {
                    "rank": 1,
                    "title": "...",
                    "content": "...",
                    "source": "...",
                    "date": "...",
                    "url": "...",
                    "score": 0.87,
                    "tfidf_score": 0.75,
                    "bm25_score": 0.99
                }
            ],
            "total": 500,
            "page": 1,
            "per_page": 10,
            "total_pages": 50,
            "processing_time_ms": 45
        }
    """
    if _engine is None:
        return jsonify({"error": "Search engine belum diinisialisasi."}), 503

    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    top_n = int(data.get("top_n", 10))
    page = max(1, int(data.get("page", 1)))
    method = data.get("method", "combined")

    if not query:
        return jsonify({"error": "Query tidak boleh kosong."}), 400

    if top_n < 1 or top_n > 100:
        top_n = 10

    try:
        results, meta = _engine.search(
            query=query,
            top_n=top_n,
            page=page,
            method=method,
        )
        return jsonify({
            "query": query,
            "results": results,
            **meta,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@search_bp.route("/stats", methods=["GET"])
def stats():
    """
    GET /stats
    
    Response:
        {
            "total_documents": 700,
            "sources": ["Kompas.com", "CNN Indonesia", ...],
            "date_range": {"min": "...", "max": "..."}
        }
    """
    if _engine is None:
        return jsonify({"error": "Search engine belum diinisialisasi."}), 503

    info = _engine.get_stats()
    return jsonify(info)


@search_bp.route("/refresh", methods=["POST"])
def refresh():
    """
    POST /refresh
    Trigger pengambilan data baru dan rebuild model.
    """
    if _engine is None:
        return jsonify({"error": "Search engine belum diinisialisasi."}), 503

    try:
        _engine.rebuild(force_refresh=True)
        return jsonify({"message": "Dataset dan model berhasil diperbarui."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
