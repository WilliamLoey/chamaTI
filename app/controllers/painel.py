"""Controller do painel de indicadores — restrito ao perfil Gestor."""
from flask import Blueprint, jsonify, render_template

from app.controllers.seguranca import somente_gestor
from app.services import indicadores_service

bp = Blueprint("painel", __name__, url_prefix="/painel")


@bp.get("/")
@somente_gestor
def indicadores():
    return render_template("painel/indicadores.html", dados=indicadores_service.resumo())


@bp.get("/api/indicadores")
@somente_gestor
def api_indicadores():
    """Consumido pelo JavaScript da tela para desenhar os gráficos sem recarregar."""
    return jsonify(indicadores_service.resumo())
