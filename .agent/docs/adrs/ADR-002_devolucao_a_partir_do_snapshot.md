# ADR-002: NF-e de devolução nasce do snapshot da nota original, com saldo por item

**Status:** Accepted
**Data:** 2026-09-17
**Decidido por:** Agente de IA (sessão TASK003-BACKEND)
**Última atualização:** 2026-09-17

## Contexto
A devolução (finalidade 4) precisa espelhar "fielmente o que foi cobrado no documento de origem" (spec TASK003 § 2.7). O cadastro de produto muda com o tempo (NCM, CST, preço) e a venda pode ter sido editada; o único registro do que a SEFAZ viu é o **snapshot** `DocumentoFiscalItem`, congelado na emissão (existe desde 05/09/2026 exatamente para a tela não mentir). Além disso, a mesma nota pode ser devolvida em partes, ao longo do tempo, e nada impedia devolver a mesma peça duas vezes.

## Decisão
1. **Fonte dos itens = snapshot da origem**, nunca `produto.fiscal` nem `venda.itens`. Código, descrição, unidade, NCM, CST/CSOSN, alíquota de ICMS e preço unitário vêm de `DocumentoFiscalItem`.
2. **Tributos recalculados pelo `tax_engine`** sobre a quantidade devolvida, alimentado com o CST/CSOSN e a alíquota de ICMS congelados (`_itens_para_o_motor`). PIS/COFINS não estão no snapshot: vêm do regime (Simples = CST 49 zerado) ou do cadastro fiscal efetivo do produto — o mesmo caminho da emissão original.
3. **CFOP de entrada derivado do CFOP de saída** (`derivacao/cfop.py::cfop_devolucao`): 5102→1202, 5101→1201, 5405/5403/5404→1411, 6xxx→2xxx; desconhecido cai em 1202/2202.
4. **Saldo por item**: `DocumentoFiscalItem.quantidade_devolvida_acumulada` (milésimos), incrementado **só na transição para AUTORIZADA** — síncrona ou pelo polling (`consultar_documento`). Excedente é 422 antes de reservar número.
5. **Estoque** volta na mesma transição, via `movimentacao_estoque.registrar_movimentacao` com origem `DEVOLUCAO`, quando `DocumentoFiscal.devolver_estoque` (coluna própria — a decisão precisa sobreviver até o polling).
6. A devolução é um `DocumentoFiscal` comum (`finalidade_emissao=4`, `documento_referenciado_id`, `chave_documento_referenciado`): entra na lista, no drawer, no ZIP do contador e na inutilização como qualquer NF-e.

## Alternativas Consideradas

### Recalcular tudo do cadastro atual (`_preparar_dados_emissao` da venda)
**Por que rejeitada:** um NCM ou CST alterado depois da venda faria a devolução divergir da nota original — e a SEFAZ cruza os dois (Rejeição 327 e afins).

### Multiplicar bases/valores do snapshot por `fator_proporcao` (spec § 4.2)
**Por que rejeitada:** o snapshot só guarda base/valor de ICMS, não de PIS/COFINS; e o rateio de centavos do motor (`rateio.py`) é mais fiel do que multiplicar valores já arredondados. Alimentar o motor com os dados congelados dá o mesmo resultado para impostos lineares e reusa código testado.

### Flag "devolver estoque" em `motivo_rejeicao` ou em memória
**Por que rejeitada:** a autorização pode chegar minutos depois pelo polling, em outra requisição; sem coluna a decisão se perde ou vira gambiarra.

## Consequências

### ✅ Benefícios
- A devolução é o espelho exato do que a SEFAZ viu; parciais consecutivas fecham a conta.
- Rejeição/INDETERMINADA não devolvem nada (testado): sem nota duplicada de estoque.
- Reuso do motor, do snapshot, da movimentação de estoque e da esteira de emissão.

### ❌ Riscos/Custos
- Documentos anteriores a 05/09/2026 (sem snapshot) **não podem ser devolvidos** pelo sistema — 422 "sem itens registrados".
- Operação interestadual segue bloqueada (idDest 1), como na emissão normal.
- `_parear_itens` casa por `codigo_produto`; uma nota com o mesmo produto em dois itens (raro) acumularia no primeiro.

### 🔄 Mitigation
- Migration idempotente por coluna (`u4v5w6x7y8z9`).
- `test_falha_de_rede_consome_o_numero_e_fica_indeterminada` e `test_rejeicao_da_sefaz_nao_consome_saldo` protegem o invariante central.

## Referências
- Spec: `.agent/specs/completed/TASK003-BACKEND-NotaDevolucao.md`
- Código: `app/services/fiscal/devolucao.py`, `payload_builder.py::montar_payload_devolucao`, `derivacao/cfop.py::cfop_devolucao`
- ADR-001 (carta de correção — o outro "documento anexo" fiscal)
- Progresso: `.agent/docs/progress/TASK003-BACKEND.md`

## Próximos Passos
- [ ] TASK003-FRONTEND: modal de devolução no drawer.
- [ ] Quando o interestadual sair do bloqueio, `interestadual` em `emitir_devolucao` passa a vir da UF do destinatário.
