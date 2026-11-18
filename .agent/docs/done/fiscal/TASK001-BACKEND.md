# TASK001-BACKEND — Locker de confirmação da numeração fiscal

**Status:** ✅ concluída · **Data:** 2026-09-17 · **Spec:** `specs/completed/TASK001-BACKEND-LockerNumeracaoFiscal.md`

## Objetivo
Impedir emissão (NF-e e NFC-e) enquanto o operador não confirmar série e último número — prevenção da Rejeição 204 em lojas migradas de outro ERP.

## Arquivos tocados
| Arquivo | O quê |
|---|---|
| `app/db/models/empresa_fiscal_settings.py` | coluna `numeracao_confirmada` (Boolean, `server_default="0"`) |
| `alembic/versions/s2t3u4v5w6x7_numeracao_confirmada.py` | migration idempotente + backfill |
| `app/schemas/empresa.py` | `FiscalSettingsBase.numeracao_confirmada: bool`, `FiscalSettingsUpdate.numeracao_confirmada: Optional[bool]` |
| `app/schemas/emissao_fiscal.py` | `FiscalConfiguracao.numeracao_confirmada` |
| `app/services/empresa.py` | `CAMPOS_QUE_CONFIRMAM_NUMERACAO` + auto-confirmação em `update_fiscal_settings` |
| `app/services/fiscal/validators.py` | pendência impeditiva em `verificar_emitente` |
| `app/api/v1/endpoints/fiscal.py` | `_montar_configuracao(fs)` compartilhado por GET/PUT `/configuracao` (removeu 30 linhas duplicadas) |
| `test/api/v1/fiscal/conftest.py` | **novo** — `client` sem lifespan (ver baseline) |

## TDD — ciclo RED → GREEN
| Teste | RED | GREEN |
|---|---|---|
| `test/services/fiscal/test_gate_numeracao_confirmada.py` (8 casos) | `AttributeError: numeracao_confirmada` / gate não acusa | ✅ |
| `test/api/v1/fiscal/test_configuracao_numeracao.py` (4 casos) | `KeyError: 'numeracao_confirmada'` | ✅ |
| `test/db/test_migracao_numeracao_confirmada.py` (4 casos) | migration não rodava (ver incidente) | ✅ |

Gate de regressão: `pytest test/services test/core test/db test/api/v1/fiscal` → **823 passed**, 0 failed.

## Critérios de aceite
| # | Critério | Como foi verificado | |
|---|---|---|---|
| 1 | Bloqueio efetivo: 422, nenhum número consumido, nenhuma chamada à emissora | `test_emissao_barrada_nao_consome_numero_nem_chama_a_emissora` (monkeypatch em `get_fiscal_client` registra chamadas; `ultimo_numero_nfe` continua 0) | ✅ |
| 2 | Destravamento via `PUT /configuracao` com `numeracao_confirmada: true` ou alterando série/número | `test_put_com_numeracao_confirmada_true_destrava`, `test_put_alterando_ultimo_numero_nfe_auto_confirma` | ✅ |
| 3 | Com `True`, `verificar_emitente` passa | `test_numeracao_confirmada_libera_o_gate` | ✅ |
| 4 | Cobertura: bloqueio, liberação, auto-confirmação | 8 casos de serviço + 4 de API | ✅ |

## Desvios da spec (aplicados e justificados)
1. **Backfill**: a spec filtrava por `notas_fiscais.empresa_id`; a tabela real é `documento_fiscal` e **não tem `empresa_id`** (banco de uma empresa só). Critério adotado: existe qualquer documento `AUTORIZADA` → confirma. Testado com AUTORIZADA (confirma) e REJEITADA (não confirma).
2. **`server_default`**: `text("0")` em vez de `text("false")` — SQLite guarda Boolean como inteiro.
3. **Migration manual** com `_tem_coluna → return` em vez de `autogenerate` (padrão do projeto: `create_all()` roda antes; testado o cenário "coluna já criada").
4. **Regra extra**: `numeracao_confirmada=False` enviado junto com um número novo **não** reabre a trava (o número manda). Evita a tela desfazer a confirmação por mandar o objeto inteiro.
5. **DRY**: GET e PUT `/configuracao` tinham o mapeamento copiado; extraído `_montar_configuracao`.

## Incidente durante a sessão (registrado para não repetir)
`alembic/env.py` **ignora `sqlalchemy.url`** do `Config` e lê `settings.DATABASE_URL`. A primeira versão do teste de migration carimbou e migrou o **banco real** (`%LOCALAPPDATA%\StartBigERP\data\start_big.db`): `alembic_version` foi de `h1i2j3k4l5m6` para `s2t3u4v5w6x7` e a coluna foi criada. Restaurado na hora (coluna removida, revisão devolvida; backup em `start_big.db.bak-antes-restauracao-20260917-211847`; o banco tinha 0 documentos fiscais). O teste agora redireciona `settings.DATABASE_URL` via `monkeypatch` e se recusa a rodar fora do `tmp_path`.

## Pendências / observações para as próximas sessões
- Testes de endpoint pré-existentes que criarem `EmpresaFiscalSettings` e esperarem emissão limpa precisarão de `numeracao_confirmada=True` quando a fixture `client` for consertada (hoje erram antes disso).
- **Deploy**: exige `npm run build:sidecar`. Na primeira subida, lojas sem documento autorizado ficam travadas até confirmar em Emissão Estadual — comportamento desejado, mas precisa de comunicação (a TASK001-FRONTEND entrega a tela).
