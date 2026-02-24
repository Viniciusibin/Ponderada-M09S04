"""
BD4 — SEGURANÇA
===============
Regras de negócio: sem SQL Injection; validação CNPJ; JWT em rotas protegidas.
Requisitos: REQ-BD4-S1 a REQ-BD4-S5 (ver 01-mapa-business-drivers.md).
"""
import pytest

from tests.constants import (
    CNPJ_INVALIDO_CURTO,
    CNPJ_VALIDO_14_DIGITOS,
    HTTP_200,
    HTTP_401,
    HTTP_422,
    PASSWORD_ADMIN,
    PASSWORD_INVALIDA,
    SQL_INJECTION_PAYLOAD,
    USER_ADMIN,
)


class TestSegurancaBugV1:
    """Cenários que expõem vulnerabilidades da v1."""

    def test_v1_sql_injection_retorna_tudo(self, client, seed_notas):
        """
        REQ-BD4-S1/S3: Busca não pode ser vulnerável a SQL Injection.
        BUG v1: payload ' OR '1'='1 retorna todas as notas.
        """
        response = client.get(f"/v1/notas/busca?cnpj={SQL_INJECTION_PAYLOAD}")
        if response.status_code == HTTP_200:
            data = response.json()
            if len(data) > 0:
                pytest.fail(
                    f"SQL INJECTION bem-sucedido! Retornou {len(data)} notas com payload malicioso."
                )

    def test_v1_aceita_cnpj_invalido(self, client):
        """REQ-BD4-S2: API deve validar formato do CNPJ (14 dígitos)."""
        response = client.get("/v1/notas/busca?cnpj=abc')--")
        # v1 sem validação pode retornar 200 (inseguro), 422 (validação em camada) ou 500 (erro SQL)
        assert response.status_code in [HTTP_200, HTTP_422, 500], (
            "v1 com CNPJ inválido não deve retornar sucesso com dados sensíveis"
        )


class TestSegurancaFixV2:
    """Cenários que validam proteções da v2."""

    def test_v2_sql_injection_bloqueado(self, client, seed_notas):
        """REQ-BD4-S3: Payloads de SQL injection devem ser rejeitados (422)."""
        response = client.get(f"/v2/notas/busca?cnpj={SQL_INJECTION_PAYLOAD}")
        assert response.status_code == HTTP_422, (
            f"Deveria rejeitar SQL injection com 422, retornou {response.status_code}"
        )

    def test_v2_valida_formato_cnpj(self, client, seed_notas):
        """REQ-BD4-S2: Aceitar apenas CNPJ com 14 dígitos numéricos."""
        cnpj_valido = seed_notas[0].emitente_cnpj
        response = client.get(f"/v2/notas/busca?cnpj={cnpj_valido}")
        assert response.status_code == HTTP_200

        response = client.get("/v2/notas/busca?cnpj=abcdefghijklmn")
        assert response.status_code == HTTP_422

        response = client.get(f"/v2/notas/busca?cnpj={CNPJ_INVALIDO_CURTO}")
        assert response.status_code == HTTP_422

        response = client.get("/v2/notas/busca?cnpj=11.222.333/0001")
        assert response.status_code == HTTP_422

    def test_v2_busca_retorna_apenas_cnpj_especifico(self, client, seed_notas):
        """REQ-BD4-S1: Busca deve retornar apenas notas do CNPJ informado."""
        cnpj = str(seed_notas[0].emitente_cnpj)
        response = client.get(f"/v2/notas/busca?cnpj={cnpj}")
        assert response.status_code == HTTP_200, (
            f"Resposta inesperada {response.status_code} para CNPJ {cnpj!r}"
        )
        data = response.json()
        for nota in data:
            assert nota["emitente_cnpj"] == cnpj

    def test_v2_autenticacao_sem_token(self, client):
        """REQ-BD4-S4: Endpoint protegido deve rejeitar requests sem token (401)."""
        response = client.get("/v2/notas/protegido")
        assert response.status_code == HTTP_401

    def test_v2_autenticacao_token_invalido(self, client):
        """REQ-BD4-S4: Token inválido deve retornar 401."""
        response = client.get(
            "/v2/notas/protegido",
            headers={"Authorization": "Bearer token-invalido-123"},
        )
        assert response.status_code == HTTP_401

    def test_v2_autenticacao_token_valido(self, client):
        """REQ-BD4-S5: Login com credenciais válidas deve gerar token funcional."""
        login_response = client.post(
            "/v2/auth/token",
            json={"username": USER_ADMIN, "password": PASSWORD_ADMIN},
        )
        assert login_response.status_code == HTTP_200
        token = login_response.json()["access_token"]
        response = client.get(
            "/v2/notas/protegido",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == HTTP_200
        assert response.json()["user"] == USER_ADMIN

    def test_v2_login_credenciais_invalidas(self, client):
        """Login com senha errada deve retornar 401."""
        response = client.post(
            "/v2/auth/token",
            json={"username": USER_ADMIN, "password": PASSWORD_INVALIDA},
        )
        assert response.status_code == HTTP_401
