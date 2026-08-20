"""Carga inicial: tabelas de domínio, usuários e chamados de demonstração."""
import random
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import (Categoria, Chamado, Interacao, Perfil, Prioridade,
                        Status, Usuario)

CATEGORIAS = [
    ("Hardware", "Equipamentos, periféricos e impressoras"),
    ("Software", "Instalação, licença e erro de aplicativo"),
    ("Rede e Internet", "Conexão, VPN e Wi-Fi"),
    ("Acesso e Senha", "Bloqueio de conta e permissões"),
    ("E-mail", "Caixa postal, listas e assinatura"),
]

PRIORIDADES = [("Baixa", 72, 1), ("Média", 24, 2), ("Alta", 8, 3), ("Crítica", 4, 4)]

STATUS = [("Aberto", False, 1), ("Em atendimento", False, 2),
          ("Resolvido", True, 3), ("Cancelado", True, 4)]

USUARIOS = [
    ("Ana Ribeiro", "ana.gestora@chamati.dev", Perfil.GESTOR, "TI"),
    ("Bruno Carvalho", "bruno.tecnico@chamati.dev", Perfil.TECNICO, "TI"),
    ("Carla Menezes", "carla.tecnica@chamati.dev", Perfil.TECNICO, "TI"),
    ("Diego Souza", "diego@chamati.dev", Perfil.SOLICITANTE, "Financeiro"),
    ("Elisa Prado", "elisa@chamati.dev", Perfil.SOLICITANTE, "Comercial"),
]
SENHA_PADRAO = "chamati123"

TITULOS = [
    ("Impressora do 2º andar não imprime", "A impressora acusa erro de comunicação desde ontem. "
                                           "Já reiniciei o equipamento e o computador."),
    ("Não consigo acessar o sistema de notas", "Ao entrar aparece a mensagem 'usuário sem "
                                               "permissão'. Preciso do acesso para fechar o mês."),
    ("Wi-Fi cai a cada 10 minutos na sala 3", "A conexão cai e volta sozinha. Acontece com todos "
                                              "os notebooks da sala."),
    ("Excel trava ao abrir a planilha de fechamento", "O arquivo tem 40 MB e o Excel para de "
                                                      "responder ao abrir a aba de resumo."),
    ("E-mails da lista comercial não chegam", "Desde segunda-feira não recebo as mensagens "
                                              "enviadas para comercial@empresa.com."),
    ("Notebook desliga sozinho", "O equipamento desliga após cerca de 20 minutos de uso, mesmo "
                                 "conectado à tomada."),
    ("Senha bloqueada após troca", "Troquei a senha ontem e hoje a conta apareceu bloqueada."),
    ("VPN não conecta de casa", "A VPN fica em 'conectando' e depois expira. Testei em duas redes."),
]


def _obter_ou_criar(modelo, filtros, **campos):
    registro = modelo.query.filter_by(**filtros).first()
    if registro is None:
        registro = modelo(**{**filtros, **campos})
        db.session.add(registro)
    return registro


def popular(quantidade_chamados=60, semente=42):
    """Idempotente: pode ser executado mais de uma vez sem duplicar domínios."""
    aleatorio = random.Random(semente)

    for nome, descricao in CATEGORIAS:
        _obter_ou_criar(Categoria, {"nome": nome}, descricao=descricao, ativo=True)
    for nome, sla, ordem in PRIORIDADES:
        _obter_ou_criar(Prioridade, {"nome": nome}, sla_horas=sla, ordem=ordem)
    for nome, encerra, ordem in STATUS:
        _obter_ou_criar(Status, {"nome": nome}, encerra=encerra, ordem=ordem)
    db.session.commit()

    for nome, email, perfil, departamento in USUARIOS:
        if Usuario.query.filter_by(email=email).first() is None:
            usuario = Usuario(nome=nome, email=email, perfil=perfil,
                              departamento=departamento)
            usuario.definir_senha(SENHA_PADRAO)
            db.session.add(usuario)
    db.session.commit()

    if Chamado.query.count() >= quantidade_chamados:
        return {"chamados": Chamado.query.count(), "usuarios": Usuario.query.count()}

    categorias = Categoria.query.all()
    prioridades = Prioridade.query.all()
    status_por_nome = {s.nome: s for s in Status.query.all()}
    solicitantes = Usuario.query.filter_by(perfil=Perfil.SOLICITANTE).all()
    tecnicos = Usuario.query.filter_by(perfil=Perfil.TECNICO).all()

    agora = datetime.now(timezone.utc)
    ano = agora.year
    for i in range(1, quantidade_chamados + 1):
        titulo, descricao = TITULOS[(i - 1) % len(TITULOS)]
        abertura = agora - timedelta(days=aleatorio.randint(0, 60),
                                     hours=aleatorio.randint(0, 23))
        sorteio = aleatorio.random()
        if sorteio < 0.45:
            nome_status = "Resolvido"
        elif sorteio < 0.8:
            nome_status = "Em atendimento"
        else:
            nome_status = "Aberto"

        status = status_por_nome[nome_status]
        tecnico = aleatorio.choice(tecnicos) if nome_status != "Aberto" else None
        encerramento = None
        solucao = None
        if nome_status == "Resolvido":
            encerramento = abertura + timedelta(hours=aleatorio.randint(1, 60))
            solucao = "Atendimento concluído: causa identificada, correção aplicada e " \
                      "funcionamento validado com o solicitante."

        chamado = Chamado(
            protocolo=f"{ano}-{i:06d}",
            titulo=f"{titulo} ({i})",
            descricao=descricao,
            categoria_id=aleatorio.choice(categorias).id,
            prioridade_id=aleatorio.choice(prioridades).id,
            status_id=status.id,
            solicitante_id=aleatorio.choice(solicitantes).id,
            tecnico_id=tecnico.id if tecnico else None,
            data_abertura=abertura,
            data_encerramento=encerramento,
            solucao=solucao,
        )
        db.session.add(chamado)
        db.session.flush()
        db.session.add(Interacao(chamado_id=chamado.id,
                                 autor_id=chamado.solicitante_id,
                                 mensagem="Chamado aberto pelo solicitante.",
                                 tipo="sistema",
                                 criado_em=abertura))
    db.session.commit()
    return {"chamados": Chamado.query.count(), "usuarios": Usuario.query.count()}
