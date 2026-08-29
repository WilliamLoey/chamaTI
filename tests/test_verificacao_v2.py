"""Testes de regressão dos defeitos encontrados na verificação da versão 1.0.

Cada teste aqui reproduz um defeito real, documentado em
docs/verificacao-v1.md. Todos falham na versão 1.0 e passam na 2.0.
"""
from datetime import datetime, time, timedelta, timezone

import pytest

from app import create_app, regras
from app.extensions import db as _db
from app.models import Anexo, Chamado, Perfil, Usuario
from app.services import chamado_service, usuario_service
from app.services.erros import ErroDeNegocio, PermissaoNegada


def abrir(solicitante, categoria, prioridade, **kwargs):
    return chamado_service.abrir(
        solicitante, kwargs.pop("titulo", "Impressora sem imprimir"),
        kwargs.pop("descricao", "A impressora do segundo andar não responde."),
        categoria.id, prioridade.id, **kwargs)


# ---------------------------------------------------------------------- V-01
def test_v01_cadastro_publico_nao_permite_escolher_o_perfil(client):
    """V-01 (crítico): qualquer visitante podia se cadastrar como Gestor
    apenas selecionando a opção no formulário, obtendo acesso a todos os
    chamados da empresa."""
    client.post("/auth/cadastro", data={
        "nome": "Pessoa Curiosa",
        "email": "curiosa@teste.dev",
        "senha": "senha123",
        "perfil": "gestor",          # tentativa de escalar privilégio
    }, follow_redirects=True)

    usuario = Usuario.query.filter_by(email="curiosa@teste.dev").first()
    assert usuario is not None
    assert usuario.perfil == Perfil.SOLICITANTE


def test_v01_area_do_gestor_bloqueada_para_quem_se_cadastrou(client):
    client.post("/auth/cadastro", data={
        "nome": "Pessoa Curiosa", "email": "curiosa2@teste.dev",
        "senha": "senha123", "perfil": "gestor"}, follow_redirects=True)
    assert client.get("/painel/").status_code == 403


def test_v01_somente_gestor_cria_conta_com_perfil_elevado(app, solicitante, gestor):
    with pytest.raises(PermissaoNegada):
        usuario_service.cadastrar_por_gestor(
            solicitante, "Novo Tecnico", "novo@teste.dev", "senha123", Perfil.TECNICO)

    criado = usuario_service.cadastrar_por_gestor(
        gestor, "Novo Tecnico", "novo@teste.dev", "senha123", Perfil.TECNICO)
    assert criado.perfil == Perfil.TECNICO


def test_v01_somente_gestor_promove(app, solicitante, tecnico, gestor):
    with pytest.raises(PermissaoNegada):
        usuario_service.promover(solicitante, solicitante, Perfil.GESTOR)

    usuario_service.promover(gestor, solicitante, Perfil.TECNICO)
    assert solicitante.perfil == Perfil.TECNICO


# ---------------------------------------------------------------------- V-02
def test_v02_post_sem_token_csrf_e_rejeitado():
    """V-02 (alto): nenhum formulário tinha proteção contra CSRF, então um
    site externo conseguia agir em nome do usuário logado."""
    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = True     # liga a proteção só neste teste
    with app.app_context():
        _db.create_all()
        cliente = app.test_client()
        resposta = cliente.post("/auth/login",
                                data={"email": "a@b.dev", "senha": "senha123"})
        assert resposta.status_code == 400
        _db.session.remove()
        _db.drop_all()


def test_v02_formularios_publicam_o_token(client):
    for rota in ("/auth/login", "/auth/cadastro"):
        html = client.get(rota).get_data(as_text=True)
        assert "csrf_token" in html


# ---------------------------------------------------------------------- V-03
def test_v03_conteudo_do_anexo_e_gravado(app, solicitante, categoria, prioridade):
    """V-03 (alto): o sistema registrava nome e tamanho, mas descartava o
    arquivo — não havia sequer coluna para guardá-lo."""
    conteudo = b"conteudo real do print de tela"
    chamado = abrir(solicitante, categoria, prioridade,
                    anexos=[("print.png", conteudo, "image/png")])

    anexo = Anexo.query.filter_by(chamado_id=chamado.id).first()
    assert anexo.conteudo == conteudo
    assert anexo.tamanho_bytes == len(conteudo)
    assert anexo.tipo_mime == "image/png"


def test_v03_anexo_pode_ser_baixado(client, solicitante, categoria, prioridade,
                                    autenticar):
    conteudo = b"evidencia-do-erro"
    chamado = abrir(solicitante, categoria, prioridade,
                    anexos=[("erro.png", conteudo, "image/png")])
    anexo = Anexo.query.filter_by(chamado_id=chamado.id).first()

    autenticar(solicitante.email)
    resposta = client.get(f"/chamados/{chamado.id}/anexo/{anexo.id}")
    assert resposta.status_code == 200
    assert resposta.data == conteudo


def test_v03_anexo_de_outro_usuario_e_bloqueado(client, solicitante,
                                                outro_solicitante, categoria,
                                                prioridade, autenticar):
    chamado = abrir(solicitante, categoria, prioridade,
                    anexos=[("erro.png", b"segredo", "image/png")])
    anexo = Anexo.query.filter_by(chamado_id=chamado.id).first()

    autenticar(outro_solicitante.email)
    assert client.get(f"/chamados/{chamado.id}/anexo/{anexo.id}").status_code == 403


# ---------------------------------------------------------------------- V-04
def test_v04_extensao_executavel_e_recusada(app):
    """V-04 (médio): qualquer extensão era aceita, inclusive .exe."""
    with pytest.raises(ErroDeNegocio) as excecao:
        chamado_service.validar_anexo("instalador.exe", 1024)
    assert excecao.value.campo == "anexo"


@pytest.mark.parametrize("nome", ["print.png", "foto.JPG", "relatorio.pdf",
                                  "saida.log", "dados.csv"])
def test_v04_extensoes_de_evidencia_sao_aceitas(app, nome):
    assert chamado_service.validar_anexo(nome, 1024) is True


@pytest.mark.parametrize("nome", ["script.sh", "macro.bat", "app.jar", "semextensao"])
def test_v04_outras_extensoes_sao_recusadas(app, nome):
    with pytest.raises(ErroDeNegocio):
        chamado_service.validar_anexo(nome, 1024)


def test_v04_arquivo_vazio_e_recusado(app):
    with pytest.raises(ErroDeNegocio, match="vazio"):
        chamado_service.validar_anexo("print.png", 0)


# ---------------------------------------------------------------------- V-05
def test_v05_protocolo_duplicado_e_contornado(app, solicitante, categoria,
                                              prioridade, monkeypatch):
    """V-05 (médio): `gerar_protocolo` lê o último número e só grava depois.
    Dois pedidos concorrentes calculavam o mesmo valor e a gravação estourava
    na constraint UNIQUE. Agora a colisão é detectada e o número recalculado.

    O teste simula a corrida forçando a primeira tentativa a devolver um
    protocolo que já existe.
    """
    primeiro = abrir(solicitante, categoria, prioridade)

    real = chamado_service.gerar_protocolo
    chamadas = {"n": 0}

    def gerar_com_colisao():
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            return primeiro.protocolo      # colide de propósito
        return real()

    monkeypatch.setattr(chamado_service, "gerar_protocolo", gerar_com_colisao)

    segundo = abrir(solicitante, categoria, prioridade)
    assert segundo.id is not None
    assert segundo.protocolo != primeiro.protocolo
    assert Chamado.query.count() == 2


# ---------------------------------------------------------------------- V-06
def test_v06_filtro_respeita_o_fuso_brasileiro(app, db, solicitante, categoria,
                                               prioridade):
    """V-06 (médio): as datas do filtro eram tratadas como UTC. Um chamado
    aberto às 23h no Brasil vira 02:00 UTC do dia seguinte, e sumia do filtro
    de "hoje"."""
    chamado = abrir(solicitante, categoria, prioridade)

    hoje_local = datetime.now(regras.FUSO_LOCAL).date()
    as_23h_local = datetime.combine(hoje_local, time(23, 0), tzinfo=regras.FUSO_LOCAL)
    chamado.data_abertura = as_23h_local.astimezone(timezone.utc)
    db.session.commit()

    # a data em UTC já é do dia seguinte...
    assert chamado.data_abertura.date() != hoje_local
    # ...mas o filtro do usuário, que pensa no fuso local, precisa encontrá-lo
    pagina = chamado_service.listar(solicitante, data_inicio=hoje_local,
                                    data_fim=hoje_local)
    assert pagina.total == 1


def test_v06_madrugada_local_nao_entra_no_dia_anterior(app, db, solicitante,
                                                       categoria, prioridade):
    chamado = abrir(solicitante, categoria, prioridade)
    hoje_local = datetime.now(regras.FUSO_LOCAL).date()
    a_01h_local = datetime.combine(hoje_local, time(1, 0), tzinfo=regras.FUSO_LOCAL)
    chamado.data_abertura = a_01h_local.astimezone(timezone.utc)
    db.session.commit()

    ontem = hoje_local - timedelta(days=1)
    assert chamado_service.listar(solicitante, data_inicio=ontem, data_fim=ontem).total == 0
    assert chamado_service.listar(solicitante, data_inicio=hoje_local,
                                  data_fim=hoje_local).total == 1


# ---------------------------------------------------------------------- V-07
def test_v07_tecnico_mantem_acesso_ao_chamado_que_atendeu(app, solicitante, gestor,
                                                          tecnico, outro_tecnico,
                                                          categoria, prioridade):
    """V-07 (médio): ao passar o chamado para outro técnico, o primeiro perdia
    o acesso — inclusive ao histórico que ele mesmo havia escrito."""
    chamado = abrir(solicitante, categoria, prioridade)
    chamado_service.atribuir(chamado, gestor, tecnico)
    chamado_service.comentar(chamado, tecnico, "Troquei o cabo de rede e vou monitorar.")

    chamado_service.atribuir(chamado, gestor, outro_tecnico)

    assert chamado.tecnico_id == outro_tecnico.id
    assert tecnico.pode_ver_chamado(chamado) is True


def test_v07_tecnico_sem_relacao_nao_ve_chamado_alheio(app, solicitante, gestor,
                                                       tecnico, outro_tecnico,
                                                       categoria, prioridade):
    chamado = abrir(solicitante, categoria, prioridade)
    chamado_service.atribuir(chamado, gestor, tecnico)
    assert outro_tecnico.pode_ver_chamado(chamado) is False


# ---------------------------------------------------------------------- V-08
def test_v08_limite_de_anexo_e_um_numero(app):
    """V-08 (baixo): ANEXO_MAX_BYTES era declarado com @property numa classe
    lida pelo Flask como atributo simples, então a configuração guardava o
    objeto property em vez do número."""
    valor = app.config["ANEXO_MAX_BYTES"]
    assert isinstance(valor, int)
    assert valor == 5 * 1024 * 1024


# ---------------------------------------------------------------------- V-09
def test_v09_regras_tem_fonte_unica(app):
    """V-09 (baixo): os limites viviam duplicados entre config.py e os
    serviços, com risco de divergirem numa alteração futura."""
    assert chamado_service.DESCRICAO_MIN is regras.DESCRICAO_MIN
    assert chamado_service.ITENS_POR_PAGINA is regras.ITENS_POR_PAGINA
    assert chamado_service.ANEXO_MAX_BYTES is regras.ANEXO_MAX_BYTES
    assert usuario_service.SENHA_MIN is regras.SENHA_MIN
    assert app.config["DESCRICAO_MIN"] == regras.DESCRICAO_MIN
