# Code review — as 5 specs (commits `de3f937..6c34529`)

**Data:** 2026-09-17 · **Escopo:** `git diff 35a7946..HEAD` (59 arquivos, +5746/−77) · **Ferramentas:** `/code-review high` + checklist § 4 da `skills/code-quality/SKILL.md` + AGENT.md § 8 + `rules/`.

## Achados de correção (todos corrigidos no commit de review)

| # | Sev. | Arquivo | Achado | Correção |
|---|---|---|---|---|
| 1 | alta | `services/fiscal/devolucao.py` | `_parear_itens` casava por `codigo_produto`: nulo (nota de teste/snapshot antigo) ou repetido (mesmo produto em 2 linhas) → saldo não incrementava → devolução infinita | Snapshot da devolução guarda o `numero_item` **da origem**; pareamento por ele. Teste `test_saldo_e_incrementado_mesmo_sem_codigo_produto_e_com_produto_repetido` |
| 2 | alta | `db/crud/fiscal.py` | Devolução copia `origem_*` e é AUTORIZADA → `get_documento_ativo_por_venda/os`, `ativos_por_vendas`, `relevantes_por_vendas` podiam devolvê-la como "a nota da venda" (lista de vendas, PDV, mensagem de duplicidade) | Filtro `_SO_NOTA_DA_OPERACAO` (`finalidade_emissao != 4`) nas 4 consultas. Teste `test_devolucao_nao_vira_o_documento_ativo_da_venda` |
| 3 | alta | `composables/useDevolucaoItens.ts` | `Date.parse` num timestamp UTC sem fuso → janela deslocada 3 h (NFC-e de 40 min ainda mostrava "Cancelar") | `parseTimestampBackend` (utilitário existente). Teste `timestamp sem fuso do backend é UTC` |
| 4 | média | `services/fiscal/devolucao.py` | NF-e de OS nunca resolvia o cliente → sempre exigia avulso | `_cliente_da_origem` trata `origem_tipo == "OS"` via `get_os_completa().objeto.cliente` |
| 5 | média | `services/fiscal/devolucao.py` | Cliente com endereço incompleto passava sem `enderDest` → SEFAZ rejeita depois de consumir número (a emissão normal tem gate; a devolução não tinha) | Só usa o cadastro se `_montar_destinatario` produziu `endereco`; senão avulso ou 422 **antes** de reservar número. Teste `test_cliente_com_endereco_incompleto_exige_avulso` |
| 6 | média | `endpoints/fiscal.py` | `/devolucao` não agendava `poll_nfe_status_async`; `reconciliar_pendentes` não é chamado por ninguém → PROCESSANDO ficava para sempre sem saldo/estoque | `BackgroundTasks` + polling quando PROCESSANDO, como `/emitir/nfe` |
| 7 | baixa | `services/fiscal/carta_correcao.py` | Docstring prometia registro ERRO após falha de rede; o rollback do endpoint o descarta | Docstring e nome do teste corrigidos (o rollback é desejado: não deixa PROCESSANDO preso) |

## Checklist code-quality § 4

| Item | Resultado |
|---|---|
| DRY | GET/PUT `/configuracao` unificados em `_montar_configuracao`; `useToast.warning` estendido em vez de toast paralelo; ViaCEP reaproveitado; `_sincronizar_cartas_pendentes` espelha `sincronizar_pendentes` (duplicação aceita: mesma estrutura, entidades diferentes; unificar exigiria abstração sobre 2 modelos — YAGNI) |
| YAGNI | Linha do tempo da CC-e (spec § 5.6) e `modelo`/`destinatario_dados` (tipos da spec FE) não implementados; `interestadual` fixo em `False` com o gancho no lugar |
| Nomes | Português, específicos (`aplicar_efeitos_autorizacao`, `saldo_devolvivel`, `podeTerCartaCorrecao`) |
| Funções > 25 linhas | Refatoradas no review: `emitir_devolucao` 81→~30 (`_criar_documento_devolucao`, `_transmitir`), `emitir_carta_correcao` 51→~30 (`_transmitir_carta`), `_itens_para_o_motor` 44→~26 (`_pis_cofins`). **Aceitas**: `montar_payload_devolucao` (53) e `_montar_itens_devolucao` (47) são literais de mapeamento, como o `_montar_itens` existente (140); `_montar_configuracao` (38) idem; `_sincronizar_cartas_pendentes` (47) segue a função irmã |
| Nível de abstração | Endpoints delegam a services (`_handle_db_transaction`); services chamam crud; models sem imports de `app/` |
| Comentários | "Por quê" (incidentes, decisões SEFAZ); nenhum "o quê" |
| Erros | Rejeição SEFAZ ≠ falha de plataforma ≠ falha de rede, nos dois eventos; 422 com `codigo` para o frontend agir (`CCE_SOMENTE_NFE`, `CCE_LIMITE_ATINGIDO`, `DESTINATARIO_OBRIGATORIO`) |

## AGENT.md § 8

- [x] Português em nomes/mensagens · [x] Zod/TS ↔ Pydantic sincronizados (`FiscalConfiguracaoUpdate`, `CartaCorrecaoRead`, `EmissaoDevolucaoPayload`, `DocumentoItemResumo`) · [x] Testes unitários backend (86 novos) e Vitest (19) · [x] Sem `console.log` novo · [x] Constantes centralizadas (`CARTA_CORRECAO_*`, `LIMITE_CARTAS_POR_NOTA`, `JANELA_CANCELAMENTO_MS`, `CAMPOS_QUE_CONFIRMAM_NUMERACAO`) · [x] Backend valida tudo (o frontend só replica para UX) · [x] Enum `MovimentacaoOrigem.DEVOLUCAO` — frontend não tem espelho desse enum (só exibe `origem` como texto) · [x] Commits na convenção.

## Fora do escopo (pendências registradas)
- Fixture `client` do `test/conftest.py` roda lifespan no banco real (552 erros pré-existentes) — ver `00-baseline.md`.
- ESLint quebrado (v9 sem flat config).
- `reconciliar_pendentes` existe e não é chamado por ninguém (pré-existente): documentos PROCESSANDO/INDETERMINADA de qualquer origem dependem do polling da própria requisição.
- API intermediária: rota `/erp/fiscal/nfe/carta-correcao` a criar.
