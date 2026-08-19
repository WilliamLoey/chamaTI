"""Tabelas de domínio — resultado da normalização até a 3FN do modelo lógico.

Categoria, Prioridade e Status eram, no PIT I, colunas de texto livre dentro da
tabela de chamados. Foram extraídas para tabelas próprias para eliminar
redundância e garantir integridade referencial.
"""
from app.extensions import db


class Categoria(db.Model):
    __tablename__ = "categoria"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(60), nullable=False, unique=True)
    descricao = db.Column(db.String(200))
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    chamados = db.relationship("Chamado", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria {self.nome}>"


class Prioridade(db.Model):
    __tablename__ = "prioridade"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(30), nullable=False, unique=True)
    # Prazo de atendimento em horas — base do cálculo de SLA
    sla_horas = db.Column(db.Integer, nullable=False, default=24)
    ordem = db.Column(db.Integer, nullable=False, default=0)

    chamados = db.relationship("Chamado", back_populates="prioridade")

    def __repr__(self):
        return f"<Prioridade {self.nome} ({self.sla_horas}h)>"


class Status(db.Model):
    __tablename__ = "status"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(30), nullable=False, unique=True)
    # Marca os status que encerram o ciclo de vida do chamado
    encerra = db.Column(db.Boolean, nullable=False, default=False)
    ordem = db.Column(db.Integer, nullable=False, default=0)

    chamados = db.relationship("Chamado", back_populates="status")

    def __repr__(self):
        return f"<Status {self.nome}>"
