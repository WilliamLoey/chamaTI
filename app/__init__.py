"""Application factory do ChamaTI.

Organização em camadas (MVC):
    app/models      -> Model      (entidades e persistência)
    app/templates   -> View       (Jinja2 + HTML/CSS/JS)
    app/controllers -> Controller (blueprints Flask)
    app/services    -> regras de negócio, isoladas dos controllers
"""
from datetime import datetime, timezone

from flask import Flask, render_template

from app.config import get_config
from app.extensions import db


def create_app(config_nome=None):
    app = Flask(__name__)
    app.config.from_object(get_config(config_nome))
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # trava de borda do servidor

    db.init_app(app)

    from app.controllers import auth, chamados, main, painel
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(chamados.bp)
    app.register_blueprint(painel.bp)

    _registrar_context(app)
    _registrar_erros(app)
    _registrar_filtros(app)
    _registrar_cli(app)
    return app


def _registrar_context(app):
    from flask import g

    from app.controllers.seguranca import usuario_atual

    @app.before_request
    def _limpar_cache_do_usuario():
        """O usuário da sessão é memorizado em `g` durante a requisição. Se o
        contexto de aplicação for reaproveitado entre requisições (caso dos
        testes), esse cache precisa ser descartado no início de cada uma —
        caso contrário um logout não teria efeito na requisição seguinte."""
        g.pop("usuario", None)

    @app.context_processor
    def injetar():
        return {"usuario": usuario_atual(), "ano_atual": datetime.now(timezone.utc).year}


def _registrar_erros(app):
    @app.errorhandler(404)
    def nao_encontrado(_):
        return render_template(
            "erros/404.html",
            mensagem="A página que você tentou acessar não existe ou foi movida."), 404

    @app.errorhandler(403)
    def proibido(_):
        return render_template(
            "erros/403.html",
            mensagem="Você não tem permissão para acessar este recurso."), 403

    @app.errorhandler(413)
    def arquivo_grande(_):
        return render_template(
            "erros/413.html",
            mensagem="O arquivo enviado é grande demais. O limite por anexo é de 5 MB."), 413

    @app.errorhandler(500)
    def erro_interno(_):
        db.session.rollback()
        return render_template(
            "erros/500.html",
            mensagem="Ocorreu um erro inesperado. A equipe foi notificada; "
                     "tente novamente em alguns minutos."), 500


def _registrar_filtros(app):
    @app.template_filter("data_hora")
    def data_hora(valor):
        if valor is None:
            return "—"
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.strftime("%d/%m/%Y às %H:%M")

    @app.template_filter("data")
    def data(valor):
        if valor is None:
            return "—"
        return valor.strftime("%d/%m/%Y")


def _registrar_cli(app):
    """Comandos de terminal: flask init-db e flask seed."""
    import click

    @app.cli.command("init-db")
    def init_db():
        """Cria as tabelas a partir dos models."""
        db.create_all()
        click.echo("Tabelas criadas.")

    @app.cli.command("seed")
    def seed():
        """Popula o banco com domínios, usuários e chamados de demonstração."""
        from app.seed import popular
        db.create_all()
        resumo = popular()
        click.echo(f"Banco populado: {resumo}")
