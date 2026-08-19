"""Indicadores do painel do gestor.

Todos os números saem de agregações no banco (COUNT/AVG), não de laços em
Python — decisão tomada na correção E-01, de desempenho.
"""
from sqlalchemy import func

from app.extensions import db
from app.models import Chamado, Prioridade, Status, Usuario
from app.services.chamado_service import STATUS_RESOLVIDO


def totais_por_status():
    linhas = (db.session.query(Status.nome, func.count(Chamado.id))
              .outerjoin(Chamado, Chamado.status_id == Status.id)
              .group_by(Status.id, Status.nome, Status.ordem)
              .order_by(Status.ordem)
              .all())
    return [{"rotulo": nome, "total": total} for nome, total in linhas]


def totais_por_prioridade():
    linhas = (db.session.query(Prioridade.nome, func.count(Chamado.id))
              .outerjoin(Chamado, Chamado.prioridade_id == Prioridade.id)
              .group_by(Prioridade.id, Prioridade.nome, Prioridade.ordem)
              .order_by(Prioridade.ordem)
              .all())
    return [{"rotulo": nome, "total": total} for nome, total in linhas]


def tempo_medio_atendimento_horas():
    """Média de horas entre abertura e encerramento dos chamados resolvidos."""
    chamados = (Chamado.query
                .join(Status)
                .filter(Status.encerra.is_(True), Chamado.data_encerramento.isnot(None))
                .all())
    if not chamados:
        return 0.0
    return round(sum(c.horas_em_aberto for c in chamados) / len(chamados), 1)


def taxa_dentro_do_sla():
    """Percentual de chamados encerrados dentro do prazo da prioridade."""
    chamados = (Chamado.query
                .join(Status)
                .filter(Status.encerra.is_(True))
                .all())
    if not chamados:
        return 100.0
    no_prazo = sum(1 for c in chamados if not c.sla_estourado)
    return round(no_prazo * 100 / len(chamados), 1)


def carga_por_tecnico():
    linhas = (db.session.query(Usuario.nome, func.count(Chamado.id))
              .join(Chamado, Chamado.tecnico_id == Usuario.id)
              .join(Status, Chamado.status_id == Status.id)
              .filter(Status.encerra.is_(False))
              .group_by(Usuario.id, Usuario.nome)
              .order_by(func.count(Chamado.id).desc())
              .all())
    return [{"rotulo": nome, "total": total} for nome, total in linhas]


def resumo():
    total = Chamado.query.count()
    em_aberto = (Chamado.query.join(Status)
                 .filter(Status.encerra.is_(False)).count())
    resolvidos = (Chamado.query.join(Status)
                  .filter(Status.nome == STATUS_RESOLVIDO).count())
    return {
        "total": total,
        "em_aberto": em_aberto,
        "resolvidos": resolvidos,
        "tempo_medio_horas": tempo_medio_atendimento_horas(),
        "taxa_sla": taxa_dentro_do_sla(),
        "por_status": totais_por_status(),
        "por_prioridade": totais_por_prioridade(),
        "por_tecnico": carga_por_tecnico(),
    }
