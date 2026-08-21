# ChamaTI — Sistema Web de Gestão de Chamados de TI

Aplicação web para abertura, triagem, atendimento e encerramento de chamados de
suporte técnico, com controle de SLA, histórico completo e painel de indicadores
para o gestor.

Projeto desenvolvido para a disciplina **Projeto Integrador Transdisciplinar em
Engenharia de Software II**, dando continuidade ao planejamento realizado no PIT I.

![Lista de chamados](docs/img/tela-lista-chamados.png)

---

## Sumário

- [O problema](#o-problema)
- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Como rodar localmente](#como-rodar-localmente)
- [Contas de demonstração](#contas-de-demonstração)
- [Testes](#testes)
- [Deploy](#deploy)
- [Documentação do projeto](#documentação-do-projeto)
- [Estrutura de diretórios](#estrutura-de-diretórios)
- [Telas](#telas)
- [Licença](#licença)

---

## O problema

Pequenas e médias empresas costumam controlar o suporte técnico por e-mail e
planilhas. O resultado é conhecido: pedidos que se perdem na caixa de entrada,
nenhuma noção de prazo, retrabalho por falta de histórico e nenhum dado para o
gestor decidir onde reforçar a equipe.

O ChamaTI centraliza esse fluxo em um só lugar, com protocolo, responsável,
prazo e histórico para cada solicitação.

## Funcionalidades

**Solicitante**

- Cadastro e login
- Abertura de chamado com categoria, prioridade e anexos (até 5 MB por arquivo)
- Protocolo único no formato `AAAA-NNNNNN`
- Acompanhamento do próprio chamado, com histórico e comentários
- Busca por protocolo

**Técnico**

- Fila de chamados com filtros por status, prioridade, período e texto livre
- Atribuição de responsável
- Registro de interações
- Encerramento com descrição obrigatória da solução

**Gestor**

- Acesso a todos os chamados
- Painel com total de chamados, chamados em aberto, tempo médio de atendimento
  e taxa de cumprimento de SLA
- Distribuição por status, por prioridade e carga por técnico

**Transversal**

- Três perfis de acesso com permissões verificadas no servidor
- Cálculo de SLA por prioridade, com sinalização de prazo vencido
- Interface responsiva (a tabela vira lista de cartões no celular)
- Mensagens de erro no padrão "o que aconteceu + como resolver"

## Arquitetura

Organização em camadas seguindo o padrão **MVC**, com as regras de negócio
isoladas em uma camada de serviços:

```
Navegador
   │  HTTP
   ▼
Controller  app/controllers/   blueprints Flask: rotas, sessão e permissões
   │
   ▼
Service     app/services/      regras de negócio e validações
   │
   ▼
Model       app/models/        entidades SQLAlchemy e persistência
   │
   ▼
PostgreSQL

View        app/templates/ + app/static/   Jinja2, CSS e JavaScript
```

Por que a camada de serviços existe: as regras (limite de anexo, tamanho
mínimo da descrição, transições de status válidas, quem pode resolver um
chamado) precisam valer igualmente para a tela, para a API e para os testes.
Deixá-las no controller as tornaria dependentes da requisição HTTP.

O diagrama de classes, os casos de uso e os diagramas de sequência e atividades
estão em [`docs/uml/`](docs/uml/).

## Tecnologias

| Camada               | Tecnologia                                                   |
| -------------------- | ------------------------------------------------------------ |
| Back-end             | Python 3.12 · Flask 3 · SQLAlchemy 2                         |
| Front-end            | HTML5 · CSS3 (sem framework) · JavaScript (sem dependências) |
| Banco de dados       | PostgreSQL 16 (SQLite no desenvolvimento local)              |
| Testes               | pytest                                                       |
| Servidor de produção | Gunicorn                                                     |
| Hospedagem           | Render                                                       |

O front-end foi escrito à mão, sem framework de CSS, para manter o controle
sobre acessibilidade e responsividade — decisão registrada em [`docs/ihc.md`](docs/ihc.md).

## Como rodar localmente

Pré-requisitos: Python 3.11 ou superior. O PostgreSQL é opcional — sem a
variável `DATABASE_URL`, a aplicação usa SQLite automaticamente.

```bash
git clone https://github.com/SEU-USUARIO/chamati.git
cd chamati

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env             # ajuste SECRET_KEY

export FLASK_APP=run.py          # Windows: set FLASK_APP=run.py
flask init-db                    # cria as tabelas
flask seed                       # popula com dados de demonstração

python run.py
```

Acesse <http://localhost:5000>.

### Com PostgreSQL

```bash
createdb chamati
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/chamati"

psql "$DATABASE_URL" -f database/ddl.sql     # projeto físico
psql "$DATABASE_URL" -f database/seed.sql    # tabelas de domínio
flask seed                                   # usuários e chamados de exemplo
```

## Contas de demonstração

Criadas pelo comando `flask seed`. Senha para todas: `chamati123`.

| Perfil      | E-mail                      | O que consegue fazer                    |
| ----------- | --------------------------- | --------------------------------------- |
| Gestor      | `ana.gestora@chamati.dev`   | Tudo, incluindo o painel de indicadores |
| Técnico     | `bruno.tecnico@chamati.dev` | Atender, atribuir e resolver chamados   |
| Solicitante | `diego@chamati.dev`         | Abrir e acompanhar os próprios chamados |

## Testes

```bash
pytest              # suíte completa
pytest -v           # detalhado
```

A suíte tem **55 testes** cobrindo regras de negócio, permissões, validações,
ciclo de vida do chamado, indicadores e rotas HTTP. (`test_regressao_e01_…`).

O plano de testes completo está em [`docs/plano-de-testes.md`](docs/plano-de-testes.md).

## Deploy

O arquivo [`render.yaml`](render.yaml) descreve a infraestrutura. No Render:

1. **New → Blueprint** e aponte para este repositório;
2. o Render cria o serviço web e o banco PostgreSQL, e injeta `DATABASE_URL`;
3. após o primeiro deploy, rode `flask seed` no shell do serviço para carregar
   os dados de demonstração.

A rota `/health` é usada como _health check_.

## Documentação do projeto

| Documento                                                            | Conteúdo                                                                |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| [`docs/escopo.md`](docs/escopo.md)                                   | Problema, público-alvo, escopo do MVP e o que ficou para a fase 2       |
| [`docs/requisitos.md`](docs/requisitos.md)                           | Requisitos funcionais e não funcionais, rastreados até o código         |
| [`docs/uml/`](docs/uml/)                                             | Casos de uso, classes, sequência e atividades (Mermaid)                 |
| [`docs/modelo-de-dados.md`](docs/modelo-de-dados.md)                 | Modelo conceitual, lógico normalizado e projeto físico                  |
| [`database/dicionario-de-dados.md`](database/dicionario-de-dados.md) | Dicionário de dados completo                                            |
| [`docs/ihc.md`](docs/ihc.md)                                         | Princípios de interface aplicados, padrão de mensagens e acessibilidade |
| [`docs/plano-de-testes.md`](docs/plano-de-testes.md)                 | Estratégia de verificação e validação                                   |
| [`docs/manual-do-usuario.md`](docs/manual-do-usuario.md)             | Manual de uso por perfil                                                |
| [`docs/melhorias-pit1.md`](docs/melhorias-pit1.md)                   | O que mudou em relação ao PIT I e por quê                               |
| [`laudos/`](laudos/)                                                 | Formulário de teste, laudos preenchidos e evidências                    |

## Estrutura de diretórios

```
chamati/
├── app/
│   ├── controllers/     # Controller — blueprints Flask
│   ├── models/          # Model — entidades SQLAlchemy
│   ├── services/        # Regras de negócio
│   ├── templates/       # View — Jinja2
│   ├── static/          # CSS e JavaScript
│   ├── config.py        # Configuração por ambiente
│   └── seed.py          # Carga de demonstração
├── database/            # DDL, seed e dicionário de dados
├── docs/                # Documentação e diagramas
├── laudos/              # Testes com usuários e evidências
├── tests/               # Suíte pytest
├── render.yaml          # Infraestrutura como código
└── run.py               # Ponto de entrada
```

## Telas

|                                                          |                                                        |
| -------------------------------------------------------- | ------------------------------------------------------ |
| ![Início](docs/img/tela-inicio.png)                      | ![Painel do gestor](docs/img/tela-painel-gestor.png)   |
| ![Detalhe do chamado](docs/img/tela-detalhe-chamado.png) | ![Erro de validação](docs/img/tela-erro-validacao.png) |
| ![Celular](docs/img/tela-celular.png)                    | ![Acesso negado](docs/img/tela-acesso-negado.png)      |

## Licença

[MIT](LICENSE).
