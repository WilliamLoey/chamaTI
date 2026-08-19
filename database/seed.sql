-- ============================================================================
-- ChamaTI — carga inicial das tabelas de domínio.
-- Executar depois de database/ddl.sql:
--   psql "$DATABASE_URL" -f database/seed.sql
--
-- Usuários e chamados de demonstração são criados pelo comando `flask seed`,
-- que gera o hash das senhas pela própria aplicação.
-- ============================================================================

BEGIN;

INSERT INTO categoria (nome, descricao) VALUES
    ('Hardware',        'Equipamentos, periféricos e impressoras'),
    ('Software',        'Instalação, licença e erro de aplicativo'),
    ('Rede e Internet', 'Conexão, VPN e Wi-Fi'),
    ('Acesso e Senha',  'Bloqueio de conta e permissões'),
    ('E-mail',          'Caixa postal, listas e assinatura')
ON CONFLICT (nome) DO NOTHING;

INSERT INTO prioridade (nome, sla_horas, ordem) VALUES
    ('Baixa',   72, 1),
    ('Média',   24, 2),
    ('Alta',     8, 3),
    ('Crítica',  4, 4)
ON CONFLICT (nome) DO NOTHING;

INSERT INTO status (nome, encerra, ordem) VALUES
    ('Aberto',         FALSE, 1),
    ('Em atendimento', FALSE, 2),
    ('Resolvido',      TRUE,  3),
    ('Cancelado',      TRUE,  4)
ON CONFLICT (nome) DO NOTHING;

COMMIT;
