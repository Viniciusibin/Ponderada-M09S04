# Ponderada M09S04 — ASIS TaxTech

Atividade ponderada do módulo M09S04: **documentar regras de negócio em código** e **aferir a qualidade dos requisitos** por meio de testes automatizados, no contexto do projeto ASIS TaxTech. Código de testes e aplicação de referência incluídos; documentação alinhada a parâmetros de engenharia de software.

## Projeto e parceiro

- **Projeto:** Obter sistemas resilientes, com controle de qualidade baseado em código, como ativo de software.
- **Parceiro:** ASIS TaxTech (Primeira Tax Tech da América Latina).
- **Professor orientador:** Reginaldo Arakaki.
- **Referência:** [asis-bd-lab](https://github.com/canaldoovidio/asis-bd-lab) — API com endpoints v1 (bugados) e v2 (corrigidos) para 4 Business Drivers.

**Os dois direcionadores de negócio em foco nesta atividade** (detalhados nos documentos 02 e 03 e nas suites `test_01` e `test_02`) são:
1. **Volumetria (BD1)** — listagem paginada; suporte a alto volume sem degradação.
2. **Rastreabilidade (BD2)** — Correlation ID e log estruturado em toda requisição.

O mapa (doc 01) cobre ainda **Acesso Simultâneo (BD3)** e **Segurança (BD4)**.

## Estrutura do repositório

```
Ponderada-M09S04/
├── README.md
├── requirements.txt
├── app/                    # API FastAPI (referência para testes)
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   └── schemas.py
├── tests/                  # Suite de testes automatizados
│   ├── __init__.py
│   ├── conftest.py         # Fixtures e ambiente (SQLite em memória)
│   ├── constants.py        # Constantes (evita números/strings mágicos)
│   ├── test_01_volumetria.py
│   ├── test_02_rastreabilidade.py
│   ├── test_03_concorrencia.py
│   └── test_04_seguranca.py
└── docs/
    ├── README.md
    ├── 01-mapa-business-drivers.md
    ├── 02-estrategia-massa-testes.md
    └── 03-codificacao-documentacao-testes.md
```

## Entregas da atividade

| Entrega | Descrição | Documento |
|---------|-----------|-----------|
| **Mapa do Business Drivers** [3,0 pts] | Mapa dos direcionadores; identificadores REQ-BDx; regras em código; rastreabilidade requisito ↔ código ↔ teste. | [docs/01-mapa-business-drivers.md](docs/01-mapa-business-drivers.md) |
| **Estratégia e massa de testes** [4,0 pts] | Estratégia; técnicas de projeto (equivalência, fronteira); massa de dados; casos para BD1 e BD2. | [docs/02-estrategia-massa-testes.md](docs/02-estrategia-massa-testes.md) |
| **Codificação como documentação de testes** [3,0 pts] | Constantes, AAA, nomes, rastreabilidade; tabelas requisito ↔ teste ↔ asserção. | [docs/03-codificacao-documentacao-testes.md](docs/03-codificacao-documentacao-testes.md) |

## Pré-requisitos

- Python 3.11+ (recomendado para compatibilidade com dependências)
- pip

## Como executar os testes

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

Os testes rodam contra a API em `app/` usando SQLite em memória (variável de ambiente `TESTING=1`); não é necessário PostgreSQL.

## Parâmetros de engenharia de software aplicados

- **Identificadores:** REQ-BD1-V1, REQ-BD2-R1, etc., com rastreabilidade até o código e aos casos de teste.
- **Constantes:** `tests/constants.py` para valores de fronteira e dados de teste (evita magic numbers).
- **Técnicas de teste:** particionamento de equivalência, valor de fronteira (limit 0, 1, 100, 500).
- **Padrão AAA:** Arrange-Act-Assert nos métodos de teste quando útil.
- **Referências:** ISO/IEC 29119 (testes), IEEE 829 (documentação de testes), rastreabilidade bidirecional.

## Restrições (conteúdo restrito)

Conforme escopo do projeto: código fonte, endpoints ou elementos que remetam à plataforma ASIS não devem ser compartilhados; apenas os **artefatos gerados** (estrutura de documentos, estratégia, boas práticas, código de teste genérico) podem ser compartilhados no GitHub.

---

*Atividade Ponderada M09S04 — Qualidade e testes na API ASIS TaxTech.*
