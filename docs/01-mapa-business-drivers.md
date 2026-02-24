# Mapa do Business Drivers — ASIS TaxTech Lab

**Projeto:** Obter sistemas resilientes, com controle de qualidade baseado em código  
**Parceiro:** ASIS TaxTech  
**Referências:** ISO/IEC 25010 (qualidade de produto), IEEE 829 (documentação de teste), rastreabilidade requisito ↔ código ↔ caso de teste.

---

## 1. Visão geral

Em arquiteturas **API First**, a API é o contrato e o ponto de acesso à lógica de negócios. Os **Business Drivers** traduzem necessidades do negócio em requisitos verificáveis e em comportamento implementado no código. Este mapa fornece:

- **Identificador único** por requisito (REQ-BDx-y) e rastreabilidade até o código e aos casos de teste (TC-xxx).
- **Regra de negócio** em linguagem natural e **especificação em código** (comportamento esperado).
- **Localização no código** (arquivo, endpoint, trecho) e **como aferir** (execução da suite de testes).

---

## 2. Convenções e identificadores

| Convenção | Formato | Exemplo |
|-----------|---------|---------|
| Requisito | REQ-BD\<driver\>-\<número ou letra\> | REQ-BD1-V1, REQ-BD2-R1 |
| Caso de teste | \<arquivo\>::\<classe\>::\<método\> | test_01_volumetria.py::TestVolumetriaFixV2::test_v2_paginacao_com_limit |
| Regra de negócio em código | RN-\<driver\>-\<id\> | RN-V1 (Volumetria), RN-R1 (Rastreabilidade) |

**Normas referenciadas:** ISO/IEC 29119 (testes de software), IEEE 829-2008 (documentação de testes), boas práticas de rastreabilidade bidirecional requisito ↔ teste.

---

## 3. Mapa dos Business Drivers

| ID Driver | Nome | Regra de negócio (resumo) | Requisitos | Código (v2) | Suite |
|-----------|------|----------------------------|------------|-------------|-------|
| BD1 | Volumetria | Listagens paginadas e limitadas; suporte a 50k+ notas sem degradação | REQ-BD1-V1 a V4 | `GET /v2/notas` | `test_01_volumetria.py` |
| BD2 | Rastreabilidade | Toda requisição rastreável por Correlation ID e log estruturado | REQ-BD2-R1 a R5 | Middleware + `GET /v2/notas/{id}` | `test_02_rastreabilidade.py` |
| BD3 | Acesso Simultâneo | Atualizações de estoque seguras sob concorrência (sem lost update) | REQ-BD3-C1 a C4 | `PUT /v2/produtos/{id}/estoque?version=` | `test_03_concorrencia.py` |
| BD4 | Segurança | Sem SQL Injection; validação CNPJ; JWT em rotas protegidas | REQ-BD4-S1 a S5 | `/v2/notas/busca`, `/v2/auth/token`, `/v2/notas/protegido` | `test_04_seguranca.py` |

---

## 4. Regras de negócio em código (detalhamento)

### 4.1 BD1 — Volumetria

**Regra de negócio (linguagem natural):**  
A API deve suportar listagem de grande volume de notas fiscais (50k+) sem degradar o serviço. Nenhum endpoint de listagem pode retornar todos os registros de uma vez; deve haver paginação com limite máximo por página e uso de eager loading para evitar N+1.

| ID Requisito | Especificação | Localização no código |
|--------------|----------------|------------------------|
| REQ-BD1-V1 | Listagem de notas deve aceitar `limit` (1–100) e `offset` (≥ 0). | `app/main.py`: `listar_notas_v2(limit=Query(20, le=100, ge=1), offset=Query(0, ge=0))` |
| REQ-BD1-V2 | Valor padrão de `limit` deve ser 20. | `Query(default=20, ...)` |
| REQ-BD1-V3 | Resposta deve conter no máximo `limit` itens. | `.limit(limit)` antes de `.all()`. |
| REQ-BD1-V4 | Carregamento de itens da nota em uma única query (eager loading). | `joinedload(NotaFiscal.itens)` em `listar_notas_v2`. |

**Aferição:** execução de `pytest tests/test_01_volumetria.py -v`. Casos de teste mapeados na seção 6.

---

### 4.2 BD2 — Rastreabilidade

**Regra de negócio (linguagem natural):**  
Cada requisição à API deve ser identificável de ponta a ponta. O sistema deve registrar logs estruturados com identificador de correlação e tempo de resposta, permitindo auditoria em ambiente fiscal.

| ID Requisito | Especificação | Localização no código |
|--------------|----------------|------------------------|
| REQ-BD2-R1 | Toda resposta deve incluir header `X-Correlation-ID` (UUID). | `app/main.py`: `correlation_id_middleware` → `response.headers["X-Correlation-ID"]` |
| REQ-BD2-R2 | Se o cliente enviar `X-Correlation-ID`, o mesmo valor deve ser devolvido. | Middleware: `request.headers.get("X-Correlation-ID", str(uuid.uuid4()))` |
| REQ-BD2-R3 | Resposta deve incluir tempo de processamento em header. | `response.headers["X-Response-Time"] = f"{duration:.4f}s"` |
| REQ-BD2-R4 | Logs estruturados (não `print`) com `correlation_id`. | `logger.info("request_started", extra={...})` |
| REQ-BD2-R5 | Endpoint de nota por ID deve incluir `correlation_id` no body. | `obter_nota_v2` retorna `"correlation_id": cid`. |

**Aferição:** `pytest tests/test_02_rastreabilidade.py -v`.

---

### 4.3 BD3 — Acesso Simultâneo (Concorrência)

**Regra de negócio (linguagem natural):**  
Atualizações de estoque devem ser seguras sob acesso concorrente. Não pode ocorrer lost update; em caso de conflito, o cliente deve receber 409 e ser orientado a recarregar.

| ID Requisito | Especificação | Localização no código |
|--------------|----------------|------------------------|
| REQ-BD3-C1 | Atualização de estoque deve exigir parâmetro `version`. | `atualizar_estoque_v2(..., version: int = Query(...))` |
| REQ-BD3-C2 | UPDATE condicional: `WHERE id = :id AND version = :version`; incrementar `version`. | `text(""" UPDATE produtos SET ... WHERE id = :id AND version = :version """)` |
| REQ-BD3-C3 | Se nenhuma linha for afetada, retornar 409 Conflict. | `if result.rowcount == 0: raise HTTPException(409, ...)` |
| REQ-BD3-C4 | Resposta de sucesso deve retornar novo `estoque` e nova `version`. | `return {"id", "estoque", "version"}`. |

**Aferição:** `pytest tests/test_03_concorrencia.py -v`.

---

### 4.4 BD4 — Segurança

**Regra de negócio (linguagem natural):**  
O sistema lida com dados fiscais sensíveis. Busca por CNPJ não pode ser vulnerável a SQL Injection; entrada deve ser validada (14 dígitos). Endpoints sensíveis devem exigir JWT.

| ID Requisito | Especificação | Localização no código |
|--------------|----------------|------------------------|
| REQ-BD4-S1 | Busca por CNPJ deve usar query parametrizada ou ORM. | `db.query(NotaFiscal).filter(NotaFiscal.emitente_cnpj == cnpj)` |
| REQ-BD4-S2 | Parâmetro `cnpj` validado: exatamente 14 dígitos numéricos. | `Query(..., min_length=14, max_length=14, pattern=r"^\d{14}$")` |
| REQ-BD4-S3 | Payloads de SQL injection rejeitados (422). | Validação do pattern rejeita strings maliciosas. |
| REQ-BD4-S4 | Endpoints protegidos exigem `Authorization: Bearer <token>`. | `endpoint_protegido`: verificação de header e `jwt.decode`. |
| REQ-BD4-S5 | Token obtido via `POST /v2/auth/token` com credenciais válidas. | `login()` com bcrypt e emissão de JWT. |

**Aferição:** `pytest tests/test_04_seguranca.py -v`.

---

## 5. Rastreabilidade requisito ↔ código ↔ caso de teste

Cada requisito é coberto por pelo menos um caso de teste. A qualidade dos requisitos é aferida ao **executar** a suite.

| Requisito | Caso(s) de teste que validam |
|-----------|------------------------------|
| REQ-BD1-V1 a V4 | `test_01_volumetria.py::TestVolumetriaFixV2::test_v2_paginacao_*`, `test_v2_limite_maximo_100`, `test_v2_limit_minimo_1` |
| REQ-BD2-R1 a R5 | `test_02_rastreabilidade.py::TestRastreabilidadeFixV2::test_v2_retorna_correlation_id_*`, `test_v2_propaga_*`, `test_v2_retorna_response_time`, `test_v2_correlation_id_no_body`, `test_v2_cada_request_tem_id_unico` |
| REQ-BD3-C1 a C4 | `test_03_concorrencia.py::TestConcorrenciaFixV2::test_v2_update_com_version_correta`, `test_v2_conflito_*`, `test_v2_updates_sequenciais_corretos` |
| REQ-BD4-S1 a S5 | `test_04_seguranca.py::TestSegurancaFixV2::test_v2_sql_injection_*`, `test_v2_valida_formato_cnpj`, `test_v2_busca_retorna_*`, `test_v2_autenticacao_*`, `test_v2_login_credenciais_invalidas` |

**Comando para aferir conformidade:**

```bash
pytest tests/ -v
```

Suite passando indica que a implementação v2 está em conformidade com as regras documentadas.

---

## 6. Foco da atividade (pelo menos 2 direcionadores)

Nos documentos **02-estrategia-massa-testes.md** e **03-codificacao-documentacao-testes.md** são detalhados em profundidade:

1. **Volumetria (BD1)** — Estratégia de testes, massa de dados, técnicas de projeto (fronteira, equivalência) e codificação como documentação.
2. **Rastreabilidade (BD2)** — Mesmo tratamento.

Os drivers BD3 e BD4 permanecem mapeados neste documento e podem ser expandidos nos mesmos moldes.

---

*Documento alinhado a parâmetros de engenharia de software (ISO/IEC 29119, IEEE 829, rastreabilidade). Atividade Ponderada M09S04.*
