# Entry point Flask application untuk Information Retrieval System.

import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

# Tambahkan root project ke Python path
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

from search.engine import SearchEngine
from routes.search import search_bp, init_engine

# flask init
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["JSON_AS_ASCII"] = False


# init search engine
engine = SearchEngine()

# Parse argumen CLI
force_refresh = "--refresh" in sys.argv
force_rebuild = "--rebuild" in sys.argv

engine.initialize(
    force_refresh=force_refresh,
    force_rebuild=force_rebuild,
)

# Inject engine ke blueprint
init_engine(engine)

# register blueprint
app.register_blueprint(search_bp)


# main route
@app.route("/")
def index():
    """Halaman utama - tampilkan UI search engine."""
    stats = engine.get_stats()
    return render_template("index.html", stats=stats)


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "engine_ready": engine.is_ready,
        "total_documents": len(engine.df) if engine.df is not None else 0,
    })


# run
if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    print(f"\n[START] Server berjalan di: http://127.0.0.1:{port}")
    print(f"   Tekan Ctrl+C untuk menghentikan server.\n")

    app.run(host=host, port=port, debug=debug, use_reloader=False)
