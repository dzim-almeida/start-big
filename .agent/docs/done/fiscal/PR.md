# Título

feat(fiscal): trava de numeração, carta de correção e NF-e de devolução

# Corpo

## O que muda

Cinco specs de `.agent/specs/` implementadas em commits separados, com TDD no backend e Vitest no frontend, mais um commit com os achados do code review.

| Commit | Spec | Resumo |
|---|---|---|
| `de3f937` | TASK001-BACKEND | `empresa_fiscal_settings.numeracao_confirmada` + pendência impeditiva em `verificar_emitente`: nenhuma NF-e/NFC-e sai antes de alguém confirmar série e último número (previne Rejeição 204 em loja migrada). Alterar série/número pelo `PUT /configuracao` confirma por si só. Backfill: quem já tem documento AUTORIZADO nasce confirmado. |
| `dd32a55` | TASK001-FRONTEND | Chip "Ação necessária: confirme a numeração" no card de Emissão Estadual, banner empresa nova × migração no modal, e guarda `useNumeracaoConfirmada` antes de toda emissão (venda, PDV, OS, Centro Fiscal manual/lote/teste) com toast + botão "Configurar". **Vitest entra no projeto** (`npm run test`). |
| `6c872ca` | TASK002 | Carta de Correção Eletrônica: tabela `carta_correcao_fiscal` (evento anexo, até 20 por NF-e — ADR-001), client real/mock, endpoints `POST …/carta-correcao`, `GET …/cartas-correcao`, PDF/XML por carta, arquivamento `_cce_NN`, sincronização e pasta `CartasCorrecao/` no ZIP do contador. Drawer com botão âmbar `(n/20)`, form pré-preenchido com a última carta e histórico. |
| `b3d3f85` | TASK003-BACKEND | NF-e de devolução (modelo 55, entrada, finalidade 4) a partir de NF-e/NFC-e autorizada: itens do **snapshot** da origem (ADR-002), tributos pelo tax_engine com CST/alíquota congelados, CFOP saída→entrada (`cfop_devolucao`), 4 pilares da Focus no payload, saldo por item (`quantidade_devolvida_acumulada`), estoque de volta só na autorização (síncrona ou polling). |
| `6c34529` | TASK003-FRONTEND | Modal de devolução (total/parcial, saldo por linha, destinatário avulso com ViaCEP + IBGE, motivo, estoque, total ao vivo). No drawer, passado o prazo legal (24 h / 30 min) o cancelamento some e "Emitir NF-e de Devolução" vira a ação principal. |
| `548eee6` | Code review | 7 achados corrigidos (abaixo). |

## Por quê

Fora da janela de cancelamento (24 h NF-e / 30 min NFC-e) a loja não tinha como reverter uma operação nem corrigir um erro de texto, e uma loja vinda de outro ERP podia emitir a nota nº 1 de novo. As três specs fecham esses buracos sem sair do fluxo do Centro Fiscal.

## O que o revisor precisa saber

- **Migrations** (`s2t3u4v5w6x7`, `t3u4v5w6x7y8`, `u4v5w6x7y8z9`) são idempotentes e usam `op.add_column` direto, **não** `batch_alter_table`: o batch recria a tabela e, com `PRAGMA foreign_keys=ON` no boot, o DROP de `documento_fiscal` falha porque `documento_fiscal_item` a referencia. Isso derrubou um boot de teste; a migration também limpa `_alembic_tmp_*` órfã.
- **`pytest test/` completo toca o banco real da máquina**: a fixture `client` de `test/conftest.py` roda o lifespan (`create_all` + migrations) no engine real, e `alembic/env.py` ignora a URL do `Config`. Não é desta PR (552 erros pré-existentes), mas está documentado em `.agent/docs/progress/00-baseline.md` e vale um fix próprio. Os testes novos de endpoint usam um `TestClient` sem lifespan (`test/api/v1/fiscal/conftest.py`). Gate usado: `pytest test/services test/core test/db test/api/v1/fiscal` → **893 passed**.
- **Dependência externa (bloqueia a CC-e em homologação):** a API intermediária precisa expor `POST /erp/fiscal/nfe/carta-correcao` (`{ref, correcao}`) repassando à Focus `POST /v2/nfe/{ref}/carta_correcao`. Até lá o fluxo roda inteiro no `FiscalClientMock`.
- **Deploy:** backend mudou → `npm run build:sidecar` antes de qualquer instalador. Na primeira subida, lojas sem documento autorizado ficam travadas até confirmar a numeração em Emissão Estadual (é o objetivo da TASK001; precisa de comunicação).
- **Achados do review corrigidos em `548eee6`:** pareamento devolução→origem por `numero_item` (por `codigo_produto` falhava com código nulo/repetido e o saldo não fechava); devolução excluída das consultas de "documento da venda/OS" (`finalidade_emissao != 4`); janela de cancelamento no frontend lia timestamp UTC como hora local (`parseTimestampBackend`); NF-e de OS resolve o cliente; cliente com endereço incompleto cai no avulso **antes** de reservar número; `/devolucao` agenda o polling; docstring da carta corrigida.
- Desvios das specs estão listados no rodapé de cada spec em `.agent/specs/completed/` e em `.agent/docs/progress/` (pasta `.agent/` fica fora do git por decisão do dono — está espelhada em `C:\dev\bigpdv\.agent`).
- ESLint está quebrado no repositório (v9 sem flat config) — pré-existente; usei `vue-tsc --noEmit` (0 erros) e Prettier nos arquivos novos.

## Como testar

```bash
cd backend-fastapi && pytest test/services test/core test/db test/api/v1/fiscal -q   # 893 passed
cd frontend && npm run test && npx vue-tsc --noEmit                                  # 19 passed, 0 erros
```

Aceite ponta a ponta feito no navegador com `FISCAL_MOCK_ENABLED=true` e banco de teste: trava de numeração (badge, PUT, guard sem request), CC-e (registro, `(1/20)`, pré-preenchimento), devolução (janela expirada, saldo, ViaCEP, motivo mínimo, saldo 0,5 após parcial).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
