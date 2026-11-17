# <Módulo> (`<módulo>`) — Visão geral

> **Modelo.** Copie `docs/_modelo/` para `docs/{módulo}/`, troque os `<marcadores>` e apague esta nota. Este arquivo é **mantido pelo time**: o agente só propõe mudanças.
> Mantenha curto. O agente lê só as seções que a tarefa toca (skill `doc` §2).

## 1. O que é

<Para que o módulo existe, quem usa e o que resolve, em poucas linhas.>

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/<módulo>/` |
| Backend (endpoint) | `backend-fastapi/app/api/v1/endpoints/<arquivo>.py` |
| Backend (regras) | `backend-fastapi/app/services/<domínio>/` |
| Backend (banco) | `backend-fastapi/app/db/crud/<domínio>/` · `app/db/models/<arquivo>.py` |
| Backend (contratos) | `backend-fastapi/app/schemas/<domínio>/` |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| <Termo> | <Definição simples> |

## 4. Fluxos principais

<Os 2–4 fluxos mais importantes, em passos numerados ou diagrama em texto.>

## 5. Decisões de arquitetura

<Decisões que moldam o módulo (permissões, integrações, regras fiscais/financeiras) e onde estão registradas: `ACORDO.md`, `adr/`.>

## 6. Integração com outros módulos

<O que o módulo consome e o que expõe.>
