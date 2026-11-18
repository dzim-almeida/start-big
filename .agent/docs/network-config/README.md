# Rede e Conexão (`network-config`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças. As regras de papel da máquina estão no `CLAUDE.md` ("Papel da máquina (servidor × terminal)"): **não as repita aqui, consulte lá**.

## 1. O que é

O assistente que define o **papel da máquina** — **servidor** (roda o backend e guarda o banco) ou **terminal** (usa o backend de outra máquina da rede) — e a tela de **erro de conexão**. Rotas: `/configuracao-rede` e `/erro-conexao`.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/network-config/` — `views/` (`NetworkConfigView`, `ConnectionErrorView`), `components/` (`TipoMaquinaStep`, `ServidorConfigStep`, `TerminalConfigStep`, `ConexaoStatusStep`), `composables/` (`useNetworkConfig`, `useAutoDiscovery`), `schemas/network-config.schema.ts` |
| Estado | `frontend/src/shared/stores/networkConfig.store.ts` · `frontend/src/api/backendUrl.ts` (onde está o backend) |
| Tauri (Rust) | `frontend/src-tauri/src/network/` (`config.rs` lê/escreve o `system-config.json`, `discovery.rs`, `local_ip.rs`, `log.rs`) · `backend.rs` (`ensure_backend`) · `hwid.rs` |
| Backend | `backend-fastapi/app/core/discovery.py` (anúncio mDNS do servidor) · `app/core/hwid.py` |
| Diagnóstico | `rede.log` ao lado do `system-config.json`; painel em Configurações › Rede e Conexão |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Servidor** | A máquina que roda o backend (sidecar) e guarda o banco. |
| **Terminal** | Máquina que aponta para o servidor pela rede. |
| **Auto-descoberta (mDNS)** | O servidor se anuncia na rede local e o terminal o encontra sozinho. |
| **`system-config.json`** | Arquivo do papel da máquina, **por usuário do Windows**. |
| **Sidecar** | O backend empacotado como `.exe` que o Tauri sobe. |

## 4. Fluxos principais

1. **Primeira execução:** escolhe o tipo de máquina → configura servidor (porta) ou terminal (descobre/digita o servidor) → testa a conexão.
2. **Servidor já configurado que não conecta:** vai para `/erro-conexao` em modo servidor (reiniciar/reparar serviço); **nunca** volta ao assistente de tipo de máquina.
3. **Portas:** dev usa **8000**; app instalado usa **8080–8083** (ver `CLAUDE.md`).

## 5. Decisões de arquitetura

- As regras que **não podem regredir** (loopback para servidor, `set_role_client` recusando o IP da própria máquina, `--data-dir` sempre passado ao sidecar etc.) estão no `CLAUDE.md`; uma mudança aqui é **trilha completa** e exige ler aquela seção.
- Rotas deste módulo usam `skipLicenseCheck: true` e `requiresAuth: false`.
- Os anúncios mDNS usam todos os IPv4 locais (nunca `127.0.0.1`) e re-anunciam quando o IP muda.

## 6. Integração com outros módulos

- **`license`/`auth`/`sign-in`:** só funcionam depois que o app sabe onde está o backend.
- **`configuracoes`:** seção "Rede" com o diagnóstico.
- **`mainLayout`:** indicadores de conexão.

## 7. Referências

- `CLAUDE.md` — "Papel da máquina" e "Portas".
- `docs/licenca-troca-de-servidor.md` (mudança de servidor).
