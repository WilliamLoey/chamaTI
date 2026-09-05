# Verificação da versão 1.0 — defeitos encontrados e corrigidos

Este documento registra a etapa de **verificação** exigida pela Situação-Problema 3:

> "Realizar e documentar os testes (verificação e validação) mostrando que o
> comportamento esperado foi realizado."

Verificação e validação são coisas distintas, e este documento cobre a primeira:

| | Verificação | Validação |
|---|---|---|
| **Pergunta** | Estamos construindo o produto **corretamente**? | Estamos construindo o **produto certo**? |
| **Quem faz** | O próprio desenvolvedor | Usuários reais |
| **Como** | Revisão de código, análise e testes automatizados | Teste de aceitação com o formulário de laudo |
| **Onde está** | Este documento | [`laudos/`](../laudos/) |

---

## Método

A versão 1.0 foi submetida a uma revisão crítica linha a linha, com foco em
quatro dimensões: **segurança**, **integridade de dados**, **correção funcional**
e **manutenibilidade**.

Cada suspeita foi confirmada por **execução**, não por leitura. Nenhum defeito
abaixo é hipótese: todos foram reproduzidos com código rodando, e a saída do
teste está registrada na coluna de evidência.

Ambiente: Python 3.12, SQLite (testes) e PostgreSQL 16 (DDL).

---

## Defeitos encontrados

Nove defeitos, sendo **um crítico**, **dois altos**, **quatro médios** e **dois baixos**.

### V-01 · Escalada de privilégio no cadastro público · **Crítica**

**O que acontecia.** O formulário de cadastro expunha um campo "Perfil de acesso"
com as três opções — Solicitante, Técnico e Gestor — e o back-end aceitava o valor
enviado sem questionar. Qualquer visitante criava uma conta de Gestor em segundos
e passava a ver todos os chamados da empresa, incluindo o painel gerencial.

Ironicamente, o próprio formulário trazia o aviso *"em produção, os perfis Técnico
e Gestor são atribuídos pelo administrador"* — texto que descrevia uma regra que o
código não implementava.

**Evidência.** Conta criada via `POST /auth/cadastro` com `perfil=gestor`:
perfil resultante `gestor`, e `GET /painel/` respondeu **200**.

**Correção.** O perfil deixou de ser entrada do usuário. `cadastrar_publico()`
sempre cria Solicitante. Contas com perfil elevado passam por
`cadastrar_por_gestor()` ou `promover()`, ambas exigindo um gestor autenticado.
O campo saiu do formulário.

**Testes.** `test_v01_cadastro_publico_nao_permite_escolher_o_perfil`,
`test_v01_area_do_gestor_bloqueada_para_quem_se_cadastrou`,
`test_v01_somente_gestor_cria_conta_com_perfil_elevado`,
`test_v01_somente_gestor_promove`

---

### V-02 · Ausência de proteção contra CSRF · **Alta**

**O que acontecia.** Nenhum dos formulários tinha token anti-CSRF. Uma página
maliciosa aberta em outra aba conseguia fazer o navegador de um usuário logado
enviar requisições ao ChamaTI — encerrando chamados, reatribuindo técnicos ou
alterando dados — sem que ele percebesse, porque o cookie de sessão viaja junto
automaticamente.

**Evidência.** A palavra `csrf` aparecia **0 vezes** no HTML de todas as telas.

**Correção.** `CSRFProtect` (Flask-WTF) inicializado na factory, protegendo todo
POST da aplicação, e `{{ csrf_token() }}` incluído nos 7 formulários.

**Testes.** `test_v02_post_sem_token_csrf_e_rejeitado` (POST sem token → 400),
`test_v02_formularios_publicam_o_token`

---

### V-03 · O anexo era descartado · **Alta**

**O que acontecia.** O sistema gravava apenas o **nome** e o **tamanho** do
arquivo. O conteúdo enviado era lido para medir os bytes e jogado fora — a tabela
`anexo` não tinha sequer coluna para armazená-lo. Na tela, o anexo aparecia
listado, dando a impressão de que estava guardado.

Isso invalidava um requisito explícito do enunciado: os testadores devem
"colocar snapshots das telas com erros para facilitar sua correção".

**Evidência.** Colunas da tabela: `id, chamado_id, nome_arquivo, tamanho_bytes,
enviado_em`. Nenhuma armazena o arquivo.

**Correção.** Colunas `conteudo` (BYTEA) e `tipo_mime` acrescentadas, o conteúdo
passou a ser persistido, e criou-se a rota `GET /chamados/<id>/anexo/<id>` para
download — com a permissão conferida contra o chamado, de modo que adivinhar o
id de um anexo não dá acesso ao arquivo de outra pessoa.

Guardar no banco em vez de em disco é decisão consciente: a hospedagem gratuita
usa sistema de arquivos efêmero, apagado a cada reinício do serviço.

**Testes.** `test_v03_conteudo_do_anexo_e_gravado`,
`test_v03_anexo_pode_ser_baixado`, `test_v03_anexo_de_outro_usuario_e_bloqueado`

---

### V-04 · Qualquer extensão de arquivo era aceita · **Média**

**O que acontecia.** Não havia validação de tipo. Um `.exe`, `.bat` ou `.sh` era
aceito como anexo de chamado.

**Evidência.** `validar_anexo("virus.exe", 1024)` retornava sucesso.

**Correção.** Lista de extensões permitidas em `app/regras.py` — png, jpg, jpeg,
gif, webp, pdf, txt, log e csv, que são os formatos que servem como evidência.
A restrição é aplicada na aplicação **e** por `CHECK` no banco.

**Testes.** `test_v04_extensao_executavel_e_recusada`,
`test_v04_extensoes_de_evidencia_sao_aceitas` (5 casos),
`test_v04_outras_extensoes_sao_recusadas` (4 casos),
`test_v04_arquivo_vazio_e_recusado`

---

### V-05 · Protocolos duplicados sob concorrência · **Média**

**O que acontecia.** `gerar_protocolo()` consulta o maior número existente e soma
um, mas a gravação só ocorre depois. Dois chamados abertos ao mesmo tempo
calculavam o mesmo protocolo, e o segundo estourava na constraint `UNIQUE` — erro
500 na cara do usuário, com o chamado perdido.

**Evidência.** Duas chamadas consecutivas a `gerar_protocolo()`, sem commit entre
elas, retornaram `2026-000002` nas duas vezes.

**Correção.** A gravação passou a ser feita com retentativa: ao detectar
`IntegrityError`, a transação é revertida, o número recalculado e a operação
repetida (até 5 vezes). Se ainda assim falhar, o usuário recebe mensagem
orientando a tentar de novo, em vez de um erro 500.

**Teste.** `test_v05_protocolo_duplicado_e_contornado` — simula a corrida
forçando a primeira tentativa a devolver um protocolo já existente.

---

### V-06 · Filtro de data ignorava o fuso brasileiro · **Média**

**O que acontecia.** As fronteiras do dia eram calculadas em UTC. Como o Brasil
está em UTC−3, um chamado aberto às 23h de segunda é gravado como 02:00 UTC de
terça — e desaparecia do filtro de "segunda-feira".

Na prática: chamados abertos no fim da tarde e à noite, justamente o horário de
pico de pedidos de suporte, sumiam da busca por data.

**Evidência.** `02:00 UTC` corresponde a `23:00` do dia anterior em Brasília.

**Correção.** As datas digitadas passam a ser interpretadas no fuso
`America/Sao_Paulo` e convertidas para UTC antes da consulta. Os dados continuam
armazenados em UTC — apenas a fronteira do dia é traduzida.

**Testes.** `test_v06_filtro_respeita_o_fuso_brasileiro`,
`test_v06_madrugada_local_nao_entra_no_dia_anterior`

---

### V-07 · Técnico perdia acesso ao chamado que atendeu · **Média**

**O que acontecia.** A regra de visibilidade dava acesso ao técnico apenas se ele
fosse o responsável **atual**. Assim que o chamado era passado a outro colega, o
técnico anterior perdia o acesso — inclusive ao histórico que ele próprio havia
escrito. Se ele precisasse consultar o que já tinha diagnosticado, não conseguia.

**Evidência.** Após reatribuição, `pode_ver_chamado()` retornava `False` para o
técnico que havia comentado no chamado.

**Correção.** `Usuario.pode_ver_chamado` passou a considerar também a
participação: quem registrou alguma interação no chamado continua enxergando-o.
Técnicos sem qualquer relação com o chamado seguem sem acesso.

**Testes.** `test_v07_tecnico_mantem_acesso_ao_chamado_que_atendeu`,
`test_v07_tecnico_sem_relacao_nao_ve_chamado_alheio`

---

### V-08 · Configuração devolvia um objeto em vez de um número · **Baixa**

**O que acontecia.** `ANEXO_MAX_BYTES` foi declarado com `@property` dentro da
classe de configuração. O Flask lê configuração como atributo simples, então
`app.config["ANEXO_MAX_BYTES"]` devolvia o objeto `property`, não os 5.242.880
bytes. Qualquer comparação numérica com esse valor teria comportamento errado.

**Evidência.** `app.config["ANEXO_MAX_BYTES"]` → `<property object at 0x...>`.

**Correção.** O valor passou a ser constante calculada em `app/regras.py`.

**Teste.** `test_v08_limite_de_anexo_e_um_numero`

---

### V-09 · Regras de negócio duplicadas · **Baixa**

**O que acontecia.** `DESCRICAO_MIN`, `ITENS_POR_PAGINA` e `SENHA_MIN` existiam
em `app/config.py` **e** de novo nos serviços. Os valores coincidiam por sorte;
alterar um e esquecer o outro produziria um sistema que valida uma coisa e
informa outra ao usuário.

**Evidência.** Os três pares de constantes existiam em módulos diferentes.

**Correção.** Criado `app/regras.py` como fonte única. Configuração e serviços
passaram a importar de lá.

**Teste.** `test_v09_regras_tem_fonte_unica`

---

## Resultado

| | Versão 1.0 | Versão 2.0 |
|---|---|---|
| Defeitos conhecidos em aberto | 9 | 0 |
| Testes automatizados | 55 | **82** |
| Testes de regressão dos defeitos | — | 27 |
| Formulários com proteção CSRF | 0 de 7 | 7 de 7 |
| Anexos efetivamente armazenados | não | sim |

A verificação fechou com esses 82 testes passando. Os 27 novos falham no código
da versão 1.0 e passam na 2.0 — é isso que os torna testes de regressão, e não
apenas testes novos. A suíte cresceu depois, na etapa de validação; o total de
hoje está no [`README.md`](../README.md) e em
[`plano-de-testes.md`](plano-de-testes.md).

```bash
pytest -q                              # suíte completa
pytest tests/test_verificacao_v2.py -v # só os defeitos desta verificação
```

## O que esta verificação não cobre

Honestidade sobre os limites do método: revisão e teste automatizado encontram
defeitos de **lógica, segurança e integridade**. Não encontram problemas de
**usabilidade** — se a tela é confusa, se a mensagem faz sentido para quem não
escreveu o sistema, se o fluxo corresponde ao que o usuário espera.

Isso só aparece com pessoas reais usando o sistema, e é o objeto da etapa de
**validação**, documentada em [`laudos/`](../laudos/).
