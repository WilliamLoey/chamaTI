"""Ponto de entrada da aplicação.

Desenvolvimento:  python run.py
Produção (Render): gunicorn "run:app"
"""
import os

from app import create_app
from app.extensions import db

app = create_app()


@app.before_request
def _garantir_banco():
    """Em desenvolvimento com SQLite, cria as tabelas na primeira requisição."""
    if app.config.get("DEBUG") and not getattr(app, "_banco_pronto", False):
        db.create_all()
        app._banco_pronto = True


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=app.config.get("DEBUG", False))
