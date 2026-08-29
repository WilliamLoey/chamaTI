"""Regras de negócio de usuário: cadastro e autenticação."""
import re

from app import regras
from app.extensions import db
from app.models import Perfil, Usuario
from app.services.erros import ErroDeNegocio, PermissaoNegada

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
SENHA_MIN = regras.SENHA_MIN
NOME_MIN = regras.NOME_MIN


def _limpar(texto):
    return (texto or "").strip()


def validar_cadastro(nome, email, senha, perfil):
    nome = _limpar(nome)
    email = _limpar(email).lower()

    if len(nome) < NOME_MIN:
        raise ErroDeNegocio(
            f"Informe seu nome completo (mínimo de {NOME_MIN} caracteres).", campo="nome")
    if not RE_EMAIL.match(email):
        raise ErroDeNegocio("Informe um e-mail válido, no formato nome@empresa.com.", campo="email")
    if len(senha or "") < SENHA_MIN:
        raise ErroDeNegocio(
            f"A senha deve ter pelo menos {SENHA_MIN} caracteres. "
            "Escolha uma senha mais longa.", campo="senha")
    if perfil not in Perfil.TODOS:
        raise ErroDeNegocio("Perfil inválido. Selecione um perfil da lista.", campo="perfil")
    if Usuario.query.filter_by(email=email).first():
        raise ErroDeNegocio(
            "Já existe uma conta com este e-mail. Faça login ou use outro endereço.",
            campo="email")
    return nome, email


def cadastrar_publico(nome, email, senha, departamento=None):
    """Auto cadastro pela tela pública. Sempre cria perfil Solicitante.

    V-01: até a versão 1.0 o formulário de cadastro deixava o visitante
    escolher o próprio perfil, inclusive Gestor — bastava selecionar a opção
    para obter acesso a todos os chamados da empresa. O perfil deixou de ser
    entrada do usuário; virou decisão administrativa (ver `promover`).
    """
    return _criar(nome, email, senha, Perfil.SOLICITANTE, departamento)


def cadastrar_por_gestor(gestor, nome, email, senha, perfil, departamento=None):
    """Criação de conta com perfil definido — exclusiva do Gestor."""
    if gestor is None or not gestor.eh_gestor:
        raise PermissaoNegada("Somente um gestor pode criar contas de técnico ou gestor.")
    return _criar(nome, email, senha, perfil, departamento)


def _criar(nome, email, senha, perfil, departamento):
    nome, email = validar_cadastro(nome, email, senha, perfil)
    usuario = Usuario(nome=nome, email=email, perfil=perfil,
                      departamento=_limpar(departamento) or None)
    usuario.definir_senha(senha)
    db.session.add(usuario)
    db.session.commit()
    return usuario


def promover(gestor, usuario, novo_perfil):
    """Muda o perfil de uma conta existente. Só o gestor pode."""
    if gestor is None or not gestor.eh_gestor:
        raise PermissaoNegada("Somente um gestor pode alterar perfis de acesso.")
    if novo_perfil not in Perfil.TODOS:
        raise ErroDeNegocio("Perfil inválido.", campo="perfil")
    usuario.perfil = novo_perfil
    db.session.commit()
    return usuario


def autenticar(email, senha):
    usuario = Usuario.query.filter_by(email=_limpar(email).lower()).first()
    # Mensagem propositalmente genérica: não revela se o e-mail existe.
    if not usuario or not usuario.conferir_senha(senha):
        raise ErroDeNegocio("E-mail ou senha incorretos. Verifique os dados e tente novamente.")
    if not usuario.ativo:
        raise ErroDeNegocio("Esta conta está inativa. Procure o gestor da equipe.")
    return usuario


def listar_tecnicos():
    return (Usuario.query
            .filter_by(perfil=Perfil.TECNICO, ativo=True)
            .order_by(Usuario.nome)
            .all())
