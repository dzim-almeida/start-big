# TASK002 — Carta de Correção Eletrônica (CC-e) — backend + frontend

**Status:** ✅ concluída · **Data:** 2026-09-17 · **Spec:** `specs/completed/TASK002-EmitirCartaCorrecao.md` · **ADR:** [ADR-001](../adrs/ADR-001_eventos_fiscais_em_tabela_propria.md)

## Objetivo
Corrigir erros não fiscais de uma NF-e autorizada (texto, endereço, transporte) sem cancelar nem reemitir, via evento CC-e da Focus NFe (`POST /v2/nfe/{ref}/carta_correcao`), com histórico, arquivos e limite de 20 cartas.

## Backend — arquivos
| Arquivo | O quê |
|---|---|
| `app/db/models/carta_correcao_fiscal.py` | **novo** — tabela de eventos; relação `DocumentoFiscal.cartas_correcao` |
| `alembic/versions/t3u4v5w6x7y8_tabela_carta_correcao_fiscal.py` | `has_table → return` |
| `app/schemas/emissao_fiscal.py` | `CartaCorrecaoRequest` (15–1000), `CartaCorrecaoRead.de_registro` |
| `app/schemas/documento_fiscal.py` + `services/documento_fiscal.py` | `total_cartas_correcao`, `ultima_carta_correcao` (só AUTORIZADAS) |
| `app/services/fiscal/http/client.py` | protocolo `emitir_carta_correcao`; `EmissaoResultado.numero_carta_correcao` |
| `app/services/fiscal/http/client_startbig.py` | rota `/erp/fiscal/nfe/carta-correcao`, sem `data_evento`; `_parse_response` aceita `caminho_*_carta_correcao`; 4xx → `_recusa_local`, 5xx → raise |
| `app/services/fiscal/http/client_mock.py` | contador de sequência por `ref` |
| `app/services/fiscal/carta_correcao.py` | **novo** — travas, registro antes do HTTP, `_aplicar_resultado_carta`, arquivamento `_cce_NN` |
| `app/api/v1/endpoints/fiscal.py` | `POST …/carta-correcao`, `GET …/cartas-correcao`, `GET /cartas-correcao/{id}/pdf|xml` |
| `app/services/fiscal/arquivos.py` | `_sincronizar_cartas_pendentes` dentro de `sincronizar_pendentes` |
| `app/services/fiscal/exportacao_xml.py` | pasta `CartasCorrecao/` no ZIP do contador |

## TDD
| Arquivo | Casos | RED | GREEN |
|---|---|---|---|
| `test/services/fiscal/test_carta_correcao.py` | 23 (schema, travas, sucesso/imutabilidade, rejeição≠erro, listagem, arquivos/sync) | `ModuleNotFoundError` → depois 1 falha de flush (409 indevido) | ✅ |
| `test/api/v1/fiscal/test_carta_correcao_api.py` | 6 (POST, 422 schema, 422 NFC-e, listagem + totais no detalhe, zero/nulo, PDF 404) | rotas inexistentes | ✅ |

Gate: `pytest test/services test/core test/db test/api/v1/fiscal` → **852 passed** (823 antes).

## Frontend — arquivos
| Arquivo | O quê |
|---|---|
| `types/fiscal.types.ts` | `CartaCorrecaoRead`; `DocumentoFiscalRead.total_cartas_correcao/ultima_carta_correcao` |
| `services/fiscal.service.ts` | `emitirCartaCorrecao`, `listarCartasCorrecao`, `baixarPdf/XmlCartaCorrecao` |
| `constants/fiscal.constants.ts` | `fiscalKeys.cartasCorrecao`, `CARTA_CORRECAO_MINIMO/MAXIMO`, `LIMITE_CARTAS_POR_NOTA`, status `ERRO` |
| `composables/useFiscalCartaCorrecaoMutation.ts` | `resolverDesfechoCarta` (puro) + mutation; **não** invalida `resumo()` |
| `composables/useFiscalCartasCorrecaoQuery.ts` | `podeTerCartaCorrecao` (puro) + query `enabled` só NF-e autorizada |
| `components/detalhes/FiscalDocumentoDetailsDrawer.vue` | botão âmbar `(n/20)`, form inline com pré-preenchimento, histórico com PDF/XML |

Vitest: `composables/__tests__/cartaCorrecao.spec.ts` (4) → **8/8** no total. `vue-tsc --noEmit` → 0 erros.

## Critérios de aceite
| # | Critério | Evidência | |
|---|---|---|---|
| 1 | Contrato: `{ref, correcao}` sem `data_evento`; resposta mapeada | `client_startbig.emitir_carta_correcao`; `test_carta_autorizada_grava_sequencia_protocolo_e_mensagem` | ✅ |
| 2 | Somente NF-e: NFC-e → 422 `CCE_SOMENTE_NFE` sem chamar o client; botão ausente | `test_nfce_nao_recebe_carta_e_nao_chama_o_client`, API idem; `v-if="podeEmitirCarta"` | ✅ |
| 3 | Somente autorizada | parametrizado CANCELADA/REJEITADA/PROCESSANDO/NAO_TRANSMITIDA → 422 | ✅ |
| 4 | Nota imutável | `test_carta_nao_altera_a_nota` (snapshot de 7 campos) | ✅ |
| 5 | Limite 20 local; botão desabilitado em 20/20 | `test_limite_de_20_cartas_e_barrado_localmente`; `:disabled="limiteCartasAtingido"` | ✅ |
| 6 | Consolidação: textarea pré-preenchido com a última | navegador: reabrir o form após a 1ª carta mostrou o texto anterior | ✅ |
| 7 | Rejeição SEFAZ ≠ erro | `erro_autorizacao` → REJEITADA (HTTP 200, toast warning); 4xx → ERRO | ✅ |
| 8 | Arquivos com sufixo `_cce_NN`, sem sobrescrever a nota; no ZIP | `test_xml_da_carta_e_guardado_com_sufixo…`, `test_sincronizacao…`; `exportacao_xml` | ✅ |
| 9 | Mock: fluxo inteiro sem plataforma | aceite no navegador com `FISCAL_MOCK_ENABLED` (POST 200, toast "nº 1 registrada", lista, `(1/20)`, PDF/XML 404 → toast) | ✅ |

## Desvios da spec
1. `data_criacao` com `server_default=func.now()` (padrão do projeto) em vez de `default=datetime.utcnow`.
2. Endpoints devolvem `CartaCorrecaoRead` direto (padrão do módulo fiscal), não envelope `{status, data}` da rule § 1 — o módulo inteiro já é assim; mudar só aqui quebraria a consistência.
3. Linha do tempo (§ 5.6, opcional) não implementada — YAGNI; a seção "Cartas de Correção" já cumpre o papel.
4. `ERRO` adicionado a `STATUS_COLORS/LABELS` para o chip da carta.

## Dependência externa (bloqueante para homologação)
`POST https://api.startbig.com.br/erp/fiscal/nfe/carta-correcao` **não existe**. Precisa receber `{ref, correcao}`, chamar a Focus e devolver o JSON com os nomes da Focus (`numero_carta_correcao`, `caminho_xml_carta_correcao`, `caminho_pdf_carta_correcao`, `status_sefaz`) — `_parse_response` já aceita as duas grafias.
