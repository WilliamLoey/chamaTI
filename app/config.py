"""Configurações da aplicação, separadas por ambiente."""
import os
from pathlib import Path

from app import regras

BASE_DIR = Path(__file__).resolve().parent.parent


def _normalizar_url(url: str) -> str:
    """O Render publica a URL do PostgreSQL com o esquema legado 'postgres://',
    que o SQLAlchemy 2.x não aceita. Normaliza para 'postgresql://'."""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "chave-de-desenvolvimento-troque-em-producao")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # V-02: proteção CSRF em todos os formulários
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # As regras de negócio moram em app/regras.py (fonte única).
    # Expostas aqui apenas para leitura nos templates via config[...].
    # V-08: eram declaradas com @property, o que fazia o Flask guardar o
    # objeto property em vez do número.
    TITULO_MIN = regras.TITULO_MIN
    DESCRICAO_MIN = regras.DESCRICAO_MIN
    ANEXO_MAX_MB = regras.ANEXO_MAX_MB
    ANEXO_MAX_BYTES = regras.ANEXO_MAX_BYTES
    ITENS_POR_PAGINA = regras.ITENS_POR_PAGINA
    SENHA_MIN = regras.SENHA_MIN


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _normalizar_url(
        os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'chamati_dev.db'}"
    )


class TestingConfig(Config):
    TESTING = True
    # Desligado nos testes para que eles exercitem as regras de negócio, e não
    # o mecanismo de token. A proteção em si é verificada em test_seguranca.py,
    # que liga o CSRF explicitamente.
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _normalizar_url(os.environ.get("DATABASE_URL", ""))
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(nome=None):
    nome = nome or os.environ.get("FLASK_ENV", "development")
    return CONFIGS.get(nome, DevelopmentConfig)
