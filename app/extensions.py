"""Extensões instanciadas fora da factory para evitar importação circular."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
