# Título

feat(fiscal): operação interestadual — perfil tributário, DIFAL/FCP, ICMS-ST e payload

# Corpo

## O que muda

A NF-e deixa de ser bloqueada em operação interestadual não presencial. Seis specs de `.agent/specs/` (TASK004–009) implementadas em commits separados, com TDD no backend, mais um commit com os achados do code review. **Só backend** nesta rodada — a interface fica para a próxima.

| Commit | Spec | Resumo |
|---|---|---|
| `f79b960` | TASK004 | Tabelas `perfil_tributario` e `regra_perfil_tributario` (UF destino × NCM exceção: alíquota interestadual, interna do destino, FCP, base dupla, MVA-ST, redução). Migration `v5w6x7y8z9a0` decide pela ausência da tabela (o `create_all` roda antes). |
| `5674d59` | TASK005 | `/fiscal/perfis-tributarios` — listar, criar, detalhar, atualizar (replace-all das regras), excluir (409 `PERFIL_EM_USO`). Schemas garantem um fallback único e sem (UF, NCM) repetida — o que a UNIQUE do SQLite não garante com NULL. |
| `9415aec` | TASK006 | `produto_fiscal.perfil_tributario_id` (FK `SET NULL`, migration `w6x7y8z9a0b1`), `resolver_regra_perfil` (UF+NCM > UF > fallback em uma query), guard real de exclusão. Corrige `crud.produto_fiscal.upsert`, que zerava campo omitido. |
| `ecf7ac8` | TASK007 | Motor DIFAL/FCP (base simples e dupla) no pipeline; trava liberada para não contribuinte com perfil em todos os itens; ICMS próprio pela alíquota interestadual. DIFAL fora do vNF. |
| `be458b8` | TASK008 | ICMS-ST do remetente substituto (MVA, redução, dedução do próprio); ST **dentro** do vNF. CFOP (6102/6107/6108/6403/6404) e CST/CSOSN (10/70, 201/202) derivados da operação. Trava do contribuinte cai. |
| `8f85431` | TASK009 | Payload no formato Focus NFe: `ICMSUFDest`, grupo ST, totais, `local_destino` pelo grupo do CFOP calculado (mesma decisão do resolver). Guard da IE do contribuinte antes de reservar número. Contrato da plataforma § 3.1. |
| `37ca3bb` | code review | 5 achados corrigidos — ver abaixo. |

`48df9d8` tira `.agent/` do versionamento (como na `feat/fiscal-nfe`).

## Como funciona

```
venda → resolver_aliquotas_venda
          ├─ balcão / mesma UF ............ interna, como antes
          ├─ NFC-e para outra UF .......... barrada (cupom é sempre interno)
          ├─ não contribuinte, Simples .... sem DIFAL, sem perfil, CFOP 6107/6108
          ├─ não contribuinte, normal ..... perfil obrigatório → DIFAL/FCP, ICMS próprio 7/12%
          └─ contribuinte (PJ com IE) ..... perfil obrigatório → MVA na regra?
                                              sim: ICMS-ST, 6403/6404, CST 10/70 ou CSOSN 201/202
                                              não: revenda comum, 6101/6102
       → calcular_impostos (ICMS → DIFAL | ST → PIS/COFINS → totais)
       → montar_payload_nfe (nomes da Focus, idDest = grupo do CFOP)
```

Tudo que barra, barra em `_preparar_dados_emissao`, **antes** de reservar número.

## Code review (`37ca3bb`)

1. **Nomes dos campos DIFAL** vinham da spec e não são os da Focus (conferido em `campos.focusnfe.com.br`): agora `icms_base_calculo_uf_destino`, `icms_aliquota_interna_uf_destino`, `icms_aliquota_interestadual`, `icms_valor_uf_destino`, `icms_valor_uf_remetente`, `fcp_*_uf_destino`; totais `icms_valor_total_uf_destino` / `fcp_valor_total_uf_destino`. Sem isso a nota sairia sem `ICMSUFDest` (Rej. 694).
2. **NFC-e** com entrega a domicílio para outra UF voltou a ser barrada antes da reserva de número.
3. Itens **CST 40/41/60 / CSOSN 500** fora do estado voltam a ser recusados (saíam com DIFAL zerado), exceto substituído a contribuinte com MVA (vira substituto).
4. CST 10/70 com `st_mva = 0` recusado.
5. `POST /produtos` com bloco `fiscal` passa pela validação do perfil da empresa.

## Testes

- Gate `pytest test/services test/core test/db test/api/v1/fiscal`: **893 → 1072 passed**.
- Cenários numéricos das specs exatos (DIFAL A–E, ST 1–3).
- Boot real simulado para as duas migrations (loja carimbada na revisão anterior → `create_all` → `aplicar_migracoes`).
- A suíte completa continua fora do gate: o lifespan toca o banco real (ver `docs/done/fiscal/00-baseline.md`).

## ⚠️ Decisões que precisam de confirmação

1. **Simples Nacional sem DIFAL** — remetente optante não recolhe o DIFAL de partilha (STF ADI 5464); a operação a não contribuinte foi **liberada** sem perfil. Confirmar com o contador; reverter é um `if` em `resolver._resolver_item_interestadual`.
2. **Total da venda com ICMS-ST** — o vNF é produtos + ST e o builder exige que a venda feche com ele (Rej. 767). Até o checkout somar a ST ao total a cobrar, venda B2B **com ST** é recusada com "Pagamentos não fecham". B2C (DIFAL) e B2B sem ST funcionam.
3. **Plataforma web** — o Zod precisa aceitar os campos de `docs/contrato-api-fiscal-plataforma.md` § 3.1 (ou `.passthrough()`). Se ela foi preparada a partir da spec da TASK009, os nomes do DIFAL estão errados lá.
4. `indFinal` numa NF-e B2B continua vindo de `nota_fiscal.consumidor_final` (default 1).

## Antes de instalar em loja

- `npm run build:sidecar` — o backend mudou (2 migrations novas).
- Nenhuma tabela existente é alterada além da coluna nova em `produto_fiscal` (nasce NULL).

## Fora deste PR (próxima rodada, interface)

- Telas de perfis tributários (TASK005 § 6), select de perfil na aba fiscal do produto (TASK006 § 7), badges "Interestadual B2C/B2B" e linhas ICMS-ST/DIFAL no checkout com total a cobrar (TASK009 § 6).

Documentação completa em `.agent/docs/done/fiscal/` (`TASK004.md`…`TASK009.md`, `CODE-REVIEW-interestadual.md`, `README-interestadual.md`).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
