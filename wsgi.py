"""
WSGI entry point for SaveInCloud (Apache + mod_wsgi).
FastAPI (ASGI) -> WSGI adapter using a2wsgi.
"""
from a2wsgi import ASGIMiddleware
from app.main import app

# Adaptar FastAPI (ASGI) a WSGI para mod_wsgi
application = ASGIMiddleware(app)
