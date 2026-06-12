"""Create all tables from SQLAlchemy models (no Alembic needed for fresh install)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db

with app.app_context():
    db.create_all()
    print("Database initialised at:", app.config['SQLALCHEMY_DATABASE_URI'])
