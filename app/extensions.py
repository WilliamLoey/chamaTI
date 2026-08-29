"""Extensões instanciadas fora da factory para evitar importação circular."""
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()

# V-02: protege todo request POST/PUT/PATCH/DELETE contra Cross-Site Request
# Forgery. O token é injetado nos formulários com {{ csrf_token() }}.
csrf = CSRFProtect()
