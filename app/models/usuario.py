"""Model de usuário e perfis de acesso."""
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class Perfil:
    """Perfis de acesso do sistema. Não é tabela: é um enumerado estável,
    referenciado por código, para evitar consulta desnecessária ao banco."""

    SOLICITANTE = "solicitante"
    TECNICO = "tecnico"
    GESTOR = "gestor"

    TODOS = (SOLICITANTE, TECNICO, GESTOR)
    ROTULOS = {
        SOLICITANTE: "Solicitante",
        TECNICO: "Técnico",
        GESTOR: "Gestor",
    }

    @classmethod
    def rotulo(cls, perfil: str) -> str:
        return cls.ROTULOS.get(perfil, perfil)


class Usuario(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(20), nullable=False, default=Perfil.SOLICITANTE)
    departamento = db.Column(db.String(80))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False,
                          default=lambda: datetime.now(timezone.utc))

    chamados_abertos = db.relationship(
        "Chamado", foreign_keys="Chamado.solicitante_id",
        back_populates="solicitante")
    chamados_atribuidos = db.relationship(
        "Chamado", foreign_keys="Chamado.tecnico_id",
        back_populates="tecnico")

    # ------------------------------------------------------------------ senha
    def definir_senha(self, senha_plana: str) -> None:
        self.senha_hash = generate_password_hash(senha_plana)

    def conferir_senha(self, senha_plana: str) -> bool:
        return check_password_hash(self.senha_hash, senha_plana or "")

    # ------------------------------------------------------------- permissões
    @property
    def rotulo_perfil(self) -> str:
        return Perfil.ROTULOS.get(self.perfil, self.perfil)

    @property
    def eh_gestor(self) -> bool:
        return self.perfil == Perfil.GESTOR

    @property
    def eh_tecnico(self) -> bool:
        return self.perfil == Perfil.TECNICO

    @property
    def eh_solicitante(self) -> bool:
        return self.perfil == Perfil.SOLICITANTE

    def pode_ver_chamado(self, chamado) -> bool:
        """Gestor vê tudo; solicitante vê apenas os próprios chamados.

        V-07: até a versão 1.0, o técnico perdia o acesso ao chamado assim que
        ele era reatribuído a outro colega — inclusive ao histórico que ele
        próprio havia escrito. Agora ele continua enxergando os chamados em que
        participou.
        """
        if self.eh_gestor:
            return True
        if self.eh_tecnico:
            if chamado.tecnico_id in (None, self.id):
                return True
            if chamado.solicitante_id == self.id:
                return True
            # participou do atendimento em algum momento
            return any(i.autor_id == self.id for i in chamado.interacoes)
        return chamado.solicitante_id == self.id

    def __repr__(self):
        return f"<Usuario {self.email} ({self.perfil})>"
