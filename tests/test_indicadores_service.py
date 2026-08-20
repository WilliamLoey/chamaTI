"""Testes dos indicadores do painel do gestor."""
from datetime import datetime, timedelta, timezone

from app.services import chamado_service, indicadores_service


def _abrir(solicitante, categoria, prioridade, titulo="Chamado de teste do painel"):
    return chamado_service.abrir(solicitante, titulo,
                                 "Descrição suficientemente longa para validar.",
                                 categoria.id, prioridade.id)


def test_resumo_de_banco_vazio_nao_quebra(app):
    dados = indicadores_service.resumo()
    assert dados["total"] == 0
    assert dados["tempo_medio_horas"] == 0.0
    assert dados["taxa_sla"] == 100.0


def test_totais_por_status_batem_com_a_listagem(app, solicitante, gestor, tecnico,
                                                categoria, prioridade):
    _abrir(solicitante, categoria, prioridade)
    segundo = _abrir(solicitante, categoria, prioridade)
    chamado_service.atribuir(segundo, gestor, tecnico)

    por_status = {i["rotulo"]: i["total"] for i in indicadores_service.totais_por_status()}
    assert por_status["Aberto"] == 1
    assert por_status["Em atendimento"] == 1
    assert por_status["Resolvido"] == 0
    assert sum(por_status.values()) == indicadores_service.resumo()["total"]


def test_tempo_medio_de_atendimento(app, db, solicitante, gestor, tecnico,
                                    categoria, prioridade):
    chamado = _abrir(solicitante, categoria, prioridade)
    chamado_service.atribuir(chamado, gestor, tecnico)
    chamado_service.mudar_status(chamado, tecnico, chamado_service.STATUS_RESOLVIDO,
                                 solucao="Problema corrigido e validado com o usuário.")

    abertura = datetime.now(timezone.utc) - timedelta(hours=10)
    chamado.data_abertura = abertura
    chamado.data_encerramento = abertura + timedelta(hours=4)
    db.session.commit()

    assert indicadores_service.tempo_medio_atendimento_horas() == 4.0


def test_taxa_de_sla_considera_apenas_encerrados(app, db, solicitante, gestor, tecnico,
                                                 categoria, prioridade):
    chamado = _abrir(solicitante, categoria, prioridade)   # Média = 24h
    chamado_service.atribuir(chamado, gestor, tecnico)
    chamado_service.mudar_status(chamado, tecnico, chamado_service.STATUS_RESOLVIDO,
                                 solucao="Problema corrigido e validado com o usuário.")

    abertura = datetime.now(timezone.utc) - timedelta(hours=40)
    chamado.data_abertura = abertura
    chamado.data_encerramento = abertura + timedelta(hours=30)   # estourou o SLA
    db.session.commit()

    assert indicadores_service.taxa_dentro_do_sla() == 0.0


def test_carga_por_tecnico_ignora_chamados_encerrados(app, solicitante, gestor, tecnico,
                                                      categoria, prioridade):
    aberto = _abrir(solicitante, categoria, prioridade)
    chamado_service.atribuir(aberto, gestor, tecnico)

    encerrado = _abrir(solicitante, categoria, prioridade)
    chamado_service.atribuir(encerrado, gestor, tecnico)
    chamado_service.mudar_status(encerrado, tecnico, chamado_service.STATUS_RESOLVIDO,
                                 solucao="Problema corrigido e validado com o usuário.")

    carga = indicadores_service.carga_por_tecnico()
    assert carga == [{"rotulo": tecnico.nome, "total": 1}]
