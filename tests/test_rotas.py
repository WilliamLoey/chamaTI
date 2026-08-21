"""Testes de integração das rotas (controllers + templates)."""
from app.models import Chamado
from app.services import chamado_service


def test_health_responde_ok(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.get_json()["status"] == "ok"


def test_pagina_inicial_abre_sem_login(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "ChamaTI" in resposta.get_data(as_text=True)


def test_listagem_exige_login(client):
    resposta = client.get("/chamados/", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/auth/login" in resposta.headers["Location"]


def test_login_com_credenciais_validas(client, solicitante, autenticar):
    resposta = autenticar(solicitante.email)
    assert resposta.status_code == 200
    assert "Diego Souza" in resposta.get_data(as_text=True)


def test_login_com_senha_errada_retorna_401(client, solicitante):
    resposta = client.post("/auth/login",
                           data={"email": solicitante.email, "senha": "errada"})
    assert resposta.status_code == 401
    assert "E-mail ou senha incorretos" in resposta.get_data(as_text=True)


def test_cadastro_pela_tela_cria_conta_e_autentica(client):
    resposta = client.post("/auth/cadastro", data={
        "nome": "Fernanda Lima",
        "email": "fernanda@teste.dev",
        "senha": "senha123",
        "perfil": "solicitante",
    }, follow_redirects=True)

    assert resposta.status_code == 200
    assert "Fernanda Lima" in resposta.get_data(as_text=True)


def test_cadastro_invalido_devolve_400_com_mensagem(client):
    resposta = client.post("/auth/cadastro", data={
        "nome": "Ana", "email": "sem-arroba", "senha": "senha123", "perfil": "solicitante"})
    assert resposta.status_code == 400
    assert "e-mail válido" in resposta.get_data(as_text=True)


def test_abrir_chamado_pela_tela(client, solicitante, categoria, prioridade, autenticar):
    autenticar(solicitante.email)
    resposta = client.post("/chamados/novo", data={
        "titulo": "Notebook não liga",
        "descricao": "O equipamento não liga mesmo conectado à tomada.",
        "categoria_id": categoria.id,
        "prioridade_id": prioridade.id,
    }, follow_redirects=True)

    assert resposta.status_code == 200
    assert Chamado.query.count() == 1
    assert "aberto com sucesso" in resposta.get_data(as_text=True)


def test_abrir_chamado_invalido_devolve_400(client, solicitante, categoria, prioridade,
                                            autenticar):
    autenticar(solicitante.email)
    resposta = client.post("/chamados/novo", data={
        "titulo": "Notebook não liga",
        "descricao": "   ",
        "categoria_id": categoria.id,
        "prioridade_id": prioridade.id,
    })

    assert resposta.status_code == 400
    assert Chamado.query.count() == 0


def test_regressao_e04_painel_e_bloqueado_para_solicitante_via_url(client, solicitante,
                                                                   autenticar):
    """E-04 (Colega 4): tentativa de acesso direto pela URL a uma área restrita."""
    autenticar(solicitante.email)
    resposta = client.get("/painel/")
    assert resposta.status_code == 403
    assert "restrita" in resposta.get_data(as_text=True)


def test_painel_abre_para_gestor(client, gestor, autenticar):
    autenticar(gestor.email)
    resposta = client.get("/painel/")
    assert resposta.status_code == 200
    assert "Painel de indicadores" in resposta.get_data(as_text=True)


def test_api_de_indicadores_retorna_json(client, gestor, autenticar):
    autenticar(gestor.email)
    dados = client.get("/painel/api/indicadores").get_json()
    assert "total" in dados and "por_status" in dados


def test_detalhe_de_chamado_alheio_retorna_403(client, solicitante, outro_solicitante,
                                               categoria, prioridade, autenticar):
    chamado = chamado_service.abrir(solicitante, "Título válido aqui",
                                    "Descrição detalhada do problema relatado.",
                                    categoria.id, prioridade.id)
    autenticar(outro_solicitante.email)
    assert client.get(f"/chamados/{chamado.id}").status_code == 403


def test_chamado_inexistente_retorna_404(client, solicitante, autenticar):
    autenticar(solicitante.email)
    assert client.get("/chamados/9999").status_code == 404


def test_pagina_inexistente_retorna_404_amigavel(client):
    resposta = client.get("/rota-que-nao-existe")
    assert resposta.status_code == 404
    assert "não existe" in resposta.get_data(as_text=True)


def test_logout_encerra_a_sessao(client, solicitante, autenticar):
    autenticar(solicitante.email)
    client.post("/auth/logout", follow_redirects=True)
    assert client.get("/chamados/", follow_redirects=False).status_code == 302
