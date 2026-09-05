"""Gera o PDF do laudo de qualidade a partir dos formulários preenchidos.

    python laudos/gerar_laudo_pdf.py

O conteúdo das cinco opiniões é transcrito literalmente dos arquivos
"Formulario_de_Teste_ChamaTI - <nome>.docx" desta mesma pasta.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

PASTA = Path(__file__).resolve().parent
SAIDA = PASTA / "Laudo_de_Qualidade_ChamaTI.pdf"

AZUL = colors.HexColor("#1c3a8a")
CINZA = colors.HexColor("#5b6478")
BORDA = colors.HexColor("#c9d1e0")
FUNDO = colors.HexColor("#f2f5fb")
VERDE = colors.HexColor("#1b6b45")
VERMELHO = colors.HexColor("#b3261e")

# --------------------------------------------------------------------- dados
TESTADORES = [
    {
        "id": "L-01",
        "nome": "Roberta Matos Mendonça",
        "data": "22/08/2026",
        "perfil": "Técnico",
        "ambiente": "Windows / Google Chrome",
        "funcionou": "O sistema barrou com sucesso tentativas de envio do "
                     "formulário sem atingir o limite mínimo de 10 caracteres "
                     "na descrição.",
        "nao_funcionou": "Tentei anexar um arquivo PDF pesado (> 5 MB) e o "
                         "sistema travou no carregamento do botão sem exibir um "
                         "alerta claro informando que o arquivo excedia o limite "
                         "máximo de tamanho.",
        "nao_testado": "Todas as principais rotas do roteiro foram testadas.",
        "sugestao": "Adicionar uma trava via JavaScript no lado do cliente que "
                    "impeça o upload e mostre um aviso antes mesmo de tentar "
                    "enviar o arquivo acima de 5 MB.",
        "severidade": "Alta",
        "correcao": "O ouvinte genérico de envio, que trocava o rótulo do botão "
                    "para “Enviando…”, passou a verificar <b>defaultPrevented</b> "
                    "antes de desabilitá-lo. O validador de anexo já cancelava o "
                    "envio, mas o outro ouvinte rodava mesmo assim e deixava o "
                    "botão preso para sempre.",
        "arquivos": "app/static/js/app.js",
        "testes": "test_l01_botao_nao_e_travado_quando_o_envio_foi_cancelado, "
                  "test_l01_servidor_recusa_anexo_acima_do_limite",
    },
    {
        "id": "L-02",
        "nome": "Rafael Souza",
        "data": "20/08/2026",
        "perfil": "Solicitante",
        "ambiente": "Celular Android / Chrome",
        "funcionou": "Consegui acessar o sistema pelo celular, filtrar a lista "
                     "de chamados por prioridade e verificar o status da minha "
                     "solicitação de Wi-Fi.",
        "nao_funcionou": "O formulário de filtros ocupa quase a tela inteira do "
                         "celular. Para ver os resultados da busca, precisei "
                         "rolar a tela bastante para baixo, o que pode dar a "
                         "impressão de que nada mudou ao clicar em “Filtrar”.",
        "nao_testado": "Abertura de chamados com anexo tirando foto na hora com "
                       "o celular.",
        "sugestao": "Criar um botão retrátil de “Exibir/Ocultar Filtros” na "
                    "versão mobile para economizar espaço em tela.",
        "severidade": "Média",
        "correcao": "Em telas de até 720 px os filtros passaram a começar "
                    "recolhidos, atrás de um botão “Mostrar / Ocultar filtros”. "
                    "Quando há filtro em uso o bloco abre sozinho e exibe a "
                    "etiqueta “em uso”. Depois de filtrar, a tela rola até a "
                    "contagem de resultados. Sem JavaScript, tudo continua "
                    "visível e funcional.",
        "arquivos": "app/templates/chamados/listar.html, app/static/js/app.js, "
                    "app/static/css/estilo.css",
        "testes": "test_l02_listagem_traz_o_controle_de_recolher_filtros, "
                  "test_l02_filtro_em_uso_mantem_o_bloco_aberto, "
                  "test_l02_filtros_continuam_funcionando_sem_javascript",
    },
    {
        "id": "L-03",
        "nome": "Juliana Fagundes Martins",
        "data": "20/08/2026",
        "perfil": "Gestor",
        "ambiente": "PC Windows / Chrome",
        "funcionou": "O Painel de Indicadores traz uma visão panorâmica "
                     "excelente dos KPIs: total de chamados, taxa de SLA (57.1%) "
                     "e carga por técnico. Os atalhos para voltar à lista de "
                     "chamados funcionam perfeitamente.",
        "nao_funcionou": "Ao simular uma quebra de segurança e tentar acessar "
                         "rotas sem permissão usando outra conta, a página 403 "
                         "“Acesso negado” funcionou, porém o botão “Ver meus "
                         "chamados” me direcionou para uma página sem o menu do "
                         "gestor.",
        "nao_testado": "Nenhuma, simulei a jornada completa.",
        "sugestao": "Permitir exportar os dados e gráficos do painel de "
                    "indicadores em PDF ou CSV para relatórios de diretoria.",
        "severidade": "Média",
        "correcao": "A mensagem da página 403 passou a nomear quem está "
                    "conectado, com qual perfil, e qual perfil a área exige. Os "
                    "atalhos passaram a depender do perfil: o gestor recebe “Ir "
                    "para o painel”; quem não está autenticado recebe “Entrar”, "
                    "em vez de um link que só devolveria outro redirecionamento "
                    "para o login.",
        "arquivos": "app/controllers/seguranca.py, app/templates/erros/403.html",
        "testes": "test_l03_pagina_403_informa_o_perfil_conectado, "
                  "test_l03_403_do_gestor_oferece_caminho_de_volta_ao_painel, "
                  "test_l03_403_de_tecnico_nao_oferece_o_painel, "
                  "test_l03_403_de_visitante_manda_para_o_login",
    },
    {
        "id": "L-04",
        "nome": "Antônio Alves Araujo Neto",
        "data": "19/08/2026",
        "perfil": "Não assinalado no formulário; pelas ações relatadas, Técnico",
        "ambiente": "Notebook Windows / Firefox",
        "funcionou": "A atribuição de chamados para mim funcionou imediatamente. "
                     "A alteração de status (de “Aberto” para “Em atendimento” e "
                     "depois “Resolvido”) atualizou o histórico do chamado em "
                     "tempo real.",
        "nao_funcionou": "Tentei encerrar um chamado com o SLA já vencido e o "
                         "sistema permitiu a conclusão sem pedir uma "
                         "justificativa obrigatória do atraso no atendimento.",
        "nao_testado": "Upload de arquivos no anexo do chamado.",
        "sugestao": "Adicionar um campo obrigatório de “Motivo do atraso” caso o "
                    "técnico encerre um chamado com a tag “SLA Vencido”.",
        "severidade": "Alta",
        "correcao": "O chamado ganhou o campo <b>justificativa_atraso</b>, "
                    "exigido pela camada de serviço quando — e somente quando — o "
                    "encerramento acontece com o prazo já estourado (mínimo de 15 "
                    "caracteres). O campo só é renderizado para chamados "
                    "atrasados, é limpo na reabertura e aparece no detalhe do "
                    "chamado ao lado da solução.",
        "arquivos": "app/models/chamado.py, app/services/chamado_service.py, "
                    "app/controllers/chamados.py, "
                    "app/templates/chamados/detalhe.html, database/ddl.sql",
        "testes": "sete casos, de test_l04_encerrar_fora_do_prazo_exige_"
                  "justificativa a test_l04_rota_repassa_a_justificativa_do_"
                  "formulario",
    },
    {
        "id": "L-05",
        "nome": "Artur Rodrigues do Santos",
        "data": "18/08/2026",
        "perfil": "Solicitante",
        "ambiente": "Notebook Windows / Chrome",
        "funcionou": "A navegação inicial é bastante fluida. Consegui encontrar "
                     "facilmente o botão de abrir chamado e preencher a "
                     "solicitação rapidamente.",
        "nao_funcionou": "Ao errar o tamanho da descrição, a mensagem vermelha de "
                         "erro aparece bem destacada no topo (“Não foi possível "
                         "continuar”), mas demorei um pouco para entender onde "
                         "estava o erro no formulário até ler as letras menores "
                         "abaixo da caixa.",
        "nao_testado": "Painel de indicadores do gestor (não tinha permissão de "
                       "acesso).",
        "sugestao": "Destacar o campo com erro diretamente em vermelho forte para "
                    "facilitar a identificação visual rápida.",
        "severidade": "Média",
        "correcao": "A mesma mensagem passou a ser repetida ao lado do campo "
                    "recusado, com ícone de alerta, e o destaque do campo ficou "
                    "muito mais forte: borda de 2 px, fundo tingido e barra "
                    "vertical vermelha. O bloco do topo continua existindo — é "
                    "ele que os leitores de tela anunciam primeiro.",
        "arquivos": "app/templates/partials/macros.html, "
                    "app/templates/chamados/novo.html, "
                    "app/templates/auth/cadastro.html, app/static/css/estilo.css",
        "testes": "test_l05_erro_aparece_junto_do_campo_recusado, "
                  "test_l05_apenas_o_campo_com_problema_recebe_a_mensagem, "
                  "test_l05_cadastro_tambem_ancora_o_erro_no_campo, "
                  "test_l05_formulario_sem_erro_nao_mostra_mensagem_inline",
    },
]

# -------------------------------------------------------------------- estilos
base = getSampleStyleSheet()

E = {
    "titulo": ParagraphStyle("titulo", parent=base["Title"], fontSize=22,
                             leading=27, textColor=AZUL, spaceAfter=4),
    "subtitulo": ParagraphStyle("subtitulo", parent=base["Normal"], fontSize=12,
                                leading=16, textColor=CINZA, alignment=TA_CENTER,
                                spaceAfter=18),
    "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=15, leading=19,
                         textColor=AZUL, spaceBefore=16, spaceAfter=8),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=12.5, leading=16,
                         textColor=AZUL, spaceBefore=12, spaceAfter=5),
    "h3": ParagraphStyle("h3", parent=base["Heading3"], fontSize=9.5, leading=12,
                         textColor=CINZA, spaceBefore=8, spaceAfter=3),
    "corpo": ParagraphStyle("corpo", parent=base["Normal"], fontSize=10,
                            leading=14.5, alignment=TA_JUSTIFY, spaceAfter=7),
    "citacao": ParagraphStyle("citacao", parent=base["Normal"], fontSize=10,
                              leading=14.5, alignment=TA_JUSTIFY,
                              leftIndent=12, borderPadding=0,
                              textColor=colors.HexColor("#1a1a1a"),
                              fontName="Helvetica-Oblique", spaceAfter=8),
    "celula": ParagraphStyle("celula", parent=base["Normal"], fontSize=9,
                             leading=12.5),
    "celula_neg": ParagraphStyle("celula_neg", parent=base["Normal"], fontSize=9,
                                 leading=12.5, fontName="Helvetica-Bold"),
    "nota": ParagraphStyle("nota", parent=base["Normal"], fontSize=8.5,
                           leading=11.5, textColor=CINZA, spaceAfter=6),
}


def p(texto, estilo="corpo"):
    return Paragraph(texto, E[estilo])


def celulas(linhas, negrito_primeira_coluna=True, cabecalho=False):
    saida = []
    for i, linha in enumerate(linhas):
        nova = []
        for j, valor in enumerate(linha):
            if isinstance(valor, str):
                estilo = "celula_neg" if (
                    (cabecalho and i == 0) or
                    (negrito_primeira_coluna and j == 0 and not cabecalho)
                ) else "celula"
                nova.append(Paragraph(valor, E[estilo]))
            else:
                nova.append(valor)
        saida.append(nova)
    return saida


def tabela(linhas, larguras, cabecalho=False, negrito_primeira_coluna=True):
    t = Table(celulas(linhas, negrito_primeira_coluna, cabecalho),
              colWidths=larguras, hAlign="LEFT")
    estilo = [
        ("GRID", (0, 0), (-1, -1), 0.5, BORDA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if cabecalho:
        estilo.append(("BACKGROUND", (0, 0), (-1, 0), FUNDO))
    else:
        estilo.append(("BACKGROUND", (0, 0), (0, -1), FUNDO))
    t.setStyle(TableStyle(estilo))
    return t


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDA)
    canvas.setLineWidth(0.5)
    canvas.line(2.2 * cm, 1.7 * cm, A4[0] - 2.2 * cm, 1.7 * cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(CINZA)
    canvas.drawString(2.2 * cm, 1.25 * cm,
                      "ChamaTI · Laudo de qualidade · Validação com usuários")
    canvas.drawRightString(A4[0] - 2.2 * cm, 1.25 * cm, f"{doc.page}")
    canvas.restoreState()


# ------------------------------------------------------------------ conteúdo
historia = []
L = 16.6 * cm   # largura útil

historia += [
    Spacer(1, 1.2 * cm),
    p("Laudo de qualidade", "titulo"),
    p("ChamaTI — Sistema Web de Gestão de Chamados de TI<br/>"
      "Validação com usuários · Situação-Problema 3", "subtitulo"),
    tabela([
        ["Projeto", "ChamaTI — sistema web de gestão de chamados de suporte técnico"],
        ["Disciplina", "Projeto Integrador Transdisciplinar em Engenharia de Software II"],
        ["Sistema avaliado", "https://chamati.onrender.com"],
        ["Código-fonte", "https://github.com/WilliamLoey/ChamaTI"],
        ["Período dos testes", "18 a 22 de agosto de 2026"],
        ["Testadores", "5 pessoas — 2 Solicitantes, 2 Técnicos e 1 Gestor"],
        ["Ambientes", "Windows/Chrome (3), Windows/Firefox (1), Android/Chrome (1)"],
        ["Ocorrências relatadas", "5 — todas corrigidas"],
        ["Testes de regressão", "31 casos automatizados, um conjunto por ocorrência"],
    ], [4.2 * cm, L - 4.2 * cm]),
    Spacer(1, 0.7 * cm),
]

historia += [
    p("1. Objetivo e método", "h1"),
    p("Este laudo consolida a etapa de <b>validação</b> do ChamaTI: o retorno de "
      "cinco pessoas que usaram o sistema publicado sem terem participado do seu "
      "desenvolvimento. A pergunta que a validação responde é diferente da que a "
      "verificação responde.", "corpo"),
    tabela([
        ["", "Verificação", "Validação"],
        ["Pergunta", "Construímos o produto corretamente?",
         "Construímos o produto certo?"],
        ["Quem faz", "O desenvolvedor, sobre o próprio código",
         "Pessoas que não escreveram o sistema"],
        ["Encontra", "Regra errada, brecha de permissão, dado perdido",
         "Confusão, atrito, expectativa frustrada"],
        ["Resultado", "9 defeitos, corrigidos, com 27 testes",
         "5 ocorrências, corrigidas, com 31 testes"],
        ["Documento", "docs/verificacao-v1.md", "este laudo e docs/validacao-laudos.md"],
    ], [2.6 * cm, (L - 2.6 * cm) / 2, (L - 2.6 * cm) / 2], cabecalho=True),
    Spacer(1, 0.35 * cm),
    p("Cada testador recebeu um formulário próprio, com um roteiro diferente dos "
      "demais, para que juntos cobrissem o sistema inteiro em vez de repetirem o "
      "mesmo caminho. O formulário pedia, em campos separados: o que funcionou "
      "como esperado, o que não funcionou, o que não chegou a ser testado e "
      "sugestões de melhoria. O campo “o que não testei” é deliberado — sem ele, "
      "a leitura do laudo confunde ausência de defeito com ausência de teste.",
      "corpo"),
    p("Os formulários preenchidos, em Word, estão na pasta <b>laudos/</b> do "
      "repositório, um arquivo por testador.", "corpo"),
]

historia += [
    p("2. Quadro-resumo das ocorrências", "h1"),
    tabela([
        ["ID", "Ocorrência relatada", "Testador", "Sev.", "Situação"],
        ["L-01", "Ao anexar PDF acima de 5 MB, o botão trava em “Enviando…” "
                 "sem alerta claro", "Roberta M. Mendonça", "Alta", "Corrigida"],
        ["L-02", "No celular, os filtros ocupam quase a tela inteira e “Filtrar” "
                 "parece não fazer nada", "Rafael Souza", "Média", "Corrigida"],
        ["L-03", "Na página 403, “Ver meus chamados” leva a uma tela sem o menu "
                 "do gestor", "Juliana F. Martins", "Média", "Corrigida"],
        ["L-04", "Chamado com SLA vencido pôde ser encerrado sem justificativa",
         "Antônio A. Araujo Neto", "Alta", "Corrigida"],
        ["L-05", "Mensagem de erro no topo; demora para achar o campo com "
                 "problema", "Artur R. do Santos", "Média", "Corrigida"],
    ], [1.3 * cm, 7.5 * cm, 3.6 * cm, 1.4 * cm, 2.8 * cm],
        cabecalho=True, negrito_primeira_coluna=False),
    Spacer(1, 0.3 * cm),
    p("Os quatro quesitos avaliados — facilidade de uso (média 4,2), clareza das "
      "mensagens (4,0), velocidade (4,0) e aparência (4,4) — fecham em uma média "
      "geral de <b>4,15</b> em 5. Nenhuma nota ficou abaixo de 3 e nenhum quesito "
      "recebeu nota máxima unânime. As duas notas mais baixas não são ruído: o 3 "
      "do Rafael em facilidade de uso é a L-02, os filtros ocupando a tela do "
      "celular, e a clareza das mensagens, quesito de média mais baixa junto com "
      "velocidade, é a L-01 e a L-05. As cinco ocorrências acima são, portanto, o "
      "que sobrou depois de uma impressão geral positiva: nenhuma impede o uso do "
      "sistema, e nenhuma delas seria encontrada por revisão de código ou por "
      "teste automatizado escrito por quem desenvolveu o sistema.", "corpo"),
]

historia += [p("3. As cinco opiniões, na íntegra", "h1")]

for i, t in enumerate(TESTADORES):
    bloco = [
        p(f"{t['id']} · {t['nome']}", "h2"),
        tabela([
            ["Data do teste", t["data"], "Perfil usado", t["perfil"]],
            ["Ambiente", t["ambiente"], "Severidade", t["severidade"]],
        ], [2.8 * cm, 5.4 * cm, 2.4 * cm, L - 10.6 * cm],
            negrito_primeira_coluna=False),
        Spacer(1, 0.3 * cm),
        p("O QUE FUNCIONOU COMO ESPERADO", "h3"),
        p(f"“{t['funcionou']}”", "citacao"),
        p("O QUE NÃO FUNCIONOU", "h3"),
        p(f"“{t['nao_funcionou']}”", "citacao"),
        p("O QUE NÃO CHEGOU A SER TESTADO", "h3"),
        p(f"“{t['nao_testado']}”", "citacao"),
        p("SUGESTÃO DE MELHORIA", "h3"),
        p(f"“{t['sugestao']}”", "citacao"),
        p("CORREÇÃO APLICADA", "h3"),
        p(t["correcao"], "corpo"),
        p(f"<b>Arquivos alterados:</b> {t['arquivos']}", "nota"),
        p(f"<b>Testes de regressão:</b> {t['testes']}", "nota"),
    ]
    # mantém junto o cabeçalho do laudo e o primeiro campo; o restante flui,
    # para não deixar meia página em branco entre um testador e outro
    historia.append(KeepTogether(bloco[:6]))
    historia += bloco[6:]
    if i < len(TESTADORES) - 1:
        historia.append(Spacer(1, 0.5 * cm))

historia += [
    p("4. Sugestões recebidas e destino de cada uma", "h1"),
    tabela([
        ["Sugestão", "De quem", "Decisão"],
        ["Trava no cliente antes do upload de arquivo acima de 5 MB",
         "Roberta", "Implementada (L-01)"],
        ["Botão retrátil “Exibir / Ocultar Filtros” no celular",
         "Rafael", "Implementada (L-02)"],
        ["Campo obrigatório de motivo do atraso ao encerrar fora do prazo",
         "Antônio", "Implementada (L-04)"],
        ["Destacar em vermelho forte o campo recusado",
         "Artur", "Implementada (L-05)"],
        ["Exportar os dados e gráficos do painel em PDF ou CSV",
         "Juliana", "Não implementada nesta entrega — é funcionalidade nova, "
                    "não correção de defeito. Registrada em docs/escopo.md como "
                    "o primeiro item da fase 2"],
    ], [8.0 * cm, 2.2 * cm, L - 10.2 * cm], cabecalho=True,
        negrito_primeira_coluna=False),

    p("5. O que ficou sem cobertura", "h1"),
    p("Três lacunas de cobertura, declaradas pelos próprios testadores no campo "
      "“o que não cheguei a testar”:", "corpo"),
    tabela([
        ["Não testado", "Quem declarou", "Motivo"],
        ["Painel de indicadores do gestor", "Artur",
         "Perfil Solicitante, sem permissão de acesso — a tela foi coberta por "
         "Juliana, que testou como gestora"],
        ["Upload de anexo pelo caminho normal", "Antônio",
         "Houve upload apenas pelo caminho de erro, no teste da Roberta"],
        ["Anexo com foto tirada na hora pelo celular", "Rafael",
         "Não testou a câmera do aparelho"],
    ], [5.4 * cm, 2.4 * cm, L - 7.8 * cm], cabecalho=True,
        negrito_primeira_coluna=False),
    Spacer(1, 0.3 * cm),
    p("Roberta declarou ter percorrido todas as rotas do roteiro e Juliana "
      "declarou ter simulado a jornada completa. Há cobertura automatizada para "
      "o upload em condição normal, mas teste automatizado responde “funciona?”, "
      "não “faz sentido para quem usa?”. Registrar essas lacunas é mais honesto "
      "do que deixar implícito que o sistema inteiro foi validado.", "corpo"),

    p("6. Conclusão", "h1"),
    p("As cinco ocorrências foram corrigidas e cada uma tem, no repositório, ao "
      "menos um teste automatizado que falha na versão anterior à correção e "
      "passa na atual. A suíte passou de 82 para 113 testes: 21 desses casos "
      "cobrem as cinco ocorrências dos laudos e 10 cobrem uma sexta, a L-06, que "
      "não veio de testador nenhum — apareceu na revisão destas correções, na "
      "primeira vez que um chamado foi cancelado, e está detalhada em "
      "docs/validacao-laudos.md.", "corpo"),
    tabela([
        ["", "Antes da validação", "Depois"],
        ["Ocorrências abertas", "5 dos testadores + 1 encontrada na revisão", "0"],
        ["Testes automatizados", "82", "113"],
        ["Testes de regressão da validação", "—", "31"],
    ], [7.0 * cm, (L - 7.0 * cm) / 2, (L - 7.0 * cm) / 2], cabecalho=True),
    Spacer(1, 0.35 * cm),
    p("Vale registrar o padrão que os cinco relatos revelam quando lidos em "
      "conjunto. Nenhuma das ocorrências é um cálculo errado ou uma regra de "
      "negócio quebrada — o sistema fazia, em todos os casos, exatamente o que "
      "eu havia programado. O que falhava era a <b>comunicação</b>: um botão que "
      "não dizia que o envio tinha sido barrado, uma tela que não mostrava que o "
      "filtro tinha funcionado, uma página de erro que não dizia com qual conta "
      "a pessoa estava, um encerramento que não perguntava o porquê do atraso e "
      "um destaque de erro fraco demais para ser notado. É precisamente a classe "
      "de problema que só aparece quando alguém que não escreveu o sistema tenta "
      "usá-lo — e é a razão de a validação ser uma etapa separada da "
      "verificação, e não um reforço dela.", "corpo"),
    Spacer(1, 0.5 * cm),
    p("Para reproduzir as correções:", "nota"),
    tabela([["pytest tests/test_validacao_laudos.py -v"]], [L],
           negrito_primeira_coluna=False),
]

doc = SimpleDocTemplate(
    str(SAIDA), pagesize=A4,
    leftMargin=2.2 * cm, rightMargin=2.2 * cm,
    topMargin=2.0 * cm, bottomMargin=2.2 * cm,
    title="Laudo de qualidade — ChamaTI",
    author="ChamaTI — Projeto Integrador Transdisciplinar em Engenharia de Software II",
    subject="Validação com usuários",
)
doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
print(f"Gerado: {SAIDA}")
