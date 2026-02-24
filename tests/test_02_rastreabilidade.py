"""
BD2 — RASTREABILIDADE
=====================
Regras de negócio: Correlation ID em toda requisição; log estruturado; tempo de resposta.
Requisitos: REQ-BD2-R1 a REQ-BD2-R5 (ver 01-mapa-business-drivers.md).
"""
import uuid

import pytest

from tests.constants import HTTP_200, HTTP_404, ID_NOTAS_INEXISTENTE


class TestRastreabilidadeBugV1:
    """Cenários que expõem a ausência de rastreabilidade na v1."""

    def test_v1_nao_retorna_correlation_id(self, client, seed_notas):
        """
        REQ-BD2: Resposta deve permitir correlação com o request.
        BUG v1: body não inclui correlation_id; impossível correlacionar logs.
        """
        nota_id = seed_notas[0].id
        response = client.get(f"/v1/notas/{nota_id}")
        assert response.status_code == HTTP_200
        data = response.json()
        assert "correlation_id" not in data, (
            "v1 não deveria ter correlation_id — é o bug!"
        )

    def test_v1_erro_sem_contexto(self, client):
        """
        REQ-BD2: Erros devem ser auditáveis (contexto de rastreio).
        BUG v1: 404 sem informação de correlação no response.
        """
        response = client.get(f"/v1/notas/{ID_NOTAS_INEXISTENTE}")
        assert response.status_code == HTTP_404


class TestRastreabilidadeFixV2:
    """Cenários que validam rastreabilidade na v2 (middleware + endpoint)."""

    def test_v2_retorna_correlation_id_no_header(self, client, seed_notas):
        """REQ-BD2-R1: Toda resposta deve incluir header X-Correlation-ID (UUID)."""
        nota_id = seed_notas[0].id
        response = client.get(f"/v2/notas/{nota_id}")
        assert response.status_code == HTTP_200
        assert "x-correlation-id" in response.headers, (
            "Response deve conter header X-Correlation-ID"
        )
        cid = response.headers["x-correlation-id"]
        uuid.UUID(cid)

    def test_v2_propaga_correlation_id_do_client(self, client, seed_notas):
        """REQ-BD2-R2: Se o cliente enviar X-Correlation-ID, o mesmo valor deve ser devolvido."""
        meu_id = str(uuid.uuid4())
        nota_id = seed_notas[0].id
        response = client.get(
            f"/v2/notas/{nota_id}",
            headers={"X-Correlation-ID": meu_id},
        )
        assert response.headers["x-correlation-id"] == meu_id, (
            "Deve propagar o Correlation ID fornecido pelo client"
        )

    def test_v2_correlation_id_no_body(self, client, seed_notas):
        """REQ-BD2-R5: Endpoint de nota por ID deve incluir correlation_id no body."""
        nota_id = seed_notas[0].id
        response = client.get(f"/v2/notas/{nota_id}")
        data = response.json()
        assert "correlation_id" in data, (
            "Body do response deve incluir correlation_id para facilitar debug"
        )

    def test_v2_retorna_response_time(self, client, seed_notas):
        """REQ-BD2-R3: Resposta deve incluir tempo de processamento no header."""
        nota_id = seed_notas[0].id
        response = client.get(f"/v2/notas/{nota_id}")
        assert "x-response-time" in response.headers, (
            "Header X-Response-Time é essencial para monitoramento"
        )

    def test_v2_cada_request_tem_id_unico(self, client, seed_notas):
        """Cada request sem header explícito deve receber Correlation ID único."""
        nota_id = seed_notas[0].id
        r1 = client.get(f"/v2/notas/{nota_id}")
        r2 = client.get(f"/v2/notas/{nota_id}")
        cid1 = r1.headers["x-correlation-id"]
        cid2 = r2.headers["x-correlation-id"]
        assert cid1 != cid2, "Cada request deve ter um Correlation ID único"
