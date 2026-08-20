"""Controle de acesso: usuário da sessão e decoradores de permissão.

E-04 do laudo (Colega 4) originou o reforço aqui: a proteção não pode depender
de o link estar escondido no menu — a verificação acontece no servidor, em toda
requisição.
"""
from functools import wraps

from flask import flash, g, redirect, request, session, url_for

from app.models import Perfil, Usuario


def usuario_atual():
    if "usuario" not in g:
        usuario_id = session.get("usuario_id")
        g.usuario = Usuario.query.get(usuario_id) if usuario_id else None
    return g.usuario


def login_obrigatorio(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if usuario_atual() is None:
            flash("Faça login para continuar.", "info")
            return redirect(url_for("auth.login_form", proximo=request.path))
        return view(*args, **kwargs)
    return wrapper


def perfis_permitidos(*perfis):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            usuario = usuario_atual()
            if usuario is None:
                flash("Faça login para continuar.", "info")
                return redirect(url_for("auth.login_form", proximo=request.path))
            if usuario.perfil not in perfis:
                from flask import render_template
                return render_template(
                    "erros/403.html",
                    mensagem="Esta área é restrita e o seu perfil não tem acesso a ela. "
                             "Se você precisa dessa permissão, fale com o gestor da equipe."), 403
            return view(*args, **kwargs)
        return wrapper
    return decorator


somente_gestor = perfis_permitidos(Perfil.GESTOR)
gestor_ou_tecnico = perfis_permitidos(Perfil.GESTOR, Perfil.TECNICO)
