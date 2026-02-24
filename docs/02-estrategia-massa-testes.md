# Estratégia e Massa de Testes — ASIS TaxTech Lab

**Projeto:** ASIS TaxTech — Qualidade baseada em código  
**Escopo:** Direcionadores **Volumetria (BD1)** e **Rastreabilidade (BD2)**  
**Referências:** ISO/IEC 29119-2 (técnicas de teste), IEEE 829 (plano de teste), Test Data Driven.

Este documento descreve a estratégia de testes e a massa de dados utilizada para aferir os requisitos REQ-BD1 e REQ-BD2, com identificação de casos de teste e técnicas de projeto aplicadas.

---

## 1. Estratégia de testes

### 1.1 Objetivos (alinhados ao MVP do projeto)

- Validar o **comportamento da API** conforme regras de negócio documentadas no Mapa de Business Drivers.
- Detectar **regressões** comparando versões v1 (bugada) e v2 (corrigida).
- Permitir **execução local e em linha de comando** e integração a CI/CD (desejável).
- Cobrir **caminho feliz** e **fronteiras** (limites de parâmetros, ausência de headers).

### 1.2 Abordagem: Test Data Driven e contrato v1 vs v2

O lab adota duas versões de endpoint para o mesmo recurso:

- **v1:** implementação com bug intencional (sem paginação, sem correlation ID, etc.).
- **v2:** implementação que atende aos requisitos.

A estratégia é **test data driven** no sentido de:

1. **Dados de teste controlados** — fixtures (`seed_notas`, `seed_produtos`) garantem massa conhecida e reproduzível.
2. **Asserções sobre o contrato** — status HTTP, headers, formato e conteúdo do body.
3. **Execução repetível** — mesmo conjunto de dados e mesmos critérios a cada execução.

Para cada driver existem duas classes de teste:

- **Test*BugV1:** expõem o comportamento incorreto (ex.: v1 retorna todos os registros).
- **Test*FixV2:** validam a correção (ex.: v2 respeita limit/offset e X-Correlation-ID).

### 1.3 Pirâmide e tipos de teste

| Tipo | Escopo | Ferramenta | Uso no projeto |
|------|--------|------------|----------------|
| Testes de contrato/API | Request/response HTTP por endpoint | pytest + FastAPI TestClient | Principal: `test_01_volumetria.py`, `test_02_rastreabilidade.py`, etc. |
| Testes de integração | API + banco (SQLite em memória) | `conftest.py` (override `get_db`) | Todos os testes usam banco de teste isolado por função. |
| Dados de teste | Massa controlada | Fixtures `seed_produtos`, `seed_notas` | Garantem cenários reproduzíveis. |

Não há testes unitários isolados de funções internas; o foco é a **API como contrato** (visão API First).

### 1.4 Técnicas de projeto de testes aplicadas

| Técnica | Aplicação |
|---------|-----------|
| **Particionamento de equivalência** | limit válido (1–100) vs inválido (< 1 ou > 100). |
| **Valor de fronteira** | limit = 0, 1, 20 (default), 100, 500; offset = 0, 10. |
| **Análise de valor limite** | REQ-BD1: máximo 100, mínimo 1. |
| **Cenário positivo/negativo** | v1 sem correlation ID (negativo); v2 com header e body (positivo). |

### 1.5 Ambiente de execução

- **Banco:** SQLite em memória (`sqlite:///:memory:?cache=shared`) com `TESTING=1` para desabilitar seed do lifespan.
- **Ciclo por teste:** criar tabelas → popular (quando usa fixture) → executar teste → teardown.
- **Comando:** `pytest tests/ -v` ou `pytest tests/test_01_volumetria.py tests/test_02_rastreabilidade.py -v`.

---

## 2. Direcionador BD1 — Volumetria: estratégia e massa

### 2.1 Requisitos cobertos

REQ-BD1-V1 a REQ-BD1-V4 (paginação limit/offset, default 20, máximo 100, eager loading).

### 2.2 Massa de dados

Definida em `tests/conftest.py` e constantes em `tests/constants.py`:

| Fixture / Constante | Conteúdo | Uso |
|--------------------|----------|-----|
| `seed_produtos` | 10 produtos (TEST-0001 a TEST-0010), estoque 100 | Suporte a itens de nota. |
| `seed_notas` | **50 notas fiscais** (TST-000001 a TST-000050), 1 item por nota; 3 CNPJs emitentes, 5 destinatários | Base para afirmar que v1 retorna “todos” (50) e v2 respeita limit. |
| `TOTAL_NOTAS_FIXTURE` | 50 | Asserção em testes de bug v1. |
| `PAGINATION_DEFAULT_LIMIT`, `PAGINATION_MAX_LIMIT`, `PAGINATION_MIN_LIMIT` | 20, 100, 1 | Valores de fronteira. |

**Justificativa:** 50 notas são suficientes para demonstrar o bug da v1 (retorno total) e para validar páginas (offset) e limites. O requisito de “suportar 50k+” é garantido pelo design (paginação + eager loading), validado pelos comportamentos de limit/offset.

### 2.3 Casos de teste (massa × cenário)

| Caso | Objetivo | Entrada / Params | Asserção principal | Requisito |
|------|----------|------------------|--------------------|-----------|
| test_v1_retorna_todos_registros_sem_limite | Expor bug | `GET /v1/notas` | `len(data) == 50` | REQ-BD1 |
| test_v1_nao_aceita_parametro_limit | Expor bug | `GET /v1/notas?limit=5` | `len(data) > 5` | REQ-BD1 |
| test_v2_paginacao_padrao_20 | Validar default | `GET /v2/notas` | `len(data) <= 20` | REQ-BD1-V2 |
| test_v2_paginacao_com_limit | Validar limit | `GET /v2/notas?limit=5` | `len(data) == 5` | REQ-BD1-V1/V3 |
| test_v2_paginacao_com_offset | Validar páginas | `limit=10&offset=0` e `offset=10` | IDs página 1 ∩ página 2 = ∅ | REQ-BD1-V1 |
| test_v2_limite_maximo_100 | Fronteira | `GET /v2/notas?limit=500` | status 422 | REQ-BD1 |
| test_v2_limit_minimo_1 | Fronteira | `GET /v2/notas?limit=0` | status 422 | REQ-BD1 |

### 2.4 Cobertura do driver Volumetria

- **Caminho feliz:** listar com default, com limit e offset explícitos.
- **Fronteiras:** limit 0, limit > 100.
- **Comportamento indesejado (v1):** retorno total sem paginação e ignorar limit.

---

## 3. Direcionador BD2 — Rastreabilidade: estratégia e massa

### 3.1 Requisitos cobertos

REQ-BD2-R1 a REQ-BD2-R5 (X-Correlation-ID, propagação do client, X-Response-Time, correlation_id no body, ID único por request).

### 3.2 Massa de dados

- **seed_notas** (50 notas): usado para `GET /v2/notas/{id}` com ID existente (ex.: `seed_notas[0].id`).
- **ID_NOTAS_INEXISTENTE** (99999): caso negativo para 404 sem contexto em v1.

### 3.3 Casos de teste (massa × cenário)

| Caso | Objetivo | Entrada / Params | Asserção principal | Requisito |
|------|----------|------------------|--------------------|-----------|
| test_v1_nao_retorna_correlation_id | Expor bug | `GET /v1/notas/{id}` | `"correlation_id" not in data` | REQ-BD2 |
| test_v1_erro_sem_contexto | Expor bug | `GET /v1/notas/99999` | status 404 | REQ-BD2 |
| test_v2_retorna_correlation_id_no_header | Validar header | `GET /v2/notas/{id}` | header presente; valor é UUID | REQ-BD2-R1 |
| test_v2_propaga_correlation_id_do_client | Propagação | Header `X-Correlation-ID: <uuid>` | `response.headers["x-correlation-id"] == meu_id` | REQ-BD2-R2 |
| test_v2_correlation_id_no_body | Body | `GET /v2/notas/{id}` | `"correlation_id" in data` | REQ-BD2-R5 |
| test_v2_retorna_response_time | Header tempo | `GET /v2/notas/{id}` | header `x-response-time` presente | REQ-BD2-R3 |
| test_v2_cada_request_tem_id_unico | Unicidade | Duas chamadas GET sem header | `cid1 != cid2` | REQ-BD2 |

### 3.4 Cobertura do driver Rastreabilidade

- **Caminho feliz:** request com e sem Correlation ID enviado; resposta 200 com headers e body esperados.
- **Fronteira:** nota inexistente (404).
- **Comportamento indesejado (v1):** ausência de correlation ID.

---

## 4. Resumo da massa de testes (BD1 e BD2)

| Driver | Fixtures | Quantidade | Nº de casos (exemplo) |
|--------|----------|------------|----------------------|
| Volumetria | seed_produtos, seed_notas | 10 produtos, 50 notas | 7 (2 bug v1 + 5 fix v2) |
| Rastreabilidade | seed_notas | 50 notas + ID inexistente | 7 (2 bug v1 + 5 fix v2) |

A qualidade dos requisitos é aferida ao executar esses testes: se os Fix V2 passam e os Bug V1 se comportam como documentado, os requisitos estão cobertos e verificáveis por código.

---

## 5. Integração com execução e relatórios

- **Execução local:** `pytest tests/test_01_volumetria.py tests/test_02_rastreabilidade.py -v`
- **Suite completa:** `pytest tests/ -v`
- **Relatório HTML (opcional):** `pytest tests/ -v --html=report.html --self-contained-html` (requer pytest-html)
- **CI/CD:** job que execute `pytest tests/ -v` e publique o relatório; critério de sucesso: todos os testes passando.

---

*Documento alinhado a ISO/IEC 29119 e IEEE 829. Atividade Ponderada M09S04.*
