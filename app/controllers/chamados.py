"""Controller dos chamados: listagem, abertura, detalhe e mudanças de estado."""
import io

from flask import (Blueprint, flash, redirect, render_template, request,
                   send_file, url_for)
from werkzeug.utils import secure_filename

from app.controllers.seguranca import (gestor_ou_tecnico, login_obrigatorio,
                                       usuario_atual)
from app.models import Categoria, Prioridade, Status, Usuario
from app.services import chamado_service, usuario_service
from app.services.erros import ErroDeNegocio, PermissaoNegada

bp = Blueprint("chamados", __name__, url_prefix="/chamados")


def _dominios():
    return {
        "categorias": Categoria.query.filter_by(ativo=True).order_by(Categoria.nome).all(),
        "prioridades": Prioridade.query.order_by(Prioridade.ordem).all(),
        "status_lista": Status.query.order_by(Status.ordem).all(),
    }


@bp.get("/")
@login_obrigatorio
def listar():
    usuario = usuario_atual()
    filtros = {
        "status_id": request.args.get("status_id", type=int),
        "categoria_id": request.args.get("categoria_id", type=int),
        "prioridade_id": request.args.get("prioridade_id", type=int),
        "busca": request.args.get("busca", "").strip(),
        "data_inicio": request.args.get("data_inicio", "").strip(),
        "data_fim": request.args.get("data_fim", "").strip(),
    }
    erro = None
    try:
        inicio = chamado_service.parse_data(filtros["data_inicio"])
        fim = chamado_service.parse_data(filtros["data_fim"])
        if inicio and fim and inicio > fim:
            raise ErroDeNegocio("A data inicial não pode ser posterior à data final.",
                                campo="data_inicio")
    except ErroDeNegocio as e:
        erro, inicio, fim = e.mensagem, None, None

    pagina = chamado_service.listar(
        usuario,
        pagina=request.args.get("pagina", 1, type=int),
        status_id=filtros["status_id"],
        categoria_id=filtros["categoria_id"],
        prioridade_id=filtros["prioridade_id"],
        busca=filtros["busca"],
        data_inicio=inicio,
        data_fim=fim,
    )
    return render_template("chamados/listar.html", pagina=pagina, filtros=filtros,
                           erro=erro, **_dominios())


@bp.get("/novo")
@login_obrigatorio
def novo_form():
    return render_template("chamados/novo.html", dados={}, **_dominios())


@bp.post("/novo")
@login_obrigatorio
def novo():
    dados = request.form.to_dict()
    # V-03: o conteúdo do arquivo passou a ser lido e persistido, em vez de
    # apenas o nome e o tamanho.
    anexos = []
    for arquivo in request.files.getlist("anexo"):
        if not arquivo or not arquivo.filename:
            continue
        anexos.append((secure_filename(arquivo.filename),
                       arquivo.read(),
                       arquivo.mimetype))

    try:
        chamado = chamado_service.abrir(
            solicitante=usuario_atual(),
            titulo=dados.get("titulo"),
            descricao=dados.get("descricao"),
            categoria_id=_int(dados.get("categoria_id")),
            prioridade_id=_int(dados.get("prioridade_id")),
            anexos=anexos,
        )
    except ErroDeNegocio as erro:
        return render_template("chamados/novo.html", dados=dados, erro=erro.mensagem,
                               campo_erro=erro.campo, **_dominios()), 400

    flash(f"Chamado {chamado.protocolo} aberto com sucesso.", "sucesso")
    return redirect(url_for("chamados.detalhe", chamado_id=chamado.id))


def _int(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


@bp.get("/<int:chamado_id>")
@login_obrigatorio
def detalhe(chamado_id):
    try:
        chamado = chamado_service.obter(chamado_id, usuario_atual())
    except PermissaoNegada as erro:
        return render_template("erros/403.html", mensagem=erro.mensagem), 403
    except ErroDeNegocio as erro:
        return render_template("erros/404.html", mensagem=erro.mensagem), 404

    return render_template("chamados/detalhe.html", chamado=chamado,
                           tecnicos=usuario_service.listar_tecnicos(),
                           transicoes=sorted(
                               chamado_service.TRANSICOES.get(chamado.status.nome, set())),
                           **_dominios())


@bp.get("/<int:chamado_id>/anexo/<int:anexo_id>")
@login_obrigatorio
def baixar_anexo(chamado_id, anexo_id):
    """V-03: agora existe de fato o que baixar.

    A permissão é conferida contra o chamado — não basta adivinhar o id do
    anexo para obter o arquivo de outra pessoa.
    """
    try:
        chamado = chamado_service.obter(chamado_id, usuario_atual())
    except PermissaoNegada as erro:
        return render_template("erros/403.html", mensagem=erro.mensagem), 403
    except ErroDeNegocio as erro:
        return render_template("erros/404.html", mensagem=erro.mensagem), 404

    anexo = next((a for a in chamado.anexos if a.id == anexo_id), None)
    if anexo is None:
        return render_template("erros/404.html",
                               mensagem="Anexo não encontrado neste chamado."), 404

    return send_file(io.BytesIO(anexo.conteudo),
                     mimetype=anexo.tipo_mime,
                     as_attachment=True,
                     download_name=anexo.nome_arquivo)


@bp.post("/<int:chamado_id>/comentar")
@login_obrigatorio
def comentar(chamado_id):
    usuario = usuario_atual()
    try:
        chamado = chamado_service.obter(chamado_id, usuario)
        chamado_service.comentar(chamado, usuario, request.form.get("mensagem"))
        flash("Comentário registrado.", "sucesso")
    except PermissaoNegada as erro:
        return render_template("erros/403.html", mensagem=erro.mensagem), 403
    except ErroDeNegocio as erro:
        flash(erro.mensagem, "erro")
    return redirect(url_for("chamados.detalhe", chamado_id=chamado_id))


@bp.post("/<int:chamado_id>/atribuir")
@gestor_ou_tecnico
def atribuir(chamado_id):
    usuario = usuario_atual()
    try:
        chamado = chamado_service.obter(chamado_id, usuario)
        tecnico = Usuario.query.get(_int(request.form.get("tecnico_id")))
        chamado_service.atribuir(chamado, usuario, tecnico)
        flash("Chamado atribuído.", "sucesso")
    except PermissaoNegada as erro:
        return render_template("erros/403.html", mensagem=erro.mensagem), 403
    except ErroDeNegocio as erro:
        flash(erro.mensagem, "erro")
    return redirect(url_for("chamados.detalhe", chamado_id=chamado_id))


@bp.post("/<int:chamado_id>/status")
@login_obrigatorio
def mudar_status(chamado_id):
    usuario = usuario_atual()
    try:
        chamado = chamado_service.obter(chamado_id, usuario)
        chamado_service.mudar_status(chamado, usuario,
                                     request.form.get("status", "").strip(),
                                     solucao=request.form.get("solucao"))
        flash("Status atualizado.", "sucesso")
    except PermissaoNegada as erro:
        return render_template("erros/403.html", mensagem=erro.mensagem), 403
    except ErroDeNegocio as erro:
        flash(erro.mensagem, "erro")
    return redirect(url_for("chamados.detalhe", chamado_id=chamado_id))
