# Middleware que filtra por IP recusa o TestClient inteiro

- **Data:** 2026-11-20
- **Módulo:** _shared
- **Spec relacionada:** LIC-04
- **Tipo:** armadilha

## Contexto
A LIC-04 pôs na API local um middleware que só aceita IPs da rede da loja (`app/core/rede_local.py`).

## Aprendizado
O `TestClient` do Starlette se apresenta como host `"testclient"` (não é um IP), então um filtro por endereço devolve `403` para **todos** os testes de rota. O `test/conftest.py` troca o padrão do construtor para `("127.0.0.1", 50000)`. Para simular outro computador, passe `TestClient(app, client=("8.8.8.8", 50000))`; sem o `with`, o TestClient nem roda o startup (rápido, sem banco).

## Como aplicar
Teste de rota que precisa vir "de fora" passa `client=` explícito. Se um dia o `conftest.py` deixar de ser carregado (teste solto, outra pasta), lembre que a falha é `403 FORA_DA_REDE_DA_LOJA`, não permissão.
