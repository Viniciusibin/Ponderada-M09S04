"""
Constantes para testes — evita números e strings mágicos.
Ref.: boas práticas de manutenibilidade (Clean Code / IEEE).
"""
# Volumetria (BD1)
PAGINATION_DEFAULT_LIMIT = 20
PAGINATION_MAX_LIMIT = 100
PAGINATION_MIN_LIMIT = 1
TOTAL_NOTAS_FIXTURE = 50

# Rastreabilidade (BD2)
ID_NOTAS_INEXISTENTE = 99_999

# Segurança (BD4)
CNPJ_VALIDO_14_DIGITOS = "11222333000100"
CNPJ_INVALIDO_CURTO = "1122233"
SQL_INJECTION_PAYLOAD = "' OR '1'='1"
USER_ADMIN = "admin"
PASSWORD_ADMIN = "admin123"
PASSWORD_INVALIDA = "senha-errada"

# HTTP
HTTP_200 = 200
HTTP_401 = 401
HTTP_404 = 404
HTTP_409 = 409
HTTP_422 = 422
