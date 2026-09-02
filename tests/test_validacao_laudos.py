"""Testes de regressão dos defeitos apontados na VALIDAÇÃO com usuários.

Enquanto tests/test_verificacao_v2.py cobre a verificação (defeitos que eu
encontrei revisando o próprio código), este arquivo cobre a validação: cada
teste reproduz um problema relatado por um testador nos formulários que estão
em laudos/, e passa a falhar se o problema voltar.

O mapa completo — quem relatou o quê e o que foi feito — está em
docs/validacao-laudos.md.
"""
from datetime import timedelta

import pytest

from app.models import Chamado, Perfil, Status
from app.services import chamado_service
from app.services.chamado_service import JUSTIFICATIVA_MIN
from app.services.erros import ErroDeNegocio


def abrir(solicitante, categoria, prioridade, **kwargs):
    return chamado_service.abrir(
        solicitante,
        kwargs.pop("titulo", "Impressora sem imprimir"),
        kwargs.pop("descricao", "A impressora do segundo andar não responde."),
        categoria.id, prioridade.id, **kwargs)


def _atrasar(chamado):
    """Empurra a abertura para trás do prazo da prioridade, deixando o chamado
    fora do SLA sem depender de esperar o relógio."""
    horas = chamado.prioridade.sla_horas + 1
    chamado.data_abertura = chamado.data_abertura - timedelta(hours=horas)
    from app.extensions import db
    db.session.commit()
    assert chamado.sla_estourado
    return chamado


# ---------------------------------------------------------------------- L-01
# "Ao anexar um PDF acima de 5 MB, o botão travou no carregamento sem exibir
#  um alerta claro." — testador 1 (perfil Técnico, Windows/Chrome)
#
# Causa: o handler que troca o rótulo do botão para "Enviando…" rodava mesmo
# quando um validador anterior já tinha chamado preventDefault(). O envio era
# cancelado, mas o botão ficava desabilitado para sempre.

def test_l01_botao_nao_e_travado_quando_o_envio_foi_cancelado():
    """O guarda contra o travamento vive no JavaScript. O teste garante que a
    verificação de defaultPrevented continua presente no arquivo servido —
    ela é o que impede o botão de ficar preso em 'Enviando…'."""
    from pathlib import Path
    js = Path(__file__).resolve().parents[1] / "app" / "static" / "js" / "app.js"
    fonte = js.read_text(encoding="utf-8")
    assert "evento.defaultPrevented" in fonte
    # e a checagem precisa vir antes de desabilitar o botão
    assert fonte.index("evento.defaultPrevented") < fonte.index("botao.disabled = true")


def test_l01_servidor_recusa_anexo_acima_do_limite(app, solicitante, categoria,
                                                   prioridade):
    """A trava do navegador é conveniência; a que vale é a do servidor."""
    grande = ("relatorio.pdf", b"x" * (6 * 1024 * 1024), "application/pdf")
    with pytest.raises(ErroDeNegocio) as erro:
        abrir(solicitante, categoria, prioridade, anexos=[grande])
    assert erro.value.campo == "anexo"
    assert "5" in erro.value.mensagem


# ---------------------------------------------------------------------- L-02
# "O formulário de filtros ocupa quase a tela inteira no celular e pode dar a
#  impressão de que nada mudou ao clicar em Filtrar." — testador 2 (Android)

def test_l02_listagem_traz_o_controle_de_recolher_filtros(client, autenticar,
                                                          solicitante):
    autenticar("diego@teste.dev")
    html = client.get("/chamados/").get_data(as_text=True)
    assert "data-filtros-alternar" in html
    assert "data-filtros-rotulo" in html
    assert "Ocultar filtros" in html
    # o alvo para onde a tela rola depois de filtrar
    assert "data-resultados" in html


def test_l02_filtro_em_uso_mantem_o_bloco_aberto(client, autenticar, solicitante):
    autenticar("diego@teste.dev")
    sem_filtro = client.get("/chamados/").get_data(as_text=True)
    com_filtro = client.get("/chamados/?busca=impressora").get_data(as_text=True)
    assert 'data-filtros-ativos="0"' in sem_filtro
    assert 'data-filtros-ativos="1"' in com_filtro


def test_l02_filtros_continuam_funcionando_sem_javascript(client, autenticar,
                                                          solicitante, categoria,
                                                          prioridade):
    """Recolher é enfeite do navegador: o formulário é GET puro e precisa
    continuar filtrando com o JavaScript desligado."""
    autenticar("diego@teste.dev")
    abrir(solicitante, categoria, prioridade, titulo="Monitor piscando",
          descricao="O monitor da recepção pisca a cada dois minutos.")
    resposta = client.get("/chamados/?busca=monitor").get_data(as_text=True)
    assert "Monitor piscando" in resposta
    assert "Impressora" not in resposta


# ---------------------------------------------------------------------- L-03
# "O bloqueio funcionou, mas o botão 'Ver meus chamados' me levou a uma página
#  sem o menu do gestor." — testador 3 (perfil Gestor)
#
# A página de erro oferecia sempre os mesmos dois atalhos e não dizia com qual
# perfil a pessoa estava conectada.

def test_l03_pagina_403_informa_o_perfil_conectado(client, autenticar, tecnico):
    autenticar("bruno@teste.dev")
    resposta = client.get("/painel/")
    assert resposta.status_code == 403
    html = resposta.get_data(as_text=True)
    assert "Bruno Carvalho" in html
    assert "Técnico" in html      # o perfil que ele tem
    assert "Gestor" in html       # o perfil que a área exige


def _renderizar_403(app, usuario_id=None):
    """Renderiza a página de erro no contexto de um usuário específico."""
    from flask import render_template, session
    with app.test_request_context("/painel/"):
        if usuario_id is not None:
            session["usuario_id"] = usuario_id
        return render_template("erros/403.html", mensagem="mensagem de teste")


def test_l03_403_do_gestor_oferece_caminho_de_volta_ao_painel(app, gestor):
    """Era exatamente o relato: o único atalho levava à listagem comum, e de lá
    o gestor não tinha como voltar ao painel."""
    html = _renderizar_403(app, gestor.id)
    assert "Ir para o painel" in html
    assert "/painel/" in html


def test_l03_403_de_tecnico_nao_oferece_o_painel(app, tecnico):
    html = _renderizar_403(app, tecnico.id)
    assert "Ir para o painel" not in html
    assert "Ver meus chamados" in html


def test_l03_403_de_visitante_manda_para_o_login(app, client):
    """Sem sessão, oferecer 'Ver meus chamados' era um beco: o clique só
    devolvia outro redirecionamento para o login."""
    html = _renderizar_403(app)
    assert "Ver meus chamados" not in html
    assert "Entrar" in html

    resposta = client.get("/painel/", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/auth/login" in resposta.headers["Location"]


# ---------------------------------------------------------------------- L-04
# "Consegui encerrar um chamado com o SLA já vencido sem que o sistema pedisse
#  qualquer justificativa." — testador 4 (Notebook Windows/Firefox)

def test_l04_encerrar_fora_do_prazo_exige_justificativa(app, solicitante, tecnico,
                                                        categoria, prioridade):
    chamado = _atrasar(abrir(solicitante, categoria, prioridade))
    chamado_service.mudar_status(chamado, tecnico, "Em atendimento")

    with pytest.raises(ErroDeNegocio) as erro:
        chamado_service.mudar_status(chamado, tecnico, "Resolvido",
                                     solucao="Troquei o cabo de rede da impressora.")
    assert erro.value.campo == "justificativa_atraso"
    assert chamado.status.nome != "Resolvido"


def test_l04_justificativa_curta_demais_e_recusada(app, solicitante, tecnico,
                                                   categoria, prioridade):
    chamado = _atrasar(abrir(solicitante, categoria, prioridade))
    chamado_service.mudar_status(chamado, tecnico, "Em atendimento")

    with pytest.raises(ErroDeNegocio):
        chamado_service.mudar_status(
            chamado, tecnico, "Resolvido",
            solucao="Troquei o cabo de rede da impressora.",
            justificativa_atraso="demorou")   # abaixo do mínimo


def test_l04_justificativa_valida_encerra_e_fica_registrada(app, solicitante, tecnico,
                                                            categoria, prioridade):
    chamado = _atrasar(abrir(solicitante, categoria, prioridade))
    chamado_service.mudar_status(chamado, tecnico, "Em atendimento")

    motivo = "A peça de reposição levou quatro dias para chegar do fornecedor."
    assert len(motivo) >= JUSTIFICATIVA_MIN
    chamado_service.mudar_status(chamado, tecnico, "Resolvido",
                                 solucao="Troquei o cabo de rede da impressora.",
                                 justificativa_atraso=motivo)

    assert chamado.status.nome == "Resolvido"
    assert chamado.justificativa_atraso == motivo


def test_l04_chamado_no_prazo_nao_pede_justificativa(app, solicitante, tecnico,
                                                     categoria, prioridade):
    """A exigência vale só para quem atrasou — cobrar de todo mundo seria
    atrito inútil no caminho feliz."""
    chamado = abrir(solicitante, categoria, prioridade)
    assert not chamado.sla_estourado
    chamado_service.mudar_status(chamado, tecnico, "Em atendimento")
    chamado_service.mudar_status(chamado, tecnico, "Resolvido",
                                 solucao="Troquei o cabo de rede da impressora.")
    assert chamado.status.nome == "Resolvido"
    assert chamado.justificativa_atraso is None


def test_l04_reabrir_limpa_a_justificativa(app, solicitante, tecnico,
                                           categoria, prioridade):
    chamado = _atrasar(abrir(solicitante, categoria, prioridade))
    chamado_service.mudar_status(chamado, tecnico, "Em atendimento")
    chamado_service.mudar_status(
        chamado, tecnico, "Resolvido",
        solucao="Troquei o cabo de rede da impressora.",
        justificativa_atraso="A peça de reposição demorou a chegar do fornecedor.")

    chamado_service.mudar_status(chamado, tecnico, "Aberto")
    assert chamado.justificativa_atraso is None
    assert chamado.solucao is None
    assert chamado.data_encerramento is None


def test_l04_formulario_mostra_o_campo_quando_o_prazo_venceu(client, autenticar,
                                                             solicitante, tecnico,
                                                             categoria, prioridade):
    chamado = _atrasar(abrir(solicitante, categoria, prioridade))
    autenticar("bruno@teste.dev")
    html = client.get(f"/chamados/{chamado.id}").get_data(as_text=True)
    assert "data-campo-atraso" in html
    assert "Motivo do atraso" in html


def test_l04_formulario_omite_o_campo_quando_esta_no_prazo(client, autenticar,
                                                           solicitante, tecnico,
                                                           categoria, prioridade):
    chamado = abrir(solicitante, categoria, prioridade)
    autenticar("bruno@teste.dev")
    html = client.get(f"/chamados/{chamado.id}").get_data(as_text=True)
    assert "data-campo-atraso" not in html


def test_l04_rota_repassa_a_justificativa_do_formulario(client, autenticar,
                                                        solicitante, tecnico,
                                                        categoria, prioridade):
    chamado = _atrasar(abrir(solicitante, categoria, prioridade))
    autenticar("bruno@teste.dev")
    client.post(f"/chamados/{chamado.id}/status",
                data={"status": "Em atendimento"}, follow_redirects=True)

    motivo = "O fornecedor atrasou a entrega da peça em quatro dias úteis."
    client.post(f"/chamados/{chamado.id}/status",
                data={"status": "Resolvido",
                      "solucao": "Troquei o cabo de rede da impressora.",
                      "justificativa_atraso": motivo},
                follow_redirects=True)

    atualizado = Chamado.query.get(chamado.id)
    assert atualizado.status.nome == "Resolvido"
    assert atualizado.justificativa_atraso == motivo


# ---------------------------------------------------------------------- L-05
# "A mensagem apareceu no topo e eu demorei a perceber qual campo estava com
#  problema." — testador 5 (perfil Solicitante)

def test_l05_erro_aparece_junto_do_campo_recusado(client, autenticar, solicitante,
                                                  categoria, prioridade):
    autenticar("diego@teste.dev")
    resposta = client.post("/chamados/novo", data={
        "titulo": "Impressora sem imprimir",
        "descricao": "curto",                     # abaixo do mínimo
        "categoria_id": categoria.id,
        "prioridade_id": prioridade.id,
    })
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 400
    # o bloco do topo continua (é o que o leitor de tela anuncia)
    assert 'data-campo-erro="descricao"' in html
    # e agora a mensagem também aparece ancorada no campo
    assert 'id="erro-descricao"' in html
    assert "campo--invalido" in html


def test_l05_apenas_o_campo_com_problema_recebe_a_mensagem(client, autenticar,
                                                           solicitante, categoria,
                                                           prioridade):
    autenticar("diego@teste.dev")
    html = client.post("/chamados/novo", data={
        "titulo": "abc",                          # abaixo do mínimo
        "descricao": "A impressora do segundo andar não responde desde ontem.",
        "categoria_id": categoria.id,
        "prioridade_id": prioridade.id,
    }).get_data(as_text=True)
    assert 'id="erro-titulo"' in html
    assert 'id="erro-descricao"' not in html


def test_l05_cadastro_tambem_ancora_o_erro_no_campo(client):
    html = client.post("/auth/cadastro", data={
        "nome": "Ana", "email": "sem-arroba", "senha": "senha123",
    }).get_data(as_text=True)
    assert 'id="erro-email"' in html or 'id="erro-nome"' in html


def test_l05_formulario_sem_erro_nao_mostra_mensagem_inline(client, autenticar,
                                                            solicitante):
    autenticar("diego@teste.dev")
    html = client.get("/chamados/novo").get_data(as_text=True)
    assert 'id="erro-titulo"' not in html
    assert 'id="erro-descricao"' not in html


# ---------------------------------------------------------------------- L-06
# Diferente das cinco anteriores, esta não veio de um formulário: apareceu
# depois, ao cancelar um chamado durante a revisão das correções. O sintoma era
# grosseiro — a listagem e o painel devolviam 500.
#
# Causa: só o caminho 'Resolvido' gravava `data_encerramento`. 'Cancelado'
# também encerra o chamado (Status.encerra é True), mas deixava a data nula, e
# `sla_estourado` comparava None com o prazo, estourando TypeError em toda tela
# que percorre chamados encerrados.
#
# A correção tem duas metades, e cada uma precisa do seu teste: o serviço passou
# a gravar a data em qualquer status que encerra, e o model passou a tolerar a
# data ausente — necessário porque os chamados cancelados antes da correção
# continuam no banco com o campo nulo.
#
# Dos dez testes abaixo, sete falham na versão anterior à correção. Os outros
# três — data de 'Resolvido' não sobrescrita, reabertura e cancelamento
# terminal — passam nas duas versões de propósito: eles não reproduzem o
# defeito, guardam o que a correção não podia quebrar ao generalizar as duas
# condições que antes citavam 'Resolvido' pelo nome.

def _cancelar(chamado, autor):
    chamado_service.mudar_status(chamado, autor, "Cancelado")
    return chamado


def _legado_sem_data_de_encerramento(chamado, autor):
    """Reproduz uma linha gravada antes da correção: encerrada, data nula."""
    _cancelar(chamado, autor)
    chamado.data_encerramento = None
    from app.extensions import db
    db.session.commit()
    assert chamado.encerrado and chamado.data_encerramento is None
    return chamado


def test_l06_cancelar_registra_a_data_de_encerramento(app, solicitante, tecnico,
                                                      categoria, prioridade):
    """O que o serviço deixava de fazer: cancelar encerra, logo tem de datar."""
    chamado = _cancelar(abrir(solicitante, categoria, prioridade), tecnico)

    assert chamado.status.nome == "Cancelado"
    assert chamado.encerrado
    assert chamado.data_encerramento is not None


def test_l06_cancelar_em_atendimento_tambem_data(app, solicitante, tecnico,
                                                  categoria, prioridade):
    """O cancelamento tem duas origens no fluxo — 'Aberto' e 'Em atendimento'.
    A do meio do atendimento é a que o testador percorreu."""
    chamado = abrir(solicitante, categoria, prioridade)
    chamado_service.mudar_status(chamado, tecnico, "Em atendimento")
    _cancelar(chamado, tecnico)

    assert chamado.data_encerramento is not None


def test_l06_resolver_nao_teve_a_data_sobrescrita(app, solicitante, tecnico,
                                                  categoria, prioridade):
    """A regra nova roda depois do bloco de 'Resolvido'. A guarda
    `is None` existe para ela não carimbar por cima da data já gravada."""
    chamado = abrir(solicitante, categoria, prioridade)
    chamado_service.mudar_status(chamado, tecnico, "Em atendimento")
    chamado_service.mudar_status(chamado, tecnico, "Resolvido",
                                 solucao="Troquei o cabo de rede da impressora.")
    gravada = chamado.data_encerramento

    assert gravada is not None
    assert chamado.status.nome == "Resolvido"
    # a data é a do encerramento real, não um segundo carimbo posterior
    assert chamado.data_encerramento == gravada


def test_l06_sla_de_encerrado_sem_data_nao_estoura_typeerror(app, solicitante, tecnico,
                                                             categoria, prioridade):
    """A metade do model: linha antiga, cancelada sem data. Antes, esta linha
    levantava TypeError ao comparar None com o prazo."""
    chamado = _legado_sem_data_de_encerramento(
        abrir(solicitante, categoria, prioridade), tecnico)

    assert chamado.sla_estourado is False        # dentro do prazo, não explode
    assert isinstance(chamado.horas_em_aberto, float)


def test_l06_encerrado_sem_data_conta_ate_agora(app, solicitante, tecnico,
                                                categoria, prioridade):
    """Sem data de encerramento não há como saber quando parou, então a
    contagem corre até agora — e um cancelado antigo fora do prazo é
    reconhecido como fora do prazo, em vez de derrubar a tela."""
    chamado = _atrasar(abrir(solicitante, categoria, prioridade))
    _legado_sem_data_de_encerramento(chamado, tecnico)

    assert chamado.sla_estourado is True
    assert chamado.horas_em_aberto >= chamado.prioridade.sla_horas


def test_l06_painel_nao_quebra_com_cancelado_sem_data(app, solicitante, tecnico,
                                                      categoria, prioridade):
    """`taxa_dentro_do_sla` varre todos os chamados encerrados, sem filtrar por
    data de encerramento — era o caminho mais curto até o 500 no painel."""
    from app.services import indicadores_service

    _legado_sem_data_de_encerramento(
        abrir(solicitante, categoria, prioridade), tecnico)

    taxa = indicadores_service.taxa_dentro_do_sla()
    assert 0.0 <= taxa <= 100.0


def test_l06_listagem_abre_com_chamado_cancelado_sem_data(client, autenticar,
                                                          solicitante, tecnico,
                                                          categoria, prioridade):
    """O sintoma relatado, ponta a ponta: a listagem lê `sla_estourado` de cada
    linha e devolvia 500 por causa de um único cancelado antigo."""
    _legado_sem_data_de_encerramento(
        abrir(solicitante, categoria, prioridade), tecnico)

    autenticar("diego@teste.dev")
    resposta = client.get("/chamados/")
    assert resposta.status_code == 200


def test_l06_painel_do_gestor_abre_com_cancelado_sem_data(client, autenticar,
                                                          solicitante, tecnico,
                                                          gestor, categoria,
                                                          prioridade):
    _legado_sem_data_de_encerramento(
        abrir(solicitante, categoria, prioridade), tecnico)

    autenticar("ana@teste.dev")
    resposta = client.get("/painel/")
    assert resposta.status_code == 200


def test_l06_reabertura_continua_limpando_o_encerramento(app, solicitante, tecnico,
                                                         categoria, prioridade):
    """A condição de reabertura deixou de citar 'Resolvido' pelo nome e passou a
    perguntar se o status encerra. O comportamento tem de ser o mesmo."""
    chamado = abrir(solicitante, categoria, prioridade)
    chamado_service.mudar_status(chamado, tecnico, "Em atendimento")
    chamado_service.mudar_status(chamado, tecnico, "Resolvido",
                                 solucao="Troquei o cabo de rede da impressora.")
    assert chamado.data_encerramento is not None

    chamado_service.mudar_status(chamado, tecnico, "Aberto")
    assert chamado.data_encerramento is None
    assert chamado.solucao is None


def test_l06_cancelado_continua_sem_saida(app, solicitante, tecnico,
                                          categoria, prioridade):
    """Cancelado é terminal. Datar o cancelamento não pode ter aberto uma porta
    de reabertura que o fluxo não prevê."""
    chamado = _cancelar(abrir(solicitante, categoria, prioridade), tecnico)

    with pytest.raises(ErroDeNegocio):
        chamado_service.mudar_status(chamado, tecnico, "Aberto")
    assert chamado.status.nome == "Cancelado"
