from pathlib import Path
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "medical_demo.db"

def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}", future=True)
