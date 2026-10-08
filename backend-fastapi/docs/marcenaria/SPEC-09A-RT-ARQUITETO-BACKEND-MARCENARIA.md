# Spec 09A — RT do Arquiteto e Custo no Resultado (Backend)

| Campo        | Valor                                                                                  |
|--------------|----------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                        |
| Camada       | Backend (FastAPI) ⚠️ código compartilhado (finalização de OS, custo do resultado do mês) |
| Dependências | Specs 04A (configuração), 05 (motor), 06A (tabela de RT), 08A (aprovação, `origem`)     |
| Bloqueia     | Specs 09B, 10A (regra de baixa), 11A (regra de categoria)                               |
| Referência   | SPEC-00: C5a, C5b, C5c, C5d, C5d+, C5e, C9, F2, F2a, F2b, F4a, E6b, R15-MIG · PR1, PR4, PR6, PR7, PR8 |
| Revisões     | 1 (08/10/2026): pedidos da Spec 09B e convergência com a branch — ver o fim do documento |

---

## 1. Objetivo

1. Quando a OS de um orçamento com arquiteto é **finalizada**, criar a **conta a pagar** do RT de cada arquiteto (C5b), na categoria certa e com o vencimento configurado.
2. Manter essas contas coerentes quando a OS é **reaberta** ou **cancelada**.
3. Corrigir uma **contagem dupla** que a 08A deixaria no resultado do mês (F2a, §4.3): o custo dos itens que vieram do orçamento não pode entrar no CMV, porque cada parte dele já entra por outro caminho.

## 2. Escopo

**Dentro do escopo**
- Ganchos genéricos de finalização, reabertura e cancelamento da OS.
- Criação, manutenção e cancelamento das contas de RT.
- Categoria "Comissão de arquitetos (RT)" e o parâmetro de vencimento.
- Regra do CMV para itens com `origem` (F2a), com prova de não regressão.

**Fora do escopo**
- Telas (09B): campo do arquiteto no orçamento, RT previsto na OS, parâmetro em Configurações.
- RT pago **antes** da finalização (adiantamento ao arquiteto): fora da fase 1 (§9).
- Nota fiscal do arquiteto (RPA, retenções): fora (§9).

---

## 3. Arquivos afetados

```
backend-fastapi/
├── alembic/versions/
│   └── 195109da93f7_rt_arquiteto_marcenaria.py          # CRIAR — filha da 08A (971eb6cc5a33; Revisão 1)
├── app/
│   ├── services/
│   │   ├── ordem_servico_ganchos.py                     # CRIAR ⚠️ — registro genérico de ganchos
│   │   ├── ordem_servico.py                             # ALTERAR ⚠️ — chama os ganchos (3 pontos)
│   │   └── marcenaria/
│   │       ├── rt.py                                    # CRIAR — contas de RT
│   │       └── __init__.py                              # ALTERAR — registra os ganchos
│   ├── db/
│   │   ├── crud/relatorio_custo.py                      # ALTERAR ⚠️ — CMV ignora item com origem (F2a)
│   │   └── models/
│   │       ├── marcenaria/orcamento.py                  # ALTERAR — conta_pagar_id em marcenaria_orcamento_rt
│   │       └── configuracao_marcenaria.py               # ALTERAR — rt_vencimento_dias, rt_plano_conta_id (arquivo da 04A)
│   └── schemas/configuracao_marcenaria.py               # ALTERAR — campo novo no GET/PUT (arquivo da 04A)
└── test/
    ├── services/marcenaria/test_rt.py                   # CRIAR
    ├── services/test_os_ganchos.py                      # CRIAR — sem gancho, nada muda
    └── services/test_cmv_origem.py                      # CRIAR — F2a e não regressão
```

---

## 4. Decisões

### 4.1. Conta a pagar do RT

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | A conta nasce na **finalização** da OS (C5b), **uma por arquiteto** com RT maior que zero, na mesma transação da finalização | Não se paga RT de obra que não terminou. Cada arquiteto é um fornecedor diferente (C5a) |
| D2 | **Valor:** o RT total do que foi **aprovado** (motor com `so_aprovados=True`, 08A) repartido entre os arquitetos pelo **maior resto**, com peso = percentual de cada um. A soma das contas é exatamente o RT total | C5d+, Revisão 6 (RT sobre o total com desconto). O orçamento aprovado é somente leitura, então o cálculo na finalização dá o mesmo número da aprovação |
| D3 | Mudanças na OS depois da aprovação (desconto final, frete, item manual) **não** mudam o RT. Quando o total da OS na finalização for diferente do total aprovado, o evento registra os dois números e a conta leva na observação: "Total aprovado R$ 7.360,36; OS finalizada com R$ 7.200,00. RT calculado sobre o aprovado." | O RT é o combinado com o arquiteto sobre a venda que ele indicou. O dono ajusta o valor da conta, se quiser, na tela de Contas a Pagar (a alteração de valor já é auditada) |
| D4 | **Descrição:** "RT arquiteto — Studio Renascer — OS-2026-000512 (ORC-2026-000084)". `fornecedor_id` = arquiteto | Quem lê a lista de contas sabe de onde veio sem abrir nada |
| D5 | **Categoria:** "Comissão de arquitetos (RT)", tipo `DESPESA`, criada na primeira vez que for necessária (busca pelo nome; não sendo achada, cria com `padrao = false`). O dono pode renomear: a busca usa o **id** guardado em `configuracoes_marcenaria.rt_plano_conta_id` depois da primeira criação | RT é despesa de venda, não custo de mercadoria. Guardar o id evita criar outra categoria quando o dono renomear a primeira |
| D6 | **Vencimento:** data da finalização + `rt_vencimento_dias` (configuração nova, padrão **30**, de 0 a 180) | É comum pagar o arquiteto no fechamento do mês. Configurável porque cada marcenaria combina diferente ⚠️ padrão a confirmar |
| D7 | A conta é criada **com ou sem** o módulo Financeiro contratado | Mesmo padrão das contas a receber da OS (`registrar_promessas_de_os`): o dado nasce sempre; o módulo decide quem vê. Se a loja contratar depois, o RT devido já está lá |

### 4.2. Reabrir e cancelar

| # | Decisão | Motivo |
|---|---------|--------|
| D8 | **Reabrir** OS finalizada: contas de RT **pendentes** são canceladas (pelo `cancelar_conta_pagar`, que audita); contas **pagas** ficam | A obra voltou a estar em aberto; a próxima finalização recria. O que já foi pago ao arquiteto não se desfaz sozinho |
| D9 | **Finalizar de novo:** para cada arquiteto, se já existe conta **paga**, nada é criado; se existe **pendente**, nada é criado (idempotente); se não existe ou foi cancelada, cria | Reabrir e refinalizar não pode duplicar o RT nem cobrar duas vezes |
| D10 | **Cancelar** OS finalizada: pendentes são canceladas; pagas ficam, com evento "RT já pago ao arquiteto Studio Renascer (R$ 588,82). Combine a devolução por fora." | A loja precisa saber que há dinheiro com o arquiteto de uma obra cancelada; o sistema não inventa estorno |
| D11 | Cada linha de `marcenaria_orcamento_rt` guarda o `conta_pagar_id` da conta **atual** (a última criada) | O vínculo fica do lado da marcenaria (mesma razão da 08A D7) |

### 4.3. Custo no resultado do mês (F2a) ⚠️ a confirmar

| # | Decisão | Motivo |
|---|---------|--------|
| D12 | O CMV (`get_custo_manual_os`) passa a **ignorar** itens de OS com `origem` preenchida. O `custo_unitario` desses itens continua servindo à **comissão** (C5, C5d), que não muda | O custo do item da marcenaria é custo direto + RT (C5d). Sem esta regra, o resultado do mês contaria **duas vezes**: o RT (no CMV e na conta paga, que é despesa), a mão de obra própria (no CMV e nos salários pagos) e o material (no CMV e na baixa de estoque da OS, Spec 10A) |
| D13 | Com D12, cada custo da marcenaria entra no resultado **uma vez, pelo registro real**: material pela baixa de estoque ligada à OS (Spec 10A); RT pela conta paga (esta spec); mão de obra pelos salários; terceirizado pela conta da central (Spec 11A) | O resultado mostra o que aconteceu, inclusive a perda real de chapa, e não a estimativa do orçamento |
| D14 | **Regras para as specs seguintes** (Revisão 1, com F2b e E6b): o material chega ao CMV pelo livro de estoque, com `origem = ORDEM_SERVICO` e o `ordem_servico_id`, seja na retirada da separação (10A) seja na finalização, que baixa as peças embutidas que sobraram (regra de hoje). As peças embutidas já ficam fora de `get_custo_manual_os` (têm `produto_id`). A conta da central: com o Compras, o recebimento a lança **sem categoria**, e conta sem categoria já conta como despesa (`crud/financeiro._total_pago`); sem o Compras, o usuário a lança em Contas a Pagar numa categoria de tipo `DESPESA` (nunca `CUSTO`, que fica fora do resultado) | Sem estas regras, material sairia do resultado ou o terceirizado não entraria. O material **comprado** pelo Compras tem um problema próprio do Compras (PEND-003), fora da marcenaria |
| D15 | Para as lojas atuais nada muda: nenhum item delas tem `origem` | PR1 (§7) |

---

## 5. Modelo de dados

```sql
ALTER TABLE marcenaria_orcamento_rt ADD COLUMN conta_pagar_id INTEGER REFERENCES contas_pagar(id);   -- D11
ALTER TABLE configuracoes_marcenaria ADD COLUMN rt_vencimento_dias INTEGER NOT NULL DEFAULT 30;       -- D6
ALTER TABLE configuracoes_marcenaria ADD COLUMN rt_plano_conta_id INTEGER REFERENCES planos_conta(id); -- D5
```

Migração `195109da93f7`, filha de `971eb6cc5a33` (08A), mesma regra da 08A §5.1: `ADD COLUMN` só se a coluna não existir, sem `batch` (Revisão 1, R15-MIG).

O `GET /configuracoes/marcenaria` (04A) passa a trazer `rt_vencimento_dias` **no bloco de custos** (só com `inclui_custos`); o `PUT` aceita o campo com `manage_custos_marcenaria`, de 0 a 180, mensagem "O prazo do RT deve ficar entre 0 e 180 dias."

---

## 6. Especificação técnica

### 6.1. Ganchos da OS — `services/ordem_servico_ganchos.py` ⚠️

```python
"""Pontos onde outros módulos reagem ao ciclo de vida da OS, sem o serviço da OS conhecê-los.

Cada gancho roda DENTRO da transação da OS: se ele falhar, a finalização (ou a
reabertura, ou o cancelamento) inteira é desfeita. Lista vazia = comportamento de sempre.
"""
from typing import Callable

# (db, os, usuario_token, contexto). `contexto` leva o que só o chamador sabe;
# hoje, no cancelamento, {"status_anterior": "FINALIZADA"} (Revisão 1).
GanchoOS = Callable[["Session", "OSModel", dict | None, dict], None]

ao_finalizar: list[GanchoOS] = []      # depois de a OS virar FINALIZADA
ao_reabrir: list[GanchoOS] = []        # depois de a OS sair de FINALIZADA/CANCELADA
ao_cancelar: list[GanchoOS] = []       # depois de a OS virar CANCELADA (contexto["status_anterior"])


def disparar(ganchos: list[GanchoOS], db, os_, usuario_token, contexto: dict | None = None) -> None:
    """Chama cada gancho na ordem em que foi registrado; `contexto` vazio por padrão."""
    for gancho in ganchos:
        gancho(db, os_, usuario_token, contexto or {})
```

No `ordem_servico.py`, três linhas, cada uma **antes** do `update_ordem_servico` final de `finalizar_ordem_servico`, `reabrir_ordem_servico` e `cancelar_ordem_servico`, ao lado das chamadas da fábrica que já estão lá (`trilho_fabrica.ao_finalizar` etc., inertes, FB1). O cancelamento guarda o status anterior numa variável local **antes** de trocar o status e o passa em `contexto={"status_anterior": ...}` (o RT só importa se a OS estava finalizada).

A marcenaria registra os seus em `services/marcenaria/__init__.py`, importado pelo `api.py` junto com as rotas da marcenaria:

```python
ganchos.ao_finalizar.append(rt.criar_contas_ao_finalizar)
ganchos.ao_reabrir.append(rt.cancelar_pendentes_ao_reabrir)
ganchos.ao_cancelar.append(rt.tratar_cancelamento)
```

Cada função da marcenaria começa por `orc = crud.orcamento_por_os(db, os_.id)` (índice `ix_marcenaria_orcamentos_os`) e **sai na hora** se não houver orçamento: nas outras lojas o custo é uma consulta por índice que não acha nada.

### 6.2. Criar as contas — `services/marcenaria/rt.py`

```python
def criar_contas_ao_finalizar(db: Session, os_: OSModel, usuario: dict | None, contexto: dict | None = None) -> None:
    """Uma conta a pagar por arquiteto, na finalização da OS (D1–D7, D9)."""
    orc = crud.orcamento_por_os(db, os_.id)
    if orc is None or not orc.rts:                                   # OS sem orçamento ou sem arquiteto
        return
    resultado = motor.calcular(montar_entrada_motor(orc, so_aprovados=True))  # D2: o aprovado
    linhas = [rt for rt in orc.rts if rt.rt_bp > 0]
    valores = repartir_maior_resto(resultado.rt_total_centavos, [rt.rt_bp for rt in linhas])  # soma exata
    config = config_crud.get(db)
    plano_id = _plano_do_rt(db, config)                              # D5: acha ou cria, guarda o id
    vencimento = hoje_local() + timedelta(days=config.rt_vencimento_dias)   # D6

    for rt, valor in zip(linhas, valores):
        if valor <= 0:
            continue                                                 # percentual tão pequeno que deu zero
        atual = rt.conta_pagar
        if atual and atual.status in ("PAGA", "PENDENTE"):           # D9: idempotente
            continue
        conta = financeiro_service.criar_conta_pagar(                # o caminho de sempre (auditoria inclusa)
            db, empresa_id=_empresa_da_os(os_),
            dados=ContaPagarCreate(
                descricao=_descricao(rt, os_, orc),                  # D4
                valor=valor, vencimento=vencimento,
                plano_conta_id=plano_id, fornecedor_id=rt.fornecedor_id,
                observacao=_observacao_de_divergencia(os_, resultado),   # D3: só quando os totais divergem
            ),
            usuario_token=usuario or {},
        )
        rt.conta_pagar_id = conta["id"]                              # D11
    registrar_evento(db, orc, "RT_CONTAS_CRIADAS", ..., os_id=os_.id)
```

- `criar_conta_pagar` devolve o dicionário serializado; o id vem dele.
- O valor de cada arquiteto também vai no evento, para o histórico mostrar "RT de R$ 588,82 para Studio Renascer".

### 6.3. Reabrir e cancelar

```python
def cancelar_pendentes_ao_reabrir(db, os_, usuario, contexto: dict | None = None) -> None:
    """D8: a obra voltou a estar aberta; o RT pendente sai e volta na próxima finalização."""
    for rt in _rts_com_conta(db, os_):
        if rt.conta_pagar.status == "PENDENTE":
            financeiro_service.cancelar_conta_pagar(db, _empresa_da_os(os_), rt.conta_pagar_id, usuario or {})


def tratar_cancelamento(db, os_, usuario, contexto: dict) -> None:
    """D10: só importa se a OS estava finalizada (só aí existe conta de RT)."""
    if contexto.get("status_anterior") != "FINALIZADA":           # Revisão 1: vem no contexto
        return
    orc = crud.orcamento_por_os(db, os_.id)                          # Revisão 1: faltava no trecho
    if orc is None:                                                  # OS que não veio de orçamento
        return
    cancelar_pendentes_ao_reabrir(db, os_, usuario)                 # mesma regra para as pendentes
    pagas = [rt for rt in _rts_com_conta(db, os_) if rt.conta_pagar.status == "PAGA"]
    if pagas:                                                        # a loja precisa saber
        registrar_evento(db, orc, "RT_PAGO_EM_OS_CANCELADA", _frase_pagas(pagas), os_id=os_.id)
```

### 6.4. CMV — `db/crud/relatorio_custo.py` ⚠️ (D12)

```python
        .where(
            and_(
                OrdemServicoItem.custo_unitario.isnot(None),
                OrdemServicoItem.produto_id.is_(None),
                # Item que veio de outro documento (ex.: orçamento de marcenaria) tem
                # o custo lançado pelos registros reais: baixa de estoque da OS,
                # contas pagas (RT, terceirizado) e salários. Somar o custo
                # declarado aqui contaria tudo de novo (SPEC-09A, F2a). O custo
                # declarado continua valendo para a comissão.
                OrdemServicoItem.origem.is_(None),
                # ...demais condições de hoje, sem mudança
```

Corrigir também a docstring de `get_custo_manual_os` com a terceira exclusão.

---

## 7. Prova de não regressão (⚠️ PR1)

1. Suíte inteira verde, incluindo testes de OS, financeiro e relatórios.
2. **Ganchos:** com as listas vazias (teste sem importar a marcenaria), finalizar, reabrir e cancelar OS dão exatamente o mesmo resultado de antes.
3. **Ganchos registrados, OS de informática:** finalização igual; nenhuma conta a pagar criada; uma consulta a mais por índice (medir: < 1 ms).
4. **CMV:** num banco copiado de cada loja em produção, `calcular_cmv` do mês atual e dos três anteriores é **idêntico** antes e depois (nenhum item tem `origem`).
5. **Comissão:** `get_comissao_base` não muda (o arquivo não é tocado).

## 8. Efeito no resultado do mês da marcenaria

Exemplo ilustrativo com um móvel (material e mão de obra da Torre Quente, **supondo-a produzida na fábrica**, e a parte dela no RT do cenário B), com a OS finalizada, o RT pago no mês e o material baixado (separação ou finalização):

| Parcela | Sem D12 | Com D12 |
|---------|---------|---------|
| Material (baixa da OS, peças embutidas) | 1.460,00 | 1.460,00 |
| Material (custo declarado no item do móvel) | 1.460,00 | — |
| RT (parte da linha, declarada no item) | 320,93 | — |
| RT (parte da linha na conta paga, despesa) | 320,93 | 320,93 |
| Mão de obra (custo declarado no item) | 300,00 | — |
| Salários (despesa) | (já no mês) | (já no mês) |

Sem D12, o mesmo móvel tiraria do lucro 2.080,93 a mais do que custou (Revisão 1: a versão anterior misturava a parte da Torre no material com o RT do orçamento inteiro, 739,11).

## 9. Limitações conhecidas

- **RT antecipado** ao arquiteto (antes da finalização): não previsto; quem pagar adiantado lança uma conta à mão e, na finalização, cancela a conta duplicada que o sistema criar.
- **Retenções e nota do arquiteto** (RPA, ISS): fora; o valor é bruto.
- **Divergência de total** (D3): o sistema avisa, mas não recalcula o RT.
- **Sem a Spec 10A**, o material entra no resultado mesmo assim: a finalização baixa as peças embutidas (F2b, regra de hoje da OS). A 10A muda **quando** ele sai do estoque (na separação), não **se** ele entra no resultado (Revisão 1).

## 10. Entrega (PR7)

`npm run build:sidecar`.

---

## 11. Critérios de aceite

- [ ] Finalizar a OS de um orçamento com um arquiteto de 8% cria uma conta pendente com o RT do aprovado, na categoria de RT, vencendo em 30 dias, com o fornecedor certo.
- [ ] Dois arquitetos (5% e 3%): duas contas cuja soma é o RT total.
- [ ] Reabrir cancela as pendentes; refinalizar recria; conta paga nunca é duplicada nem cancelada.
- [ ] Cancelar uma OS finalizada com RT pago registra o aviso no histórico.
- [ ] Total da OS diferente do aprovado: observação na conta e no evento; valor do RT sobre o aprovado.
- [ ] CMV ignora itens com origem; resultado das lojas atuais idêntico.
- [ ] Prazo do RT editável em Configurações (API) com a permissão de custos.
- [ ] Código comentado (PR6); suíte verde.

## 12. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Cenário B aprovado inteiro, RT 8%, finalizar | Uma conta de 73911 (Spec 05), `PENDENTE`, categoria de RT, vencimento hoje + 30 |
| 02 | RT 5% + 3% | Contas que somam o RT total; repartição pelo maior resto |
| 03 | Aprovação parcial | RT sobre o total aprovado |
| 04 | Orçamento sem arquiteto | Nenhuma conta; nenhum evento |
| 05 | Reabrir com a conta pendente | Conta `CANCELADA`; histórico da conta registra |
| 06 | Reabrir e refinalizar | Nova conta pendente; uma só ativa |
| 07 | Pagar a conta, reabrir, refinalizar | Conta paga intacta; nenhuma nova |
| 08 | Cancelar OS finalizada com conta paga | Evento `RT_PAGO_EM_OS_CANCELADA` |
| 09 | Cancelar OS não finalizada | Nada acontece com RT |
| 10 | Desconto alterado na finalização | Conta com o RT do aprovado e a observação de divergência |
| 11 | Dono renomeia a categoria; outra finalização | Usa a mesma categoria (pelo id) |
| 12 | Dono apaga a categoria; outra finalização | Cria de novo e guarda o novo id |
| 13 | Gancho que levanta exceção | Finalização desfeita inteira (rollback) |
| 14 | Listas de ganchos vazias | Finalizar/reabrir/cancelar iguais aos de antes (comparação de estado) |
| 15 | CMV com item `origem` e custo declarado | Custo do item fora do CMV; comissão continua usando o custo |
| 16 | CMV num banco de loja real, antes × depois | Idêntico |
| 17 | `PUT /configuracoes/marcenaria` com `rt_vencimento_dias = 200` | `422` com a mensagem |
| 18 | Loja sem o módulo Financeiro | Conta criada igual |


---

## Revisão 1 (08/10/2026) — pedidos da Spec 09B e convergência com a branch

1. **Conta de RT no detalhe do orçamento.** Com `view_custos`, cada linha de `arquitetos` no detalhe (06A §6.2) ganha `conta`: `{ "id", "status", "valor_centavos", "vencimento" }` da conta **atual** (`conta_pagar_id`, D11), ou `null` antes da finalização. No orçamento `APROVADO`, `valor_previsto_centavos` (06A Revisão 3) passa a ser calculado sobre o **aprovado** (`so_aprovados=True`), o mesmo número da conta que a finalização criará. Sem `view_custos`, nenhum dos dois sai.
2. **Gancho com contexto.** `GanchoOS` recebe um quarto argumento, `contexto` (dict). No cancelamento, `{"status_anterior": ...}`. Corrige a versão anterior, em que o tipo tinha 3 argumentos e `tratar_cancelamento` esperava 4, e em que `orc` não era definido.
3. **Caminhos.** O model e o schema da configuração são os da 04A: `app/db/models/configuracao_marcenaria.py` e `app/schemas/configuracao_marcenaria.py`.
4. **Migração** `195109da93f7`, filha de `971eb6cc5a33` (R15-MIG).
5. **CMV com peças embutidas (F2b).** A regra da D12 (`origem IS NULL` em `get_custo_manual_os`) tira do CMV o custo declarado dos itens de **serviço** do orçamento; as **peças embutidas** já ficavam de fora pelo filtro `produto_id IS NULL` e chegam ao CMV pelo livro de estoque. Nada mais muda na D12.
6. **Terceirizado (E6b).** D14 reescrita: com o Compras, a conta do recebimento sai sem categoria (= despesa); sem ele, a conta manual vai numa categoria `DESPESA`.

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 19 | Detalhe de orçamento aprovado, antes de finalizar, com `view_custos` | `arquitetos[0].conta = null`; `valor_previsto_centavos` sobre o aprovado |
| 20 | Depois de finalizar | `conta` com id, `PENDENTE`, valor e vencimento |
| 21 | Detalhe sem `view_custos` | Sem `conta` e sem `valor_previsto_centavos` |
| 22 | Cancelar OS finalizada: o gancho recebe `contexto["status_anterior"] == "FINALIZADA"` | D10 aplicada |
| 23 | Cancelar OS aberta | `contexto["status_anterior"] == "ABERTA"`; nada acontece com RT |
| 24 | CMV de uma OS aprovada com peças embutidas, finalizada sem separação | Material pelo livro (baixa na finalização); custo declarado dos móveis fora; peças embutidas fora de `get_custo_manual_os` |

