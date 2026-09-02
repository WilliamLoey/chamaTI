"""Models de chamado, interações e anexos."""
from datetime import datetime, timedelta, timezone

from app.extensions import db


def agora():
    return datetime.now(timezone.utc)


class Chamado(db.Model):
    __tablename__ = "chamado"
    __table_args__ = (
        # Índices que sustentam os filtros e a ordenação padrão da listagem
        db.Index("ix_chamado_status", "status_id"),
        db.Index("ix_chamado_data_abertura", "data_abertura"),
        db.Index("ix_chamado_solicitante", "solicitante_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(20), nullable=False, unique=True, index=True)
    titulo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=False)

    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), nullable=False)
    prioridade_id = db.Column(db.Integer, db.ForeignKey("prioridade.id"), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey("status.id"), nullable=False)

    solicitante_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))

    data_abertura = db.Column(db.DateTime, nullable=False, default=agora)
    data_encerramento = db.Column(db.DateTime)
    solucao = db.Column(db.Text)
    # L-04: obrigatória quando o chamado é encerrado com o prazo já estourado
    justificativa_atraso = db.Column(db.Text)

    categoria = db.relationship("Categoria", back_populates="chamados")
    prioridade = db.relationship("Prioridade", back_populates="chamados")
    status = db.relationship("Status", back_populates="chamados")
    solicitante = db.relationship("Usuario", foreign_keys=[solicitante_id],
                                  back_populates="chamados_abertos")
    tecnico = db.relationship("Usuario", foreign_keys=[tecnico_id],
                              back_populates="chamados_atribuidos")
    interacoes = db.relationship("Interacao", back_populates="chamado",
                                 cascade="all, delete-orphan",
                                 order_by="Interacao.criado_em")
    anexos = db.relationship("Anexo", back_populates="chamado",
                             cascade="all, delete-orphan")

    # ------------------------------------------------------------------- SLA
    @property
    def prazo_sla(self):
        if not self.prioridade:
            return None
        return self._aware(self.data_abertura) + timedelta(hours=self.prioridade.sla_horas)

    @property
    def encerrado(self) -> bool:
        return bool(self.status and self.status.encerra)

    @property
    def sla_estourado(self) -> bool:
        prazo = self.prazo_sla
        if prazo is None:
            return False
        referencia = self._aware(self.data_encerramento) if self.encerrado else agora()
        return referencia > prazo

    @property
    def horas_em_aberto(self):
        fim = self._aware(self.data_encerramento) if self.encerrado else agora()
        delta = fim - self._aware(self.data_abertura)
        return round(delta.total_seconds() / 3600, 1)

    @staticmethod
    def _aware(valor):
        """SQLite devolve datetime sem fuso; normaliza para UTC antes de comparar."""
        if valor is None:
            return None
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)

    def __repr__(self):
        return f"<Chamado {self.protocolo}>"


class Interacao(db.Model):
    """Histórico do chamado: cada mudança de status ou comentário vira uma linha.
    Atende ao requisito de rastreabilidade levantado na revisão do PIT I."""

    __tablename__ = "interacao"

    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey("chamado.id"), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default="comentario")  # comentario | sistema
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    chamado = db.relationship("Chamado", back_populates="interacoes")
    autor = db.relationship("Usuario")

    def __repr__(self):
        return f"<Interacao {self.tipo} chamado={self.chamado_id}>"


class Anexo(db.Model):
    """V-03: até a versão 1.0 esta tabela guardava apenas o nome e o tamanho —
    o arquivo enviado era descartado. O conteúdo passou a ser gravado na coluna
    `conteudo`, dentro do próprio banco.

    Guardar no banco, e não em disco, é decisão consciente: a hospedagem
    gratuita usa sistema de arquivos efêmero, que é apagado a cada reinício do
    serviço. Para o volume deste projeto (5 MB por arquivo) a escolha é segura.
    """

    __tablename__ = "anexo"

    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey("chamado.id"), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    tipo_mime = db.Column(db.String(100), nullable=False, default="application/octet-stream")
    tamanho_bytes = db.Column(db.Integer, nullable=False)
    conteudo = db.Column(db.LargeBinary, nullable=False)
    enviado_em = db.Column(db.DateTime, nullable=False, default=agora)

    chamado = db.relationship("Chamado", back_populates="anexos")

    @property
    def tamanho_legivel(self):
        kb = self.tamanho_bytes / 1024
        return f"{kb:.1f} KB" if kb < 1024 else f"{kb / 1024:.1f} MB"

    def __repr__(self):
        return f"<Anexo {self.nome_arquivo}>"
