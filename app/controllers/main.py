"""Rotas gerais: página inicial, busca por protocolo e verificação de saúde."""
from flask import Blueprint, redirect, render_template, request, url_for

from app.controllers.seguranca import login_obrigatorio, usuario_atual
from app.services import chamado_service
from app.services.erros import ErroDeNegocio, PermissaoNegada

bp = Blueprint("main", __name__)


@bp.get("/")
def inicio():
    if usuario_atual():
        return redirect(url_for("chamados.listar"))
    return render_template("inicio.html")


@bp.get("/buscar")
@login_obrigatorio
def buscar():
    protocolo = request.args.get("protocolo", "").strip()
    try:
        chamado = chamado_service.buscar_por_protocolo(protocolo, usuario_atual())
    except PermissaoNegada as erro:
        return render_template("erros/403.html", mensagem=erro.mensagem), 403
    except ErroDeNegocio as erro:
        return render_template("erros/404.html", mensagem=erro.mensagem), 404
    return redirect(url_for("chamados.detalhe", chamado_id=chamado.id))


@bp.get("/health")
def health():
    """Endpoint usado pelo Render para verificar se a aplicação está no ar."""
    return {"status": "ok"}, 200
