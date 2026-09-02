# Validação com usuários — laudos e correções aplicadas

Este documento fecha a etapa de **validação** da Situação-Problema 3. Ele registra
o que cinco pessoas encontraram usando o ChamaTI publicado em
<https://chamati.onrender.com>, o que foi feito com cada achado e onde está o
teste que impede o problema de voltar.

A etapa anterior, a **verificação**, está em
[`verificacao-v1.md`](verificacao-v1.md) — nove defeitos que eu encontrei
revisando o próprio código. São coisas diferentes:

| | Verificação | Validação |
|---|---|---|
| Pergunta | Construímos o produto corretamente? | Construímos o produto certo? |
| Quem faz | Eu, sobre o meu código | Pessoas que não escreveram o sistema |
| Acha o quê | Regra errada, brecha de permissão, dado perdido | Confusão, atrito, expectativa frustrada |
| Onde está | `docs/verificacao-v1.md` | este arquivo |

Os cinco defeitos abaixo têm uma característica em comum: **nenhum deles seria
encontrado por revisão de código ou por teste automatizado escrito por mim.**
Todos são consequência de alguém esperar do sistema algo diferente do que eu
assumi ao escrevê-lo. É exatamente o que a validação existe para pegar.

---

## Os testes

| | |
|---|---|
| Período | 18 a 22 de agosto de 2026 |
| Testadores | 5 |
| Perfis cobertos | Solicitante (2), Técnico (2), Gestor (1) |
| Ambientes | Windows/Chrome (3), Windows/Firefox (1), Android/Chrome (1) |
| Formulários preenchidos | `laudos/laudo-01-roberta.docx` … `laudo-05-artur.docx` |

| # | Testador | Perfil | Ambiente | Data |
|---|---|---|---|---|
| 01 | Roberta Matos Mendonça | Técnico | Windows / Chrome | 22/08/2026 |
| 02 | Rafael Souza | Solicitante | Celular Android / Chrome | 20/08/2026 |
| 03 | Juliana Fagundes Martins | Gestor | PC Windows / Chrome | 20/08/2026 |
| 04 | Antônio Alves Araujo Neto | não assinalado; pelas ações relatadas, Técnico | Notebook Windows / Firefox | 19/08/2026 |
| 05 | Artur Rodrigues do Santos | Solicitante | Notebook Windows / Chrome | 18/08/2026 |

Cada testador recebeu um roteiro diferente, para que juntos cobrissem o sistema
inteiro em vez de repetirem o mesmo caminho feliz. Os cinco avaliaram
facilidade, clareza, velocidade e aparência — e nos quatro quesitos a nota foi a
máxima, o que torna os cinco achados abaixo ainda mais úteis: são o que sobrou
quando a impressão geral já era boa.

---

## Ocorrências

### L-01 · Botão travado em "Enviando…" ao anexar arquivo grande

| | |
|---|---|
| Relatado por | Roberta Matos Mendonça — perfil Técnico, Windows/Chrome, 22/08/2026 |
| Severidade | **Alta** — o formulário fica inutilizável até recarregar a página |
| Situação | Corrigido |

**O relato.** *"Tentei anexar um arquivo PDF pesado (> 5 MB) e o sistema travou
no carregamento do botão sem exibir um alerta claro informando que o arquivo
excedia o limite máximo de tamanho."*

Ela sugeriu, com precisão cirúrgica, a correção certa: uma trava no lado do
cliente que impeça o upload e mostre o aviso antes de tentar enviar.

**A causa.** Havia dois ouvintes no `submit` do formulário. O primeiro validava
o tamanho do anexo e chamava `preventDefault()` quando o arquivo era grande
demais. O segundo — genérico, aplicado a todos os formulários para evitar duplo
clique — desabilitava o botão e trocava o texto para "Enviando…". O
`preventDefault()` cancela o envio, mas **não impede o segundo ouvinte de
rodar**. Resultado: o envio era barrado, o botão era desabilitado, e nada mais
acontecia. O aviso de tamanho até aparecia, mas acima do botão, fora do campo de
visão de quem estava olhando para ele.

**A correção.** O ouvinte genérico passou a checar `evento.defaultPrevented`
antes de desabilitar o botão. Se alguém já cancelou o envio, ele não faz nada.

`app/static/js/app.js`, função `evitarEnvioDuplicado`.

**Testes.** `tests/test_validacao_laudos.py::test_l01_botao_nao_e_travado_quando_o_envio_foi_cancelado`
e `::test_l01_servidor_recusa_anexo_acima_do_limite`.

---

### L-02 · Filtros ocupam a tela inteira no celular

| | |
|---|---|
| Relatado por | Rafael Souza — perfil Solicitante, Android/Chrome, 20/08/2026 |
| Severidade | **Média** — usabilidade; nada quebra, mas o sistema parece não responder |
| Situação | Corrigido |

**O relato.** *"O formulário de filtros ocupa quase a tela inteira do celular.
Para ver os resultados da busca, precisei rolar a tela bastante para baixo, o que
pode dar a impressão de que nada mudou ao clicar em 'Filtrar'."*

A sugestão dele foi literalmente um botão retrátil de "Exibir / Ocultar Filtros"
na versão mobile.

**A medição.** Confirmei o relato antes de mexer no código: com viewport de
727 px de altura, a página de listagem tinha 1 870 px — **2,6 telas**. Os seis
campos de filtro empurravam a lista de resultados inteiramente para fora da
primeira dobra. Depois de submeter, a página recarrega no topo, e o topo é
sempre o mesmo formulário. Quem não rolasse veria exatamente a tela anterior.

**A correção.** Duas mudanças, ambas só em telas de até 720 px:

1. Um botão "Mostrar / Ocultar filtros" acima do formulário, que começa
   **recolhido** — a menos que já haja algum filtro em uso, caso em que abre
   aberto e exibe uma etiqueta "em uso", para o filtro ativo nunca ficar
   invisível.
2. Depois de filtrar, a tela rola até a contagem de resultados.

O formulário continua sendo um `GET` comum: com o JavaScript desligado, tudo
aparece como antes e o filtro funciona igual. O recolhimento é conveniência, não
requisito.

`app/templates/chamados/listar.html`, `app/static/js/app.js`
(`filtrosRecolhiveis`, `irParaResultados`), `app/static/css/estilo.css`.

**Testes.** `::test_l02_listagem_traz_o_controle_de_recolher_filtros`,
`::test_l02_filtro_em_uso_mantem_o_bloco_aberto`,
`::test_l02_filtros_continuam_funcionando_sem_javascript`.

---

### L-03 · Página de acesso negado leva a um beco sem saída

| | |
|---|---|
| Relatado por | Juliana Fagundes Martins — perfil Gestor, Windows/Chrome, 20/08/2026 |
| Severidade | **Média** — o bloqueio funciona; o que falha é a saída |
| Situação | Corrigido |

**O relato.** *"Ao simular uma quebra de segurança e tentar acessar rotas sem
permissão usando outra conta, a página 403 'Acesso negado' funcionou, porém o
botão 'Ver meus chamados' me direcionou para uma página sem o menu do gestor."*

Repare no detalhe que explica tudo: ela estava **usando outra conta**.

**A causa.** A página 403 tinha dois botões fixos — "Ir para o início" e "Ver
meus chamados" — iguais para todo mundo. Para quem administra o sistema, nenhum
dos dois é o destino desejado: o gestor quer voltar ao painel. E a mensagem
dizia apenas que "o seu perfil não tem acesso", sem informar **qual** perfil
estava ativo — o que importa muito para quem tem mais de uma conta e testa o
sistema alternando entre elas, que era exatamente o caso.

**A correção.**

- A mensagem passou a nomear quem está conectado, com qual perfil, e qual perfil
  a área exige: *"Você está conectado como Fulano, com o perfil Técnico. Esta
  área é restrita ao perfil Gestor…"*
- Os atalhos passaram a depender do perfil: o gestor ganha "Ir para o painel";
  quem não está autenticado recebe "Entrar" em vez de um "Ver meus chamados" que
  só devolveria outro redirecionamento para o login.

`app/controllers/seguranca.py`, `app/templates/erros/403.html`.

**Testes.** `::test_l03_pagina_403_informa_o_perfil_conectado`,
`::test_l03_403_do_gestor_oferece_caminho_de_volta_ao_painel`,
`::test_l03_403_de_tecnico_nao_oferece_o_painel`,
`::test_l03_403_de_visitante_manda_para_o_login`.

---

### L-04 · Chamado fora do prazo é encerrado sem explicação

| | |
|---|---|
| Relatado por | Antônio Alves Araujo Neto — Notebook Windows/Firefox, 19/08/2026 |
| Severidade | **Alta** — compromete o indicador de SLA, que é o entregável do painel |
| Situação | Corrigido |

**O relato.** *"Tentei encerrar um chamado com o SLA já vencido e o sistema
permitiu a conclusão sem pedir uma justificativa obrigatória do atraso no
atendimento."*

A sugestão foi um campo obrigatório de "Motivo do atraso" quando o técnico
encerra um chamado marcado como SLA vencido — que é exatamente o que foi feito.

**Por que importa.** O sistema já exigia descrever a solução para encerrar, e já
marcava o chamado como vencido. Mas o painel do gestor mostrava *que* se atrasou
e nunca *por quê* — e "por quê" é a única informação que permite agir. Um atraso
por falta de peça, um por fila alta e um por chamado esquecido geram decisões
completamente diferentes, e os três apareciam idênticos no indicador.

**A correção.** Um campo `justificativa_atraso` no chamado, exigido pela camada
de serviço quando — e somente quando — o chamado é encerrado com o prazo já
estourado. Mínimo de 15 caracteres, para não virar um "atrasou" de uma palavra.
No formulário o campo só é renderizado para chamados que de fato atrasaram: quem
está no prazo não vê nem responde nada disso. Reabrir o chamado limpa a
justificativa junto com a solução e a data de encerramento.

A justificativa aparece no detalhe do chamado, num bloco próprio ao lado da
solução.

`app/models/chamado.py`, `app/services/chamado_service.py`,
`app/controllers/chamados.py`, `app/templates/chamados/detalhe.html`,
`database/ddl.sql`, `database/dicionario-de-dados.md`.

**Testes.** Sete casos, de `::test_l04_encerrar_fora_do_prazo_exige_justificativa`
a `::test_l04_rota_repassa_a_justificativa_do_formulario` — incluindo o caminho
negativo (chamado no prazo **não** deve pedir nada) e a limpeza na reabertura.

---

### L-05 · Mensagem de erro longe do campo que a causou

| | |
|---|---|
| Relatado por | Artur Rodrigues do Santos — perfil Solicitante, Windows/Chrome, 18/08/2026 |
| Severidade | **Média** — atrito na tarefa mais frequente do sistema |
| Situação | Corrigido |

**O relato.** *"Ao errar o tamanho da descrição, a mensagem vermelha de erro
aparece bem destacada no topo ('Não foi possível continuar'), mas demorei um
pouco para entender onde estava o erro no formulário até ler as letras menores
abaixo da caixa."*

O relato é preciso sobre a causa: ele achou o campo, mas achou pelo texto de
ajuda em corpo pequeno — não pelo destaque, que era fraco demais para competir
com o alerta do topo.

**A causa.** O formulário de abertura de chamado tem seis campos. A mensagem
vinha num bloco único no topo, e o campo responsável recebia apenas uma borda
vermelha de 1 px — que, num formulário longo e depois de rolar, some. Havia
inclusive um foco automático via JavaScript, mas foco não é destaque visual:
quem estava lendo o topo não via o cursor lá embaixo.

**A correção.**

- A mesma mensagem passou a ser repetida **ao lado do campo**, com um ícone de
  alerta (macro `erro_do_campo`, em `app/templates/partials/macros.html`).
- O destaque do campo ficou muito mais forte: borda de 2 px, fundo tingido e uma
  barra vertical vermelha na lateral, no padrão que o próprio sistema já usa
  para blocos de alerta.
- O bloco do topo **continua existindo**. Ele é o que os leitores de tela
  anunciam primeiro e o que o JavaScript usa para dar foco. Remover teria
  trocado um problema de usabilidade por um de acessibilidade.

`app/templates/partials/macros.html`, `chamados/novo.html`, `auth/cadastro.html`,
`app/static/css/estilo.css`.

**Testes.** `::test_l05_erro_aparece_junto_do_campo_recusado`,
`::test_l05_apenas_o_campo_com_problema_recebe_a_mensagem`,
`::test_l05_cadastro_tambem_ancora_o_erro_no_campo`,
`::test_l05_formulario_sem_erro_nao_mostra_mensagem_inline`.

---

## Sugestões recebidas e não implementadas

| Sugestão | Quem | Decisão |
|---|---|---|
| Exportar o painel de indicadores em PDF/CSV | Juliana | **Fora do escopo do MVP.** É um pedido legítimo e provavelmente o próximo item da lista, mas é funcionalidade nova, não correção de defeito. Registrado em `docs/escopo.md` como trabalho futuro. |

---

## O que ficou sem cobertura

Honestidade sobre o alcance destes testes — três trechos do sistema não foram
exercitados por ninguém:

| Não testado | Quem declarou | Por quê |
|---|---|---|
| Painel de indicadores do gestor | Artur | Perfil Solicitante, sem permissão de acesso |
| Upload de anexo pelo fluxo normal | Antônio | Não chegou a anexar arquivo; só Roberta anexou, e pelo caminho do erro |
| Anexo com foto tirada na hora pelo celular | Rafael | Não testou a câmera |

Roberta declarou ter percorrido todas as rotas do roteiro; Juliana declarou ter
simulado a jornada completa.

O upload em condição normal e o painel têm cobertura automatizada
(`tests/test_verificacao_v2.py`), mas cobertura automatizada responde "funciona?",
não "faz sentido para quem usa?". Esses três pontos seguem sem validação humana,
e é justo dizer isso em vez de deixar implícito que o sistema inteiro foi
validado.

---

## Resultado

| | Antes | Depois |
|---|---|---|
| Defeitos abertos da validação | 5 | 0 |
| Testes automatizados | 82 | 103 |
| Testes de regressão da validação | — | 21 |

```bash
pytest tests/test_validacao_laudos.py -v
```
