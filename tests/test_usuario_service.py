"""Testes unitários das regras de cadastro e autenticação."""
import pytest

from app.models import Perfil, Usuario
from app.services import usuario_service
from app.services.erros import ErroDeNegocio


def test_cadastro_valido_cria_usuario_com_senha_criptografada(app):
    usuario = usuario_service.cadastrar_publico("Maria Silva", "Maria@Teste.dev ", "senha123")

    assert usuario.id is not None
    assert usuario.email == "maria@teste.dev"          # normalizado para minúsculas
    assert usuario.senha_hash != "senha123"            # nunca em texto puro
    assert usuario.conferir_senha("senha123") is True


def test_cadastro_recusa_email_invalido(app):
    with pytest.raises(ErroDeNegocio) as excecao:
        usuario_service.cadastrar_publico("Maria Silva", "maria-sem-arroba", "senha123")
    assert excecao.value.campo == "email"


def test_cadastro_recusa_senha_curta(app):
    with pytest.raises(ErroDeNegocio) as excecao:
        usuario_service.cadastrar_publico("Maria Silva", "maria@teste.dev", "123")
    assert excecao.value.campo == "senha"


def test_cadastro_recusa_email_duplicado(app, solicitante):
    with pytest.raises(ErroDeNegocio) as excecao:
        usuario_service.cadastrar_publico("Outro Nome", solicitante.email, "senha123")
    assert excecao.value.campo == "email"


def test_autenticacao_com_senha_correta(app, solicitante):
    assert usuario_service.autenticar(solicitante.email, "senha123").id == solicitante.id


def test_autenticacao_com_senha_errada_falha(app, solicitante):
    with pytest.raises(ErroDeNegocio):
        usuario_service.autenticar(solicitante.email, "senha-errada")


def test_autenticacao_de_conta_inativa_falha(app, db, solicitante):
    solicitante.ativo = False
    db.session.commit()
    with pytest.raises(ErroDeNegocio, match="inativa"):
        usuario_service.autenticar(solicitante.email, "senha123")


def test_listar_tecnicos_traz_apenas_perfil_tecnico(app, tecnico, gestor, solicitante):
    tecnicos = usuario_service.listar_tecnicos()
    assert [t.id for t in tecnicos] == [tecnico.id]
