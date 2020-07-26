"""
Gunicorn application object

Run with: `gunicorn3 -b 0.0.0.0:8080 wsgi:app`
"""
import os

from application import create_app
from config.settings import ProdConfig

os.makedirs(ProdConfig().DB_PATH, exist_ok=True)

app = create_app()
