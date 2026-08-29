from zoneinfo import ZoneInfo

# Chamado
TITULO_MIN = 5
DESCRICAO_MIN = 10
COMENTARIO_MIN = 3
SOLUCAO_MIN = 10

# Anexo
ANEXO_MAX_MB = 5
ANEXO_MAX_BYTES = ANEXO_MAX_MB * 1024 * 1024
# V-04: apenas formatos usados como evidência de chamado
ANEXO_EXTENSOES = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp",
                             ".pdf", ".txt", ".log", ".csv"})

# Listagem
ITENS_POR_PAGINA = 25

# Usuário
NOME_MIN = 3
SENHA_MIN = 6


FUSO_LOCAL = ZoneInfo("America/Sao_Paulo")
