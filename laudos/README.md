# Laudo de qualidade — ChamaTI

**Situação: concluído.** Cinco pessoas testaram o sistema publicado em
<https://chamati.onrender.com> entre 18 e 22 de agosto de 2026. Os cinco
formulários preenchidos estão nesta pasta, e as cinco ocorrências relatadas
foram corrigidas.

Os números e as citações desta página saem dos formulários desta pasta. Onde
houver divergência, o `.docx` é a fonte.

---

## Resumo

| | |
|---|---|
| Período dos testes | 18 a 22 de agosto de 2026 |
| Número de testadores | 5 |
| Perfis cobertos | Solicitante (2), Técnico (2), Gestor (1) |
| Ambientes | Windows/Chrome (3), Windows/Firefox (1), Android/Chrome (1) |
| Ocorrências relatadas | 5 |
| Ocorrências corrigidas | 5 (+ 1 encontrada depois, ver L-06) |
| Testes de regressão criados | 31 |

### Quem testou

| # | Testador | Perfil | Ambiente | Data |
|---|---|---|---|---|
| 01 | Roberta Matos Mendonça | Técnico | Windows / Google Chrome | 22/08/2026 |
| 02 | Rafael Souza | Solicitante | Celular Android / Chrome | 20/08/2026 |
| 03 | Juliana Fagundes Martins | Gestor | PC Windows / Chrome | 20/08/2026 |
| 04 | Antônio Alves Araujo Neto | não assinalado no formulário; Técnico pelas ações relatadas | Notebook Windows / Firefox | 19/08/2026 |
| 05 | Artur Rodrigues do Santos | Solicitante | Notebook Windows / Chrome | 18/08/2026 |

Cada testador recebeu um roteiro diferente, para que juntos cobrissem o sistema
inteiro em vez de repetirem o mesmo caminho feliz.

---

## Avaliação geral

Notas de 1 a 5, como marcadas nos formulários:

| Aspecto | Roberta | Rafael | Juliana | Antônio | Artur | Média |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Facilidade de uso | 4 | 3 | 5 | 4 | 5 | **4,2** |
| Clareza das mensagens | 3 | 4 | 5 | 4 | 4 | **4,0** |
| Velocidade | 3 | 4 | 4 | 4 | 5 | **4,0** |
| Aparência | 4 | 4 | 5 | 4 | 5 | **4,4** |
| | | | | | | **4,15** |

Nenhuma nota abaixo de 3, nenhum quesito com média abaixo de 4 — e nenhum
quesito com nota máxima unânime. As duas notas mais baixas confirmam as
ocorrências: **clareza das mensagens** (média 4,0) é o que a Roberta e o Artur
relataram em L-01 e L-05, e o 3 do Rafael em **facilidade de uso** — a nota mais
baixa recebida — é o filtro tomando a tela do celular, L-02.

---

## O que funcionou

Registrado pelos próprios testadores, no campo 2 do formulário:

| Testador | Relato |
|---|---|
| Roberta | O sistema barrou com sucesso os envios sem os 10 caracteres mínimos de descrição |
| Rafael | Acesso pelo celular, filtro da lista por prioridade e consulta ao status da própria solicitação |
| Juliana | O painel de indicadores dá visão panorâmica dos KPIs — total de chamados, taxa de SLA (57,1%) e carga por técnico; os atalhos de volta à lista funcionam |
| Antônio | A atribuição de chamados foi imediata; a troca de status (Aberto → Em atendimento → Resolvido) atualizou o histórico em tempo real |
| Artur | Navegação inicial fluida; encontrou o botão de abrir chamado e preencheu a solicitação rapidamente |

---

## Ocorrências relatadas

| ID | Defeito relatado | Testador | Severidade | Correção aplicada | Teste de regressão | Situação |
|---|---|---|---|---|---|---|
| L-01 | Ao anexar PDF acima de 5 MB, o botão trava no carregamento sem alerta claro de que o arquivo excede o limite | Roberta Matos Mendonça (Técnico) | Alta | O ouvinte genérico de envio passou a respeitar `defaultPrevented` | `test_l01_*` (2) | ✅ Corrigido |
| L-02 | No celular, o formulário de filtros ocupa quase a tela inteira; é preciso rolar muito para ver os resultados, e "Filtrar" parece não fazer nada | Rafael Souza (Solicitante) | Média | Filtros recolhíveis em telas pequenas + rolagem até os resultados | `test_l02_*` (3) | ✅ Corrigido |
| L-03 | Na página 403, o botão "Ver meus chamados" leva a uma tela sem o menu do gestor | Juliana Fagundes Martins (Gestor) | Média | 403 passou a nomear o perfil conectado e a oferecer atalhos por perfil | `test_l03_*` (4) | ✅ Corrigido |
| L-04 | Chamado com SLA já vencido pôde ser encerrado sem justificativa obrigatória do atraso | Antônio Alves Araujo Neto (Técnico) | Alta | Campo "Motivo do atraso", obrigatório só quando o prazo estourou | `test_l04_*` (8) | ✅ Corrigido |
| L-05 | A mensagem de erro aparece destacada no topo, mas demorou a achar qual campo do formulário estava recusado | Artur Rodrigues do Santos (Solicitante) | Média | Mensagem repetida ao lado do campo + destaque visual forte | `test_l05_*` (4) | ✅ Corrigido |

O detalhamento de cada uma — relato, causa, correção e arquivos tocados — está em
[`docs/validacao-laudos.md`](../docs/validacao-laudos.md).

### L-06 · encontrada depois dos laudos

| ID | Defeito | Origem | Severidade | Correção aplicada | Teste de regressão | Situação |
|---|---|---|---|---|---|---|
| L-06 | Cancelar um chamado derrubava a listagem e o painel com `TypeError` | Revisão das correções, não relatada por testador | Alta | `Cancelado` também grava `data_encerramento`; o cálculo de SLA tolera a data ausente das linhas antigas | `test_l06_*` (10) | ✅ Corrigido |

Só o caminho "Resolvido" gravava a data de encerramento. "Cancelado" encerra o
chamado do mesmo jeito (`Status.encerra` é `True`), mas deixava a data nula, e
`sla_estourado` comparava `None` com o prazo. Não veio dos laudos: nenhum dos
cinco roteiros passava por cancelar um chamado.

---

## Sugestões de melhoria

Todas do campo 5 dos formulários:

| Sugestão | Testador | Decisão |
|---|---|---|
| Trava no lado do cliente que impeça o upload e avise antes de tentar enviar arquivo acima de 5 MB | Roberta Matos Mendonça | ✅ Implementada (L-01) |
| Botão retrátil "Exibir / Ocultar filtros" no celular | Rafael Souza | ✅ Implementada (L-02) |
| Campo obrigatório "Motivo do atraso" ao encerrar chamado com a tag "SLA Vencido" | Antônio Alves Araujo Neto | ✅ Implementada (L-04) |
| Destacar em vermelho forte o campo com erro, para identificação visual rápida | Artur Rodrigues do Santos | ✅ Implementada (L-05) |
| Exportar os dados e gráficos do painel de indicadores em PDF ou CSV | Juliana Fagundes Martins | ⏭ Fora do escopo do MVP — é funcionalidade nova, não correção. Registrada como trabalho futuro |

Quatro das cinco sugestões viraram código. A quinta é a única que pede
funcionalidade nova em vez de conserto.

---

## O que não foi coberto

Três lacunas declaradas pelos próprios testadores, no campo 4:

| Não testado | Quem declarou | Por quê |
|---|---|---|
| Painel de indicadores do gestor | Artur | Perfil Solicitante, sem permissão de acesso — Juliana, gestora, cobriu essa tela |
| Upload de arquivo no anexo do chamado | Antônio | Não chegou a testar; o upload só foi exercitado no caminho de erro, no teste da Roberta |
| Anexo com foto tirada na hora pelo celular | Rafael | Não testou a câmera |

Roberta declarou ter testado todas as principais rotas do roteiro; Juliana
declarou ter simulado a jornada completa.

Há cobertura automatizada para o upload em condição normal, mas teste
automatizado responde "funciona?", não "faz sentido para quem usa?".

E a lacuna que os formulários não declaram, porque nenhum roteiro pedia:
**cancelar um chamado**. Foi exatamente onde a L-06 estava.

---

## Verificação × validação

A Situação-Problema 3 pede as duas coisas, e elas estão em documentos diferentes:

| | Verificação | Validação |
|---|---|---|
| **Pergunta** | Construímos o produto corretamente? | Construímos o produto certo? |
| **Quem faz** | O desenvolvedor | Usuários reais |
| **Resultado** | 9 defeitos encontrados e corrigidos | 5 ocorrências relatadas e corrigidas |
| **Documento** | [`docs/verificacao-v1.md`](../docs/verificacao-v1.md) | [`docs/validacao-laudos.md`](../docs/validacao-laudos.md) |
| **Testes** | `tests/test_verificacao_v2.py` (27) | `tests/test_validacao_laudos.py` (31) |

A L-06 é o contraexemplo útil da tabela: não é verificação nem validação de
usuário, é o defeito que só apareceu ao exercitar um caminho que nenhum dos
dois lados tinha percorrido.

---

## Arquivos desta pasta

| Arquivo | Conteúdo |
|---|---|
| `Formulario_de_Teste_ChamaTI - <nome>.docx` | Os cinco formulários preenchidos pelos testadores |
| `formulario-de-teste.md` | O formulário em branco, em Markdown |
| `gerar_laudo_pdf.py` | Gera a consolidação das cinco opiniões em PDF |
| `evidencias/` | Prints de tela das ocorrências |

---

## Como reproduzir as correções

```bash
pytest tests/test_validacao_laudos.py -v
```

Cada teste dos blocos L-01 a L-05 falha na versão anterior à sua correção e
passa na atual. No bloco L-06, sete dos dez fazem isso; os outros três passam
nas duas versões de propósito — guardam o que a correção não podia quebrar ao
generalizar o tratamento de encerramento, e estão marcados como tais no arquivo.
