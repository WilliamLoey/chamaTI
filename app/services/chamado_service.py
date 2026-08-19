"""Regras de negócio do ciclo de vida do chamado.

Toda a validação relevante mora aqui — não apenas no front-end. Essa decisão
veio da correção E-04: o teste do Colega 4 mostrou que a validação feita apenas
no navegador era contornável.
"""
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Anexo, Categoria, Chamado, Interacao, Prioridade, Status, Usuario
from app.services.erros import ErroDeNegocio, PermissaoNegada

DESCRICAO_MIN = 10
TITULO_MIN = 5
ANEXO_MAX_BYTES = 5 * 1024 * 1024   # E-03
ITENS_POR_PAGINA = 25               # E-01

STATUS_ABERTO = "Aberto"
STATUS_EM_ATENDIMENTO = "Em atendimento"
STATUS_RESOLVIDO = "Resolvido"
STATUS_CANCELADO = "Cancelado"

# Transições permitidas — impede pular etapas do fluxo (ex.: Aberto → Resolvido)
TRANSICOES = {
    STATUS_ABERTO: {STATUS_EM_ATENDIMENTO, STATUS_CANCELADO},
    STATUS_EM_ATENDIMENTO: {STATUS_RESOLVIDO, STATUS_ABERTO, STATUS_CANCELADO},
    STATUS_RESOLVIDO: {STATUS_ABERTO},          # reabertura
    STATUS_CANCELADO: set(),
}


def _limpar(texto):
    return (texto or "").strip()


def _status(nome):
    st = Status.query.filter_by(nome=nome).first()
    if st is None:
        raise ErroDeNegocio(f"Status '{nome}' não está cadastrado no sistema.")
    return st


def gerar_protocolo():
    """Formato AAAA-NNNNNN, sequencial por ano de abertura."""
    ano = datetime.now(timezone.utc).year
    prefixo = f"{ano}-"
    ultimo = (Chamado.query
              .filter(Chamado.protocolo.like(f"{prefixo}%"))
              .order_by(Chamado.protocolo.desc())
              .first())
    sequencial = int(ultimo.protocolo.split("-")[1]) + 1 if ultimo else 1
    return f"{prefixo}{sequencial:06d}"


# --------------------------------------------------------------------- criação
def validar_dados(titulo, descricao, categoria_id, prioridade_id):
    titulo = _limpar(titulo)
    descricao = _limpar(descricao)   # E-04: trim antes de medir o tamanho

    if len(titulo) < TITULO_MIN:
        raise ErroDeNegocio(
            f"O título deve ter pelo menos {TITULO_MIN} caracteres. "
            "Resuma o problema em uma frase curta.", campo="titulo")
    if len(descricao) < DESCRICAO_MIN:
        raise ErroDeNegocio(
            f"A descrição deve ter pelo menos {DESCRICAO_MIN} caracteres. "
            "Explique o que aconteceu e o que você já tentou.", campo="descricao")
    if not Categoria.query.get(categoria_id or 0):
        raise ErroDeNegocio("Selecione uma categoria válida.", campo="categoria_id")
    if not Prioridade.query.get(prioridade_id or 0):
        raise ErroDeNegocio("Selecione uma prioridade válida.", campo="prioridade_id")
    return titulo, descricao


def validar_anexo(nome_arquivo, tamanho_bytes):
    """E-03: o limite é conferido no servidor, com mensagem explícita."""
    if tamanho_bytes > ANEXO_MAX_BYTES:
        limite_mb = ANEXO_MAX_BYTES // (1024 * 1024)
        atual_mb = round(tamanho_bytes / (1024 * 1024), 1)
        raise ErroDeNegocio(
            f"O arquivo '{nome_arquivo}' tem {atual_mb} MB e o limite é {limite_mb} MB. "
            "Compacte o arquivo ou envie uma imagem menor.", campo="anexo")
    return True


def abrir(solicitante, titulo, descricao, categoria_id, prioridade_id, anexos=None):
    titulo, descricao = validar_dados(titulo, descricao, categoria_id, prioridade_id)

    chamado = Chamado(
        protocolo=gerar_protocolo(),
        titulo=titulo,
        descricao=descricao,
        categoria_id=int(categoria_id),
        prioridade_id=int(prioridade_id),
        status_id=_status(STATUS_ABERTO).id,
        solicitante_id=solicitante.id,
    )
    db.session.add(chamado)
    db.session.flush()

    for nome_arquivo, tamanho in (anexos or []):
        validar_anexo(nome_arquivo, tamanho)
        db.session.add(Anexo(chamado_id=chamado.id, nome_arquivo=nome_arquivo,
                             tamanho_bytes=tamanho))

    registrar(chamado, solicitante, "Chamado aberto pelo solicitante.", tipo="sistema")
    db.session.commit()
    return chamado


def registrar(chamado, autor, mensagem, tipo="comentario"):
    interacao = Interacao(chamado_id=chamado.id, autor_id=autor.id,
                          mensagem=mensagem, tipo=tipo)
    db.session.add(interacao)
    return interacao


def comentar(chamado, autor, mensagem):
    mensagem = _limpar(mensagem)
    if len(mensagem) < 3:
        raise ErroDeNegocio("Escreva um comentário com pelo menos 3 caracteres.",
                            campo="mensagem")
    if not autor.pode_ver_chamado(chamado):
        raise PermissaoNegada("Você não tem acesso a este chamado.")
    interacao = registrar(chamado, autor, mensagem)
    db.session.commit()
    return interacao


# ------------------------------------------------------------------- atribuição
def atribuir(chamado, gestor_ou_tecnico, tecnico):
    if not (gestor_ou_tecnico.eh_gestor or gestor_ou_tecnico.eh_tecnico):
        raise PermissaoNegada("Somente técnicos e gestores podem assumir chamados.")
    if not tecnico or not tecnico.eh_tecnico:
        raise ErroDeNegocio("Selecione um técnico válido.", campo="tecnico_id")
    if chamado.encerrado:
        raise ErroDeNegocio("Este chamado já foi encerrado e não pode ser reatribuído.")

    chamado.tecnico_id = tecnico.id
    if chamado.status.nome == STATUS_ABERTO:
        chamado.status_id = _status(STATUS_EM_ATENDIMENTO).id
    registrar(chamado, gestor_ou_tecnico,
              f"Chamado atribuído a {tecnico.nome}.", tipo="sistema")
    db.session.commit()
    return chamado


def mudar_status(chamado, autor, novo_status, solucao=None):
    atual = chamado.status.nome
    if novo_status == atual:
        raise ErroDeNegocio(f"O chamado já está com o status '{atual}'.")
    if novo_status not in TRANSICOES.get(atual, set()):
        raise ErroDeNegocio(
            f"Não é possível mudar de '{atual}' para '{novo_status}'. "
            "Confira o fluxo de atendimento na documentação.", campo="status")
    if novo_status == STATUS_RESOLVIDO:
        if autor.eh_solicitante:
            raise PermissaoNegada("Somente o técnico responsável ou o gestor pode resolver "
                                  "um chamado.")
        if len(_limpar(solucao)) < DESCRICAO_MIN:
            raise ErroDeNegocio(
                f"Descreva a solução aplicada com pelo menos {DESCRICAO_MIN} caracteres "
                "antes de encerrar o chamado.", campo="solucao")
        chamado.solucao = _limpar(solucao)
        chamado.data_encerramento = datetime.now(timezone.utc)
    if novo_status == STATUS_ABERTO and atual == STATUS_RESOLVIDO:
        chamado.data_encerramento = None
        chamado.solucao = None

    chamado.status_id = _status(novo_status).id
    registrar(chamado, autor, f"Status alterado de '{atual}' para '{novo_status}'.",
              tipo="sistema")
    db.session.commit()
    return chamado


# --------------------------------------------------------------------- consulta
def _fim_do_dia(data):
    """E-02: o filtro passou a incluir o dia final inteiro do intervalo."""
    return datetime.combine(data, time.max).replace(tzinfo=timezone.utc)


def _inicio_do_dia(data):
    return datetime.combine(data, time.min).replace(tzinfo=timezone.utc)


def parse_data(texto):
    texto = _limpar(texto)
    if not texto:
        return None
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ErroDeNegocio("Data inválida. Use o formato dd/mm/aaaa.", campo="data")


def listar(usuario, pagina=1, status_id=None, categoria_id=None, prioridade_id=None,
           busca=None, data_inicio=None, data_fim=None, por_pagina=ITENS_POR_PAGINA):
    """Listagem paginada e filtrada. joinedload evita o N+1 detectado no E-01."""
    consulta = (Chamado.query
                .options(joinedload(Chamado.status),
                         joinedload(Chamado.categoria),
                         joinedload(Chamado.prioridade),
                         joinedload(Chamado.solicitante),
                         joinedload(Chamado.tecnico)))

    if usuario.eh_solicitante:
        consulta = consulta.filter(Chamado.solicitante_id == usuario.id)

    if status_id:
        consulta = consulta.filter(Chamado.status_id == int(status_id))
    if categoria_id:
        consulta = consulta.filter(Chamado.categoria_id == int(categoria_id))
    if prioridade_id:
        consulta = consulta.filter(Chamado.prioridade_id == int(prioridade_id))
    if busca:
        termo = f"%{_limpar(busca)}%"
        consulta = consulta.filter(
            db.or_(Chamado.protocolo.ilike(termo),
                   Chamado.titulo.ilike(termo),
                   Chamado.descricao.ilike(termo)))
    if data_inicio:
        consulta = consulta.filter(Chamado.data_abertura >= _inicio_do_dia(data_inicio))
    if data_fim:
        consulta = consulta.filter(Chamado.data_abertura <= _fim_do_dia(data_fim))

    return (consulta.order_by(Chamado.data_abertura.desc())
            .paginate(page=max(int(pagina or 1), 1), per_page=por_pagina, error_out=False))


def obter(chamado_id, usuario):
    chamado = Chamado.query.get(chamado_id)
    if chamado is None:
        raise ErroDeNegocio("Chamado não encontrado.")
    if not usuario.pode_ver_chamado(chamado):
        raise PermissaoNegada("Você não tem acesso a este chamado.")
    return chamado


def buscar_por_protocolo(protocolo, usuario):
    chamado = Chamado.query.filter_by(protocolo=_limpar(protocolo)).first()
    if chamado is None:
        raise ErroDeNegocio(f"Nenhum chamado encontrado com o protocolo '{protocolo}'.")
    if not usuario.pode_ver_chamado(chamado):
        raise PermissaoNegada("Você não tem acesso a este chamado.")
    return chamado
