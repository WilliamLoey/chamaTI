-- ============================================================================
-- ChamaTI — Migração da versão 2.0 para a 2.1
--
-- A validação com usuários (L-04, laudo de Antônio Alves Araujo Neto) exigiu
-- registrar o motivo do atraso quando um chamado é encerrado fora do prazo.
--
-- Este script altera a tabela existente sem apagar dado nenhum, ao contrário
-- do ddl.sql, que recria o esquema do zero. Use este em banco que já está em
-- produção; use o ddl.sql apenas em banco novo ou quando quiser zerar a base.
--
-- Execução:
--   psql "$DATABASE_URL" -f database/migracao-2.1.sql
--
-- É idempotente: rodar duas vezes não causa erro.
-- ============================================================================

BEGIN;

ALTER TABLE chamado
    ADD COLUMN IF NOT EXISTS justificativa_atraso TEXT;

COMMENT ON COLUMN chamado.justificativa_atraso IS
    'Motivo do atraso. Exigido pela aplicação (mínimo de 15 caracteres) quando '
    'o chamado é encerrado depois de vencido o prazo da prioridade. Fica nulo '
    'quando o encerramento acontece dentro do SLA.';

COMMIT;

-- Conferência:
--   \d chamado
-- deve listar: justificativa_atraso | text
