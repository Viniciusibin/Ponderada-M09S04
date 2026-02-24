"""
Conexão com o banco de dados.
Suporta PostgreSQL (produção) e SQLite (testes via override em conftest).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://asis:asis123@localhost:5432/asis_taxtech",
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency: fornece sessão do banco por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
