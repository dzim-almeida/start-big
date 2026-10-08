# Spec 10A — Separação de Material, Reserva e Lista de Compras (Backend)

| Campo        | Valor                                                                                   |
|--------------|-----------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                         |
| Camada       | Backend (FastAPI)                                                                       |
| Dependências | Specs 04A (`sofre_perda`), 06A (insumos), 08A (aprovação, ponto de extensão do desfazer), 09A (ganchos da OS, F2a) |
| Bloqueia     | Spec 10B                                                                                |
| Referência   | SPEC-00: E1, E1a, E2, E2a, E3, E3a, E4, E5, F2a, F5, P4, O8 · PR1, PR4, PR6, PR7, PR8 |

---

## 1. Objetivo

Levar o material do orçamento aprovado para a fábrica:

1. **Separação por OS:** o que precisa sair do estoque para aquela OS, produto a produto, com a quantidade **sugerida** (arredondada para cima nas unidades inteiras) e a **retirada de verdade**, que dá baixa no estoque (E2, E3).
2. **Reserva calculada** (E1): o que já está comprometido com OS abertas e ainda não saiu, para ninguém prometer a mesma chapa duas vezes.
3. **Lista de compras** (E5): o que falta para atender as OS abertas, agrupado por fornecedor.
4. **Leitor de código de barras** (E4): achar o item da separação pelo código.

## 2. Escopo

**Dentro do escopo**
- Linhas de separação por OS e produto, retirar, devolver, concluir.
- Reserva calculada e "disponível" por produto.
- Lista de compras.
- Bloqueio do "desfazer aprovação" e aviso no cancelamento da OS.
- Migração e testes, com a medição de desempenho de E1a.

**Fora do escopo**
- Telas (10B).
- Pedido de compra (E5: não existe módulo de compras nesta branch).
- Móveis terceirizados (11A): eles **não** têm material a separar (§4.1, D4).
- Plano de corte e peças (fase 2).

---

## 3. Arquivos afetados

```
backend-fastapi/
├── alembic/versions/c2d3e4f5a6b7_separacao_marcenaria.py   # CRIAR — filha da 09A
├── app/
│   ├── db/models/marcenaria/separacao.py                    # CRIAR
│   ├── db/crud/marcenaria/separacao.py                      # CRIAR — consultas agrupadas (E1a)
│   ├── schemas/marcenaria/separacao.py                      # CRIAR
│   ├── services/marcenaria/
│   │   ├── separacao.py                                     # CRIAR — linhas, retirar, devolver, concluir, leitor
│   │   ├── reserva.py                                       # CRIAR — reserva e disponível
│   │   ├── lista_compras.py                                 # CRIAR
│   │   ├── unidades.py                                      # CRIAR — unidade inteira × fracionada
│   │   └── __init__.py                                      # ALTERAR — bloqueio do desfazer + gancho de cancelamento
│   └── api/v1/endpoints/marcenaria_separacao.py             # CRIAR
└── test/services/marcenaria/test_separacao*.py, test_reserva.py, test_lista_compras.py   # CRIAR
```

Nenhum arquivo compartilhado muda: a baixa usa `registrar_movimentacao` como ele é (E2).

---

## 4. Decisões

### 4.1. O que separar

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | A separação é por **OS e produto**: todos os insumos aprovados que usam o mesmo produto viram **uma linha** | ⚠️ **Revisão de E3:** chapa se corta para vários móveis de uma vez. Separar por móvel arredondaria cada um para cima (1,4 + 1,2 + 0,6 → 2 + 2 + 1 = **5** chapas) quando a fábrica precisa de **4** (3,2 arredondado uma vez) |
| D2 | **Planejado** de um produto na OS = Σ (quantidade do insumo × quantidade do móvel × (1 + perda), a perda só se o insumo `sofre_perda`), sobre os móveis **aprovados**, com os números copiados do orçamento | É o que o orçamento cobrou (C1, C2). O orçamento aprovado não muda, então o planejado também não |
| D3 | **Sugerido** = planejado arredondado **para cima** nas unidades inteiras (todas, menos KG, G, L, ML, M, CM — mesma regra de `quantidade.ts` do frontend); nas fracionadas, o próprio planejado | E3: ninguém retira 0,4 chapa; fita de borda sai em metros quebrados |
| D4 | Móvel **terceirizado** não entra na separação (o material é da central) | E6: o que a fábrica separa é o que ela produz |
| D5 | Insumo sem produto (o produto foi excluído depois da cópia, `produto_id` nulo) aparece como linha **informativa**, "Sem cadastro — não baixa estoque", agrupada pela descrição | Não some do que a fábrica precisa, e não inventa produto para dar baixa |
| D6 | Ordem das linhas: **localização no estoque** (`produto.localizacao_estoque`), depois o nome; sem localização, no fim | Quem separa anda pelo depósito uma vez, na ordem das prateleiras |
| D7 | Cada linha mostra também **quais móveis** usam o produto e quanto cada um planejou | O marceneiro sabe para onde vai cada chapa, mesmo com a baixa por produto |

### 4.2. Retirar, devolver, concluir

| # | Decisão | Motivo |
|---|---------|--------|
| D8 | **Retirar** registra uma quantidade **real** (padrão: sugerido − já retirado; editável; maior que zero) e dá baixa com `registrar_movimentacao(SAIDA, origem=ORDEM_SERVICO, ordem_servico_id=…)` (E2). Pode ser feito várias vezes (retiradas parciais) | E2, E3. A baixa ligada à OS é o que leva o material ao resultado do mês na finalização (F2a) |
| D9 | Sem saldo, a retirada **acontece** (`permitir_negativo=True`) e a linha mostra "O estoque ficou negativo: confira a contagem." | Mesmo critério da OS de hoje: a chapa está na mão do marceneiro; travar o sistema não a faz voltar, só para a fábrica. O negativo é o sinal de que o cadastro está errado |
| D10 | **Devolver** (sobrou chapa inteira, ferragem não usada): `ENTRADA` com origem `ORDEM_SERVICO` e a mesma OS, até o total já retirado. O CMV desconta sozinho (a entrada subtrai, regra de hoje) | Sem devolução, a sobra ficaria fora do estoque e dentro do custo da OS |
| D11 | **Concluir** marca a linha como separada mesmo com retirado menor que o sugerido ("usou menos"); retirado igual ou maior que o sugerido conclui sozinho. Concluída, a linha sai da reserva. **Reabrir** volta a pendente | A reserva não pode prender material que não vai ser usado |
| D12 | Toda retirada, devolução e conclusão grava evento no histórico da marcenaria (06A D25) com quem e quanto | T7. O livro do estoque já guarda o movimento; o evento conta a história na OS |
| D13 | Só com a OS **aberta** (qualquer status menos `FINALIZADA` e `CANCELADA`). Fora disso, só leitura | A separação é trabalho da produção |
| D14 | **Orçado × real** por produto: planejado, retirado e a diferença em % ("+12% sobre o orçado"). É o número que diz se a perda de 10% está certa | E3. ⚠️ Por móvel não dá (D1): a chapa é dividida entre móveis |

### 4.3. Reserva e disponível (E1)

| # | Decisão | Motivo |
|---|---------|--------|
| D15 | **Reserva** de um produto = Σ, sobre as OS **abertas** com orçamento aprovado, de max(0, sugerido − retirado) das linhas **não concluídas** | E1: sem tabela de reserva; o número sai do que já existe |
| D16 | **Disponível** = estoque − reserva. Na tela de separação de uma OS, o disponível **para ela** desconta só a reserva das **outras** OS | Senão a própria OS "competiria" com ela mesma |
| D17 | Cálculo em **uma** consulta agrupada por (OS, produto), arredondamento em Python (o SQLite não tem `CEIL` garantido) e, por fim, soma por produto. Nunca uma consulta por produto | E1a (regra 2) |
| D18 | Calculado **só** em: tela de separação, lista de compras e busca de insumo do orçamento (`GET /estoque/disponivel`). **Nunca** na lista de produtos nem no PDV | E1a (regra 3) |

### 4.4. Leitor e lista de compras

| # | Decisão | Motivo |
|---|---------|--------|
| D19 | **Leitor:** `GET /separacao/ler?codigo=` procura o produto pelo `codigo_barras` e, não achando, pelo `codigo_produto`, **só entre as linhas desta OS**. Respostas: a linha; "Este produto não faz parte desta OS." (`404`); ou a linha com `ja_concluida: true` | E4. Leitor comum é um teclado que digita o código e Enter; a tela decide o que fazer com a linha |
| D20 | **Lista de compras:** produtos com reserva maior que zero e **disponível** (estoque − reserva) negativo; comprar = reserva − estoque. Com `repor_minimo`, entram também os produtos com reserva cujo disponível fica abaixo do `quantidade_minima`, e comprar = reserva + mínimo − estoque. Sempre arredondado para cima nas unidades inteiras. Produtos sem nenhuma reserva de marcenaria **não** entram (a lista é da produção, não do estoque inteiro da loja) | E5. O mínimo é configuração que o lojista já usa no estoque |
| D21 | Agrupada pelo **fornecedor principal** (`produto.fornecedor_id`), com o grupo "Sem fornecedor" no fim; cada item diz **quais OS** precisam dele e a localização. Com `view_custos`, o último preço de compra e o total estimado por fornecedor | E5. O preço ajuda a conferir a cotação; é custo, então segue P4 |

### 4.5. Permissões e outras regras

| # | Decisão | Motivo |
|---|---------|--------|
| D22 | Separação: permissão de **OS** (`servico`), a mesma de quem trabalha no modal de OS. Lista de compras: permissão de **produtos** (`produto`). Disponível: de orçamentos (`view_orcamentos_marcenaria`) | A separação é uma aba da OS (T1). Comprar é tarefa de quem cuida do estoque. Nenhuma chave nova na matriz de cargos |
| D23 | A separação **nunca** traz preço, custo nem valor (P4), qualquer que seja a permissão | P4: o marceneiro vê o material, não o preço |
| D24 | **Desfazer aprovação** (08A §7.6) fica bloqueado se alguma linha tiver retirado > 0: "Já há material retirado do estoque para esta OS. Devolva o material ao estoque antes de desfazer a aprovação." | O8. Desfazer com chapa já cortada deixaria o estoque e o custo sem dono |
| D25 | **Cancelar a OS** (gancho `ao_cancelar` da 09A) **não** devolve material sozinho; se houver retirado sem devolução, grava o evento "Material retirado para esta OS continua fora do estoque: 3 chapas MDF Branco TX 18mm, …" | Chapa cortada não volta à prateleira. Quem sabe o que voltou inteiro devolve antes, pela tela |
| D26 | Toda escrita leva a **revisão da linha** (inteiro, como no orçamento): retirada feita em outro computador depois de a tela carregar responde `409` e a tela recarrega | Dois marceneiros na mesma OS poderiam retirar o "padrão" duas vezes |

---

## 5. Modelo de dados

```sql
CREATE TABLE marcenaria_separacao (
  id INTEGER PRIMARY KEY,
  os_id        INTEGER NOT NULL REFERENCES ordens_servico(id),
  produto_id   INTEGER NOT NULL REFERENCES produtos(id),
  retirado_milesimos INTEGER NOT NULL DEFAULT 0,   -- líquido: retiradas − devoluções
  concluida    BOOLEAN NOT NULL DEFAULT 0,          -- D11
  revisao      INTEGER NOT NULL DEFAULT 1,          -- D26
  atualizado_por_nome VARCHAR(150),
  atualizado_em DATETIME NOT NULL,
  CONSTRAINT uq_marcenaria_separacao_os_produto UNIQUE (os_id, produto_id)
);
CREATE INDEX ix_marcenaria_separacao_produto ON marcenaria_separacao (produto_id, concluida);
```

- A linha da tabela nasce na **primeira** ação sobre o produto (retirar ou concluir). Antes disso, a linha da tela é só o planejado calculado (D2): nada é gravado ao abrir a aba.
- O planejado não é guardado: vem dos insumos aprovados (somente leitura depois da aprovação, F3).
- Unidades: milésimos, como os insumos (PR4). Na chamada a `registrar_movimentacao`, `quantidade = milesimos / 1000` (o estoque é `Float` desde antes).

---

## 6. Contrato da API

### 6.1. Rotas

| Método e rota | Permissão | O que faz |
|---------------|-----------|-----------|
| `GET /api/v1/marcenaria/os/{numero_os}/separacao` | servico | Linhas (§6.2) |
| `POST …/separacao/{produto_id}/retirar` | servico | `{quantidade_milesimos, revisao}` (D8, D26) |
| `POST …/separacao/{produto_id}/devolver` | servico | `{quantidade_milesimos, revisao}` (D10) |
| `POST …/separacao/{produto_id}/concluir` · `/reabrir` | servico | D11 |
| `GET …/separacao/ler?codigo=` | servico | D19 |
| `GET /api/v1/marcenaria/lista-compras?repor_minimo=false` | produto | D20, D21 |
| `GET /api/v1/marcenaria/estoque/disponivel?produto_ids=1,2,3` | view_orcamentos | `{produto_id: {estoque, reservado, disponivel}}` (D18) |

Toda escrita responde a **linha atualizada** (com estoque e disponível novos). Tudo `404` sem a capacidade `orcamento_tecnico` ou numa OS sem orçamento aprovado.

### 6.2. Linha da separação

```jsonc
{
  "os": { "numero_os": "OS-2026-000512", "status": "EM_ANDAMENTO", "editavel": true },
  "linhas": [
    {
      "produto_id": 55, "descricao": "MDF Branco TX 18mm", "codigo": "MDF-BR-18", "codigo_barras": "789…",
      "unidade": "UN", "localizacao": "Corredor A · Prateleira 2",
      "planejado_milesimos": 3520, "sugerido_milesimos": 4000,
      "retirado_milesimos": 0, "concluida": false, "revisao": 1,
      "estoque_milesimos": 6000, "disponivel_para_esta_os_milesimos": 5000,   // D16
      "diferenca_bp": null,                                                    // D14, depois de retirar
      "moveis": [ { "nome": "Torre Quente", "ambiente": "Cozinha Gourmet", "planejado_milesimos": 1540 } ],
      "alertas": []                       // "SEM_SALDO" | "ESTOQUE_NEGATIVO" | "SEM_CADASTRO"
    }
  ],
  "resumo": { "linhas": 12, "concluidas": 3, "com_falta": 1 }
}
```

`SEM_SALDO`: o disponível para esta OS é menor que o que falta retirar. Nenhum campo de preço (D23).

### 6.3. Lista de compras

```jsonc
{
  "grupos": [
    { "fornecedor": { "id": 4, "nome": "Madeireira Central", "telefone": "8533…" },
      "itens": [ { "produto_id": 55, "descricao": "MDF Branco TX 18mm", "unidade": "UN",
                   "estoque_milesimos": 2000, "reservado_milesimos": 9000, "comprar_milesimos": 7000,
                   "os": ["OS-2026-000512", "OS-2026-000515"], "localizacao": "Corredor A",
                   "ultimo_preco_centavos": 31500 } ],                  // só com view_custos (D21)
      "total_estimado_centavos": 220500 }                               // só com view_custos
  ],
  "gerado_em": "2026-10-08T14:00:00"
}
```

### 6.4. Erros

| Status | `detail` | Quando |
|--------|----------|--------|
| `404` | "Esta OS não tem separação de material." | OS sem orçamento aprovado, ou sem a capacidade |
| `404` | "Este produto não faz parte desta OS." | Produto sem linha nesta OS (inclusive no leitor) |
| `409` | `{codigo: "OS_FECHADA"}` · "A OS está finalizada ou cancelada; a separação não pode mais ser alterada." | D13 |
| `409` | `{codigo: "REVISAO_DESATUALIZADA"}` | D26 |
| `422` | "A quantidade deve ser maior que zero." | Retirar ou devolver com 0 |
| `422` | "Não é possível devolver mais do que foi retirado ({n})." | D10 |

---

## 7. Especificação técnica

### 7.1. Planejado e sugerido

```python
UNIDADES_FRACIONADAS = {"KG", "G", "L", "ML", "M", "CM"}   # mesma lista de shared/utils/quantidade.ts


def sugerido(planejado_milesimos: int, unidade: str | None) -> int:
    """Arredonda para cima até a unidade inteira, menos nas fracionadas (D3). Entra e sai em milésimos."""
    if (unidade or "UN").strip().upper() in UNIDADES_FRACIONADAS:
        return planejado_milesimos                       # 26,350 m de fita saem como 26,350 m
    return -(-planejado_milesimos // 1000) * 1000        # teto inteiro: 3520 -> 4000 (sem float)


def planejado_por_produto(orc: OrcamentoModel) -> dict[int | str, int]:
    """Σ qtd × qtd do móvel × (1 + perda) por produto, só móveis aprovados e não terceirizados (D2, D4)."""
    ...
    # perda em basis points; arredondamento HALF_UP em milésimos, como o motor (Spec 05)
```

### 7.2. Reserva — uma consulta (D17)

```python
def reservas_por_produto(db: Session, produto_ids: list[int] | None = None,
                         excluir_os_id: int | None = None) -> dict[int, int]:
    """Reserva em milésimos por produto, para as OS abertas com orçamento aprovado (D15)."""
    linhas = crud.planejado_agrupado(db, produto_ids, excluir_os_id)   # 1 SELECT agrupado por (os_id, produto_id),
                                                                       # já com a unidade e o retirado/concluída
    reservas: dict[int, int] = defaultdict(int)
    for linha in linhas:                                               # o laço é em memória, não no banco
        if linha.concluida:
            continue
        falta = sugerido(linha.planejado_milesimos, linha.unidade) - linha.retirado_milesimos
        reservas[linha.produto_id] += max(0, falta)
    return reservas
```

A consulta junta `marcenaria_movel_insumos → marcenaria_moveis (aprovado, INTERNA) → marcenaria_ambientes → marcenaria_orcamentos (APROVADO) → ordens_servico (status aberto)` com `LEFT JOIN marcenaria_separacao`. A perda do insumo é aplicada no `SUM` (`quantidade × qtd_movel × (10000 + perda_bp)` quando `sofre_perda`), dividida por 10000 em Python com HALF_UP.

### 7.3. Retirar

```python
def retirar(db, numero_os, produto_id, quantidade_milesimos, revisao, usuario) -> LinhaSeparacao:
    os_, orc = _os_editavel(db, numero_os)                          # D13
    linha = _linha_ou_404(db, os_, orc, produto_id)                 # só produtos planejados nesta OS
    _conferir_revisao(linha, revisao)                               # D26
    produto = produto_crud.get(db, produto_id)
    movimentacao_service.registrar_movimentacao(                   # E2: o livro de sempre
        db, produto=produto, tipo=MovimentacaoTipo.SAIDA,
        quantidade=quantidade_milesimos / 1000,                     # o estoque é Float
        origem=MovimentacaoOrigem.ORDEM_SERVICO, ordem_servico_id=os_.id,
        usuario_id=usuario.get("id"), usuario_nome=_nome(usuario),
        observacao=f"Separação marcenaria {orc.codigo}",
        permitir_negativo=True,                                     # D9
    )
    linha.retirado_milesimos += quantidade_milesimos
    linha.concluida = linha.concluida or linha.retirado_milesimos >= linha.sugerido   # D11
    linha.revisao += 1
    registrar_evento(db, orc, "MATERIAL_RETIRADO", ..., os_id=os_.id, usuario=usuario)   # D12
    return _montar_linha(db, os_, orc, produto_id)
```

### 7.4. Ganchos

- `services/marcenaria/__init__.py` acrescenta `_bloqueio_material_retirado` à lista `BLOQUEIOS_DESFAZER` (08A §7.6) e `separacao.avisar_material_no_cancelamento` a `ganchos.ao_cancelar` (09A §6.1).

### 7.5. Desempenho (E1a)

Teste de desempenho no CI (marcado, roda à parte): banco sintético com 6.000 OS e 288.000 insumos (o mesmo cenário medido em 06/10). `reservas_por_produto` sem filtro: **menos de 50 ms**; com 30 produtos: **menos de 10 ms**. O índice `ix_marcenaria_movel_insumos_produto` (06A) e os da árvore já existem; esta spec acrescenta `ix_marcenaria_separacao_produto`.

---

## 8. Limitações conhecidas

- **Orçado × real só por produto** (D1, D14), não por móvel.
- **OS cancelada com material retirado:** o material fica fora do estoque e o custo **não** entra no resultado do mês (o CMV de OS só olha OS finalizadas, regra de hoje). A perda existe e não aparece; a tela da OS avisa (D25). Registrar como pendência se o dono quiser essa perda no resultado.
- **Leitor por produto**, não por peça (peças só com plano de corte, fase 2).
- **Sem pedido de compra** (E5).

## 9. Entrega (PR7)

`npm run build:sidecar`.

---

## 10. Critérios de aceite

- [ ] A aba de separação de uma OS aprovada lista um produto por linha, com planejado (com perda), sugerido (arredondado nas unidades inteiras), localização e os móveis que usam.
- [ ] Retirar dá baixa no estoque com origem OS; retirar sem saldo funciona e avisa; devolver dá entrada; concluir libera a reserva.
- [ ] A reserva de uma chapa usada por duas OS abertas soma as duas; concluir ou retirar tudo libera.
- [ ] Lista de compras mostra só o que falta, por fornecedor, com as OS de cada item; preço só com custos.
- [ ] Leitor acha o produto da OS pelo código de barras ou pelo código; produto de fora responde a mensagem certa.
- [ ] Desfazer aprovação bloqueado com material retirado; cancelamento registra o aviso.
- [ ] Nenhum preço na separação, para ninguém.
- [ ] Finalizar a OS leva o material retirado (menos o devolvido) para o CMV do mês (F2a).
- [ ] Desempenho dentro dos limites da §7.5. Código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | MDF em 3 móveis (1,4 / 1,2 / 0,6 chapa, sem perda) | Uma linha; planejado 3200; sugerido 4000 |
| 02 | Mesmo, com perda 10% e `sofre_perda` | Planejado 3520; sugerido 4000 |
| 03 | Fita de borda em metros (26,35 m) | Sugerido 26350 (sem arredondar) |
| 04 | Móvel terceirizado | Insumos dele fora da separação |
| 05 | Móvel não aprovado | Fora da separação e da reserva |
| 06 | Insumo de produto excluído | Linha `SEM_CADASTRO`; retirar responde `404` |
| 07 | Retirar 4 chapas com estoque 6 | Estoque 2; movimento `SAIDA`, origem OS, `ordem_servico_id`; linha concluída |
| 08 | Retirar 4 com estoque 1 | Estoque −3; alerta `ESTOQUE_NEGATIVO` |
| 09 | Devolver 1 depois de retirar 4 | Estoque +1; retirado 3000; movimento `ENTRADA` |
| 10 | Devolver 5 depois de retirar 4 | `422` |
| 11 | Concluir com 3 de 4 retiradas | Concluída; reserva do produto cai a 0 para esta OS |
| 12 | Duas OS abertas precisando de 4 e 3 chapas, estoque 5 | Reserva 7; disponível −2; lista de compras: comprar 2 |
| 13 | Mesmo cenário, `repor_minimo` com mínimo 10 | Comprar 7 + 10 − 5 = 12 |
| 14 | OS finalizada | Escritas `409 OS_FECHADA`; reserva ignora a OS |
| 15 | Retirar com revisão velha | `409 REVISAO_DESATUALIZADA`; estoque intacto |
| 16 | Leitor com código de barras / com `codigo_produto` / produto de outra OS | Linha / linha / `404` |
| 17 | Desfazer aprovação com retirado > 0 | Motivo do D24 na lista de bloqueios |
| 18 | Cancelar OS com material retirado | Evento do D25; estoque não muda |
| 19 | Finalizar a OS e ler o CMV do mês | Inclui o custo das saídas menos as devoluções; não inclui o custo declarado nos itens (F2a) |
| 20 | Separação sem `view_custos` e com | Nenhum campo de preço nas duas |
| 21 | Lista de compras com e sem `view_custos` | Preço e total só com |
| 22 | Desempenho (§7.5) | Dentro dos limites |
