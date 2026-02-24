# Codificação como Documentação de Testes — ASIS TaxTech Lab

**Projeto:** ASIS TaxTech — Regras de negócio e qualidade aferida por código  
**Escopo:** Direcionadores **Volumetria (BD1)** e **Rastreabilidade (BD2)**  
**Referências:** Testes como especificação executável; padrão Arrange-Act-Assert (AAA); rastreabilidade requisito ↔ asserção.

Este documento mostra como o **código dos testes** funciona como **documentação executável** das regras de negócio, com convenções de engenharia de software aplicadas no repositório.

---

## 1. Princípio: testes como documentação viva

- **Testes são especificação executável:** o comportamento esperado está codificado em asserções.
- **Nomes e docstrings** descrevem o requisito (REQ-BDx) ou o bug em linguagem de negócio.
- **Aferição de qualidade** é feita ao **executar** os testes; passar/falhar indica conformidade.

No projeto, cada arquivo de teste:

1. Declara o **Business Driver** e os **requisitos** no topo (docstring do módulo).
2. Agrupa casos em classes **Bug V1** vs **Fix V2**.
3. Usa **constantes** (`tests/constants.py`) para evitar números e strings mágicos.
4. Usa **nomes de teste descritivos** e **docstrings** com ID do requisito quando aplicável.
5. Estrutura os métodos em **Arrange-Act-Assert** (comentários no código quando útil).

---

## 2. Convenções de codificação aplicadas

| Convenção | Aplicação no código |
|-----------|----------------------|
| **Constantes** | `tests/constants.py`: `PAGINATION_DEFAULT_LIMIT`, `HTTP_422`, `TOTAL_NOTAS_FIXTURE`, `SQL_INJECTION_PAYLOAD`, etc. |
| **Nomenclatura** | `test_<versão>_<comportamento>` (ex.: `test_v2_limite_maximo_100`, `test_v2_propaga_correlation_id_do_client`). |
| **Docstring** | Primeira linha descreve requisito (REQ-BDx) ou bug; segunda linha critério de aceite quando necessário. |
| **Uma responsabilidade por teste** | Cada método cobre um requisito ou um cenário (ex.: “limit máximo 100”, “propagar correlation ID”). |
| **Mensagem de assert** | Strings em asserts explicam o que falhou (ex.: “Deveria rejeitar limit > 100 com erro de validação”). |
| **Rastreabilidade** | Docstrings referenciam REQ-BD1, REQ-BD2, etc., alinhados ao Mapa de Business Drivers. |

---

## 3. Direcionador Volumetria (BD1) — Código como documentação

### 3.1 Documentação no nível do módulo

Em `tests/test_01_volumetria.py`:

```python
"""
BD1 — VOLUMETRIA
================
Regras de negócio: listagem paginada; limite máximo por página; sem N+1.
Requisitos: REQ-BD1-V1 a REQ-BD1-V4 (ver 01-mapa-business-drivers.md).
Técnicas: equivalência (limit válido/inválido), valor de fronteira (0, 1, 100, 101).
"""
```

### 3.2 Uso de constantes e asserções

Exemplo de teste que documenta a regra e usa constantes:

```python
def test_v2_limite_maximo_100(self, client, seed_notas):
    """REQ-BD1: limit > 100 deve ser rejeitado (validação 422)."""
    response = client.get("/v2/notas?limit=500")
    assert response.status_code == HTTP_422, (
        "Deveria rejeitar limit > 100 com erro de validação"
    )
```

### 3.3 Tabela: requisito ↔ nome do teste ↔ asserção

| Requisito | Nome do teste | Asserção principal |
|-----------|---------------|--------------------|
| Listagem não deve retornar tudo | test_v1_retorna_todos_registros_sem_limite | `len(data) == TOTAL_NOTAS_FIXTURE` |
| v1 não implementa paginação | test_v1_nao_aceita_parametro_limit | Com `limit=5`, `len(data) > 5` |
| Default 20 itens | test_v2_paginacao_padrao_20 | `len(data) <= PAGINATION_DEFAULT_LIMIT` |
| Respeitar limit | test_v2_paginacao_com_limit | `limit=5` → `len(data) == 5` |
| Páginas sem sobreposição | test_v2_paginacao_com_offset | IDs da página 1 e 2 disjuntos |
| Limite máximo 100 | test_v2_limite_maximo_100 | `limit=500` → HTTP_422 |
| Limite mínimo 1 | test_v2_limit_minimo_1 | `limit=0` → HTTP_422 |

---

## 4. Direcionador Rastreabilidade (BD2) — Código como documentação

### 4.1 Documentação no nível do módulo

Em `tests/test_02_rastreabilidade.py`:

```python
"""
BD2 — RASTREABILIDADE
=====================
Regras de negócio: Correlation ID em toda requisição; log estruturado; tempo de resposta.
Requisitos: REQ-BD2-R1 a REQ-BD2-R5 (ver 01-mapa-business-drivers.md).
"""
```

### 4.2 Tabela: requisito ↔ nome do teste ↔ asserção

| Requisito | Nome do teste | Asserção principal |
|-----------|---------------|--------------------|
| v1 sem correlation no body | test_v1_nao_retorna_correlation_id | `"correlation_id" not in data` |
| v1 erro sem contexto | test_v1_erro_sem_contexto | status HTTP_404 |
| Header X-Correlation-ID (UUID) | test_v2_retorna_correlation_id_no_header | Header presente; `uuid.UUID(cid)` |
| Propagação do ID do client | test_v2_propaga_correlation_id_do_client | `response.headers["x-correlation-id"] == meu_id` |
| correlation_id no body | test_v2_correlation_id_no_body | `"correlation_id" in data` |
| Tempo de resposta | test_v2_retorna_response_time | Header `x-response-time` presente |
| ID único por request | test_v2_cada_request_tem_id_unico | Dois requests sem header → dois IDs diferentes |

---

## 5. Boas práticas de engenharia de software

| Prática | Como aparece no código |
|---------|------------------------|
| **Testes como especificação** | Docstrings e nomes descrevem regra ou bug; asserções definem critério de aceite. |
| **Dados controlados** | Fixtures `seed_notas` e `seed_produtos`; constantes em `constants.py`. |
| **Um conceito por teste** | Cada método cobre um requisito ou cenário. |
| **Nomes legíveis** | Padrão `test_<v1|v2>_<comportamento>`. |
| **Mensagens de assert** | Strings explicam o que falhou. |
| **Separação Bug vs Fix** | Classes Test*BugV1 e Test*FixV2. |
| **Execução repetível** | `pytest tests/ -v` aferem a qualidade dos requisitos. |
| **Rastreabilidade** | Referência a REQ-BDx nas docstrings e no Mapa. |

---

## 6. Como aferir a qualidade dos requisitos

1. **Documentar a regra** no Mapa de Business Drivers (`01-mapa-business-drivers.md`) com ID (REQ-BDx).
2. **Codificar o critério** em um ou mais testes com nome e docstring que referenciam o requisito.
3. **Executar a suite:** `pytest tests/ -v`.
4. **Interpretar resultado:**
   - Testes **Fix V2** passando → implementação v2 em conformidade com os requisitos.
   - Testes **Bug V1** passando conforme comportamento documentado → requisitos usados para distinguir incorreto do correto.

A codificação dos testes serve ao mesmo tempo como **documentação das regras** e como **ferramenta de aferição de qualidade** ao executar o código.

---

*Documento alinhado a boas práticas de engenharia de software. Atividade Ponderada M09S04.*
