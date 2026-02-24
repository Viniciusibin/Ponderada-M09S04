"""
ASIS TaxTech Lab — FastAPI Application.
API com versões v1 (bugadas) e v2 (corrigidas) para exercício de Business Drivers.
"""
import os
import time
import uuid
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from app.database import Base, engine, get_db
from app.models import ItemNota, NotaFiscal, Produto
from app.schemas import (
    LoginRequest,
    NotaFiscalCreate,
    NotaFiscalResponse,
    ProdutoCreate,
    ProdutoResponse,
    ProdutoUpdate,
    Token,
)

SECRET_KEY = os.getenv("SECRET_KEY", "asis-lab-secret-key-2026")
ALGORITHM = "HS256"

logger = logging.getLogger("asis_taxtech")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria tabelas e popula dados de exemplo no startup (exceto em ambiente de teste)."""
    Base.metadata.create_all(bind=engine)
    if not os.environ.get("TESTING"):
        seed_database()
    yield


app = FastAPI(
    title="ASIS TaxTech Lab",
    description="Lab de Business Drivers — ES09 Inteli",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Injeta X-Correlation-ID e log estruturado (Driver 2 — Rastreabilidade)."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    logger.info(
        "request_started",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    start = time.time()
    response: Response = await call_next(request)
    duration = time.time() - start
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Response-Time"] = f"{duration:.4f}s"
    logger.info(
        "request_completed",
        extra={
            "correlation_id": correlation_id,
            "status_code": response.status_code,
            "duration_seconds": round(duration, 4),
        },
    )
    return response


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "asis-taxtech-lab"}


# ─── Driver 1 — Volumetria ─────────────────────────────────────────────────

@app.get("/v1/notas", response_model=list[NotaFiscalResponse])
def listar_notas_v1(db: Session = Depends(get_db)):
    """BUG: Retorna todas as notas sem paginação; N+1 ao acessar itens."""
    notas = db.query(NotaFiscal).all()
    for nota in notas:
        _ = nota.itens
    return notas


@app.get("/v2/notas", response_model=list[NotaFiscalResponse])
def listar_notas_v2(
    limit: int = Query(default=20, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Corrigido: paginação limit/offset e eager loading."""
    notas = (
        db.query(NotaFiscal)
        .options(joinedload(NotaFiscal.itens))
        .order_by(NotaFiscal.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return notas


# Rotas estáticas antes de /v2/notas/{nota_id} para evitar "protegido" e "busca" como nota_id
@app.get("/v2/notas/busca")
def buscar_notas_v2(
    cnpj: Optional[str] = Query(None, min_length=14, max_length=14, pattern=r"^\d{14}$"),
    db: Session = Depends(get_db),
):
    """Corrigido: validação CNPJ e query via ORM (Driver 4)."""
    if cnpj:
        notas = db.query(NotaFiscal).filter(NotaFiscal.emitente_cnpj == cnpj).all()
        return [
            {
                "id": n.id,
                "numero": n.numero,
                "emitente_cnpj": n.emitente_cnpj,
                "valor_total": n.valor_total,
                "status": n.status,
            }
            for n in notas
        ]
    return []


USERS_DB = {
    # hash bcrypt para senha "admin123" (rounds=12)
    "admin": "$2b$12$aPEp3KOGAsTdcETIwDQ.uOZVZ5MxhPtarufQjifpqVf84h0jVT2nq",
}


@app.post("/v2/auth/token", response_model=Token)
def login(credentials: LoginRequest):
    """Gera JWT para endpoints protegidos."""
    import bcrypt
    hashed = USERS_DB.get(credentials.username)
    if not hashed or not bcrypt.checkpw(
        credentials.password.encode("utf-8"), hashed.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = jwt.encode(
        {"sub": credentials.username, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return Token(access_token=token)


@app.get("/v2/notas/protegido")
def endpoint_protegido(request: Request, db: Session = Depends(get_db)):
    """Endpoint que requer JWT válido."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    token = auth.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return {
        "message": "Acesso autorizado",
        "user": payload.get("sub"),
        "notas_count": db.query(NotaFiscal).count(),
    }


# ─── Driver 2 — Rastreabilidade ──────────────────────────────────────────

@app.get("/v1/notas/{nota_id}")
def obter_nota_v1(nota_id: int, db: Session = Depends(get_db)):
    """BUG: Log com print(), sem correlation ID."""
    print(f"Buscando nota {nota_id}")
    nota = db.query(NotaFiscal).filter(NotaFiscal.id == nota_id).first()
    if not nota:
        print("Erro: nota não encontrada")
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return {
        "id": nota.id,
        "numero": nota.numero,
        "valor_total": nota.valor_total,
        "status": nota.status,
    }


@app.get("/v2/notas/{nota_id}")
def obter_nota_v2(nota_id: int, request: Request, db: Session = Depends(get_db)):
    """Corrigido: log estruturado e correlation_id no body."""
    cid = getattr(request.state, "correlation_id", "N/A")
    logger.info("buscar_nota", extra={"correlation_id": cid, "nota_id": nota_id})
    nota = db.query(NotaFiscal).filter(NotaFiscal.id == nota_id).first()
    if not nota:
        logger.warning("nota_nao_encontrada", extra={"correlation_id": cid, "nota_id": nota_id})
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    logger.info("nota_encontrada", extra={"correlation_id": cid, "nota_id": nota_id, "numero": nota.numero})
    return {
        "id": nota.id,
        "numero": nota.numero,
        "valor_total": nota.valor_total,
        "status": nota.status,
        "correlation_id": cid,
    }


# ─── Driver 3 — Concorrência ──────────────────────────────────────────────

@app.put("/v1/produtos/{produto_id}/estoque")
def atualizar_estoque_v1(
    produto_id: int,
    quantidade: int = Query(...),
    db: Session = Depends(get_db),
):
    """BUG: Race condition — lost update."""
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    time.sleep(0.1)
    produto.estoque = produto.estoque + quantidade
    db.commit()
    db.refresh(produto)
    return {"id": produto.id, "estoque": produto.estoque}


@app.put("/v2/produtos/{produto_id}/estoque")
def atualizar_estoque_v2(
    produto_id: int,
    quantidade: int = Query(...),
    version: int = Query(..., description="Versão atual do produto"),
    db: Session = Depends(get_db),
):
    """Corrigido: optimistic locking com version."""
    result = db.execute(
        text("""
            UPDATE produtos
            SET estoque = estoque + :quantidade, version = version + 1
            WHERE id = :id AND version = :version
        """),
        {"quantidade": quantidade, "id": produto_id, "version": version},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(
            status_code=409,
            detail="Conflito de concorrência — o registro foi alterado por outro usuário. Recarregue e tente novamente.",
        )
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    return {"id": produto.id, "estoque": produto.estoque, "version": produto.version}


# ─── Driver 4 — Segurança ─────────────────────────────────────────────────

@app.get("/v1/notas/busca")
def buscar_notas_v1(
    cnpj: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """BUG: SQL Injection via f-string."""
    if cnpj:
        query = f"SELECT * FROM notas_fiscais WHERE emitente_cnpj = '{cnpj}'"
        result = db.execute(text(query))
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    return []


# ─── CRUD Produtos (auxiliar) ─────────────────────────────────────────────

@app.get("/v2/produtos", response_model=list[ProdutoResponse])
def listar_produtos(
    limit: int = Query(default=20, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return db.query(Produto).offset(offset).limit(limit).all()


@app.get("/v2/produtos/{produto_id}", response_model=ProdutoResponse)
def obter_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto


@app.post("/v2/produtos", response_model=ProdutoResponse, status_code=201)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    db_produto = Produto(**produto.model_dump())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto


def seed_database():
    """Popula o banco com dados para os exercícios."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        if db.query(Produto).count() > 0:
            return
        produtos = []
        for i in range(1, 11):
            p = Produto(
                codigo=f"PROD-{i:04d}",
                descricao=f"Produto Fiscal {i}",
                ncm=f"{10000000 + i}",
                preco_unitario=round(50.0 + i * 12.5, 2),
                estoque=100 + i * 10,
            )
            db.add(p)
            produtos.append(p)
        db.flush()
        for i in range(1, 201):
            cnpj_emit = f"{11222333000100 + (i % 5):014d}"
            cnpj_dest = f"{44555666000100 + (i % 8):014d}"
            nf = NotaFiscal(
                numero=f"NF-{i:06d}",
                emitente_cnpj=cnpj_emit,
                destinatario_cnpj=cnpj_dest,
                valor_total=round(100.0 + i * 7.5, 2),
                status=["emitida", "autorizada", "cancelada"][i % 3],
                data_emissao=datetime(2026, 1, 1) + timedelta(hours=i),
            )
            db.add(nf)
            db.flush()
            for j in range(1, (i % 3) + 2):
                prod = produtos[(i + j) % len(produtos)]
                item = ItemNota(
                    nota_id=nf.id,
                    produto_id=prod.id,
                    quantidade=j * 2,
                    valor_unitario=prod.preco_unitario,
                    valor_total=prod.preco_unitario * j * 2,
                )
                db.add(item)
        db.commit()
        logger.info("Seed concluído: 10 produtos, 200 notas fiscais")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro no seed: {e}")
    finally:
        db.close()
