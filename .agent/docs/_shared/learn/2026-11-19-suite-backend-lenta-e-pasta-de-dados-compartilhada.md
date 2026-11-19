# A suíte do backend divide a pasta de dados real e leva mais de 1 hora em série

- **Data:** 2026-11-19
- **Módulo:** _shared
- **Spec relacionada:** LIC-01, LIC-02
- **Tipo:** ambiente

## Contexto
Rodando a suíte completa (`python -m pytest test/`, ~3.200 testes) numa sessão Linux, ela passou de 1 hora em série. Ao dividir em lotes paralelos, um lote falhou com `Can't locate revision identified by ...`.

## Aprendizado
Os testes que sobem o app (`TestClient` com o `lifespan`) abrem o banco da **pasta de dados padrão** (`~/.startbigerp/data` no Linux, `%LOCALAPPDATA%\StartBigERP\data` no Windows) e rodam as migrações nele. Duas execuções ao mesmo tempo, ou uma cópia antiga do código depois de uma migração nova, brigam pelo mesmo banco. A variável `BIGPDV_DATA_DIR` troca a pasta (`app/core/config.py`).

## Como aplicar
Para rodar em paralelo ou numa cópia do código, dê a cada processo a sua pasta: `BIGPDV_DATA_DIR=/tmp/lote1/data python -m pytest <arquivos>`. Divida os arquivos em lotes (um processo por CPU) em vez de esperar a rodada em série.
