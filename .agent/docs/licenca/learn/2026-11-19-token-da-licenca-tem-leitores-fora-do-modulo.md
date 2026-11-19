# O token da licença é lido fora do módulo de licença (fiscal e nuvem)

- **Data:** 2026-11-19
- **Módulo:** licenca
- **Spec relacionada:** LIC-01
- **Tipo:** armadilha

## Contexto
Ao trancar o token no cofre (LIC-01), a spec listava só os arquivos do módulo de licença e da nuvem. O fiscal também lê a coluna `token` crua, para o Bearer da API fiscal.

## Aprendizado
Leitores do token fora de `services/licenca/`: `get_licenca_token` (`app/db/crud/fiscal/nucleo.py`, ~30 chamadas de emissão NF-e, NFC-e e NFS-e) e `_get_license_token` (`app/services/cloud/_http.py`). Os dois abrem o token por `segredos_licenca.ler_token`. A coluna `token` é `NOT NULL`: "apagar" o token é gravar `''`.

## Como aplicar
Antes de mudar o formato ou o lugar do token, rode `grep -rn "\.token\b\|get_licenca_token" backend-fastapi/app` e trate cada leitor. Nunca leia `licenca.token` direto: use `segredos_licenca`.
