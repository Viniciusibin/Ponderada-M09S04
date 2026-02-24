"""
BD1 — VOLUMETRIA
================
Regras de negócio: listagem paginada; limite máximo por página; sem N+1.
Requisitos: REQ-BD1-V1 a REQ-BD1-V4 (ver 01-mapa-business-drivers.md).
Técnicas: equivalência (limit válido/inválido), valor de fronteira (0, 1, 100, 101).
"""
from tests.constants import (
    HTTP_200,
    HTTP_422,
    PAGINATION_DEFAULT_LIMIT,
    TOTAL_NOTAS_FIXTURE,
)


class TestVolumetriaBugV1:
    """Cenários que expõem o comportamento incorreto da v1 (sem paginação)."""

    def test_v1_retorna_todos_registros_sem_limite(self, client, seed_notas):
        """
        REQ-BD1: Listagem não deve retornar todos os registros de uma vez.
        BUG v1: GET /v1/notas retorna todo o dataset; em produção causaria timeout.
        """
        # Arrange: seed_notas garante TOTAL_NOTAS_FIXTURE notas
        # Act
        response = client.get("/v1/notas")
        # Assert
        assert response.status_code == HTTP_200
        data = response.json()
        assert len(data) == TOTAL_NOTAS_FIXTURE, (
            f"v1 retornou {len(data)} notas — DEVERIA ter paginação!"
        )

    def test_v1_nao_aceita_parametro_limit(self, client, seed_notas):
        """
        REQ-BD1: API deve respeitar parâmetros de paginação.
        BUG v1: query param limit é ignorado.
        """
        # Act
        response = client.get("/v1/notas?limit=5")
        data = response.json()
        # Assert
        assert len(data) > 5, "v1 não implementa paginação"


class TestVolumetriaFixV2:
    """Cenários que validam a implementação correta da v2 (paginação)."""

    def test_v2_paginacao_padrao_20(self, client, seed_notas):
        """REQ-BD1-V2: Valor padrão de limit deve ser 20."""
        response = client.get("/v2/notas")
        assert response.status_code == HTTP_200
        data = response.json()
        assert len(data) <= PAGINATION_DEFAULT_LIMIT, (
            f"Paginação padrão deveria limitar a {PAGINATION_DEFAULT_LIMIT}, retornou {len(data)}"
        )

    def test_v2_paginacao_com_limit(self, client, seed_notas):
        """REQ-BD1-V1/V3: Resposta deve conter no máximo limit itens."""
        limit = 5
        response = client.get(f"/v2/notas?limit={limit}")
        assert response.status_code == HTTP_200
        data = response.json()
        assert len(data) == limit

    def test_v2_paginacao_com_offset(self, client, seed_notas):
        """REQ-BD1-V1: Páginas distintas não devem sobrepor conjuntos de IDs."""
        page1 = client.get("/v2/notas?limit=10&offset=0").json()
        page2 = client.get("/v2/notas?limit=10&offset=10").json()
        ids_page1 = {n["id"] for n in page1}
        ids_page2 = {n["id"] for n in page2}
        assert ids_page1.isdisjoint(ids_page2), "Páginas não devem sobrepor"

    def test_v2_limite_maximo_100(self, client, seed_notas):
        """REQ-BD1: limit > 100 deve ser rejeitado (validação 422)."""
        response = client.get("/v2/notas?limit=500")
        assert response.status_code == HTTP_422, (
            "Deveria rejeitar limit > 100 com erro de validação"
        )

    def test_v2_limit_minimo_1(self, client, seed_notas):
        """REQ-BD1: limit < 1 deve ser rejeitado (fronteira)."""
        response = client.get("/v2/notas?limit=0")
        assert response.status_code == HTTP_422
