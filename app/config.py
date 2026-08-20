"""Configurações da aplicação, separadas por ambiente."""
import os
from pathlib import Path

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

    # Regras de negócio parametrizáveis
    DESCRICAO_MIN = 10          # E-04: tamanho mínimo da descrição do chamado
    ANEXO_MAX_MB = 5            # E-03: limite de upload
    ITENS_POR_PAGINA = 25       # E-01: paginação da listagem
    SENHA_MIN = 6

    @property
    def ANEXO_MAX_BYTES(self):
        return self.ANEXO_MAX_MB * 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _normalizar_url(
        os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'chamati_dev.db'}"
    )


class TestingConfig(Config):
    TESTING = True
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
