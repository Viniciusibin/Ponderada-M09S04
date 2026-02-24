"""
Schemas Pydantic — validação de entrada e saída da API.
"""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ProdutoBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=20)
    descricao: str = Field(..., min_length=1, max_length=200)
    ncm: str = Field(..., pattern=r"^\d{8}$")
    preco_unitario: float = Field(..., gt=0)
    estoque: int = Field(default=0, ge=0)


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    estoque: int = Field(..., ge=0)
    version: int = Field(..., description="Versão atual para optimistic locking")


class ProdutoResponse(ProdutoBase):
    id: int
    version: int

    class Config:
        from_attributes = True


class NotaFiscalBase(BaseModel):
    numero: str = Field(..., min_length=1, max_length=20)
    serie: str = Field(default="001", max_length=5)
    emitente_cnpj: str = Field(..., min_length=14, max_length=14)
    destinatario_cnpj: str = Field(..., min_length=14, max_length=14)
    valor_total: float = Field(..., gt=0)
    observacao: Optional[str] = None

    @field_validator("emitente_cnpj", "destinatario_cnpj")
    @classmethod
    def validar_cnpj(cls, v):
        if not re.match(r"^\d{14}$", v):
            raise ValueError("CNPJ deve conter exatamente 14 dígitos numéricos")
        return v


class NotaFiscalCreate(NotaFiscalBase):
    pass


class NotaFiscalResponse(NotaFiscalBase):
    id: int
    status: str
    data_emissao: datetime

    class Config:
        from_attributes = True


class BuscaNotaParams(BaseModel):
    cnpj: Optional[str] = None
    status: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
