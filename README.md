# ChamaTI — Sistema Web de Gestão de Chamados de TI

Aplicação web para abertura, triagem, atendimento e encerramento de chamados de
suporte técnico, com controle de prazo (SLA), histórico e painel de indicadores
para o gestor.

Projeto desenvolvido para a disciplina **Projeto Integrador Transdisciplinar em
Engenharia de Software II**, dando continuidade ao planejamento do PIT I.

![Lista de chamados](docs/img/tela-lista-chamados.png)

## Funcionalidades

- Cadastro e login com três perfis: solicitante, técnico e gestor
- Abertura de chamado com categoria, prioridade e anexos (até 5 MB)
- Protocolo único no formato `AAAA-NNNNNN`
- Listagem com filtros (status, prioridade, período e busca) e paginação
- Atribuição de técnico e fluxo de status controlado
- Histórico de interações com autor e data
- Encerramento com registro obrigatório da solução
- Painel de indicadores: total, em aberto, tempo médio de atendimento e taxa de SLA
- Interface responsiva, utilizável no celular

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Back-end | Python 3.12 · Flask · SQLAlchemy (padrão MVC) |
| Front-end | HTML5 · CSS3 · JavaScript |
| Banco de dados | PostgreSQL 16 (SQLite no desenvolvimento local) |
| Testes | pytest |
| Hospedagem | Render |

## Arquitetura

```
Navegador
   ▼
Controller  app/controllers/   rotas, sessão e permissões
   ▼
Service     app/services/      regras de negócio e validações
   ▼
Model       app/models/        entidades e persistência
   ▼
PostgreSQL

View        app/templates/ + app/static/
```

As regras de negócio ficam em uma camada própria (`services/`) para poderem ser
testadas sem subir o servidor e para valerem igualmente na tela e na API.

## Como rodar

```bash
git clone https://github.com/SEU-USUARIO/chamati.git
cd chamati

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export FLASK_APP=run.py          # Windows: set FLASK_APP=run.py
flask init-db                    # cria as tabelas
flask seed                       # popula com dados de exemplo

python run.py
```

Acesse <http://localhost:5000>.

Sem a variável `DATABASE_URL`, a aplicação usa SQLite. Para usar PostgreSQL:

```bash
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/chamati"
psql "$DATABASE_URL" -f database/ddl.sql
psql "$DATABASE_URL" -f database/seed.sql
flask seed
```

## Contas de demonstração

Senha para todas: `chamati123`

| Perfil | E-mail |
|---|---|
| Gestor | `ana.gestora@chamati.dev` |
| Técnico | `bruno.tecnico@chamati.dev` |
| Solicitante | `diego@chamati.dev` |

## Testes

```bash
pytest
```

São **103 testes** cobrindo regras de negócio, permissões, validações, ciclo de
vida do chamado, indicadores e rotas HTTP.

Destes, 48 são testes de regressão, divididos em duas frentes:

| Arquivo | Testes | Origem |
|---|---|---|
| `tests/test_verificacao_v2.py` | 27 | **Verificação** — os 9 defeitos que encontrei revisando a v1.0: escalada de privilégio no cadastro, ausência de CSRF, anexos descartados, fuso horário no filtro, protocolo duplicado sob concorrência e outros. Documentados em [`docs/verificacao-v1.md`](docs/verificacao-v1.md) |
| `tests/test_validacao_laudos.py` | 21 | **Validação** — as 5 ocorrências relatadas pelos testadores. Documentadas em [`docs/validacao-laudos.md`](docs/validacao-laudos.md) |

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/escopo.md`](docs/escopo.md) | Problema, público-alvo e escopo do MVP |
| [`docs/uml/`](docs/uml/) | Casos de uso, classes, sequência e atividades |
| [`docs/modelo-de-dados.md`](docs/modelo-de-dados.md) | Modelo conceitual, lógico normalizado e projeto físico |
| [`database/dicionario-de-dados.md`](database/dicionario-de-dados.md) | Dicionário de dados |
| [`docs/ihc.md`](docs/ihc.md) | Decisões de interface e acessibilidade |
| [`docs/plano-de-testes.md`](docs/plano-de-testes.md) | Estratégia de verificação e validação |
| [`docs/verificacao-v1.md`](docs/verificacao-v1.md) | Verificação: os 9 defeitos da v1.0, as correções e as evidências |
| [`docs/validacao-laudos.md`](docs/validacao-laudos.md) | Validação: as 5 ocorrências relatadas pelos testadores e as correções |
| [`docs/manual-do-usuario.md`](docs/manual-do-usuario.md) | Manual de uso por perfil |
| [`laudos/`](laudos/) | Formulários de teste dos 5 testadores e laudo de qualidade |

## Estrutura

```
chamati/
├── app/
│   ├── controllers/     # Controller
│   ├── models/          # Model
│   ├── services/        # Regras de negócio
│   ├── templates/       # View
│   └── static/          # CSS e JavaScript
├── database/            # DDL, seed e dicionário de dados
├── docs/                # Documentação e diagramas
├── laudos/              # Testes com usuários
├── tests/               # Testes automatizados
└── run.py               # Ponto de entrada
```

## Telas

| | |
|---|---|
| ![Painel do gestor](docs/img/tela-painel-gestor.png) | ![Detalhe do chamado](docs/img/tela-detalhe-chamado.png) |
| ![Erro de validação](docs/img/tela-erro-validacao.png) | ![Celular](docs/img/tela-celular.png) |
