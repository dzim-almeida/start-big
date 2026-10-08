# Spec 11A — Móveis Terceirizados (Backend)

| Campo        | Valor                                                                                 |
|--------------|---------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                       |
| Camada       | Backend (FastAPI)                                                                     |
| Dependências | Specs 06A (móvel `TERCEIRIZADA`, central), 08A (aprovação, bloqueios do desfazer), 09A (ganchos, F2a, regra D14) |
| Bloqueia     | Specs 11B, 12A (o terceirizado conta como pronto quando conferido)                    |
| Referência   | SPEC-00: E6, E6a, F2a, C5a, P4, O8, T7 · PR1, PR4, PR6, PR7, PR8 |

---

## 1. Objetivo

Acompanhar o móvel que a marcenaria **não produz**: ela compra pronto de uma **central parceira** (um fornecedor, E6) e só instala.

1. Registrar o **pedido** à central (número, data, previsão de chegada), para um ou vários móveis de uma vez.
2. Marcar o **recebimento** e a **conferência**, com o registro de problema quando o móvel chega com defeito.
3. **Oferecer** o lançamento da conta a pagar da central no recebimento, com o valor editável (E6: a nota às vezes muda) e na categoria certa (09A D14).
4. Mostrar os pedidos **atrasados** de todas as OS.

## 2. Escopo

**Dentro do escopo**
- Situação do terceirizado por móvel e as transições.
- Conta a pagar da central (por pedido, não por móvel).
- Lista geral de terceirizados em aberto.
- Bloqueio do "desfazer aprovação" e aviso no cancelamento.

**Fora do escopo**
- Telas (11B).
- Cotação entre centrais, pedido de compra formal.
- Integração com o sistema da central.

---

## 3. Arquivos afetados

```
backend-fastapi/
├── alembic/versions/d3e4f5a6b7c8_terceirizados_marcenaria.py    # CRIAR — filha da 10A
├── app/
│   ├── db/models/marcenaria/ambiente.py                          # ALTERAR — colunas do terceirizado no móvel
│   ├── db/models/marcenaria/configuracao.py                      # ALTERAR — terceirizado_plano_conta_id
│   ├── schemas/marcenaria/terceirizado.py                        # CRIAR
│   ├── services/marcenaria/terceirizado.py                       # CRIAR
│   ├── services/marcenaria/__init__.py                           # ALTERAR — bloqueio do desfazer + gancho de cancelamento
│   └── api/v1/endpoints/marcenaria_terceirizado.py               # CRIAR
└── test/services/marcenaria/test_terceirizado.py                 # CRIAR
```

Nenhum arquivo compartilhado muda: a conta usa `criar_conta_pagar` como ele é.

---

## 4. Decisões

### 4.1. Situação

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Cada móvel `TERCEIRIZADA` aprovado tem uma situação: **A pedir** → **Pedido enviado** → **Recebido** → **Conferido** (`A_PEDIR`, `ENVIADO`, `RECEBIDO`, `CONFERIDO`). Nasce `A_PEDIR` na aprovação (preenchido pela regra "aprovado e terceirizado sem situação = A_PEDIR", sem mexer na 08A) | E6, com o passo inicial que faltava: entre aprovar e pedir há dias, e o dono precisa ver o que ainda não foi pedido |
| D2 | **Enviar pedido** recebe uma lista de móveis **da mesma central**, o número do pedido externo (até 60 caracteres, opcional) e a **previsão de chegada** (data, opcional). Todos ficam com o mesmo pedido | Um pedido à central costuma cobrir vários móveis da obra |
| D3 | **Receber** recebe a lista de móveis e a data (padrão hoje). **Conferir** marca como conferido; **Registrar problema** mantém `RECEBIDO` com o texto do problema (até 500) e a data | O móvel que chega riscado não está pronto para instalar; o problema fica escrito para cobrar a central |
| D4 | **Voltar um passo** (para corrigir clique errado): `CONFERIDO → RECEBIDO → ENVIADO → A_PEDIR`. Voltar de `ENVIADO` para `A_PEDIR` limpa pedido e previsão. Bloqueado se o móvel tem conta a pagar **paga** | Erro de clique não pode exigir suporte; dinheiro pago não volta por um clique |
| D5 | Toda transição grava evento (06A D25) com quem, quando e o número do pedido | T7 |
| D6 | Só com a OS aberta (como a separação, 10A D13) | A OS fechada não tem mais o que acompanhar |
| D7 | **Atrasado:** `ENVIADO` com previsão antes de hoje. Calculado na leitura (sem coluna) | A previsão é o compromisso da central; a cobrança começa no dia seguinte |

### 4.2. Conta a pagar da central (E6)

| # | Decisão | Motivo |
|---|---------|--------|
| D8 | **Oferecida, não automática:** a resposta do **receber** traz `oferta_conta` com a central, os móveis recebidos juntos e o **valor sugerido** = Σ (valor da central × quantidade) desses móveis, copiado do orçamento. Só com `view_custos` o valor sugerido aparece; sem, vem vazio | E6: o valor da nota às vezes muda. P4: o valor do orçamento é custo |
| D9 | `POST /terceirizados/conta` cria **uma** conta para um grupo de móveis da mesma central: valor (obrigatório), vencimento (obrigatório; padrão hoje + 30), parcelas (opcional, o parcelamento que o Contas a Pagar já tem) e descrição sugerida "Madeiranit — pedido 4521 — OS-2026-000512 (Torre Quente, Painel TV)" | Uma nota = uma conta; o parcelamento existente cobre o "3x no boleto" |
| D10 | Categoria **"Produção terceirizada"**, tipo **`DESPESA`**, achada ou criada na primeira vez e guardada pelo id em `configuracoes_marcenaria.terceirizado_plano_conta_id` (mesma regra da 09A D5) | 09A D14 (F2a): em `CUSTO` ("Fornecedores / Mercadoria") o gasto ficaria fora do resultado do mês |
| D11 | Cada móvel guarda o `conta_pagar_id`. Móvel que já tem conta **ativa** (pendente ou paga) não entra em outra: `409` "O móvel Torre Quente já tem conta lançada." | Evita pagar a mesma nota duas vezes |
| D12 | Lançar a conta exige o módulo **Financeiro** e `manage_financeiro` (as mesmas travas das rotas do Contas a Pagar). A conta pode ser lançada **depois**, a qualquer momento depois do recebimento, enquanto a OS estiver aberta ou finalizada | Lançar conta é ato financeiro. Quem recebe o móvel na fábrica nem sempre é quem lança a conta |
| D13 | Diferença entre o valor lançado e o orçado vai para o evento ("Nota de R$ 3.950,00; orçado R$ 3.800,00; +3,9%") | O dono vê quanto a central cobrou a mais sem refazer conta |

### 4.3. Permissões e outras regras

| # | Decisão | Motivo |
|---|---------|--------|
| D14 | Situação (enviar, receber, conferir, problema, voltar): permissão de **OS** (`servico`), como a separação | A aba fica na OS (T1) |
| D15 | Nenhum valor nas respostas de situação sem `view_custos` (P4). Com `view_custos`, `valor_orcado_centavos` por móvel | P4 |
| D16 | **Desfazer aprovação** (08A §7.6) bloqueado com algum móvel `ENVIADO` ou além: "Já há pedido enviado à central Madeiranit (pedido 4521). Cancele com a central e volte o móvel para 'A pedir' antes de desfazer." | O8: desfazer com pedido feito deixaria a central produzindo sem OS |
| D17 | **Cancelar a OS** (gancho da 09A) com móvel `ENVIADO`/`RECEBIDO`/`CONFERIDO`: evento "Há móveis terceirizados pedidos à central para esta OS: Torre Quente (pedido 4521, Recebido). Combine com a central." Contas pendentes da central **não** são canceladas sozinhas | O móvel existe e foi pedido; a dívida com a central não some porque o cliente desistiu |
| D18 | Lista geral: `GET /marcenaria/terceirizados?situacao=&central_id=&atrasados=` com OS, cliente, móvel, central, pedido, previsão e situação, das OS abertas | O dono liga para a central uma vez por dia com a lista dos atrasados |

---

## 5. Modelo de dados

```sql
ALTER TABLE marcenaria_moveis ADD COLUMN terc_situacao VARCHAR(10);          -- NULL = A_PEDIR quando aprovado e terceirizado
ALTER TABLE marcenaria_moveis ADD COLUMN terc_pedido VARCHAR(60);
ALTER TABLE marcenaria_moveis ADD COLUMN terc_enviado_em DATE;
ALTER TABLE marcenaria_moveis ADD COLUMN terc_previsao DATE;
ALTER TABLE marcenaria_moveis ADD COLUMN terc_recebido_em DATE;
ALTER TABLE marcenaria_moveis ADD COLUMN terc_conferido_em DATE;
ALTER TABLE marcenaria_moveis ADD COLUMN terc_problema VARCHAR(500);
ALTER TABLE marcenaria_moveis ADD COLUMN terc_conta_pagar_id INTEGER REFERENCES contas_pagar(id);
ALTER TABLE configuracoes_marcenaria ADD COLUMN terceirizado_plano_conta_id INTEGER REFERENCES planos_conta(id);
CREATE INDEX ix_marcenaria_moveis_terc ON marcenaria_moveis (terc_situacao, terc_previsao);
```

Migração `d3e4f5a6b7c8`, filha de `c2d3e4f5a6b7` (10A), com a regra da 08A §5.1 (só se a coluna faltar, sem `batch`).

Colunas no próprio móvel, e não tabela de pedidos, porque o pedido aqui é só um número e uma data repetidos nos móveis do grupo; uma tabela de pedidos só se pagaria com cotação e itens de pedido, que estão fora.

---

## 6. Contrato da API

Prefixo `/api/v1/marcenaria`.

| Método e rota | Permissão | O que faz |
|---------------|-----------|-----------|
| `GET /os/{numero_os}/terceirizados` | servico | Móveis terceirizados da OS (§6.1) |
| `POST /os/{numero_os}/terceirizados/enviar` | servico | `{movel_ids, pedido?, previsao?}` (D2) |
| `POST /os/{numero_os}/terceirizados/receber` | servico | `{movel_ids, data?}` → móveis + `oferta_conta` (D8) |
| `POST /os/{numero_os}/terceirizados/conferir` | servico | `{movel_ids}` |
| `POST /os/{numero_os}/terceirizados/{movel_id}/problema` | servico | `{texto}` (D3) |
| `POST /os/{numero_os}/terceirizados/{movel_id}/voltar` | servico | D4 |
| `POST /os/{numero_os}/terceirizados/conta` | módulo FINANCEIRO + manage_financeiro | `{movel_ids, valor_centavos, vencimento, parcelas?, descricao?}` (D9) |
| `GET /terceirizados?situacao=&central_id=&atrasados=` | servico | D18 |

### 6.1. Móvel terceirizado

```jsonc
{
  "movel_id": 10, "nome": "Torre Quente", "ambiente": "Cozinha Gourmet", "quantidade": 1,
  "medidas": { "largura_mm": 700, "altura_mm": 2200, "profundidade_mm": 600 },
  "central": { "id": 9, "nome": "Madeiranit", "telefone": "8533…" },
  "situacao": "ENVIADO", "pedido": "4521", "enviado_em": "2026-10-08", "previsao": "2026-10-20",
  "atrasado": false, "recebido_em": null, "conferido_em": null, "problema": null,
  "conta": null,                                  // { id, status, valor_centavos, vencimento } quando lançada
  "valor_orcado_centavos": 380000                 // só com view_custos (D15)
}
```

### 6.2. Oferta de conta (resposta do receber)

```jsonc
"oferta_conta": {
  "central": { "id": 9, "nome": "Madeiranit" },
  "movel_ids": [10, 12],
  "valor_sugerido_centavos": 760000,              // null sem view_custos (D8)
  "descricao_sugerida": "Madeiranit — pedido 4521 — OS-2026-000512 (Torre Quente, Painel TV)",
  "vencimento_sugerido": "2026-11-07"
}
// null quando todos os móveis recebidos já têm conta (D11)
```

### 6.3. Erros

| Status | `detail` | Quando |
|--------|----------|--------|
| `422` | "Os móveis do mesmo pedido precisam ser da mesma central." | D2, D9 |
| `422` | "Este móvel não é terceirizado." | Móvel `INTERNA` |
| `409` | "Ação não permitida: o móvel Torre Quente está {situação}." | Transição fora de ordem |
| `409` | "O móvel Torre Quente já tem conta lançada." | D11 |
| `409` | "Não é possível voltar: a conta da central já foi paga." | D4 |
| `409` | `{codigo: "OS_FECHADA"}` | D6 |
| `403` | `MODULO_NAO_CONTRATADO` / permissão | D12 |

---

## 7. Especificação técnica

```python
def receber(db, numero_os, movel_ids, data, usuario) -> RecebimentoResposta:
    os_, orc = _os_editavel(db, numero_os)                              # D6
    moveis = _terceirizados_da_os(orc, movel_ids)                       # 422 se algum não for terceirizado
    for movel in moveis:
        _exigir_situacao(movel, "ENVIADO")                              # 409 fora de ordem
        movel.terc_situacao, movel.terc_recebido_em = "RECEBIDO", data or hoje_local()
    registrar_evento(db, orc, "TERCEIRIZADO_RECEBIDO", _frase(moveis), os_id=os_.id, usuario=usuario)
    return RecebimentoResposta(
        moveis=[_montar(m, usuario) for m in moveis],
        oferta_conta=_oferta(moveis, os_, usuario),                     # D8: None se todos já têm conta
    )


def lancar_conta(db, numero_os, dados: ContaTerceirizadoEntrada, usuario) -> dict:
    os_, orc = _os_com_orcamento(db, numero_os)                         # aberta ou finalizada (D12)
    moveis = _terceirizados_da_os(orc, dados.movel_ids)
    _exigir_mesma_central(moveis)                                       # D9
    _exigir_sem_conta_ativa(moveis)                                     # D11
    conta = financeiro_service.criar_conta_pagar(                       # o caminho de sempre
        db, empresa_id=_empresa(os_),
        dados=ContaPagarCreate(
            descricao=dados.descricao or _descricao_sugerida(moveis, os_),
            valor=dados.valor_centavos, vencimento=dados.vencimento, parcelas=dados.parcelas or 1,
            plano_conta_id=_plano_terceirizado(db),                     # D10: DESPESA
            fornecedor_id=moveis[0].central_fornecedor_id,
        ),
        usuario_token=usuario,
    )
    for movel in moveis:
        movel.terc_conta_pagar_id = conta["id"]                         # parcelado: a 1ª parcela (id do grupo)
    registrar_evento(db, orc, "TERCEIRIZADO_CONTA_LANCADA", _frase_diferenca(moveis, dados), os_id=os_.id)
    return conta
```

- "Conta ativa" (D11) olha o **grupo** do parcelamento: se qualquer parcela estiver paga ou pendente, está ativa; se todas foram canceladas, o móvel pode receber outra conta.
- Os bloqueios (D16) e o aviso de cancelamento (D17) entram nas listas `BLOQUEIOS_DESFAZER` (08A §7.6) e `ganchos.ao_cancelar` (09A §6.1).

---

## 8. Limitações conhecidas

- Sem cotação entre centrais nem pedido formal (fora da fase 1).
- Um pedido = um número repetido nos móveis; se a central dividir a entrega, cada móvel é recebido na sua data, mas o pedido continua o mesmo.
- O móvel terceirizado **não** tem etapas de produção (12A): para a produção, ele está pronto quando `CONFERIDO`.

## 9. Entrega (PR7)

`npm run build:sidecar`.

---

## 10. Critérios de aceite

- [ ] Móvel terceirizado aprovado aparece "A pedir"; enviar vários juntos com pedido e previsão; receber; conferir; registrar problema; voltar um passo.
- [ ] Receber oferece a conta com o valor do orçamento (só com custos), a descrição e o vencimento sugeridos; lançar cria a conta na categoria "Produção terceirizada" (despesa), com o fornecedor da central, parcelável.
- [ ] Móvel com conta ativa não entra em outra conta.
- [ ] Atrasados aparecem na lista geral.
- [ ] Desfazer aprovação bloqueado com pedido enviado; cancelamento registra o aviso.
- [ ] Nenhum valor sem `view_custos`. Código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Aprovar orçamento com 2 terceirizados | Os dois `A_PEDIR` |
| 02 | Enviar os dois, pedido 4521, previsão +12 dias | `ENVIADO`; evento com o pedido |
| 03 | Enviar móveis de centrais diferentes juntos | `422` |
| 04 | Receber um deles | `RECEBIDO`; `oferta_conta` só com ele; valor = valor da central × quantidade |
| 05 | Receber sem `view_custos` | `valor_sugerido_centavos: null` |
| 06 | Lançar conta de R$ 3.950 sobre orçado R$ 3.800, 3x | 3 parcelas; categoria "Produção terceirizada" (`DESPESA`); fornecedor da central; evento com +3,9% |
| 07 | Lançar de novo para o mesmo móvel | `409` |
| 08 | Cancelar as 3 parcelas e lançar de novo | Aceita |
| 09 | Conferir sem ter recebido | `409` |
| 10 | Registrar problema | Continua `RECEBIDO`, com o texto |
| 11 | Voltar de `ENVIADO` | `A_PEDIR`; pedido e previsão limpos |
| 12 | Voltar de `RECEBIDO` com conta paga | `409` |
| 13 | `ENVIADO` com previsão ontem | `atrasado: true`; aparece em `?atrasados=true` |
| 14 | Desfazer aprovação com um móvel `ENVIADO` | Motivo do D16 |
| 15 | Cancelar OS com móvel `RECEBIDO` | Evento do D17; conta pendente intacta |
| 16 | Lançar conta numa loja sem o módulo Financeiro | `403 MODULO_NAO_CONTRATADO` |
| 17 | Resultado do mês com a conta paga | Valor nas despesas (categoria `DESPESA`), não no CMV (F2a) |
