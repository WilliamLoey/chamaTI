"""Controle de acesso: usuário da sessão e decoradores de permissão.

A proteção não pode depender de o link estar escondido no menu: a verificação
acontece no servidor, em toda requisição. Esconder a opção é usabilidade;
bloquear no servidor é segurança.
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
                # L-03: dizer QUAL perfil está ativo e QUAL seria necessário.
                # Sem isso, quem tem mais de uma conta (o caso comum de quem
                # administra o sistema) vê "acesso negado" sem entender que o
                # problema é estar logado na conta errada — e a página de erro
                # ainda oferecia atalhos que não existem para o perfil atual.
                exigidos = " ou ".join(Perfil.rotulo(p) for p in perfis)
                return render_template(
                    "erros/403.html",
                    mensagem=(
                        f"Você está conectado como {usuario.nome}, com o perfil "
                        f"{usuario.rotulo_perfil}. Esta área é restrita ao perfil "
                        f"{exigidos}. Se você tem outra conta com essa permissão, "
                        "saia e entre com ela; caso contrário, peça o acesso ao "
                        "gestor da equipe."
                    )), 403
            return view(*args, **kwargs)
        return wrapper
    return decorator


somente_gestor = perfis_permitidos(Perfil.GESTOR)
gestor_ou_tecnico = perfis_permitidos(Perfil.GESTOR, Perfil.TECNICO)
