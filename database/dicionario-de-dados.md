# Dicionário de dados — ChamaTI

Banco: **PostgreSQL 16** · Esquema: `public` · Script de criação: [`ddl.sql`](ddl.sql)

Convenções adotadas:

- nomes de tabela no **singular** e em minúsculas;
- chave primária sempre `id` (`SERIAL`);
- chave estrangeira nomeada como `<tabela_referenciada>_id`;
- datas e horas em `TIMESTAMPTZ` (com fuso), armazenadas em UTC;
- `PK` = chave primária, `FK` = chave estrangeira, `UQ` = restrição de unicidade.

---

## Tabela `categoria`

Assunto do chamado. Tabela de domínio criada na normalização (era texto livre no PIT I).

| Atributo | Tipo | Domínio / Restrição | Obrig. | Chave | Descrição |
|---|---|---|---|---|---|
| id | SERIAL | > 0 | Sim | PK | Identificador da categoria |
| nome | VARCHAR(60) | Único, não vazio | Sim | UQ | Nome exibido (ex.: Hardware) |
| descricao | VARCHAR(200) | Texto livre | Não | — | Explicação de quando usar a categoria |
| ativo | BOOLEAN | true / false | Sim | — | Permite aposentar categorias sem apagar histórico |

## Tabela `prioridade`

Urgência do chamado. Define o prazo de atendimento (SLA).

| Atributo | Tipo | Domínio / Restrição | Obrig. | Chave | Descrição |
|---|---|---|---|---|---|
| id | SERIAL | > 0 | Sim | PK | Identificador da prioridade |
| nome | VARCHAR(30) | Baixa, Média, Alta, Crítica | Sim | UQ | Nome exibido |
| sla_horas | INTEGER | > 0 (padrão 24) | Sim | — | Prazo de atendimento, em horas |
| ordem | INTEGER | ≥ 0 | Sim | — | Ordem de exibição nas listas |

## Tabela `status`

Etapa do ciclo de vida do chamado.

| Atributo | Tipo | Domínio / Restrição | Obrig. | Chave | Descrição |
|---|---|---|---|---|---|
| id | SERIAL | > 0 | Sim | PK | Identificador do status |
| nome | VARCHAR(30) | Aberto, Em atendimento, Resolvido, Cancelado | Sim | UQ | Nome exibido |
| encerra | BOOLEAN | true / false | Sim | — | Indica se o status finaliza o chamado |
| ordem | INTEGER | ≥ 0 | Sim | — | Ordem do fluxo de atendimento |

## Tabela `usuario`

Pessoa que acessa o sistema, em um dos três perfis.

| Atributo | Tipo | Domínio / Restrição | Obrig. | Chave | Descrição |
|---|---|---|---|---|---|
| id | SERIAL | > 0 | Sim | PK | Identificador do usuário |
| nome | VARCHAR(120) | Mín. 3 caracteres (regra da aplicação) | Sim | — | Nome completo |
| email | VARCHAR(120) | Único, contém `@` | Sim | UQ | Login do usuário |
| senha_hash | VARCHAR(255) | Hash PBKDF2 (Werkzeug) | Sim | — | Senha criptografada — **nunca** em texto puro |
| perfil | VARCHAR(20) | solicitante, tecnico, gestor | Sim | — | Define as permissões de acesso |
| departamento | VARCHAR(80) | Texto livre | Não | — | Setor do solicitante |
| ativo | BOOLEAN | true / false | Sim | — | Conta bloqueada quando `false` |
| criado_em | TIMESTAMPTZ | Padrão `NOW()` | Sim | — | Data de criação da conta |

## Tabela `chamado`

Entidade central do sistema.

| Atributo | Tipo | Domínio / Restrição | Obrig. | Chave | Descrição |
|---|---|---|---|---|---|
| id | SERIAL | > 0 | Sim | PK | Identificador interno |
| protocolo | VARCHAR(20) | Único, formato `AAAA-NNNNNN` | Sim | UQ | Número informado ao usuário |
| titulo | VARCHAR(120) | Mín. 5 caracteres (CHECK) | Sim | — | Resumo do problema |
| descricao | TEXT | Mín. 10 caracteres após `trim` (CHECK) | Sim | — | Relato detalhado |
| categoria_id | INTEGER | FK → categoria(id), ON DELETE RESTRICT | Sim | FK | Assunto do chamado |
| prioridade_id | INTEGER | FK → prioridade(id), ON DELETE RESTRICT | Sim | FK | Urgência e base do SLA |
| status_id | INTEGER | FK → status(id), ON DELETE RESTRICT | Sim | FK | Etapa atual |
| solicitante_id | INTEGER | FK → usuario(id), ON DELETE RESTRICT | Sim | FK | Quem abriu o chamado |
| tecnico_id | INTEGER | FK → usuario(id), ON DELETE SET NULL | Não | FK | Responsável pelo atendimento |
| data_abertura | TIMESTAMPTZ | Padrão `NOW()` | Sim | — | Início da contagem do SLA |
| data_encerramento | TIMESTAMPTZ | ≥ `data_abertura` (CHECK) | Não | — | Preenchida ao resolver/cancelar |
| solucao | TEXT | Mín. 10 caracteres ao resolver (regra da aplicação) | Não | — | Causa e correção aplicada |

**Índices:** `ix_chamado_status`, `ix_chamado_data_abertura`, `ix_chamado_solicitante`,
`ix_chamado_tecnico`, `ix_chamado_protocolo` — sustentam os filtros mais usados
da listagem e a ordenação padrão por data.

## Tabela `interacao`

Histórico do chamado: comentários das pessoas e eventos gerados pelo sistema.

| Atributo | Tipo | Domínio / Restrição | Obrig. | Chave | Descrição |
|---|---|---|---|---|---|
| id | SERIAL | > 0 | Sim | PK | Identificador da interação |
| chamado_id | INTEGER | FK → chamado(id), ON DELETE CASCADE | Sim | FK | Chamado ao qual pertence |
| autor_id | INTEGER | FK → usuario(id), ON DELETE RESTRICT | Sim | FK | Quem registrou |
| mensagem | TEXT | Mín. 3 caracteres (regra da aplicação) | Sim | — | Conteúdo do registro |
| tipo | VARCHAR(20) | comentario, sistema (CHECK) | Sim | — | Diferencia texto humano de evento automático |
| criado_em | TIMESTAMPTZ | Padrão `NOW()` | Sim | — | Momento do registro |

## Tabela `anexo`

Arquivos enviados junto ao chamado.

| Atributo | Tipo | Domínio / Restrição | Obrig. | Chave | Descrição |
|---|---|---|---|---|---|
| id | SERIAL | > 0 | Sim | PK | Identificador do anexo |
| chamado_id | INTEGER | FK → chamado(id), ON DELETE CASCADE | Sim | FK | Chamado ao qual pertence |
| nome_arquivo | VARCHAR(255) | Extensão em png, jpg, jpeg, gif, webp, pdf, txt, log, csv (CHECK) | Sim | — | Nome original do arquivo (**V-04**) |
| tipo_mime | VARCHAR(100) | Padrão `application/octet-stream` | Sim | — | Tipo informado no envio, usado no download |
| tamanho_bytes | INTEGER | > 0 e ≤ 5.242.880 (CHECK) | Sim | — | Tamanho — limite de 5 MB |
| conteudo | BYTEA | Binário do arquivo | Sim | — | Conteúdo do anexo (**V-03**) |
| enviado_em | TIMESTAMPTZ | Padrão `NOW()` | Sim | — | Data do envio |

## Visão `vw_chamado_sla`

Visão de leitura usada pelo painel. Calcula, por chamado: `prazo_sla`,
`sla_estourado` e `horas_em_aberto`, evitando repetir a expressão nas consultas.

---

## Relacionamentos e cardinalidades

| Relacionamento | Cardinalidade | Observação |
|---|---|---|
| usuario (solicitante) → chamado | 1 : N | Um usuário abre vários chamados |
| usuario (técnico) → chamado | 0..1 : N | Chamado pode estar sem técnico atribuído |
| categoria → chamado | 1 : N | Categoria obrigatória |
| prioridade → chamado | 1 : N | Prioridade obrigatória |
| status → chamado | 1 : N | Status obrigatório |
| chamado → interacao | 1 : N | Exclusão em cascata |
| chamado → anexo | 1 : N | Exclusão em cascata |

## Domínios das regras de negócio

| Regra | Valor | Onde é aplicada |
|---|---|---|
| Tamanho mínimo do título | 5 caracteres | Serviço + CHECK no banco |
| Tamanho mínimo da descrição | 10 caracteres (após `trim`) | Serviço + CHECK no banco |
| Tamanho máximo do anexo | 5 MB | JavaScript + serviço + CHECK no banco |
| Extensões de anexo permitidas | png, jpg, jpeg, gif, webp, pdf, txt, log, csv | Serviço + CHECK no banco |
| Itens por página na listagem | 25 | Serviço |
| Transições de status permitidas | Aberto → Em atendimento/Cancelado; Em atendimento → Resolvido/Aberto/Cancelado; Resolvido → Aberto | Serviço |
