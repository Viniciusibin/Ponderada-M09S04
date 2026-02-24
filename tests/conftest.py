"""
Fixtures compartilhadas e configuração do ambiente de testes.
Garante banco isolado (SQLite em memória) e cliente HTTP para a API.
Ref.: IEEE 829 / ISO 29119 — configuração e teardown reproduzíveis.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ambiente de teste: SQLite em memória compartilhada; app não executa seed no lifespan
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///:memory:?cache=shared"

from app.database import Base, get_db
from app.main import app

# ─── Constantes de ambiente de teste ──────────────────────────────────────
SQLALCHEMY_TEST_URL = os.environ["DATABASE_URL"]

engine_test = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_TEST_URL else {},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    """Fornece sessão de teste (SQLite) em vez da sessão de produção."""
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Sessão isolada por teste: cria tabelas, entrega sessão, remove tabelas ao final."""
    Base.metadata.create_all(bind=engine_test)
    db = TestSession()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db_session):
    """Cliente HTTP (TestClient) com injeção do banco de teste."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine_test)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


# ─── Massa de dados (Test Data) ───────────────────────────────────────────

@pytest.fixture
def seed_produtos(db_session):
    """10 produtos para cenários de estoque e itens de nota. REQ: massa controlada."""
    from app.models import Produto
    produtos = []
    for i in range(1, 11):
        p = Produto(
            codigo=f"TEST-{i:04d}",
            descricao=f"Produto Teste {i}",
            ncm=f"{20000000 + i}",
            preco_unitario=round(25.0 + i * 5.0, 2),
            estoque=100,
        )
        db_session.add(p)
        produtos.append(p)
    db_session.commit()
    return produtos


@pytest.fixture
def seed_notas(db_session, seed_produtos):
    """50 notas fiscais com itens. REQ: volumetria e rastreabilidade."""
    from app.models import ItemNota, NotaFiscal
    from datetime import datetime, timedelta

    notas = []
    for i in range(1, 51):
        nf = NotaFiscal(
            numero=f"TST-{i:06d}",
            emitente_cnpj=f"{11222333000100 + (i % 3):014d}",
            destinatario_cnpj=f"{44555666000100 + (i % 5):014d}",
            valor_total=round(50.0 + i * 3.0, 2),
            status="emitida",
            data_emissao=datetime(2026, 1, 1) + timedelta(hours=i),
        )
        db_session.add(nf)
        db_session.flush()

        item = ItemNota(
            nota_id=nf.id,
            produto_id=seed_produtos[i % len(seed_produtos)].id,
            quantidade=2,
            valor_unitario=seed_produtos[i % len(seed_produtos)].preco_unitario,
            valor_total=seed_produtos[i % len(seed_produtos)].preco_unitario * 2,
        )
        db_session.add(item)
        notas.append(nf)

    db_session.commit()
    return notas
