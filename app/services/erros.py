"""Exceções de negócio.

Toda regra violada levanta ErroDeNegocio com uma mensagem já redigida para o
usuário final, seguindo o padrão de mensagem definido em docs/ihc.md:
"o que aconteceu + como resolver".
"""


class ErroDeNegocio(Exception):
    def __init__(self, mensagem, campo=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.campo = campo  # permite destacar o campo com problema na tela


class PermissaoNegada(ErroDeNegocio):
    pass
