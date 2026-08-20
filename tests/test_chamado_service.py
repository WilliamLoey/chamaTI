"""Testes das regras de negócio do chamado.

Vários testes aqui são de regressão: nasceram de defeitos encontrados pelos
colegas testadores e registrados no laudo de qualidade (E-01 a E-05).
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db as _db
from app.models import Chamado, Status
from app.services import chamado_service
from app.services.erros import ErroDeNegocio, PermissaoNegada


def abrir_chamado(solicitante, categoria, prioridade, titulo="Impressora sem imprimir",
                  descricao="A impressora do segundo andar não responde desde ontem."):
    return chamado_service.abrir(solicitante, titulo, descricao, categoria.id, prioridade.id)


# --------------------------------------------------------------------- abertura
def test_abertura_gera_protocolo_status_e_historico(app, solicitante, categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)

    assert chamado.protocolo.startswith(str(datetime.now(timezone.utc).year))
    assert chamado.status.nome == chamado_service.STATUS_ABERTO
    assert chamado.tecnico_id is None
    assert len(chamado.interacoes) == 1
    assert chamado.interacoes[0].tipo == "sistema"


def test_protocolos_sao_sequenciais_e_unicos(app, solicitante, categoria, prioridade):
    primeiro = abrir_chamado(solicitante, categoria, prioridade)
    segundo = abrir_chamado(solicitante, categoria, prioridade)

    assert primeiro.protocolo != segundo.protocolo
    assert int(segundo.protocolo.split("-")[1]) == int(primeiro.protocolo.split("-")[1]) + 1


def test_regressao_e04_descricao_so_com_espacos_e_recusada(app, solicitante, categoria,
                                                           prioridade):
    """E-04 (Colega 4): o registro era aceito com a descrição em branco."""
    with pytest.raises(ErroDeNegocio) as excecao:
        chamado_service.abrir(solicitante, "Título válido aqui", "            ",
                              categoria.id, prioridade.id)
    assert excecao.value.campo == "descricao"
    assert Chamado.query.count() == 0


def test_titulo_curto_e_recusado(app, solicitante, categoria, prioridade):
    with pytest.raises(ErroDeNegocio) as excecao:
        chamado_service.abrir(solicitante, "abc", "Descrição suficientemente longa aqui.",
                              categoria.id, prioridade.id)
    assert excecao.value.campo == "titulo"


def test_categoria_inexistente_e_recusada(app, solicitante, prioridade):
    with pytest.raises(ErroDeNegocio) as excecao:
        chamado_service.abrir(solicitante, "Título válido", "Descrição bem detalhada aqui.",
                              9999, prioridade.id)
    assert excecao.value.campo == "categoria_id"


def test_regressao_e03_anexo_acima_do_limite_e_recusado(app, solicitante, categoria, prioridade):
    """E-03 (Colega 1): o upload travava sem mensagem."""
    grande = 6 * 1024 * 1024
    with pytest.raises(ErroDeNegocio) as excecao:
        chamado_service.abrir(solicitante, "Título válido", "Descrição bem detalhada aqui.",
                              categoria.id, prioridade.id,
                              anexos=[("print-da-tela.png", grande)])
    assert excecao.value.campo == "anexo"
    assert "5 MB" in excecao.value.mensagem


def test_anexo_dentro_do_limite_e_aceito(app, solicitante, categoria, prioridade):
    chamado = chamado_service.abrir(
        solicitante, "Título válido", "Descrição bem detalhada aqui.",
        categoria.id, prioridade.id, anexos=[("print.png", 1024 * 500)])
    assert len(chamado.anexos) == 1


# ------------------------------------------------------------------- atribuição
def test_atribuir_move_para_em_atendimento(app, solicitante, tecnico, gestor,
                                           categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    chamado_service.atribuir(chamado, gestor, tecnico)

    assert chamado.tecnico_id == tecnico.id
    assert chamado.status.nome == chamado_service.STATUS_EM_ATENDIMENTO


def test_solicitante_nao_pode_atribuir(app, solicitante, tecnico, categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    with pytest.raises(PermissaoNegada):
        chamado_service.atribuir(chamado, solicitante, tecnico)


def test_atribuir_exige_usuario_com_perfil_tecnico(app, solicitante, gestor,
                                                   categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    with pytest.raises(ErroDeNegocio) as excecao:
        chamado_service.atribuir(chamado, gestor, solicitante)
    assert excecao.value.campo == "tecnico_id"


# ----------------------------------------------------------------------- status
def test_fluxo_completo_ate_resolvido(app, solicitante, tecnico, gestor,
                                      categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    chamado_service.atribuir(chamado, gestor, tecnico)
    chamado_service.mudar_status(chamado, tecnico, chamado_service.STATUS_RESOLVIDO,
                                 solucao="Cabo de rede da impressora substituído e testado.")

    assert chamado.status.nome == chamado_service.STATUS_RESOLVIDO
    assert chamado.encerrado is True
    assert chamado.data_encerramento is not None
    assert chamado.solucao.startswith("Cabo de rede")


def test_nao_permite_pular_de_aberto_para_resolvido(app, solicitante, tecnico,
                                                    categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    with pytest.raises(ErroDeNegocio, match="Não é possível mudar"):
        chamado_service.mudar_status(chamado, tecnico, chamado_service.STATUS_RESOLVIDO,
                                     solucao="Solução qualquer bem descrita.")


def test_resolver_sem_solucao_e_recusado(app, solicitante, tecnico, gestor,
                                         categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    chamado_service.atribuir(chamado, gestor, tecnico)
    with pytest.raises(ErroDeNegocio) as excecao:
        chamado_service.mudar_status(chamado, tecnico, chamado_service.STATUS_RESOLVIDO,
                                     solucao="ok")
    assert excecao.value.campo == "solucao"


def test_solicitante_nao_pode_resolver(app, solicitante, tecnico, gestor,
                                       categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    chamado_service.atribuir(chamado, gestor, tecnico)
    with pytest.raises(PermissaoNegada):
        chamado_service.mudar_status(chamado, solicitante, chamado_service.STATUS_RESOLVIDO,
                                     solucao="Resolvi sozinho, obrigado a todos.")


def test_reabertura_limpa_encerramento(app, solicitante, tecnico, gestor,
                                       categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    chamado_service.atribuir(chamado, gestor, tecnico)
    chamado_service.mudar_status(chamado, tecnico, chamado_service.STATUS_RESOLVIDO,
                                 solucao="Cabo de rede substituído e testado com o usuário.")
    chamado_service.mudar_status(chamado, solicitante, chamado_service.STATUS_ABERTO)

    assert chamado.status.nome == chamado_service.STATUS_ABERTO
    assert chamado.data_encerramento is None
    assert chamado.solucao is None


# ---------------------------------------------------------------------- consulta
def test_regressao_e02_filtro_inclui_o_dia_final(app, db, solicitante, categoria, prioridade):
    """E-02 (Colega 2): chamados abertos no último dia do intervalo sumiam."""
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    hoje = datetime.now(timezone.utc)
    chamado.data_abertura = hoje.replace(hour=23, minute=50, second=0, microsecond=0)
    db.session.commit()

    pagina = chamado_service.listar(solicitante, data_inicio=hoje.date(), data_fim=hoje.date())
    assert pagina.total == 1


def test_filtro_por_periodo_exclui_fora_do_intervalo(app, db, solicitante, categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    chamado.data_abertura = datetime.now(timezone.utc) - timedelta(days=10)
    db.session.commit()

    ontem = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    hoje = datetime.now(timezone.utc).date()
    assert chamado_service.listar(solicitante, data_inicio=ontem, data_fim=hoje).total == 0


def test_regressao_e01_listagem_e_paginada(app, solicitante, categoria, prioridade):
    """E-01 (Colega 5): a listagem trazia todos os registros de uma vez."""
    for i in range(30):
        abrir_chamado(solicitante, categoria, prioridade, titulo=f"Chamado de teste {i}")

    pagina = chamado_service.listar(solicitante, pagina=1, por_pagina=25)
    assert pagina.total == 30
    assert len(pagina.items) == 25
    assert pagina.pages == 2
    assert len(chamado_service.listar(solicitante, pagina=2, por_pagina=25).items) == 5


def test_solicitante_ve_apenas_os_proprios_chamados(app, solicitante, outro_solicitante,
                                                    categoria, prioridade):
    abrir_chamado(solicitante, categoria, prioridade)
    abrir_chamado(outro_solicitante, categoria, prioridade)

    assert chamado_service.listar(solicitante).total == 1
    assert chamado_service.listar(outro_solicitante).total == 1


def test_gestor_ve_todos_os_chamados(app, solicitante, outro_solicitante, gestor,
                                     categoria, prioridade):
    abrir_chamado(solicitante, categoria, prioridade)
    abrir_chamado(outro_solicitante, categoria, prioridade)

    assert chamado_service.listar(gestor).total == 2


def test_obter_chamado_de_outro_solicitante_e_bloqueado(app, solicitante, outro_solicitante,
                                                        categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    with pytest.raises(PermissaoNegada):
        chamado_service.obter(chamado.id, outro_solicitante)


def test_busca_por_protocolo(app, solicitante, categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    assert chamado_service.buscar_por_protocolo(chamado.protocolo, solicitante).id == chamado.id


def test_busca_por_protocolo_inexistente(app, solicitante):
    with pytest.raises(ErroDeNegocio, match="Nenhum chamado"):
        chamado_service.buscar_por_protocolo("2000-000001", solicitante)


def test_parse_data_aceita_dois_formatos_e_recusa_invalido(app):
    assert chamado_service.parse_data("2026-03-15").day == 15
    assert chamado_service.parse_data("15/03/2026").month == 3
    assert chamado_service.parse_data("") is None
    with pytest.raises(ErroDeNegocio):
        chamado_service.parse_data("15-03-26")


# -------------------------------------------------------------------------- SLA
def test_sla_estourado_quando_passa_do_prazo(app, db, solicitante, categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)   # prioridade Média = 24h
    chamado.data_abertura = datetime.now(timezone.utc) - timedelta(hours=30)
    db.session.commit()

    assert chamado.sla_estourado is True


def test_sla_no_prazo(app, solicitante, categoria, prioridade):
    chamado = abrir_chamado(solicitante, categoria, prioridade)
    assert chamado.sla_estourado is False
