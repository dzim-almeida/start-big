# Spec 10A — Separação de Material (Backend)

| Campo        | Valor                                                                                   |
|--------------|-----------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                         |
| Camada       | Backend (FastAPI)                                                                       |
| Dependências | Specs 04A (`sofre_perda`), 06A (insumos), 08A (peças embutidas, `insumos_os`, ponto de extensão do desfazer), 09A (ganchos da OS, F2a), 03A (cancelamento sem devolução, FB1) · módulo Compras (`services/compras/demanda_os.py`, usado como é) |
| Bloqueia     | Spec 10B                                                                                |
| Referência   | SPEC-00: E1b, E2, E2a, E3b, E4, E5a, F2a, F2b, F5, P4, O8, FB1, FB2 · PR1, PR4, PR6, PR7, PR8 |

> **Revisão 1 (08/10/2026) — spec reescrita (SPEC-00 Revisão 15).** A versão de 06/10 tinha uma tabela própria (`marcenaria_separacao`), uma reserva calculada própria e uma lista de compras própria. Com a Revisão 15: (1) os insumos aprovados **já estão na OS** como peças embutidas (08A Revisão 2, F2b), então a separação trabalha sobre esses itens, com as colunas que a finalização e o Compras já entendem (`quantidade_separada`, `custo_real`; E3b); (2) a reserva e o "quanto o estoque cobre" vêm do **Compras** (`demanda_os.demandas_por_produto` e `compras_da_os`, E1b, FB2); (3) a lista de compras entre OS é a tela **Necessidades** do Compras, e esta spec só entrega as **faltas da OS** (E5a). **Não há migração.** As decisões de comportamento aprovadas em 06/10 (E2a: retirada sem saldo acontece; sobra pode ser devolvida; cancelar não devolve sozinho) continuam.

---

## 1. Objetivo

Levar o material do orçamento aprovado para a fábrica:

1. **Separação por OS e produto:** o que precisa sair do estoque para aquela OS, com a quantidade **sugerida** e a **retirada de verdade**, que dá baixa no estoque (E2, E3b).
2. **Disponível e faltas:** quanto o estoque cobre para esta OS, descontado o que as OS anteriores na fila já comprometeram, e o que falta (E1b, E5a).
3. **Leitor de código de barras** (E4): achar o item da separação pelo código do produto ou da embalagem.

## 2. Escopo

**Dentro do escopo**
- Leitura da separação de uma OS (uma linha por peça embutida do orçamento).
- Retirar, devolver, concluir, reabrir.
- Leitor (código de barras, código do produto, código de embalagem).
- Faltas da OS.
- Disponível por produto para a busca de insumo do orçamento (06B).
- Bloqueio do "desfazer aprovação" e aviso no cancelamento da OS.

**Fora do escopo**
- Telas (10B).
- Lista de compras entre OS e pedido de compra: são do **Compras** (Necessidades, pedidos), módulo COMPRAS (E5a).
- Móveis terceirizados (11A): não têm material a separar (08A D1d).
- Plano de corte e peças (fase 2).
- Qualquer mudança no módulo Compras, na finalização ou no livro de estoque (FB2).

---

## 3. Arquivos afetados

```
backend-fastapi/
├── app/
│   ├── schemas/marcenaria/separacao.py                      # CRIAR
│   ├── services/marcenaria/
│   │   ├── separacao.py                                     # CRIAR — ler, retirar, devolver, concluir, reabrir
│   │   ├── leitor.py                                        # CRIAR — código → item (produto, embalagem com fator)
│   │   ├── insumos_os.py                                    # CONFERIR — planejado/sugerido (08A Revisão 2)
│   │   └── __init__.py                                      # ALTERAR — bloqueio do desfazer + gancho de cancelamento
│   └── api/v1/endpoints/marcenaria_separacao.py             # CRIAR
└── test/services/marcenaria/test_separacao.py, test_leitor.py, test/api/v1/marcenaria/test_separacao_api.py   # CRIAR
```

**Nenhum arquivo compartilhado muda.** Usados como são: `services/movimentacao_estoque.registrar_movimentacao` e `custo_atual` (livro de estoque), `services/compras/demanda_os` (`demandas_por_produto`, `compras_da_os`), `app/services/quantidade_venda.UNIDADES_FRACIONAVEIS`.

| Camada | Faz | Não faz |
|--------|-----|---------|
| `endpoints/marcenaria_separacao.py` | Token, permissão, capacidade | Regra |
| `services/marcenaria/separacao.py` | Regras das ações, eventos, montagem da resposta | SQL de reserva (é do Compras) |
| `services/marcenaria/leitor.py` | Achar o item pelo código | Mexer em estoque |

---

## 4. Decisões

### 4.1. O que separar

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Uma linha da separação = uma **peça embutida** da OS que veio do orçamento: item `PRODUTO` com `origem = "ORCAMENTO_MARCENARIA"` (08A D1a). Já é uma por produto, somando todos os móveis (E3a) | E3b. Nenhum dado novo: o item da OS é a fonte |
| D2 | **Planejado** e **sugerido** de cada linha vêm de `insumos_os.insumos_da_os(orc)` (08A D1b), lidos do orçamento aprovado (somente leitura, F3). O sugerido é a `quantidade` com que o item nasceu | O orçamento aprovado não muda, então o planejado também não; o "reabrir" sabe para onde voltar |
| D3 | Insumo do orçamento sem produto (excluído depois da cópia) aparece como linha **informativa**, "Sem cadastro — não baixa estoque", agrupada pela descrição, sem ações | Não some do que a fábrica precisa, e não inventa produto para dar baixa (08A D1c) |
| D4 | Ordem: **localização no estoque** (`produto.localizacao_estoque`), depois nome; sem localização, no fim | Quem separa anda pelo depósito uma vez |
| D5 | Cada linha mostra **quais móveis** usam o produto e quanto cada um planejou (`InsumoDaOS.moveis`) | O marceneiro sabe para onde vai cada chapa |

### 4.2. Retirar, devolver, concluir, reabrir

Vocabulário: **falta** = `quantidade − quantidade_separada` do item; **concluída** = falta zero (ou o item marcado como não usado, D11).

| # | Decisão | Motivo |
|---|---------|--------|
| D6 | **Retirar** registra a quantidade **real** (padrão: a falta; editável; maior que zero): `registrar_movimentacao(SAIDA, origem=ORDEM_SERVICO, ordem_servico_id=…, permitir_negativo=True)` e `quantidade_separada += q`. `custo_real` do item = custo médio do estoque no instante (`custo_atual`), ponderado pelas retiradas (a mesma conta que a fábrica F4 fazia) | E2, E3b. A baixa ligada à OS leva o material ao CMV (F2a). O `custo_real` fica gravado para um relatório de margem real futuro; não aparece em tela nenhuma desta fase (P4) |
| D7 | Retirar **mais** que a falta é permitido: a `quantidade` do item sobe para o total retirado, com o aviso "Retirado acima do sugerido" na resposta | E2a/E3b: a chapa já saiu; a OS consome o que saiu |
| D8 | Sem saldo, a retirada **acontece** (estoque negativo) e a linha mostra "O estoque ficou negativo: confira a contagem." | E2a. Travar não devolve a chapa; o negativo aponta o cadastro errado |
| D9 | **Devolver** (sobra, ferragem não usada): `registrar_movimentacao(ENTRADA, ORDEM_SERVICO, mesma OS)`, até o total retirado; `quantidade_separada −= q` **e** `quantidade −= q`. Se a `quantidade` chegaria a zero, o item é marcado como **não usado** (D11) | "Devolver" quer dizer "isto não vai ser usado": a OS deixa de precisar e a finalização não baixa de novo o que voltou. O CMV desconta sozinho (a entrada subtrai) |
| D10 | **Concluir** com retirado menor que a quantidade ("usou menos"): `quantidade := quantidade_separada`. A reserva solta e a finalização não baixa a diferença | A reserva não pode prender material que não vai ser usado (E3b) |
| D11 | **Concluir sem ter retirado nada** (o produto não foi usado): o item fica `status_aprovacao = REPROVADO`, com a `quantidade` intacta | A coluna exige `quantidade > 0` (`ck_os_item_quantidade_positiva`). Item `REPROVADO` já fica fora da baixa (`_itens_de_produto`), da reserva do Compras (`demanda_os`) e do CMV, sem regra nova. A marcenaria não tem aprovação por item na tela (03A D10), então a palavra não aparece para o usuário: a tela diz "não usado" |
| D12 | **Reabrir**: `status_aprovacao = APROVADO` e `quantidade := max(sugerido, quantidade_separada)` | Corrige um "concluir" por engano sem perder o que já saiu |
| D13 | Toda ação grava evento no histórico da marcenaria (06A D25) com quem, o quê e quanto | T7. O livro do estoque guarda o movimento; o evento conta a história na OS |
| D14 | Só com a OS **aberta** (fora de `FINALIZADA` e `CANCELADA`). Fora disso, só leitura | A separação é trabalho da produção |
| D15 | **Orçado × real** por produto: planejado (D2), retirado líquido e a diferença em % ("+12% sobre o orçado") | E3: é o número que diz se a perda configurada está certa. Por móvel não dá (a chapa é dividida) |
| D16 | **Concorrência:** cada escrita manda `separada_esperada` (a `quantidade_separada` que a tela tinha). Diferente da gravada → `409 REVISAO_DESATUALIZADA` e nada muda | Dois marceneiros na mesma OS retirariam o "padrão" duas vezes. Sem tabela nova: o próprio valor serve de revisão |

### 4.3. Disponível e faltas (E1b, E5a)

| # | Decisão | Motivo |
|---|---------|--------|
| D17 | **Cada linha** traz, de `compras.demanda_os.compras_da_os(db, os_id)` (chamada uma vez por leitura): `no_estoque` (quanto o estoque cobre para esta OS, na fila das OS abertas, D16 do Compras), `em_pedido` e `falta` | É exatamente a conta "Compras desta OS" que o Compras já faz e já testa; chamar a função não exige o módulo contratado (é serviço, não rota). FB2 |
| D18 | **Faltas da OS:** a lista das linhas com `falta > 0`, com produto, quantidade, unidade, localização e fornecedor principal (`produto.fornecedor_id`), para imprimir. Com o módulo COMPRAS, a tela leva às Necessidades (10B); a rota de faltas responde igual com ou sem o módulo | E5a. A lista entre OS (e o pedido) é do Compras |
| D19 | **Disponível para a busca de insumo** (06B): `GET /marcenaria/estoque/disponivel?produto_ids=` devolve `{produto_id: {estoque, reservado, disponivel}}` com `reservado = demanda_os.reservado(...)` de **todas** as OS abertas | E1b. A conta é a do Compras; só a forma da resposta é da marcenaria |

### 4.4. Leitor, permissões e outras regras

| # | Decisão | Motivo |
|---|---------|--------|
| D20 | **Leitor:** `GET /separacao/ler?codigo=` procura, **só entre as linhas desta OS**, pelo `codigo_barras` do produto, depois pelo `codigo_produto`, depois pelo código de barras de uma **embalagem** ativa do produto (`ProdutoEmbalagem`), devolvendo o `fator` (caixa de 10 = 10 unidades). Respostas: a linha (com `fator`); "Este produto não faz parte desta OS." (`404`); ou a linha com `concluida: true` | E4. É a mesma busca que a separação da fábrica fazia (`fabrica/separacao._achar`), copiada para a marcenaria (a da fábrica sai na limpeza, FB1) |
| D21 | Permissão: **OS** (`servico`) para tudo (é uma aba da OS); o disponível da busca de insumo: `view_orcamentos_marcenaria` | Nenhuma chave nova |
| D22 | A separação **nunca** traz preço, custo nem valor (P4), qualquer que seja a permissão | P4 |
| D23 | **Desfazer aprovação** (08A §7.6) bloqueado se alguma peça embutida tiver `quantidade_separada > 0`: "Já há material retirado do estoque para esta OS. Devolva o material ao estoque antes de desfazer a aprovação." | O8: desfazer com chapa cortada deixaria estoque e custo sem dono |
| D24 | **Cancelar a OS** não devolve material sozinho (03A D15); o gancho `ao_cancelar` (09A) grava o evento "Material retirado para esta OS continua fora do estoque: 3 un MDF Branco TX 18mm, …" quando houver retirado | E2a: chapa cortada não volta à prateleira |

---

## 5. Modelo de dados

**Nenhuma tabela nova e nenhuma migração.** A separação usa colunas que já existem em `ordem_servico_itens` (fábrica F4, migração `c6f2d8a4b915`):

| Coluna | Uso aqui | Quem mais lê |
|--------|----------|--------------|
| `quantidade` | O que a OS vai consumir no total (nasce = sugerido) | Finalização (baixa), Compras (reserva) |
| `quantidade_separada` | Retirado líquido (retiradas − devoluções); nula = nada retirado | Finalização (baixa só `quantidade − separada`), Compras (reserva `quantidade − separada`) |
| `custo_real` | Custo médio no instante das retiradas (D6) | Ninguém nesta fase |
| `status_aprovacao` | `REPROVADO` = não usado (D11) | Finalização, Compras, CMV (já ignoram `REPROVADO`) |
| `origem` | Identifica a peça embutida do orçamento (08A) | Trava de edição (08A) |

Unidades: o item da OS é `Float` (como o estoque). A API recebe e devolve **milésimos** (`int`, PR4) e converte na borda: `quantidade = milesimos / 1000`, `milesimos = round(quantidade * 1000)`.

---

## 6. Contrato da API

### 6.1. Rotas

Prefixo `/api/v1/marcenaria`. Tudo `404` sem a capacidade `orcamento_tecnico` ou numa OS sem orçamento aprovado.

| Método e rota | Permissão | O que faz |
|---------------|-----------|-----------|
| `GET /os/{numero_os}/separacao` | servico | Linhas (§6.2) |
| `POST /os/{numero_os}/separacao/{item_id}/retirar` | servico | `{quantidade_milesimos, separada_esperada_milesimos}` (D6, D7, D16) |
| `POST /os/{numero_os}/separacao/{item_id}/devolver` | servico | Idem (D9) |
| `POST /os/{numero_os}/separacao/{item_id}/concluir` · `/reabrir` | servico | `{separada_esperada_milesimos}` (D10–D12) |
| `GET /os/{numero_os}/separacao/ler?codigo=` | servico | D20 |
| `GET /os/{numero_os}/separacao/faltas` | servico | D18 |
| `GET /estoque/disponivel?produto_ids=1,2,3` | view_orcamentos | D19 |

Toda escrita responde a **separação inteira** atualizada (§6.2), para a tela ver o disponível e o progresso novos.

### 6.2. Separação da OS

```jsonc
{
  "os": { "numero_os": "OS-2026-000512", "status": "EM_ANDAMENTO", "editavel": true },
  "linhas": [
    {
      "item_id": 3307, "produto_id": 55, "descricao": "MDF Branco TX 18mm", "codigo": "MDF-BR-18",
      "unidade": "UN", "localizacao": "Corredor A · Prateleira 2",
      "planejado_milesimos": 2200, "sugerido_milesimos": 3000,
      "quantidade_milesimos": 3000, "separada_milesimos": 0, "falta_milesimos": 3000,
      "concluida": false, "nao_usado": false,
      "no_estoque_milesimos": 3000, "em_pedido_milesimos": 0, "sem_cobertura_milesimos": 0,   // D17 (Compras)
      "estoque_milesimos": 6000,
      "diferenca_bp": null,                                                 // D15, depois de retirar
      "moveis": [ { "nome": "Balcão", "ambiente": "Cozinha Gourmet", "planejado_milesimos": 2200 } ],
      "alertas": []                       // "SEM_COBERTURA" | "ESTOQUE_NEGATIVO" | "ACIMA_DO_SUGERIDO"
    }
  ],
  "sem_cadastro": [ { "descricao": "Puxador perfil antigo", "planejado_milesimos": 2000 } ],   // D3
  "resumo": { "linhas": 2, "concluidas": 0, "com_falta": 0 }
}
```

`sem_cobertura_milesimos` é o `falta` do Compras (o que nem o estoque nem pedido cobre). `SEM_COBERTURA` aparece quando ele é maior que zero. Nenhum campo de preço (D22).

### 6.3. Faltas da OS

```jsonc
{
  "numero_os": "OS-2026-000512", "cliente": "Studio Arquitetura & Interiores Ltda",
  "itens": [ { "produto_id": 55, "descricao": "MDF Branco TX 18mm", "unidade": "UN",
               "faltam_milesimos": 2000, "localizacao": "Corredor A",
               "fornecedor": { "id": 4, "nome": "Madeireira Central", "telefone": "8533…" } } ],
  "gerado_em": "2026-10-08T14:00:00"
}
```

### 6.4. Erros

| Status | `detail` | Quando |
|--------|----------|--------|
| `404` | "Esta OS não tem separação de material." | OS sem orçamento aprovado, ou sem a capacidade |
| `404` | "Este produto não faz parte desta OS." | Item de outra OS, ou código que não casa (leitor) |
| `409` | `{codigo: "OS_FECHADA"}` · "A OS está finalizada ou cancelada; a separação não pode mais ser alterada." | D14 |
| `409` | `{codigo: "REVISAO_DESATUALIZADA"}` · "Outra pessoa alterou este item. A lista foi atualizada." | D16 |
| `422` | "A quantidade deve ser maior que zero." | Retirar ou devolver com 0 |
| `422` | "Não é possível devolver mais do que foi retirado ({n})." | D9 |

---

## 7. Especificação técnica

### 7.1. Linhas — leitura

```python
def ler(db: Session, numero_os: str) -> SeparacaoRead:
    os_, orc = _os_com_orcamento_aprovado(db, numero_os)              # 404 sem orçamento (§6.4)
    itens = [i for i in os_.itens                                      # as peças embutidas do orçamento (D1)
             if i.origem == ORIGEM_ORCAMENTO and i.tipo == OrdemServicoItemTipo.PRODUTO]
    planejados = {p.produto_id: p for p in insumos_da_os(orc, _unidades(db, itens))}   # D2
    cobertura = {c.produto_id: c for c in demanda_os.compras_da_os(db, os_.id).itens}  # D17, uma chamada
    linhas = [_montar_linha(i, planejados.get(i.produto_id), cobertura.get(i.produto_id)) for i in itens]
    linhas.sort(key=_ordem_do_deposito)                                # D4
    return SeparacaoRead(os=..., linhas=linhas, sem_cadastro=_sem_cadastro(orc), resumo=_resumo(linhas))
```

- `compras_da_os` só lista produtos com item `APROVADO` e falta maior que zero: linhas concluídas ou não usadas aparecem sem cobertura (zeros), o que está certo.
- `_unidades` lê `unidade_medida` dos produtos numa consulta só.

### 7.2. Retirar

```python
def retirar(db, numero_os, item_id, quantidade_milesimos, separada_esperada, usuario) -> SeparacaoRead:
    os_, orc = _os_editavel(db, numero_os)                            # D14
    item = _item_da_os(os_, item_id)                                   # 404 se não for peça embutida desta OS
    _conferir_separada(item, separada_esperada)                        # D16
    q = quantidade_milesimos / 1000                                    # o livro e o item são Float
    produto = db.get(Produto, item.produto_id)
    custo_agora = movimentacao_estoque.custo_atual(produto.estoque) or 0   # D6: custo médio do instante
    movimentacao_estoque.registrar_movimentacao(                       # E2: o livro de sempre
        db, produto=produto, tipo=MovimentacaoTipo.SAIDA, quantidade=q,
        origem=MovimentacaoOrigem.ORDEM_SERVICO, ordem_servico_id=os_.id,
        usuario_id=_id(usuario), usuario_nome=_nome(usuario),
        observacao=f"Separação marcenaria {orc.codigo}",
        permitir_negativo=True,                                        # D8
    )
    antes = item.quantidade_separada or 0
    depois = round(antes + q, 3)                                       # 3 casas, como o estoque
    item.custo_real = round(((item.custo_real or 0) * antes + custo_agora * q) / depois)   # ponderado (D6)
    item.quantidade_separada = depois
    if depois > item.quantidade:                                       # D7: retirou mais que o sugerido
        item.quantidade = depois
    registrar_evento(db, orc, "MATERIAL_RETIRADO", ..., os_id=os_.id, usuario=usuario)   # D13
    db.flush()
    return ler(db, numero_os)
```

### 7.3. Devolver, concluir, reabrir

```python
def devolver(...):            # D9
    # ENTRADA no livro; separada -= q; quantidade -= q.
    # Se a quantidade chegaria a <= 0: status_aprovacao = REPROVADO (não usado) e quantidade intacta (D11).
    ...

def concluir(...):            # D10, D11
    # separada > 0: quantidade = separada. separada == 0: status_aprovacao = REPROVADO.
    ...

def reabrir(...):             # D12
    # status_aprovacao = APROVADO; quantidade = max(sugerido, separada).
    ...
```

### 7.4. Ganchos

`services/marcenaria/__init__.py` acrescenta `_bloqueio_material_retirado` à lista `BLOQUEIOS_DESFAZER` (08A §7.6) e `separacao.avisar_material_no_cancelamento` a `ganchos.ao_cancelar` (09A §6.1, assinatura com `contexto`).

---

## 8. Limitações conhecidas

- **Orçado × real só por produto** (D15), não por móvel.
- **OS cancelada com material retirado:** o material fica fora do estoque e o custo **não** entra no resultado do mês (o CMV de OS só olha OS finalizadas, regra de hoje). A tela da OS avisa (D24). Registrar como pendência se o dono quiser essa perda no resultado.
- **Leitor por produto ou embalagem**, não por peça (peças só com plano de corte, fase 2).
- **Sem lista de compras entre OS sem o módulo Compras** (E5a): sem ele, cada OS imprime as próprias faltas.
- **Material comprado pelo Compras** sai do lucro duas vezes enquanto a PEND-003 estiver aberta (problema do Compras, fora daqui).

## 9. Entrega (PR7)

`npm run build:sidecar`. Sem migração.

---

## 10. Critérios de aceite

- [ ] A separação de uma OS aprovada lista uma linha por peça embutida, com planejado (com perda), sugerido, localização, os móveis que usam e a cobertura do estoque (Compras).
- [ ] Retirar dá baixa no estoque com origem OS e soma em `quantidade_separada`; retirar sem saldo funciona e avisa; retirar acima do sugerido sobe a quantidade e avisa.
- [ ] Devolver dá entrada e reduz a necessidade; concluir com menos ajusta a quantidade; concluir sem retirar marca "não usado"; reabrir volta ao sugerido.
- [ ] A reserva do Compras e o painel "Compras desta OS" refletem cada ação, sem mudança no Compras.
- [ ] Finalizar a OS baixa só o que não foi separado (regra de hoje) e o CMV conta as retiradas menos as devoluções.
- [ ] Leitor acha o item pelo código de barras, pelo código do produto ou pela embalagem (com o fator); produto de fora responde a mensagem certa.
- [ ] Faltas da OS com fornecedor principal, com ou sem o módulo Compras.
- [ ] Desfazer aprovação bloqueado com material retirado; cancelamento não devolve e registra o aviso.
- [ ] Nenhum preço na separação, para ninguém. Código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | OS do cenário B aprovada | Duas linhas (MDF, corrediça), sem a Torre terceirizada; MDF planejado 2.200, sugerido 3.000 |
| 02 | MDF em 3 móveis (1,4 / 1,2 / 0,6, sem perda) | Uma linha; sugerido 4.000 |
| 03 | Fita de borda em `M` (26,35 m) | Sugerido 26.350 (sem arredondar) |
| 04 | Insumo de produto excluído | Em `sem_cadastro`; nenhuma ação |
| 05 | Retirar 3 com estoque 6 | Estoque 3; movimento `SAIDA`, origem OS, `ordem_servico_id`; `quantidade_separada` 3; linha concluída |
| 06 | Retirar 3 com estoque 1 | Estoque −2; alerta `ESTOQUE_NEGATIVO` |
| 07 | Retirar 4 com sugerido 3 | `quantidade` 4; alerta `ACIMA_DO_SUGERIDO` |
| 08 | Devolver 1 depois de retirar 3 | Estoque +1; `quantidade_separada` 2; `quantidade` 2; concluída |
| 09 | Devolver 4 depois de retirar 3 | `422` |
| 10 | Concluir com 2 de 3 retiradas | `quantidade` 2; a reserva do Compras para esta OS cai a 0 |
| 11 | Concluir sem retirar nada | `status_aprovacao = REPROVADO`; fora de `demandas_por_produto`; finalização não baixa |
| 12 | Reabrir o caso 11 | `APROVADO`; `quantidade` = sugerido |
| 13 | Retirar com `separada_esperada` velha | `409 REVISAO_DESATUALIZADA`; estoque intacto |
| 14 | OS finalizada | Escritas `409 OS_FECHADA` |
| 15 | Leitor com código de barras / `codigo_produto` / embalagem de 10 / produto de outra OS | Linha (fator 1) / linha (fator 1) / linha (fator 10) / `404` |
| 16 | Duas OS abertas precisando de 4 e 3 chapas, estoque 5 | Na segunda (mais nova), `no_estoque` 1 e `sem_cobertura` 2 (fila do Compras) |
| 17 | `GET /estoque/disponivel` no mesmo cenário | Reservado 7; disponível −2 |
| 18 | Faltas da OS do caso 16 (segunda OS) | MDF, faltam 2, com o fornecedor principal |
| 19 | Desfazer aprovação com retirado > 0 | Motivo do D23 na lista de bloqueios |
| 20 | Cancelar OS com material retirado | Evento do D24; estoque não muda (03A D15) |
| 21 | Finalizar com 2 de 3 retiradas e a linha **não** concluída | A finalização baixa 1 (regra de hoje); CMV = 3 chapas |
| 22 | Finalizar com 2 de 3 e a linha concluída | A finalização não baixa nada desse produto; CMV = 2 chapas |
| 23 | Separação sem `view_custos` e com | Nenhum campo de preço nas duas |
| 24 | Informática: criar, finalizar e cancelar OS com peça | Igual a antes (nenhum arquivo compartilhado mudou) |
