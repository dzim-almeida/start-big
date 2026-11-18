# Code review — rodada interestadual (TASK004–009)

**Data:** 2026-09-19 · **Escopo:** `0a72b86..8f85431` (os 7 commits da rodada; a anterior tem o seu `CODE-REVIEW.md`) · **Ferramenta:** `/code-review feat/fiscal-nfe high`

Regra do review: só achado com cenário concreto de falha. 5 achados, todos corrigidos com TDD (teste RED primeiro) no commit `fix(fiscal): achados do code review da rodada interestadual`.

| # | Sev. | Arquivo | Achado | Correção | Teste |
|---|---|---|---|---|---|
| 1 | **alta** | `payload_builder.py` `_campos_difal`/`_totais_interestaduais` | Nomes dos campos DIFAL vinham da spec e **não são os da Focus NFe**. Conferido na referência oficial (`campos.focusnfe.com.br/nfe/NotaFiscalXML.html`): vBCUFDest→`icms_base_calculo_uf_destino`, pICMSUFDest→`icms_aliquota_interna_uf_destino`, pICMSInter→`icms_aliquota_interestadual`, vICMSUFDest→`icms_valor_uf_destino`, vICMSUFRemet→`icms_valor_uf_remetente`, vBCFCPUFDest→`fcp_base_calculo_uf_destino`, pFCPUFDest→`fcp_percentual_uf_destino`, vFCPUFDest→`fcp_valor_uf_destino`; totais vICMSUFDest→`icms_valor_total_uf_destino`, vFCPUFDest→`fcp_valor_total_uf_destino`. Os de ST estavam certos. Chave desconhecida é descartada → nota sem `ICMSUFDest` → Rej. 694 com número queimado | Nomes trocados; `docs/contrato-api-fiscal-plataforma.md` § 3.1 atualizado; `pICMSInterPart` fica com o default 100 da Focus | `test_payload_interestadual.py` (chaves) |
| 2 | **alta** | `tax_engine/resolver.py` | NFC-e com entrega a domicílio (indPres 4) para cliente de outra UF deixou de ser barrada: o resolver derivava CFOP 6108/DIFAL, o cupom mantinha `idDest 1` e o número já estava reservado. Antes: `OperacaoInterestadualError` no gate | `resolver_aliquotas_venda(..., modelo_documento=55)`; para 65 a operação interestadual levanta `OperacaoInterestadualError` ("emita NF-e"); `_preparar_dados_emissao` passa o modelo | `test_nfce_interestadual_e_barrada_antes_de_reservar_numero`, `test_nfce_na_mesma_uf_ou_balcao_continua_passando` |
| 3 | média | `tax_engine/engine.py` / `resolver.py` | Item CST 40/41/60 (CSOSN 500) em operação interestadual saía com DIFAL **zerado** e `ICMSUFDest` com zeros (nota aceita e errada); antes era recusado | `_assert_situacao_cabe_fora_do_estado`: 40/41/60/500 barrados com orientação, **exceto** 60/500 a contribuinte com MVA na regra (vira substituto — 6403/6404, CST 10/70) | `test_item_isento_ou_substituido_interestadual_e_barrado` ×4, `test_substituido_para_contribuinte_com_mva_vira_substituto` |
| 4 | baixa | `calculators/icms.py` | CST 10/70 e CSOSN 201/202 aceitos com `st_mva = 0`, mas o engine só calcula ST para `> 0` → nota prometeria ST sem grupo | `_assert_substituto_tem_regra_de_st` recusa `None` **e** `≤ 0` | `test_cst_10_com_mva_zero_e_recusado` |
| 5 | baixa | `services/produto.py` | `POST /produtos` com bloco `fiscal` gravava direto no CRUD, sem a validação do perfil da empresa (perfil alheio aceito; inexistente virava 500 da FK) | Passa por `produto_fiscal_service.upsert_dados_fiscais` (mesma porta do `PUT /{id}/fiscal`) → 422 `PERFIL_TRIBUTARIO_INVALIDO` | `test_cadastro_de_produto_com_perfil_inexistente_e_422` |

Gate após as correções: `pytest test/services test/core test/db test/api/v1/fiscal` → **1072 passed** (1063 antes).

## O que o review NÃO cobriu (registrado para o desenvolvedor)
- `indFinal` (`consumidor_final`) numa NF-e B2B interestadual continua vindo do `nota_fiscal.consumidor_final` (default 1). Para revenda a contribuinte o correto tende a ser 0; não há regra da SEFAZ que rejeite, então ficou como está — confirmar com o contador junto com a decisão do Simples (TASK007).
- Gate da OS (`verificar_completude_os`) não roda o guard da IE interestadual; a OS emite NF-e pelo mesmo resolver, mas o adaptador raramente tem `indicador_presenca` ≠ 1.
- A verificação dos nomes da Focus foi feita contra a referência pública de campos; o repasse pela plataforma (`.passthrough()` no Zod) continua sendo do time web.
