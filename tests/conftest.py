"""Fixtures compartilhadas. Cada teste roda contra um banco SQLite em memória,
criado e destruído a cada função — testes independentes entre si."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app                      # noqa: E402
from app.extensions import db as _db            # noqa: E402
from app.models import Categoria, Perfil, Prioridade, Status, Usuario  # noqa: E402


@pytest.fixture
def app():
    aplicacao = create_app("testing")
    with aplicacao.app_context():
        _db.create_all()
        _criar_dominios()
        yield aplicacao
        _db.session.remove()
        _db.drop_all()


def _criar_dominios():
    for nome, descricao in [("Hardware", "Equipamentos"), ("Software", "Aplicativos")]:
        _db.session.add(Categoria(nome=nome, descricao=descricao))
    for nome, sla, ordem in [("Baixa", 72, 1), ("Média", 24, 2), ("Alta", 8, 3)]:
        _db.session.add(Prioridade(nome=nome, sla_horas=sla, ordem=ordem))
    for nome, encerra, ordem in [("Aberto", False, 1), ("Em atendimento", False, 2),
                                 ("Resolvido", True, 3), ("Cancelado", True, 4)]:
        _db.session.add(Status(nome=nome, encerra=encerra, ordem=ordem))
    _db.session.commit()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def client(app):
    return app.test_client()


def _novo_usuario(nome, email, perfil):
    usuario = Usuario(nome=nome, email=email, perfil=perfil)
    usuario.definir_senha("senha123")
    _db.session.add(usuario)
    _db.session.commit()
    return usuario


@pytest.fixture
def solicitante(app):
    return _novo_usuario("Diego Souza", "diego@teste.dev", Perfil.SOLICITANTE)


@pytest.fixture
def outro_solicitante(app):
    return _novo_usuario("Elisa Prado", "elisa@teste.dev", Perfil.SOLICITANTE)


@pytest.fixture
def tecnico(app):
    return _novo_usuario("Bruno Carvalho", "bruno@teste.dev", Perfil.TECNICO)


@pytest.fixture
def gestor(app):
    return _novo_usuario("Ana Ribeiro", "ana@teste.dev", Perfil.GESTOR)


@pytest.fixture
def categoria(app):
    return Categoria.query.first()


@pytest.fixture
def prioridade(app):
    return Prioridade.query.filter_by(nome="Média").first()


@pytest.fixture
def autenticar(client):
    """Faz login pelo formulário, exercitando o fluxo real de autenticação."""
    def _login(email, senha="senha123"):
        return client.post("/auth/login", data={"email": email, "senha": senha},
                           follow_redirects=True)
    return _login
