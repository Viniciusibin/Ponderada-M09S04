# Documentação — Atividade Ponderada M09S04

Documentos focados em **código** e **verificação de qualidade** para o projeto ASIS TaxTech, alinhados a parâmetros de engenharia de software (ISO/IEC 29119, IEEE 829, rastreabilidade requisito ↔ teste).

## Objetivos da atividade

1. **Documentar a regra de negócio em código** — regras expressas com identificadores (REQ-BDx) e rastreabilidade até a implementação e aos testes.
2. **Aferir a qualidade dos requisitos** — executando a suite de testes automatizados (`pytest tests/ -v`).

## Estrutura dos documentos

| Documento | Conteúdo | Pontuação |
|-----------|----------|-----------|
| [01-mapa-business-drivers.md](01-mapa-business-drivers.md) | Mapa dos 4 Business Drivers; identificadores REQ-BDx; regras em código; rastreabilidade requisito ↔ código ↔ caso de teste. | 3,0 |
| [02-estrategia-massa-testes.md](02-estrategia-massa-testes.md) | Estratégia de testes; técnicas de projeto (equivalência, fronteira); massa de dados; casos de teste para BD1 e BD2. | 4,0 |
| [03-codificacao-documentacao-testes.md](03-codificacao-documentacao-testes.md) | Codificação como documentação (constantes, AAA, nomes, rastreabilidade); tabelas requisito ↔ teste ↔ asserção para BD1 e BD2. | 3,0 |

## Direcionadores em foco

- **Pelo menos 2 direcionadores** detalhados nos documentos 02 e 03: **Volumetria (BD1)** e **Rastreabilidade (BD2)**.
- O mapa (01) cobre os **quatro** drivers: Volumetria, Rastreabilidade, Acesso Simultâneo e Segurança.

## Como executar os testes (aferir qualidade)

No diretório raiz do repositório:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest tests/ -v
```

Apenas BD1 e BD2:

```bash
pytest tests/test_01_volumetria.py tests/test_02_rastreabilidade.py -v
```

Relatório HTML (opcional, requer `pytest-html`):

```bash
pytest tests/ -v --html=report.html --self-contained-html
```

---

*Atividade Ponderada M09S04 — Qualidade e testes na API ASIS TaxTech. Professor orientador: Reginaldo Arakaki.*
