"""
BD3 — ACESSO SIMULTÂNEO (CONCORRÊNCIA)
========================================
Regras de negócio: optimistic locking; evitar lost update; 409 em conflito.
Requisitos: REQ-BD3-C1 a REQ-BD3-C4 (ver 01-mapa-business-drivers.md).
"""
import pytest

from tests.constants import HTTP_200, HTTP_409


class TestConcorrenciaBugV1:
    """Cenários que expõem race condition na v1 (lost update)."""

    def test_v1_lost_update(self, client, seed_produtos):
        """
        REQ-BD3: Dois updates simultâneos não devem perder alterações.
        BUG v1: sem lock; em ambiente com threads/processos o resultado pode ser
        incorreto (lost update). Este teste verifica que ambos os requests retornam
        200; em SQLite single-thread o resultado pode ser correto por acaso.
        """
        produto = seed_produtos[0]
        estoque_inicial = produto.estoque
        r1 = client.put(f"/v1/produtos/{produto.id}/estoque?quantidade=10")
        r2 = client.put(f"/v1/produtos/{produto.id}/estoque?quantidade=20")
        assert r1.status_code == HTTP_200
        assert r2.status_code == HTTP_200
        final = client.get(f"/v2/produtos/{produto.id}").json()
        esperado = estoque_inicial + 10 + 20
        assert final["estoque"] == esperado, (
            f"v1 sem lock pode perder updates. Esperado: {esperado}, Obtido: {final['estoque']}"
        )


class TestConcorrenciaFixV2:
    """Cenários que validam optimistic locking na v2."""

    def test_v2_update_com_version_correta(self, client, seed_produtos):
        """REQ-BD3-C1/C4: Update com version correta deve retornar novo estoque e version."""
        produto = seed_produtos[0]
        response = client.put(
            f"/v2/produtos/{produto.id}/estoque"
            f"?quantidade=10&version={produto.version}"
        )
        assert response.status_code == HTTP_200
        data = response.json()
        assert data["estoque"] == produto.estoque + 10
        assert data["version"] == produto.version + 1

    def test_v2_conflito_com_version_errada(self, client, seed_produtos):
        """REQ-BD3-C3: Update com version desatualizada deve retornar 409 Conflict."""
        produto = seed_produtos[0]
        r1 = client.put(
            f"/v2/produtos/{produto.id}/estoque"
            f"?quantidade=5&version={produto.version}"
        )
        assert r1.status_code == HTTP_200
        r2 = client.put(
            f"/v2/produtos/{produto.id}/estoque"
            f"?quantidade=10&version={produto.version}"
        )
        assert r2.status_code == HTTP_409, (
            "Deveria retornar 409 Conflict quando version está desatualizada"
        )

    def test_v2_conflito_mensagem_clara(self, client, seed_produtos):
        """REQ-BD3-C3: Mensagem de erro deve orientar o usuário a recarregar."""
        produto = seed_produtos[0]
        client.put(
            f"/v2/produtos/{produto.id}/estoque"
            f"?quantidade=1&version={produto.version}"
        )
        r = client.put(
            f"/v2/produtos/{produto.id}/estoque"
            f"?quantidade=1&version={produto.version}"
        )
        assert r.status_code == HTTP_409
        detail = r.json().get("detail", "").lower()
        assert "concorrência" in detail or "conflito" in detail

    def test_v2_updates_sequenciais_corretos(self, client, seed_produtos):
        """REQ-BD3-C2/C4: Sequência de updates com version correta deve somar corretamente."""
        produto = seed_produtos[0]
        estoque_inicial = produto.estoque
        version_atual = produto.version

        r1 = client.put(
            f"/v2/produtos/{produto.id}/estoque"
            f"?quantidade=10&version={version_atual}"
        )
        assert r1.status_code == HTTP_200
        version_atual = r1.json()["version"]

        r2 = client.put(
            f"/v2/produtos/{produto.id}/estoque"
            f"?quantidade=20&version={version_atual}"
        )
        assert r2.status_code == HTTP_200
        assert r2.json()["estoque"] == estoque_inicial + 30
