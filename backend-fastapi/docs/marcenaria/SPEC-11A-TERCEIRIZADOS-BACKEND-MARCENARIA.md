# Spec 11A — Móveis Terceirizados (Backend)

| Campo        | Valor                                                                                 |
|--------------|---------------------------------------------------------------------------------------|
| Status       | Implementada em 09/10/2026                                                            |
| Camada       | Backend (FastAPI)                                                                     |
| Dependências | Specs 06A (móvel `TERCEIRIZADA`, central), 08A (aprovação, bloqueios do desfazer), 09A (ganchos, F2a) · módulo Compras (`services/compras/pedidos.py`, usado como é) |
| Bloqueia     | Specs 11B, 12A (o terceirizado conta como pronto quando conferido)                    |
| Referência   | SPEC-00: E6, E6a, E6b, F2a, C5a, P4, O8, T7, FB2, R15-MIG · PR1, PR4, PR6, PR7, PR8 |

> **Implementação (09/10/2026) — o que o código acrescenta ou decide além do texto.**
> (1) **Onde ficam as regras:** a situação (D1-D3, D8) está num módulo pequeno, `terceirizado_situacao.py`, porque o bloqueio do D15 vive em `aprovacao_bloqueios.py` (que o detalhe do orçamento importa) e a 12A também usa (pronto = `CONFERIDO`); o aviso do D16 é ligado em `ganchos.py` (09A), não no `__init__.py`. A busca "OS + orçamento aprovado" e "OS aberta" virou ajudante comum (`orcamento_comum.os_e_orcamento_aprovado` e `os_aberta`), usado também pela separação (10A).
> (2) **Situação pelo pedido inteiro (D2):** com vários móveis no mesmo pedido, uma chegada parcial (`PARCIAL`) deixa todos como "Pedido enviado" até o pedido ficar `RECEBIDO` (o item do pedido não guarda o móvel). Para conferir um a um, peça um por pedido.
> (3) **Respostas:** a leitura traz também `os` (`numero_os`, `status`, `editavel`); o `pedir` responde `{pedido, terceirizados}`, com `valor_total_centavos` do pedido só para quem vê custo de compra (regra do Compras); a lista geral responde `{itens}`, com `numero_os`, `cliente` e `orcamento_codigo`, atrasados primeiro; `valor_orcado_centavos` = `terceirizado_centavos` × quantidade.
> (4) **Casos que a spec não cobria:** o desfazer também fica bloqueado com envio anotado à mão ("Volte o móvel para 'A pedir' antes de desfazer."); pedir de novo um móvel (depois de cancelar o pedido) limpa a conferência e o problema antigos; a data do problema fica no histórico (não há coluna para ela).
> (5) **Testes de migração:** os testes "banco completo = models" da 08A e da 09A passam a migrar até a `head` (com a 11A, `marcenaria_moveis` tem colunas que as migrações delas ainda não criavam).

> **Revisão 1 (08/10/2026) — spec reescrita (SPEC-00 Revisão 15, E6b).** O Compras já tem pedido de compra de **serviço** (`tipo = SERVICO`, o caminho que a fábrica F5 usava para a central de corte), com envio, recebimento e lançamento das contas a pagar no recebimento. Com o módulo COMPRAS, o pedido à central passa a ser esse pedido, e a situação do móvel **acompanha** o pedido; saem a oferta de conta própria e a categoria "Produção terceirizada" (a conta do recebimento sai sem categoria, e conta sem categoria já conta como despesa no resultado). Sem o módulo, a situação é marcada à mão, como na versão anterior, e a conta é lançada em Contas a Pagar. "Conferido" e "registrar problema" são da marcenaria nos dois casos. Migração `642b2e8f79fa`.

---

## 1. Objetivo

Acompanhar o móvel que a marcenaria **não produz**: ela compra pronto de uma **central parceira** (um fornecedor, E6) e só instala.

1. Pedir à central (um ou vários móveis de uma vez): **com o Compras**, criando o pedido de serviço lá; **sem o Compras**, anotando o número e a previsão.
2. Acompanhar o recebimento e marcar a **conferência**, com o registro de problema quando o móvel chega com defeito.
3. Mostrar os pedidos **atrasados** de todas as OS.

## 2. Escopo

**Dentro do escopo**
- Situação do terceirizado por móvel (derivada do pedido do Compras, ou manual sem ele).
- "Pedir à central" pelo Compras (pedido `SERVICO`).
- Conferir, registrar problema, voltar um passo.
- Lista geral de terceirizados em aberto.
- Bloqueio do "desfazer aprovação" e aviso no cancelamento.

**Fora do escopo**
- Telas (11B).
- Enviar, receber, cancelar o pedido e lançar a conta: são do **Compras**, como ele é (FB2).
- Cotação entre centrais; integração com o sistema da central.
- Qualquer mudança no módulo Compras.

---

## 3. Arquivos afetados

```
backend-fastapi/
├── alembic/versions/642b2e8f79fa_terceirizados_marcenaria.py    # CRIAR — filha da 09A (195109da93f7)
├── app/
│   ├── db/models/marcenaria/ambiente.py                          # ALTERAR — colunas do terceirizado no móvel
│   ├── schemas/marcenaria/terceirizado.py                        # CRIAR
│   ├── services/marcenaria/terceirizado.py                       # CRIAR
│   ├── services/marcenaria/__init__.py                           # ALTERAR — bloqueio do desfazer + gancho de cancelamento
│   └── api/v1/endpoints/marcenaria_terceirizado.py               # CRIAR
└── test/services/marcenaria/test_terceirizado.py                 # CRIAR
```

**Nenhum arquivo compartilhado muda.** Usados como são: `services/compras/pedidos` (`validar_fornecedor`, `novo_rascunho`, `_recalcular`, `_definir_parcelas`, `registrar_log`), os modelos `PedidoCompra`/`PedidoCompraItem`, `core/modulos.requer_modulo("COMPRAS")` na rota de pedir, e `services/licenca.modulos_da_licenca` para o `modo_compras` da leitura, com a **mesma regra** do `requer_modulo` para o Compras: lista vazia ou sem resposta = **não** contratado (o Compras está em `MODULOS_NEGADOS_SEM_RESPOSTA`, ao contrário do Financeiro).

---

## 4. Decisões

### 4.1. Situação

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Cada móvel `TERCEIRIZADA` aprovado tem uma situação: **A pedir** → **Pedido enviado** → **Recebido** → **Conferido** (`A_PEDIR`, `ENVIADO`, `RECEBIDO`, `CONFERIDO`) | E6a |
| D2 | **Com pedido do Compras** (`pedido_compra_id` preenchido e o pedido não cancelado), a situação é **derivada** do pedido: `RASCUNHO` → `A_PEDIR` (com o selo "pedido em rascunho" e o código); `ENVIADO`/`PARCIAL` → `ENVIADO` (previsão = `previsao_entrega` do pedido); `RECEBIDO` → `RECEBIDO`. `CONFERIDO` é da marcenaria (`terc_conferido_em`) e só vale com o pedido `RECEBIDO` | Uma fonte só para cada fato: o Compras sabe se o pedido saiu e se chegou; a fábrica sabe se o móvel está bom |
| D3 | **Sem pedido do Compras**, a situação é **gravada** no móvel (`terc_situacao`) e muda pelas ações manuais: enviar (nº do pedido em texto até 60, previsão opcional), receber (data, padrão hoje) | E6b, modo sem o módulo |
| D4 | **Registrar problema** (texto até 500): o móvel fica `RECEBIDO`, com o texto e a data, nos dois modos. **Conferir** limpa o problema | O móvel riscado não está pronto para instalar; o texto fica para cobrar a central |
| D5 | **Voltar um passo:** `CONFERIDO → RECEBIDO` nos dois modos. No modo manual, também `RECEBIDO → ENVIADO → A_PEDIR` (voltar para `A_PEDIR` limpa pedido e previsão). No modo Compras, os outros passos voltam pelo Compras (cancelar o pedido devolve o móvel a `A_PEDIR`) | Erro de clique sem suporte; e o pedido no Compras não muda por baixo dele |
| D6 | Toda ação grava evento (06A D25) com quem, quando e o pedido | T7 |
| D7 | Só com a OS aberta (como a separação, 10A D14) | A OS fechada não tem mais o que acompanhar |
| D8 | **Atrasado:** `ENVIADO` com previsão antes de hoje (a do pedido do Compras, ou a anotada). Calculado na leitura | A previsão é o compromisso da central |

### 4.2. Pedir à central pelo Compras (E6b)

| # | Decisão | Motivo |
|---|---------|--------|
| D9 | `POST /os/{n}/terceirizados/pedir` recebe móveis **da mesma central** em `A_PEDIR` e cria **um** pedido de compra pelo serviço do Compras: `novo_rascunho(db, token, central)`, `tipo = SERVICO`, um item **sem produto** por móvel (`descricao` = "Serviço: {ambiente} — {móvel} ({medidas}) · {OS}", `unidade_compra = "SV"`, `fator = 1`, `quantidade` = quantidade do móvel, `custo_unitario` = `terceirizado_centavos` copiado do orçamento), `previsao_entrega` e `observacao` opcionais. O pedido nasce **rascunho**; enviar, receber e cancelar são feitos no Compras | Mesmo caminho da fábrica F5, agora com vários móveis num pedido (E6a). O Compras cuida do WhatsApp, do recebimento parcial e das parcelas |
| D10 | Exige o módulo **COMPRAS** contratado e a permissão `manage_purchases` (a do Compras para criar pedido), além de `servico` | A trava comercial e a interna do Compras continuam as dele |
| D11 | Cada móvel guarda o `pedido_compra_id`. Móvel com pedido não cancelado não entra em outro: `409` "O móvel Torre Quente já está no pedido PC-…" | Evita pedir duas vezes |
| D12 | **Conta a pagar:** é lançada pelo **recebimento** do pedido no Compras (`recebimentos.lancar_contas`, sem categoria = despesa no resultado). A marcenaria não lança conta | FB2. F2a: o terceirizado entra no resultado uma vez, pela conta paga (09A D14) |
| D13 | O valor do pedido segue a regra de custo do Compras (quem não vê custo de compra não vê preço do pedido). A resposta da marcenaria traz `valor_orcado_centavos` só com `view_custos_marcenaria` | P4 dos dois lados |

### 4.3. Permissões e outras regras

| # | Decisão | Motivo |
|---|---------|--------|
| D14 | Leitura, conferir, problema, voltar e o modo manual: permissão de **OS** (`servico`) | A seção fica na aba da OS (T1) |
| D15 | **Desfazer aprovação** (08A §7.6) bloqueado com algum móvel com pedido do Compras não cancelado, ou `ENVIADO` ou além no modo manual: "Já há pedido à central Madeiranit (PC-000123). Cancele o pedido no Compras e volte o móvel para 'A pedir' antes de desfazer." | O8: desfazer com pedido feito deixaria a central produzindo sem OS |
| D16 | **Cancelar a OS** (gancho da 09A) com móvel pedido: evento "Há móveis pedidos à central para esta OS: Torre Quente (PC-000123, Recebido). Combine com a central." O pedido e as contas **não** são cancelados sozinhos | O móvel existe e foi pedido; a dívida com a central não some porque o cliente desistiu |
| D17 | Lista geral: `GET /marcenaria/terceirizados?situacao=&central_id=&atrasados=` com OS, cliente, móvel, central, pedido, previsão e situação, das OS abertas | O dono liga para a central uma vez por dia com a lista dos atrasados |

---

## 5. Modelo de dados

```sql
ALTER TABLE marcenaria_moveis ADD COLUMN pedido_compra_id INTEGER REFERENCES pedidos_compra(id) ON DELETE SET NULL; -- D9
ALTER TABLE marcenaria_moveis ADD COLUMN terc_situacao VARCHAR(10);    -- modo manual (D3); NULL = A_PEDIR
ALTER TABLE marcenaria_moveis ADD COLUMN terc_pedido VARCHAR(60);      -- nº anotado no modo manual
ALTER TABLE marcenaria_moveis ADD COLUMN terc_enviado_em DATE;
ALTER TABLE marcenaria_moveis ADD COLUMN terc_previsao DATE;
ALTER TABLE marcenaria_moveis ADD COLUMN terc_recebido_em DATE;
ALTER TABLE marcenaria_moveis ADD COLUMN terc_conferido_em DATE;       -- os dois modos (D2)
ALTER TABLE marcenaria_moveis ADD COLUMN terc_problema VARCHAR(500);   -- os dois modos (D4)
CREATE INDEX ix_marcenaria_moveis_pedido ON marcenaria_moveis (pedido_compra_id);
CREATE INDEX ix_marcenaria_moveis_terc ON marcenaria_moveis (terc_situacao, terc_previsao);
```

Migração `642b2e8f79fa`, filha de `195109da93f7` (09A), com a regra da 08A §5.1 (só se a coluna faltar, sem `batch`). Tabela da marcenaria: nenhuma tabela compartilhada muda.

---

## 6. Contrato da API

Prefixo `/api/v1/marcenaria`.

| Método e rota | Permissão | O que faz |
|---------------|-----------|-----------|
| `GET /os/{numero_os}/terceirizados` | servico | Móveis terceirizados da OS (§6.1) e `modo_compras` (se o módulo está ativo) |
| `POST /os/{numero_os}/terceirizados/pedir` | servico + COMPRAS + manage_purchases | `{movel_ids, previsao_entrega?, observacao?}` → o pedido criado (D9) |
| `POST /os/{numero_os}/terceirizados/enviar-manual` | servico | `{movel_ids, pedido?, previsao?}` — só sem pedido do Compras (D3) |
| `POST /os/{numero_os}/terceirizados/receber-manual` | servico | `{movel_ids, data?}` — só sem pedido do Compras (D3) |
| `POST /os/{numero_os}/terceirizados/conferir` | servico | `{movel_ids}` |
| `POST /os/{numero_os}/terceirizados/{movel_id}/problema` | servico | `{texto}` (D4) |
| `POST /os/{numero_os}/terceirizados/{movel_id}/voltar` | servico | D5 |
| `GET /terceirizados?situacao=&central_id=&atrasados=` | servico | D17 |

### 6.1. Móvel terceirizado

```jsonc
{
  "movel_id": 10, "nome": "Torre Quente", "ambiente": "Cozinha Gourmet", "quantidade": 1,
  "medidas": { "largura_mm": 700, "altura_mm": 2200, "profundidade_mm": 600 },
  "central": { "id": 9, "nome": "Madeiranit", "telefone": "8533…" },
  "situacao": "ENVIADO", "atrasado": false, "previsao": "2026-10-20",
  "pedido": { "origem": "COMPRAS", "id": 123, "codigo": "PC-000123", "situacao": "ENVIADO" },  // ou {"origem": "MANUAL", "numero": "4521"} ou null
  "enviado_em": "2026-10-08", "recebido_em": null, "conferido_em": null, "problema": null,
  "valor_orcado_centavos": 380000                 // só com view_custos_marcenaria (D13)
}
```

### 6.2. Erros

| Status | `detail` | Quando |
|--------|----------|--------|
| `422` | "Os móveis do mesmo pedido precisam ser da mesma central." | D9, D3 |
| `422` | "Este móvel não é terceirizado." | Móvel `INTERNA` |
| `409` | "Ação não permitida: o móvel Torre Quente está {situação}." | Transição fora de ordem |
| `409` | "O móvel Torre Quente já está no pedido PC-000123." | D11 |
| `409` | "Este móvel tem pedido no Compras: envie e receba por lá." | Ação manual num móvel com pedido do Compras |
| `409` | `{codigo: "OS_FECHADA"}` | D7 |
| `403` | `MODULO_NAO_CONTRATADO` / permissão do Compras | D10 |

---

## 7. Especificação técnica

```python
def pedir(db, numero_os, dados: PedidoCentralEntrada, usuario) -> PedidoServicoRead:
    os_, orc = _os_editavel(db, numero_os)                              # D7
    moveis = _terceirizados_da_os(orc, dados.movel_ids)                 # 422 se algum não for terceirizado
    _exigir_mesma_central(moveis)                                       # D9
    for movel in moveis:
        _exigir_situacao(movel, "A_PEDIR")                              # inclui "sem pedido ativo" (D11)
    central = pedidos_service.validar_fornecedor(db, moveis[0].central_fornecedor_id)
    pedido = pedidos_service.novo_rascunho(db, usuario, central)        # o Compras numera e registra
    pedido.tipo = TipoPedido.SERVICO                                    # serviço não entra no estoque
    pedido.previsao_entrega = dados.previsao_entrega
    pedido.observacao = (dados.observacao or "").strip() or None
    for movel in moveis:
        pedido.itens.append(PedidoCompraItem(
            produto_id=None,                                            # serviço: sem produto
            descricao=_descricao_servico(movel, os_)[:255],
            unidade_compra="SV", fator=1,
            quantidade=movel.quantidade,
            custo_unitario=movel.terceirizado_centavos,                 # o orçado, copiado (06A)
        ))
    pedidos_service._recalcular(pedido)                                 # totais do pedido, como o Compras faz
    pedidos_service._definir_parcelas(pedido, None)                     # parcelas padrão do Compras
    db.flush()
    pedidos_service.registrar_log(db, usuario, pedido, "CRIADO", None, SituacaoPedido.RASCUNHO,
                                  f"Central parceira da OS {os_.numero_os}")
    for movel in moveis:
        movel.pedido_compra_id = pedido.id                              # D11
    registrar_evento(db, orc, "TERCEIRIZADO_PEDIDO", ..., os_id=os_.id, usuario=usuario)   # D6
    return _pedido_read(pedido)
```

- É o mesmo uso de `pedidos_service` que `services/fabrica/terceiros.criar_pedido` fazia (código conferido em 08/10), com vários itens. As funções com `_` do Compras são usadas pelo próprio pacote e pela fábrica; se o Compras ganhar uma função pública equivalente, trocar por ela.
- `_situacao(movel, pedido)` implementa D2/D3 numa função só, usada pela leitura, pela lista geral (D17) e pela Spec 12A (pronto = `CONFERIDO`).
- Os bloqueios (D15) e o aviso de cancelamento (D16) entram nas listas `BLOQUEIOS_DESFAZER` (08A §7.6) e `ganchos.ao_cancelar` (09A §6.1).

---

## 8. Limitações conhecidas

- Sem cotação entre centrais (fora da fase 1).
- Sem o módulo Compras, a conta da central é lançada à mão em Contas a Pagar, numa categoria de despesa (09A D14).
- O móvel terceirizado **não** tem etapas de produção (12A): para a produção, ele está pronto quando `CONFERIDO`.

## 9. Entrega (PR7)

`npm run build:sidecar`.

---

## 10. Critérios de aceite

- [x] Móvel terceirizado aprovado aparece "A pedir".
- [x] Com o Compras: pedir vários móveis da mesma central cria **um** pedido `SERVICO` em rascunho, com um item por móvel; a situação acompanha o pedido (enviado, recebido) e o recebimento no Compras lança a conta.
- [x] Sem o Compras: enviar (com nº e previsão) e receber à mão.
- [x] Conferir, registrar problema e voltar um passo nos dois modos.
- [x] Atrasados na lista geral.
- [x] Desfazer aprovação bloqueado com pedido; cancelamento registra o aviso.
- [x] Nenhum valor sem `view_custos_marcenaria`; o Compras sem mudança. Código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Aprovar orçamento com 2 terceirizados | Os dois `A_PEDIR`, sem pedido |
| 02 | Com o Compras: pedir os dois (mesma central) | Um `PedidoCompra` `SERVICO` em `RASCUNHO`, 2 itens sem produto, `custo_unitario` = orçado; os dois móveis com o `pedido_compra_id`; situação `A_PEDIR` com "pedido em rascunho" |
| 03 | Pedir móveis de centrais diferentes juntos | `422` |
| 04 | Pedir de novo um móvel com pedido não cancelado | `409` (D11) |
| 05 | Enviar o pedido pelo Compras (`pedidos.enviar`) | Situação `ENVIADO`, previsão do pedido |
| 06 | Receber pelo Compras | Situação `RECEBIDO`; contas a pagar lançadas pelo Compras |
| 07 | Conferir | `CONFERIDO`; `terc_conferido_em` hoje |
| 08 | Cancelar o pedido no Compras | Os móveis voltam a `A_PEDIR` (derivado) e podem ser pedidos de novo |
| 09 | Sem o Compras: `pedir` | `403 MODULO_NAO_CONTRATADO` |
| 10 | Sem o Compras: enviar-manual (nº 4521, previsão ontem) | `ENVIADO`; `atrasado: true` |
| 11 | Receber-manual e conferir | `RECEBIDO`, depois `CONFERIDO` |
| 12 | Registrar problema | Fica `RECEBIDO`, com o texto; conferir limpa |
| 13 | Voltar de `CONFERIDO` | `RECEBIDO` |
| 14 | Ação manual num móvel com pedido do Compras | `409` |
| 15 | Desfazer aprovação com pedido em rascunho | Motivo do D15 |
| 16 | Cancelar OS com móvel `RECEBIDO` | Evento do D16; pedido e contas intactos |
| 17 | Resultado do mês com a conta do recebimento paga | Valor nas despesas (conta sem categoria), não no CMV (F2a) |
| 18 | Leitura sem `view_custos_marcenaria` | Sem `valor_orcado_centavos` |
