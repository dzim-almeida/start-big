# Spec 08A — Aprovação do Orçamento e Geração da OS (Backend)

| Campo        | Valor                                                                                    |
|--------------|------------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                          |
| Camada       | Backend (FastAPI) ⚠️ código compartilhado (serviço e itens da OS)                        |
| Dependências | Specs 03A (`origem_orcamento`), 05 (motor), 06A (orçamento, Revisões 1 e 2)              |
| Bloqueia     | Specs 08B, 09A, 10A, 11A, 12A, 13A, 14                                                   |
| Revisões     | 1 (06/10/2026): pedidos da Spec 08B · 2 (08/10/2026): insumos como peças embutidas e convergência com a branch (SPEC-00 Revisão 15) — ver o fim do documento |
| Referência   | SPEC-00: F2, F2b, F3, F4, F4a, O2, O4, O4a, O5, O7, O7a, O8, O8a, C3, C5, C5d, C5d+, C7, C9, E0a, E3b, FB1, R15-MIG · PR1, PR2, PR4, PR6, PR7, PR8 |

---

## 1. Objetivo

Transformar um orçamento aceito pelo cliente em **ordem de serviço**, sem digitar nada de novo:

1. O usuário escolhe **quais móveis** o cliente aprovou (O4) e se a instalação entra.
2. O sistema cria a OS com um **item de serviço por móvel** (F2), a instalação como item próprio (C3), os **insumos como peças embutidas** (F2b, Revisão 2), o desconto (C9), o responsável (O7), a previsão de entrega (O7) e o projeto (O5).
3. O sinal entra na OS **só se foi recebido** (§4.3, revisão de O7).
4. O orçamento fica **somente leitura** (F3), e os itens que vieram dele ficam **travados** na OS (F4).
5. Uma aprovação feita por engano pode ser **desfeita** enquanto a OS estiver aberta (O8).

## 2. Escopo

**Dentro do escopo**
- Simulação e aprovação (total ou parcial), criação da OS numa única transação.
- Coluna genérica `origem` nos itens da OS e a trava de edição (F4).
- Desfazer aprovação.
- Detalhe do orçamento aprovado (cálculo do que foi aprovado e dados da OS).
- Migração, testes, prova de não regressão da OS.

**Fora do escopo**
- Telas (Spec 08B).
- Conta a pagar do RT do arquiteto (Spec 09A; esta spec deixa o RT de cada linha no custo do item, C5d).
- Reserva e baixa de estoque, terceirizados, produção, entrega (Specs 10A–13A). Esta spec deixa o **ponto de extensão** para elas impedirem o "desfazer" (§7.6).
- Lançar o sinal no caixa: segue a regra de hoje do adiantamento da OS (§9).

---

## 3. Arquivos afetados

```
backend-fastapi/
├── alembic/versions/
│   └── 971eb6cc5a33_aprovacao_orcamento_marcenaria.py   # CRIAR — filha da 06A (683ff38df873; Revisão 2)
├── app/
│   ├── db/models/
│   │   ├── ordem_servico_item.py                        # ALTERAR ⚠️ — coluna `origem` (nula)
│   │   └── marcenaria/
│   │       ├── orcamento.py                             # ALTERAR — instalacao_aprovada, resumo aprovado
│   │       └── ambiente.py                              # ALTERAR — marcenaria_moveis.os_item_id
│   ├── schemas/
│   │   ├── ordem_servico.py                             # ALTERAR ⚠️ — `origem` em OSItemRead (só leitura)
│   │   └── marcenaria/aprovacao.py                      # CRIAR
│   ├── services/
│   │   ├── ordem_servico.py                             # ALTERAR ⚠️ — trava de item com origem
│   │   └── marcenaria/
│   │       ├── aprovacao.py                             # CRIAR — simular, aprovar, desfazer
│   │       ├── insumos_os.py                            # CRIAR — insumos aprovados → peças embutidas (Revisão 2)
│   │       └── orcamento_calculo.py                     # ALTERAR — instalação aprovada no `so_aprovados`
│   └── api/v1/endpoints/marcenaria_orcamento.py         # ALTERAR — 3 rotas
└── test/
    ├── services/marcenaria/test_aprovacao.py            # CRIAR
    ├── api/v1/marcenaria/test_aprovacao_api.py          # CRIAR
    └── services/test_os_item_origem.py                  # CRIAR — trava e não regressão
```

| Camada | Faz | Não faz |
|--------|-----|---------|
| `services/marcenaria/aprovacao.py` | Validar, chamar o motor com os aprovados, montar o `OrdemServicoCreate`, chamar `create_ordem_servico(..., origem_orcamento=True)`, gravar o vínculo e o histórico | Criar OS por SQL próprio (usa o serviço da OS) |
| `services/ordem_servico.py` | Recusar edição e remoção de item com `origem` | Saber o que é marcenaria |

---

## 4. Decisões

### 4.1. O que vira OS

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Cada móvel aprovado vira **um item `SERVICO` avulso** (sem `servico_id`): `nome` = "{móvel} — {ambiente}" (até 255), `unidade_medida = UN`, `quantidade` = quantidade do móvel, `valor_unitario` = `preco_unit_centavos`, `custo_unitario` = `custo_os_unit_centavos` (custo + parte do RT, C5d), `status_aprovacao = APROVADO`, `visivel_cliente = True`, `origem = "ORCAMENTO_MARCENARIA"` | F2. O ambiente no nome evita duas "Gaveteiro" iguais na OS. Item de serviço com custo declarado é o que a comissão já usa (C5) |
| D2 | A instalação aprovada vira um item `SERVICO` "Instalação e montagem", quantidade 1, `valor_unitario` = preço, `custo_unitario` = `custo_os_centavos` da instalação | C3: linha própria, não rateada |
| D3 | `desconto` da OS = desconto do motor **sobre os itens aprovados**. A OS confere: `valor_bruto` = bruto aprovado e `valor_total` = total aprovado. Se não bater, a aprovação é desfeita e responde `500` (nunca deve acontecer; teste de propriedade) | C9. O motor arredonda só no preço de cada móvel (C6), então a soma dos itens fecha com o bruto |
| D4 | Móvel aprovado com **preço zero** bloqueia a aprovação: `422` "O móvel {nome} está sem preço. Complete o móvel ou deixe-o de fora." | O item da OS exige valor maior que zero (`OSItemBase`); e móvel de graça é sinal de móvel incompleto |
| D5 | Campos da OS: `cliente_id` do orçamento; `funcionario_id` = vendedor (O7, **obrigatório para aprovar**); `prioridade = NORMAL`; `defeito_relatado` = "Móveis planejados conforme orçamento ORC-2026-000084 v2 — Residencial Alpha Ville - Apto 802" (até 500); `data_previsao` = data da aprovação + `prazo_entrega_dias` (O7); `dados_adicionais = {"tipo_trabalho": "planejados"}` (03A D9); `observacoes` = observações da proposta (cortadas em 500) | Nada para o usuário redigitar. O vendedor é quem recebe a comissão; sem ele a OS fica sem responsável |
| D6 | **Projeto (O5):** com `objeto_id`, a OS reaproveita o objeto (manda o `numero_serie` dele, `PRJ-…`, que o serviço da OS já reconhece) e atualiza nome e endereço da obra se mudaram. Sem `objeto_id`, cria o objeto com `modelo` = nome do projeto e `dados_adicionais.endereco_obra`; o código `PRJ-…` é gerado pelo serviço da OS como hoje. O `objeto_id` resultante é gravado no orçamento | O cliente que volta encontra o projeto (06B D21). Nada de criar objeto por fora do serviço da OS |
| D7 | O vínculo orçamento ↔ OS fica **só nas tabelas da marcenaria**: `marcenaria_orcamentos.os_id` e `marcenaria_moveis.os_item_id`. Nada vai para `dados_adicionais` da OS além do `tipo_trabalho` | O formulário da OS regrava `dados_adicionais` inteiro; um vínculo guardado ali podia sumir numa edição comum da OS |
| D8 | A OS nasce pelo **serviço existente** `create_ordem_servico(..., origem_orcamento=True)` (03A D7), na **mesma transação** que muda o orçamento e grava o histórico. Erro em qualquer passo desfaz tudo | PR2 (a OS é a de sempre). O serviço da OS só faz `flush`; o `commit` é do endpoint |

### 4.2. Aprovação parcial e valores

| # | Decisão | Motivo |
|---|---------|--------|
| D9 | O pedido traz `movel_ids` (pelo menos um) e `incluir_instalacao`. Móveis fora da lista ficam `aprovado = false` (histórico, O4) | O4 |
| D10 | Desconto e sinal são **recalculados sobre o aprovado** pelo motor (`so_aprovados=True`): em `PERCENTUAL`, o mesmo % sobre o novo total; em `VALOR`, o mesmo R$ (se passar do novo bruto, `422` do motor com `campo: "desconto"`) | O4: "o sinal é recalculado sobre o total aprovado". Desconto em R$ fixo pensado para o projeto inteiro pode não caber na parte aprovada; o usuário decide |
| D11 | O pedido pode trazer um **desconto novo** (`modo`, `valor`). Ele é gravado **no orçamento** (cabeçalho), na mesma transação, e registrado no evento | O cliente que aprova só a cozinha costuma renegociar o desconto. Gravar no orçamento mantém orçamento e OS concordando |
| D12 | `POST /aprovacao/simular` devolve os números do que **seria** aprovado (sem gravar), com o mesmo recorte de custos da 06A D23 | A tela (08B) mostra o total, o sinal e a margem antes do clique |
| D13 | Pode aprovar a partir de `RASCUNHO`, `ENVIADO` ou `VENCIDO`. De `RASCUNHO`, valem as exigências do envio (cliente, projeto, um móvel; 06A D13) e o envio é registrado junto (data de envio = agora, evento de envio). De `VENCIDO`, aprova normalmente (a tela pede confirmação) | O cliente que fecha na loja, na hora, não precisa de "enviar" antes. O que volta dois dias depois da validade também não deveria travar a venda |
| D14 | Só **uma versão** de um código pode estar `APROVADO` (O2). Como versões antigas ficam `SUBSTITUIDO`, a regra é conferida no serviço (consulta por código) e garante o caso raro de corrida | O2 |

### 4.3. Sinal (revisão de O7) ⚠️ a confirmar

| # | Decisão | Motivo |
|---|---------|--------|
| D15 | O pedido diz se o sinal **já foi recebido**: `sinal.recebido`. **Sim:** `valor_entrada` = valor informado (padrão: o sinal calculado; pode ser diferente, até o total) e `forma_pagamento_entrada_id` **obrigatória**, ou `usar_credito_cliente = true`. **Não:** `valor_entrada = 0`; o sinal combinado fica guardado no orçamento (`resumo_aprovado_sinal_centavos`) para a tela da OS mostrar "Sinal combinado R$ X — ainda não recebido", e é lançado depois pela edição de OS que já existe | `valor_entrada` na OS **é dinheiro recebido**: a finalização desconta ele do que o cliente paga. Gravar o sinal combinado como recebido faria o cliente pagar R$ 3.695 a menos na entrega se o PIX nunca chegou. O texto original de O7 ("`valor_entrada` = sinal") supunha o sinal pago na aprovação |
| D16 | `usar_credito_cliente` usa o mecanismo que já existe na criação da OS (baixa do `saldo_credito` do cliente) | É o caminho do sinal que voltou como crédito num "desfazer" (D20) |

### 4.4. Depois da aprovação

| # | Decisão | Motivo |
|---|---------|--------|
| D17 | Orçamento `APROVADO` é **somente leitura** (06A D11 já recusa escrita fora de `RASCUNHO`). Anexos seguem a 06A D31 (não em `APROVADO`) | F3 |
| D18 | **Trava de item (F4):** coluna nova e **genérica** `ordem_servico_itens.origem` (texto, nula). `update_item_os` e `remove_item_from_os` recusam item com `origem` preenchida: `409` "Este item veio do orçamento. Para mudar, desfaça a aprovação ou crie uma nova versão do orçamento." Itens adicionados à mão (origem nula) continuam editáveis | F4. Coluna genérica, sem a palavra marcenaria no serviço da OS: qualquer segmento futuro com orçamento técnico usa a mesma trava. Nula para todo item que já existe = comportamento de hoje |
| D19 | `OSItemRead` ganha `origem` (somente leitura; o `OSItemCreate` da API **não** aceita o campo) | A tela da OS (08B) mostra o cadeado; ninguém consegue criar item "travado" pela API |
| D20 | **Desfazer aprovação (O8):** só com a OS em `ABERTA`, sem pagamento registrado (`pagamentos` vazio) e sem nenhum bloqueio das specs seguintes (§7.6). Cancela a OS pelo serviço existente `cancelar_ordem_servico` (motivo "Aprovação desfeita no orçamento ORC-…: {motivo}"; **PIN do gerente** quando a loja exige para cancelar OS). O sinal recebido vira **crédito do cliente** (padrão) ou é marcado como **devolvido** (`zerar_adiantamento`), à escolha do usuário. O orçamento volta a `ENVIADO` (ou `VENCIDO`, pela regra preguiçosa), `aprovado` dos móveis volta a nulo, `os_id`/`os_item_id` são limpos; a OS cancelada fica no histórico | O8. Reaproveita as regras do cancelamento da OS, inclusive PIN e crédito. A escolha do sinal é a mesma pergunta que o cancelamento de OS já faz |
| D21 | OS **cancelada pela tela de OS** (sem passar pelo "desfazer", por exemplo depois de a produção começar): o orçamento continua `APROVADO`, o detalhe mostra a OS cancelada, e `acoes.nova_versao` passa a ser `true` | O cliente que desistiu no meio da produção cancela pela OS (onde estão as regras de dinheiro). Se ele voltar, o caminho é uma nova versão; o histórico da aprovação não é apagado |
| D22 | Permissão para aprovar e desfazer: `manage_orcamentos_marcenaria` (06A D22). O PIN do gerente, quando configurado, vale para o desfazer (é um cancelamento de OS) | Sem permissão nova; a proteção de cancelamento que a loja já escolheu continua valendo |
| D23 | Histórico (06A D25): `ORCAMENTO_APROVADO` (com `os_id`; dados: número da OS, móveis aprovados e recusados, instalação, total, desconto, sinal combinado e recebido) e `APROVACAO_DESFEITA` (motivo, número da OS, destino do sinal). Os dois eventos levam o `os_id` | T7. A OS nova e o orçamento contam a mesma história |

---

## 5. Modelo de dados

```sql
-- Genérica, na tabela da OS (⚠️ única tabela existente alterada; F1 tem esta exceção registrada na SPEC-00)
ALTER TABLE ordem_servico_itens ADD COLUMN origem VARCHAR(30);   -- NULL = item comum (todos os de hoje)

-- Marcenaria
ALTER TABLE marcenaria_moveis ADD COLUMN os_item_id INTEGER REFERENCES ordem_servico_itens(id) ON DELETE SET NULL;
ALTER TABLE marcenaria_orcamentos ADD COLUMN instalacao_aprovada BOOLEAN;           -- NULL até aprovar
ALTER TABLE marcenaria_orcamentos ADD COLUMN resumo_aprovado_total_centavos INTEGER;
ALTER TABLE marcenaria_orcamentos ADD COLUMN resumo_aprovado_sinal_centavos INTEGER; -- sinal combinado (D15)
ALTER TABLE marcenaria_orcamentos ADD COLUMN sinal_recebido_centavos INTEGER;        -- o que entrou na OS
CREATE INDEX ix_marcenaria_moveis_os_item ON marcenaria_moveis (os_item_id);
CREATE INDEX ix_marcenaria_orcamentos_os ON marcenaria_orcamentos (os_id);
```

- `os_id`, `data_aprovacao` e `aprovado` (móvel) já existem desde a 06A.
- Na lista (06A §6.3), um orçamento `APROVADO` mostra `resumo_aprovado_total_centavos` como total.

### 5.1. Migração (PR8)

`971eb6cc5a33_aprovacao_orcamento_marcenaria.py`, filha de `683ff38df873` (Revisão 2, R15-MIG):

- Para **cada** coluna: `ADD COLUMN` **só se a coluna não existir** (inspeção do schema), porque o `create_all()` do startup não altera tabela existente, mas pode ter criado as tabelas da marcenaria já com as colunas novas numa instalação nova.
- `ADD COLUMN` direto (SQLite aceita coluna nula sem valor padrão), sem `batch_alter_table`: a tabela de itens da OS é grande nas lojas antigas, e o `batch` a recriaria inteira.
- `downgrade`: remove índices e colunas da marcenaria; a coluna `origem` sai com `batch_alter_table` (o único caminho no SQLite).

---

## 6. Contrato da API

Prefixo `/api/v1/marcenaria/orcamentos`. Todas com a capacidade (06A D26), permissão `manage` e `?revisao=N` (06A D20).

### 6.1. Rotas

| Método e rota | O que faz |
|---------------|-----------|
| `POST /{id}/aprovacao/simular` | D12: números do que seria aprovado. Não grava |
| `POST /{id}/aprovar` | D9–D16: cria a OS e aprova. Responde o **detalhe** (06A §6.2) com `os` preenchido |
| `POST /{id}/desfazer-aprovacao` | D20. Responde o detalhe |

### 6.2. Simular e aprovar (entrada)

```jsonc
{
  "movel_ids": [10, 11, 14],                     // pelo menos um (D9)
  "incluir_instalacao": true,
  "desconto": { "modo": "PERCENTUAL", "valor": 500 },   // opcional (D11); ausente = o do orçamento
  "sinal": {                                     // só no /aprovar
    "recebido": true,                            // D15
    "valor_centavos": 369556,                    // padrão na tela: o sinal calculado
    "forma_pagamento_id": 2,                     // obrigatória se recebido e sem crédito
    "usar_credito_cliente": false                // D16
  }
}
```

### 6.3. Simular (saída)

```jsonc
{
  "moveis_aprovados": 3, "moveis_recusados": 4,
  "bruto_centavos": 830015, "desconto_centavos": 41501, "total_centavos": 788514,
  "sinal_centavos": 315406, "saldo_centavos": 473108,
  "credito_cliente_centavos": 0,                   // para a tela oferecer o uso do crédito (D16)
  "previsao_entrega": "2026-11-05",                // hoje + prazo (D5)
  "avisos": ["MOVEL_SEM_PRECO"],                   // D4, além dos avisos do motor
  // só com view_custos (06A D23):
  "custo_total_centavos": 436850, "rt_total_centavos": 63081, "margem_liquida_centavos": 288583, "margem_liquida_bp": 3660
}
```

### 6.4. Detalhe do orçamento aprovado (acréscimos à 06A §6.2)

```jsonc
{
  "status": "APROVADO",
  "aprovacao": {
    "data": "2026-10-06T18:40:00", "instalacao_aprovada": true,
    "total_centavos": 788514, "sinal_combinado_centavos": 315406, "sinal_recebido_centavos": 315406,
    "calculo": { /* mesmo formato de "calculo", só com os aprovados; com o recorte de custos */ }
  },
  "os": { "id": 512, "numero_os": "OS-2026-000512", "status": "ABERTA" },
  "ambientes": [ { "moveis": [ { "id": 10, "aprovado": true, "os_item_id": 3301 /* … */ } ] } ],
  "acoes": { "desfazer_aprovacao": true, "nova_versao": false /* D21 */ }
}
```

- `calculo` (do orçamento inteiro, como foi proposto) continua no detalhe; `aprovacao.calculo` é o que virou OS.
- `acoes.aprovar`: `true` em `RASCUNHO`, `ENVIADO`, `VENCIDO` com permissão. `acoes.desfazer_aprovacao`: `true` só quando D20 permitiria (a tela não oferece o que vai falhar).

### 6.5. Desfazer (entrada)

```jsonc
{ "motivo": "Aprovado no orçamento errado", "destino_sinal": "CREDITO", "codigo_gerente": "1234" }
// destino_sinal: "CREDITO" (padrão) | "DEVOLVIDO"; codigo_gerente só quando a loja exige PIN para cancelar OS
```

### 6.6. Erros

| Status | `detail` | Quando |
|--------|----------|--------|
| `409` | `{codigo: "TRANSICAO_INVALIDA"}` | Aprovar fora de `RASCUNHO`/`ENVIADO`/`VENCIDO`; desfazer fora de `APROVADO` |
| `409` | `{codigo: "REVISAO_DESATUALIZADA"}` | 06A D20 |
| `409` | `{codigo: "VERSAO_JA_APROVADA", mensagem: "A versão {n} deste orçamento já foi aprovada."}` | D14 |
| `409` | `{codigo: "DESFAZER_BLOQUEADO", mensagem: "...", motivos: ["A OS já não está aberta.", ...]}` | D20 e §7.6 (lista **todos** os motivos) |
| `400` | `REQUER_APROVACAO_GERENTE` / `PIN_GERENTE_INVALIDO` | Mesmas respostas do cancelamento de OS (D20) |
| `422` | "Escolha pelo menos um móvel." | D9 |
| `422` | "Informe o vendedor do orçamento antes de aprovar." | D5 |
| `422` | "O móvel {nome} está sem preço. Complete o móvel ou deixe-o de fora." | D4 |
| `422` | "Para aprovar, informe o cliente, o nome do projeto e pelo menos um móvel." | D13 (de `RASCUNHO`) |
| `422` | "Informe a forma de pagamento do sinal." / "O sinal não pode ser maior que o total aprovado." | D15 |
| `422` | `{codigo: "CALCULO_INVALIDO", campo: "desconto", ...}` | D10 |
| `409` | Mensagem do serviço da OS ("Saldo de crédito insuficiente…") | D16 |
| `409` | "Este item veio do orçamento. Para mudar, desfaça a aprovação ou crie uma nova versão do orçamento." | D18, nas rotas de **item da OS** |

---

## 7. Especificação técnica

### 7.1. Aprovar — `services/marcenaria/aprovacao.py`

```python
def aprovar(db: Session, orcamento_id: int, revisao: int, dados: AprovacaoEntrada, usuario: dict) -> OrcamentoModel:
    """Aprova o orçamento (todo ou em parte) e cria a OS. Uma transação; o commit é do endpoint."""
    orc = _carregar_para_escrita(db, orcamento_id, revisao)         # 404, trava otimista (06A D20)
    _assert_pode_aprovar(db, orc)                                    # status (D13), versão (D14), vendedor (D5)
    if orc.status == "RASCUNHO":
        _registrar_envio_implicito(db, orc, usuario)                 # D13: exige o mesmo que /enviar

    if dados.desconto is not None:                                   # D11: renegociado na aprovação
        orc.desconto_modo, orc.desconto_valor = dados.desconto.modo, dados.desconto.valor

    _marcar_aprovados(orc, dados.movel_ids, dados.incluir_instalacao) # D9: true/false em cada móvel
    resultado = motor.calcular(montar_entrada_motor(orc, so_aprovados=True))  # D10 (ValueError -> 422)
    _assert_sem_movel_sem_preco(orc, resultado)                      # D4
    sinal = _resolver_sinal(dados.sinal, resultado)                  # D15: (valor_entrada, forma, usar_credito)

    os_criada = os_service.create_ordem_servico(                     # D8: o serviço de sempre
        db,
        _montar_os(orc, resultado, sinal),                           # D1, D2, D3, D5, D6
        origem_orcamento=True,                                       # 03A D7: caminho legítimo
    )
    _assert_valores_conferem(os_criada, resultado)                   # D3: bruto e total iguais ao motor
    _gravar_vinculos(orc, os_criada)                                 # D7: os_id, os_item_id, objeto_id

    orc.status = "APROVADO"
    orc.data_aprovacao = agora_utc()
    orc.resumo_aprovado_total_centavos = resultado.total_centavos
    orc.resumo_aprovado_sinal_centavos = resultado.sinal_centavos    # combinado
    orc.sinal_recebido_centavos = sinal.valor_entrada                # 0 quando ainda não recebido
    orc.revisao += 1
    registrar_evento(db, orc, "ORCAMENTO_APROVADO", _frase_aprovacao(os_criada, resultado), # D23
                     dados=_dados_evento(orc, os_criada, resultado, sinal), os_id=os_criada.id, usuario=usuario)
    return orc
```

### 7.2. Montar a OS

```python
def _montar_os(orc, resultado: OrcamentoResultado, sinal: SinalResolvido) -> OrdemServicoCreate:
    """Traduz o orçamento aprovado para o payload que o serviço da OS já conhece."""
    itens = [
        OSItemCreate(
            tipo=OrdemServicoItemTipo.SERVICO,                       # comissão sobre a margem (C5)
            nome=_nome_item(movel.nome, ambiente.nome),              # "Torre Quente — Cozinha Gourmet"
            unidade_medida=UnidadeMedida.UNIDADE,
            quantidade=movel.quantidade,
            valor_unitario=calc.preco_unit_centavos,                 # preço de venda (F2)
            custo_unitario=calc.custo_os_unit_centavos,              # custo + parte do RT (C5d, C5d+)
        )
        for ambiente, movel, calc in _aprovados_com_calculo(orc, resultado)
    ]
    if resultado.instalacao is not None:                             # D2
        itens.append(OSItemCreate(tipo=OrdemServicoItemTipo.SERVICO, nome="Instalação e montagem",
                                  unidade_medida=UnidadeMedida.UNIDADE, quantidade=1,
                                  valor_unitario=resultado.instalacao.preco_centavos,
                                  custo_unitario=resultado.instalacao.custo_os_centavos))
    return OrdemServicoCreate(
        cliente_id=orc.cliente_id,
        funcionario_id=orc.funcionario_id,                           # responsável = vendedor (O7)
        prioridade=OrdemServicoPrioridade.NORMAL,
        defeito_relatado=_descricao_os(orc),                         # D5, até 500
        observacoes=(orc.observacoes_proposta or "")[:500] or None,
        dados_adicionais={"tipo_trabalho": "planejados"},            # 03A D9; nada de vínculo aqui (D7)
        objeto=_objeto_do_projeto(orc),                              # D6
        itens=itens,
        desconto=resultado.desconto_centavos,                        # C9
        valor_entrada=sinal.valor_entrada,                           # D15: só o que foi recebido
        forma_pagamento_entrada_id=sinal.forma_pagamento_id,
        usar_credito_cliente=sinal.usar_credito,                     # D16
        data_previsao=_previsao(orc.prazo_entrega_dias),             # O7
    )
```

- O `origem` **não** está no `OSItemCreate` (D19). Depois do `create_ordem_servico`, `_gravar_vinculos` preenche `item.origem = "ORCAMENTO_MARCENARIA"` nos itens criados (na mesma transação) e o `os_item_id` de cada móvel, pela ordem da lista.
- `_nome_item` corta o nome do móvel para caber "— {ambiente}" em 255 caracteres.

### 7.3. Trava de item — `services/ordem_servico.py` ⚠️

```python
item_de_outro_documento_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Este item veio do orçamento. Para mudar, desfaça a aprovação ou crie uma nova versão do orçamento.",
)

def _assert_item_sem_origem(item: OSItemModel) -> None:
    """Item criado a partir de outro documento (ex.: orçamento técnico) não se edita pela OS (F4).

    Genérico de propósito: o serviço da OS não sabe o que é marcenaria. Item com
    origem nula (todos os itens que existem hoje) passa direto.
    """
    if item.origem:
        raise item_de_outro_documento_exce
```

Chamado em `update_item_os` e `remove_item_from_os`, **depois** de achar o item e conferir que ele é da OS. Nada mais muda no serviço da OS.

### 7.4. Simular

Mesmos passos de `aprovar` até o motor (sem `_registrar_envio_implicito`, sem gravar), mais `credito_cliente_centavos` (saldo do cliente) e `previsao_entrega`. Sem `revisao` (não grava). `db.rollback()` no fim por segurança (o `_marcar_aprovados` mexeu nos objetos em memória).

### 7.5. Desfazer — `desfazer_aprovacao`

```python
def desfazer_aprovacao(db, orcamento_id, revisao, dados: DesfazerEntrada, usuario) -> OrcamentoModel:
    orc = _carregar_para_escrita(db, orcamento_id, revisao)
    motivos = motivos_que_impedem_desfazer(db, orc)                  # §7.6: lista, não o primeiro
    if motivos:
        raise HTTPException(409, detail={"codigo": "DESFAZER_BLOQUEADO",
                                         "mensagem": "Não é possível desfazer a aprovação.",
                                         "motivos": motivos})
    os_ = orc.os
    for item in os_.itens:                                           # libera a trava (D18) para o cancelamento
        item.origem = None                                           # e para o histórico da OS cancelada
    os_service.cancelar_ordem_servico(                               # D20: regras de sempre, inclusive PIN
        db, os_.numero_os,
        OrdemServicoCancelar(motivo=f"Aprovação desfeita no orçamento {orc.codigo}: {dados.motivo}",
                             zerar_adiantamento=(dados.destino_sinal == "DEVOLVIDO"),
                             codigo_gerente=dados.codigo_gerente),
        usuario_token=usuario,
    )
    for movel in _todos_os_moveis(orc):
        movel.aprovado, movel.os_item_id = None, None
    orc.status, orc.os_id, orc.data_aprovacao = "ENVIADO", None, None
    orc.instalacao_aprovada = None
    orc.resumo_aprovado_total_centavos = orc.resumo_aprovado_sinal_centavos = orc.sinal_recebido_centavos = None
    orc.revisao += 1
    registrar_evento(db, orc, "APROVACAO_DESFEITA", ..., os_id=os_.id, usuario=usuario)   # D23
    marcar_vencidos(db)                                              # se a validade já passou: VENCIDO (06A D14)
    return orc
```

> Limpar `origem` antes de cancelar é **opcional** para o cancelamento (ele não edita itens), mas mantém a regra simples: OS cancelada não tem item travado. ⚠️ Conferir na implementação se a tela da OS cancelada deve continuar mostrando o cadeado; se sim, não limpar.

### 7.6. Ponto de extensão do "desfazer"

```python
# Cada spec seguinte registra uma função que devolve os motivos que ELA conhece.
BLOQUEIOS_DESFAZER: list[Callable[[Session, OrcamentoModel], list[str]]] = [
    _bloqueio_status_da_os,          # 08A: "A OS já não está aberta (status: Em Produção)."
    _bloqueio_pagamentos_da_os,      # 08A: "A OS já tem pagamento registrado."
    # 10A: "Já há material separado/baixado para esta OS."
    # 11A: "Há pedido enviado à central parceira."
    # 12A: "A produção já começou (etapas concluídas)."
    # 13A: "Há termo de entrega registrado."
]

def motivos_que_impedem_desfazer(db, orc) -> list[str]:
    """Todos os motivos, para a tela explicar de uma vez (não o primeiro que falhar)."""
    if orc.status != "APROVADO" or orc.os is None:
        return ["O orçamento não está aprovado."]
    return [motivo for regra in BLOQUEIOS_DESFAZER for motivo in regra(db, orc)]
```

`acoes.desfazer_aprovacao` = `motivos_que_impedem_desfazer(...) == []` e permissão.

### 7.7. Cálculo dos aprovados — `orcamento_calculo.py`

`montar_entrada_motor(orc, so_aprovados=True)` (06A §7.2) passa a considerar também `instalacao_aprovada`: com `so_aprovados` e `instalacao_aprovada` falso, a instalação não entra.

---

## 8. Prova de não regressão (⚠️ PR1)

1. Suíte inteira verde, incluindo todos os testes de OS existentes.
2. Em informática, oficina e serigrafia: criar OS, editar item, remover item, finalizar, cancelar, reabrir — mesmas respostas de antes (os itens existentes têm `origem` nula).
3. `GET` de OS: o único campo novo em cada item é `origem: null`.
4. `POST` de item de OS com `"origem": "X"` no corpo: o campo é ignorado (o item nasce sem origem e continua editável).
5. Migração aplicada num banco copiado de uma loja real (as 3 em produção): nenhuma linha muda; `ordem_servico_itens` não é recriada.
6. Comissão e lucro do mês das lojas atuais: mesmos números (nenhum item delas tem origem; a fórmula não muda).

## 9. Limitações conhecidas

- **Sinal fora do caixa:** como todo adiantamento de OS hoje, o sinal recebido na aprovação não entra no fechamento de caixa (comentário em `sessao_caixa.registrar_pagamentos_de_os`). A marcenaria herda a lacuna; não é escopo daqui.
- **Comissão sobre o desconto:** a base da comissão da OS soma `valor_total − qtd × custo` **dos itens** e ignora o desconto da OS, embora a docstring de `get_comissao` diga que a base é pós-desconto. Com o desconto global da marcenaria (C9), o vendedor recebe comissão sobre o desconto que deu. **Afeta todos os segmentos** e foi registrado como **PEND-002** em `docs/pendencias-sistema.md`.
- **Numeração da OS sem nova tentativa** (06A §8): duas OS criadas no mesmo instante (uma pela aprovação, outra à mão) podem disputar o número.
- **OS alterada depois da aprovação:** desconto, taxa de entrega e itens manuais podem mudar o total da OS. O orçamento guarda o que foi aprovado; a tela (08B) mostra os dois totais quando forem diferentes.
- **RT na OS:** fica no custo dos itens (C5d); a conta a pagar ao arquiteto é da 09A.

## 10. Entrega (PR7)

`npm run build:sidecar` (backend e migração novos). Teste de atualização: instalar sobre uma loja com banco existente e conferir a migração (§8.5).

---

## 11. Critérios de aceite

- [ ] Aprovar todos os móveis cria a OS com um item por móvel, a instalação, o desconto, o vendedor como responsável, a previsão e o projeto; bruto e total da OS iguais aos do motor.
- [ ] Aprovação parcial: só os móveis escolhidos viram itens; desconto em % e sinal recalculados; os recusados ficam `aprovado = false`.
- [ ] Sinal recebido entra como adiantamento com a forma de pagamento; sinal não recebido deixa `valor_entrada = 0` e o combinado guardado.
- [ ] Itens que vieram do orçamento não podem ser editados nem removidos pela OS; itens manuais podem.
- [ ] Desfazer cancela a OS (com PIN quando a loja exige), devolve o sinal como crédito ou o marca devolvido, e volta o orçamento a `ENVIADO`.
- [ ] Desfazer com a OS fora de `ABERTA` responde com todos os motivos.
- [ ] Aprovar de `RASCUNHO` registra o envio junto; de `VENCIDO`, aprova.
- [ ] Nada muda para as OS dos outros segmentos (§8).
- [ ] Código comentado (PR6); suíte verde.

## 12. Casos de teste

### Serviço

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Cenário B da Spec 05, todos os móveis + instalação, sinal recebido em PIX | OS `ABERTA`; itens = móveis + instalação; `valor_bruto` 972515, `desconto` 48626, `valor_total` 923889; `valor_entrada` 369556; `forma_pagamento_entrada_id` do PIX |
| 02 | Mesmo cenário, sinal **não** recebido | `valor_entrada` 0; `resumo_aprovado_sinal_centavos` 369556 |
| 03 | Aprovar só a Torre Quente, sem instalação, desconto 5% | 1 item; desconto e total recalculados; demais móveis `aprovado = false` |
| 04 | Desconto `VALOR` maior que o bruto aprovado | `422` `CALCULO_INVALIDO`, `campo: "desconto"`; nada gravado; nenhuma OS |
| 05 | Desconto novo no pedido | Gravado no cabeçalho do orçamento e no evento |
| 06 | Item da OS: `custo_unitario` | `custo_os_unit_centavos` do motor (custo + RT por unidade, arredondado para baixo) |
| 07 | Projeto existente (`objeto_id`) | A OS usa o mesmo objeto; nenhum objeto novo |
| 08 | Projeto novo | Objeto com `PRJ-…`; `objeto_id` gravado no orçamento |
| 09 | Sem vendedor | `422` (D5) |
| 10 | Móvel aprovado com preço 0 | `422` (D4); nada gravado |
| 11 | Aprovar de `RASCUNHO` completo | Eventos de envio e de aprovação; `data_envio` preenchida |
| 12 | Aprovar de `RASCUNHO` sem cliente | `422` do envio |
| 13 | Falha simulada no meio (exceção depois de criar a OS) | Rollback: nenhuma OS, orçamento intacto |
| 14 | `update_item_os` / `remove_item_from_os` num item com origem | `409` (D18) |
| 15 | Mesmo, num item manual da mesma OS | Funciona |
| 16 | Desfazer com OS `ABERTA`, sinal recebido, destino `CREDITO` | OS `CANCELADA`; `saldo_credito` do cliente +369556; orçamento `ENVIADO`; vínculos limpos |
| 17 | Desfazer, destino `DEVOLVIDO` | `valor_entrada` zerado; saldo do cliente igual |
| 18 | Desfazer com OS `EM_ANDAMENTO` | `409` `DESFAZER_BLOQUEADO` com o motivo do status |
| 19 | Desfazer com PIN exigido e sem código | `400 REQUER_APROVACAO_GERENTE`; nada muda |
| 20 | Desfazer depois da validade | Orçamento `VENCIDO` |
| 21 | Reaprovar depois de desfazer, usando o crédito | Nova OS; `saldo_credito` volta ao anterior |
| 22 | OS cancelada pela tela de OS | Orçamento `APROVADO`; `acoes.nova_versao = true` |
| 23 | Propriedade: 200 orçamentos aleatórios aprovados (parcial e total) | Bruto e total da OS sempre iguais ao motor |

### API

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 24 | `simular` sem `view_custos` | Sem custo, RT e margem; com total, sinal, saldo, previsão |
| 25 | `aprovar` com `revisao` antiga | `409 REVISAO_DESATUALIZADA` |
| 26 | Duas versões: aprovar a v1 já `SUBSTITUIDO` | `409 TRANSICAO_INVALIDA` |
| 27 | Segmento serigrafia | `404` |
| 28 | `GET /ordens-servico/{n}` de uma OS da informática | Itens com `origem: null`; resto igual |
| 29 | `POST` de item de OS com `origem` no corpo | Ignorado |
| 30 | `PATCH` de item com origem pela rota da OS | `409` com a mensagem do D18 |


---

## Revisão 1 (06/10/2026) — pedidos da tela (Spec 08B)

1. **Resumo do orçamento a partir da OS.** `GET /api/v1/marcenaria/orcamentos/por-os/{numero_os}` (rota estática, antes de `/{id}`), para a aba "Orçamento" da OS:

```jsonc
{
  "orcamento_id": 84, "codigo": "ORC-2026-000084", "versao": 2, "status": "APROVADO",
  "data_aprovacao": "2026-10-06T18:40:00", "aprovado_por": "Alan Alves de Amorim",
  "projeto": "Residencial Alpha Ville - Apto 802",
  "moveis": [ { "nome": "Torre Quente", "ambiente": "Cozinha Gourmet", "quantidade": 1,
                "medidas": { "largura_mm": 700, "altura_mm": 2200, "profundidade_mm": 600 },
                "os_item_id": 3301 } ],
  "moveis_nao_aprovados": 4,
  "instalacao_aprovada": true,
  "total_aprovado_centavos": 788514,
  "sinal_combinado_centavos": 315406, "sinal_recebido_centavos": 0,
  "pode_desfazer": true, "motivos_desfazer": []
}
```

   - Permissão: `view_orcamentos_marcenaria` **ou** a permissão de OS (`servico`), porque quem trabalha na OS precisa saber o que foi vendido. **Nunca** traz custo, margem ou RT (vale para todos).
   - `404` quando a OS não veio de um orçamento (ou o segmento não tem a capacidade).
   - `sinal_recebido_centavos` lido da **OS** (`valor_entrada` atual), não do que foi gravado na aprovação: o sinal lançado depois na OS aparece aqui.

2. **Lista:** o item da lista (06A §6.3) ganha `os_numero` quando o orçamento está `APROVADO`.

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 31 | `por-os` de uma OS da aprovação, cargo só com `servico` | `200`, sem nenhuma chave de custo |
| 32 | `por-os` de uma OS sem orçamento | `404` |
| 33 | Lançar o adiantamento na OS depois | `por-os` mostra o novo `sinal_recebido_centavos` |


---

## Revisão 2 (08/10/2026) — insumos como peças embutidas e convergência com a branch

Motivo: SPEC-00 Revisão 15 (F2b, E3b, FB1, FB2, R15-MIG). O Compras (reserva, Necessidades, "Compras desta OS") enxerga material pelos **itens de produto** da OS; a OS já tem a forma de **peça embutida** (item `PRODUTO`, `valor_unitario = 0`, `visivel_cliente = false`, aceita por `OSItemBase`); e a finalização já baixa só `quantidade − quantidade_separada`. Então os insumos aprovados passam a entrar na OS assim, e a separação (10A) trabalha sobre eles.

### R2.1. Peças embutidas na aprovação (D1a, novo)

| # | Decisão | Motivo |
|---|---------|--------|
| D1a | Além dos itens de serviço (D1, D2), a aprovação cria **um item `PRODUTO` por produto** usado pelos insumos dos móveis **aprovados** de produção **`INTERNA`**: `produto_id`; `nome` = a descrição copiada do primeiro insumo desse produto (até 255); `unidade_medida` = a do produto convertida para o enum (`UnidadeMedida(...)`; texto fora do enum vira `OUTROS`, como o `_unidade_do_item` da fábrica fazia); `quantidade` = o **sugerido** (abaixo); `valor_unitario = 0`; `visivel_cliente = false`; `custo_unitario` = média dos custos copiados desse produto, ponderada pelo planejado de cada insumo (centavos, `ROUND_HALF_UP`); `status_aprovacao = APROVADO`. Depois do `create_ordem_servico`, recebe `origem = "ORCAMENTO_MARCENARIA"` como os demais (D19) | F2b. O cliente não vê nem paga (o motivo de F2); o total e a comissão não mudam (comissão só conta serviço); o Compras e a finalização passam a enxergar o material sem código novo |
| D1b | **Planejado** de um produto = Σ (`quantidade_milesimos` do insumo × `quantidade` do móvel × (10000 + `perda_bp`, só se `sofre_perda` copiado) ÷ 10000), em milésimos, `ROUND_HALF_UP` uma vez no total do produto. **Sugerido** = o planejado arredondado **para cima** até a unidade inteira, exceto nas unidades de `UNIDADES_FRACIONAVEIS` (`app/services/quantidade_venda.py`: KG, G, L, ML, M, CM, M2, M3), em que o sugerido é o próprio planejado | E3a/E3b: arredondar **uma vez** por produto (1,4 + 1,2 + 0,6 chapa → 4, e não 5). A lista de unidades é a que o sistema já usa na venda fracionada |
| D1c | Insumo sem `produto_id` (o produto foi excluído depois da cópia) **não** vira item: não há estoque para baixar. A separação o mostra como linha informativa (10A) | Item de produto sem produto não baixa nada e confundiria o Compras |
| D1d | Móvel `TERCEIRIZADA`: seus insumos **não** viram peças embutidas | O material é da central (10A D4, E6) |
| D1e | Ordem dos itens na OS: os móveis (por ambiente e ordem), a instalação, e por fim as peças embutidas (por localização do produto, depois nome) | A tela da OS mostra primeiro o que o cliente comprou |

O cálculo de D1b fica numa função pura em `services/marcenaria/insumos_os.py`, usada aqui e pela 10A (o "reabrir" da separação volta a `quantidade` ao sugerido):

```python
@dataclass(frozen=True)
class InsumoDaOS:
    produto_id: int
    nome: str                     # descrição copiada do primeiro insumo do produto
    unidade: str                  # unidade do produto, como texto (UN, CH, M, M2...)
    planejado_milesimos: int      # D1b, já com a perda
    sugerido_milesimos: int       # D1b, arredondado para cima nas unidades inteiras
    custo_unitario_centavos: int  # média ponderada dos custos copiados
    moveis: tuple[tuple[str, str, int], ...]   # (móvel, ambiente, planejado em milésimos) — para a 10A


def insumos_da_os(orc: OrcamentoModel, unidades: dict[int, str]) -> list[InsumoDaOS]:
    """Um por produto: só móveis APROVADOS e INTERNA; perda só onde `sofre_perda` (D1a–D1d).

    `unidades` = {produto_id: unidade_medida} lido do cadastro (uma consulta só).
    Inteiros e Decimal; nenhum float (PR4).
    """
    ...
```

`quantidade` do item da OS = `sugerido_milesimos / 1000` (o item da OS é `Float`, como o estoque).

### R2.2. Trava e desfazer

- **Trava de item (D18):** a verificação de `origem` entra **ao lado** da trava que já existe para a fábrica (`_assert_item_nao_gerado_pela_fabrica`, chamada em `update_item_os` e `remove_item_from_os`), nas mesmas duas chamadas. A da fábrica fica como está (inerte, FB1).
- **Desfazer (§7.6):** a Spec 10A acrescenta o bloqueio "Já há material retirado do estoque para esta OS." quando alguma peça embutida tem `quantidade_separada > 0`. Sem retirada, o cancelamento da OS não mexe em estoque (a OS aberta nunca baixou nada; e a devolução automática da fábrica só vale para OS com `fase_fabrica`, Spec 03A D15).
- **Ganchos da fábrica:** a OS criada aqui tem `fase_fabrica` nula (03A D13), então nenhuma regra do trilho se aplica a ela.

### R2.3. Correções

- Migração `971eb6cc5a33`, filha de `683ff38df873` (R15-MIG).
- Exemplo da §6.3: o custo da Cozinha Gourmet é **R$ 4.368,50** (222.250 + 2 × 107.300); com ele, margem líquida **R$ 2.885,83** (3.660 bp). O exemplo antigo usava 4.443,50.

### R2.4. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 34 | Cenário B, todos os móveis (Torre terceirizada, 2 Balcões internos) | Peças embutidas só dos Balcões: MDF Branco TX (planejado 2.200, sugerido 3.000 → `quantidade` 3) e Corrediça Tandem (planejado 6.000, sugerido 6.000) |
| 35 | Os mesmos itens | `valor_unitario = 0`, `visivel_cliente = false`, `origem = "ORCAMENTO_MARCENARIA"`, `status_aprovacao = APROVADO` |
| 36 | `valor_bruto` e `valor_total` da OS | Iguais aos do caso 01 (as peças embutidas somam zero) |
| 37 | MDF em 3 móveis internos (1,4 / 1,2 / 0,6, sem perda) | Uma peça embutida, `quantidade` 4 (e não 5) |
| 38 | Fita de borda em `M`, 26,35 m | `quantidade` 26,35 (sem arredondar) |
| 39 | Produto de unidade `CH` (fora do enum) | `unidade_medida = OUTROS`; quantidade arredondada para cima |
| 40 | Insumo cujo produto foi excluído | Nenhum item para ele; aprovação segue |
| 41 | `compras.demanda_os.demandas_por_produto` depois de aprovar | O MDF aparece com a quantidade da peça embutida, `pode_comprar = True` |
| 42 | `update_item_os` numa peça embutida | `409` (D18) |
| 43 | Finalizar a OS sem separar nada | O livro de estoque baixa as peças embutidas (regra de hoje); o CMV do mês as conta |
| 44 | Desfazer sem retirada | OS cancelada; nenhuma movimentação de estoque |

