"""Controller de autenticação: cadastro, login e logout."""
from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)

from app.models import Perfil
from app.services import usuario_service
from app.services.erros import ErroDeNegocio

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.get("/cadastro")
def cadastro_form():
    return render_template("auth/cadastro.html", perfis=Perfil.ROTULOS, dados={})


@bp.post("/cadastro")
def cadastro():
    dados = request.form.to_dict()
    try:
        usuario = usuario_service.cadastrar(
            nome=dados.get("nome"),
            email=dados.get("email"),
            senha=dados.get("senha"),
            perfil=dados.get("perfil") or Perfil.SOLICITANTE,
            departamento=dados.get("departamento"),
        )
    except ErroDeNegocio as erro:
        # E-05: a mensagem volta junto com o campo, para destacá-lo na tela
        return render_template("auth/cadastro.html", perfis=Perfil.ROTULOS,
                               dados=dados, erro=erro.mensagem,
                               campo_erro=erro.campo), 400

    session["usuario_id"] = usuario.id
    flash(f"Conta criada. Bem-vindo(a), {usuario.nome}!", "sucesso")
    return redirect(url_for("chamados.listar"))


@bp.get("/login")
def login_form():
    return render_template("auth/login.html", dados={})


@bp.post("/login")
def login():
    dados = request.form.to_dict()
    try:
        usuario = usuario_service.autenticar(dados.get("email"), dados.get("senha"))
    except ErroDeNegocio as erro:
        return render_template("auth/login.html", dados={"email": dados.get("email")},
                               erro=erro.mensagem, campo_erro=erro.campo), 401

    session.clear()
    session["usuario_id"] = usuario.id
    flash(f"Olá, {usuario.nome}.", "sucesso")
    destino = request.args.get("proximo") or url_for("chamados.listar")
    return redirect(destino)


@bp.post("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login_form"))
