"""
Gunicorn application object

Run in the most simple way with:
```
cd backend
export JWT_SECRET_KEY=SECRET-KEY
export DB_PASSWORD=passwd
gunicorn -b :8000 wsgi:app
```
"""
from backend_app import create_app
from src.models import prepare_database

app = create_app()
prepare_database(app)
