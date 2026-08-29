-- ============================================================================
-- ChamaTI — Projeto físico do banco de dados (PostgreSQL 16)
-- Derivado do modelo lógico normalizado até a 3FN (docs/modelo-de-dados.md).
--
-- Execução:
--   psql "$DATABASE_URL" -f database/ddl.sql
-- ============================================================================

BEGIN;

DROP TABLE IF EXISTS anexo CASCADE;
DROP TABLE IF EXISTS interacao CASCADE;
DROP TABLE IF EXISTS chamado CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;
DROP TABLE IF EXISTS status CASCADE;
DROP TABLE IF EXISTS prioridade CASCADE;
DROP TABLE IF EXISTS categoria CASCADE;

-- ----------------------------------------------------------------- domínios --
-- Extraídos de colunas de texto livre da modelagem do PIT I: eliminam
-- redundância, padronizam os valores e garantem integridade referencial.

CREATE TABLE categoria (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(60)  NOT NULL UNIQUE,
    descricao   VARCHAR(200),
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT ck_categoria_nome_nao_vazio CHECK (length(trim(nome)) > 0)
);

CREATE TABLE prioridade (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(30)  NOT NULL UNIQUE,
    sla_horas   INTEGER      NOT NULL DEFAULT 24,
    ordem       INTEGER      NOT NULL DEFAULT 0,
    CONSTRAINT ck_prioridade_sla_positivo CHECK (sla_horas > 0)
);

CREATE TABLE status (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(30)  NOT NULL UNIQUE,
    encerra     BOOLEAN      NOT NULL DEFAULT FALSE,
    ordem       INTEGER      NOT NULL DEFAULT 0
);

-- ------------------------------------------------------------------ usuário --

CREATE TABLE usuario (
    id            SERIAL PRIMARY KEY,
    nome          VARCHAR(120) NOT NULL,
    email         VARCHAR(120) NOT NULL UNIQUE,
    senha_hash    VARCHAR(255) NOT NULL,   -- nunca a senha em texto puro
    perfil        VARCHAR(20)  NOT NULL DEFAULT 'solicitante',
    departamento  VARCHAR(80),
    ativo         BOOLEAN      NOT NULL DEFAULT TRUE,
    criado_em     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_usuario_perfil CHECK (perfil IN ('solicitante', 'tecnico', 'gestor')),
    CONSTRAINT ck_usuario_email CHECK (position('@' in email) > 1)
);

CREATE INDEX ix_usuario_email  ON usuario (email);
CREATE INDEX ix_usuario_perfil ON usuario (perfil);

-- ------------------------------------------------------------------ chamado --

CREATE TABLE chamado (
    id                SERIAL PRIMARY KEY,
    protocolo         VARCHAR(20)  NOT NULL UNIQUE,
    titulo            VARCHAR(120) NOT NULL,
    descricao         TEXT         NOT NULL,
    categoria_id      INTEGER      NOT NULL REFERENCES categoria   (id) ON DELETE RESTRICT,
    prioridade_id     INTEGER      NOT NULL REFERENCES prioridade  (id) ON DELETE RESTRICT,
    status_id         INTEGER      NOT NULL REFERENCES status      (id) ON DELETE RESTRICT,
    solicitante_id    INTEGER      NOT NULL REFERENCES usuario     (id) ON DELETE RESTRICT,
    tecnico_id        INTEGER               REFERENCES usuario     (id) ON DELETE SET NULL,
    data_abertura     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    data_encerramento TIMESTAMPTZ,
    solucao           TEXT,
    -- A descrição precisa ter conteúdo real, não apenas espaços
    CONSTRAINT ck_chamado_descricao_minima CHECK (length(trim(descricao)) >= 10),
    CONSTRAINT ck_chamado_titulo_minimo    CHECK (length(trim(titulo))    >= 5),
    CONSTRAINT ck_chamado_encerramento     CHECK (data_encerramento IS NULL
                                                  OR data_encerramento >= data_abertura)
);

-- Índices que sustentam os filtros e a ordenação padrão da listagem
CREATE INDEX ix_chamado_status        ON chamado (status_id);
CREATE INDEX ix_chamado_data_abertura ON chamado (data_abertura DESC);
CREATE INDEX ix_chamado_solicitante   ON chamado (solicitante_id);
CREATE INDEX ix_chamado_tecnico       ON chamado (tecnico_id);
CREATE INDEX ix_chamado_protocolo     ON chamado (protocolo);

-- ---------------------------------------------------------------- interação --

CREATE TABLE interacao (
    id          SERIAL PRIMARY KEY,
    chamado_id  INTEGER     NOT NULL REFERENCES chamado (id) ON DELETE CASCADE,
    autor_id    INTEGER     NOT NULL REFERENCES usuario (id) ON DELETE RESTRICT,
    mensagem    TEXT        NOT NULL,
    tipo        VARCHAR(20) NOT NULL DEFAULT 'comentario',
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_interacao_tipo CHECK (tipo IN ('comentario', 'sistema'))
);

CREATE INDEX ix_interacao_chamado ON interacao (chamado_id, criado_em);

-- -------------------------------------------------------------------- anexo --

CREATE TABLE anexo (
    id             SERIAL PRIMARY KEY,
    chamado_id     INTEGER      NOT NULL REFERENCES chamado (id) ON DELETE CASCADE,
    nome_arquivo   VARCHAR(255) NOT NULL,
    tipo_mime      VARCHAR(100) NOT NULL DEFAULT 'application/octet-stream',
    tamanho_bytes  INTEGER      NOT NULL,
    -- V-03: o conteúdo do arquivo passou a ser armazenado. Na versão 1.0 só o
    -- nome e o tamanho eram gravados, e o arquivo enviado era descartado.
    conteudo       BYTEA        NOT NULL,
    enviado_em     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    -- O limite de 5 MB é garantido pelo banco, além da aplicação
    CONSTRAINT ck_anexo_tamanho CHECK (tamanho_bytes > 0
                                       AND tamanho_bytes <= 5242880),
    -- V-04: apenas formatos usados como evidência de chamado
    CONSTRAINT ck_anexo_extensao CHECK (
        lower(nome_arquivo) ~ '\.(png|jpg|jpeg|gif|webp|pdf|txt|log|csv)$')
);

CREATE INDEX ix_anexo_chamado ON anexo (chamado_id);

-- ------------------------------------------------------------------- visões --

-- Visão de apoio ao painel: evita repetir o cálculo de SLA nas consultas.
CREATE OR REPLACE VIEW vw_chamado_sla AS
SELECT c.id,
       c.protocolo,
       s.nome  AS status,
       p.nome  AS prioridade,
       c.data_abertura,
       c.data_encerramento,
       c.data_abertura + (p.sla_horas || ' hours')::INTERVAL AS prazo_sla,
       COALESCE(c.data_encerramento, NOW())
           > c.data_abertura + (p.sla_horas || ' hours')::INTERVAL AS sla_estourado,
       ROUND(EXTRACT(EPOCH FROM (COALESCE(c.data_encerramento, NOW())
             - c.data_abertura)) / 3600.0, 1) AS horas_em_aberto
FROM chamado c
JOIN status     s ON s.id = c.status_id
JOIN prioridade p ON p.id = c.prioridade_id;

COMMIT;
