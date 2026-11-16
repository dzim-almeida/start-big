# Módulo de Compras — o que a plataforma web precisa fazer

Escrito em 03/10/2026, na branch `feat/compras` do ERP. Para fazer **depois**
que o módulo estiver pronto no ERP (decisão do Alan). Plano completo do módulo:
`docs/compras-plano.md`.

**Resumo:** Compras **não precisa de rota nova na API web**. O ERP faz tudo
localmente; da plataforma ele só precisa saber se a loja contratou. É o mesmo
mecanismo que já liberou a NF-e: o identificador do módulo dentro da claim
`modulos` do JWT da licença.

---

## 1. O que fazer

| # | Tarefa | Detalhe |
|---|---|---|
| 1 | Cadastrar o módulo **`COMPRAS`** no catálogo de módulos | Exatamente assim: maiúsculas, sem acento, sem espaço. O ERP compara a string literal (`requer_modulo("COMPRAS")` no backend, `MODULOS.COMPRAS` no frontend) |
| 2 | Vincular `COMPRAS` ao plano **Business** | Decisão D19 do plano |
| 3 | Permitir concessão **avulsa** por cliente | Mesmo mecanismo que já existe para os outros módulos (ex.: NF-e como extra) |
| 4 | Garantir que o JWT traga `"COMPRAS"` no array `modulos` | JWT RS256, claim `modulos: string[]` — igual à NF-e (contrato fiscal, §9) |
| 5 | **Não** incluir `COMPRAS` em planos antigos nem em "todos os módulos" por padrão | É vendido à parte |
| 6 | Texto comercial do módulo (tela de planos / contratação) | Sugestão abaixo (§4) |

## 2. Regras que a web precisa saber (o ERP já faz assim)

- **Identificador imutável.** Depois que o primeiro token sair com
  `COMPRAS`, não renomeie: o JWT vive 7 dias, e renomear tiraria o módulo de
  todo cliente até o último token expirar.
- **Nega sem resposta.** Para `COMPRAS`, o ERP trata licença sem a claim ou com
  lista vazia como **não contratado** (como NF-e e NFC-e). Para os módulos
  antigos, lista vazia continua liberando. Ou seja: enquanto a plataforma não
  emitir `COMPRAS`, **nenhuma loja vê o módulo** — é seguro subir o ERP antes.
- **O que a loja vê sem o módulo:** nada muda no sistema; as rotas
  `/api/v1/compras/*` respondem 403 com `codigo: "MODULO_NAO_CONTRATADO"` e a
  mensagem "…não está incluído no seu plano. Fale com o suporte para
  contratá-lo."
- **O que o ERP grava mesmo sem o módulo:** o último preço pago por
  fornecedor, a cada nota importada por XML. Fica local, ninguém vê sem o
  módulo, e não envia nada para a web.

## 3. Pergunta em aberto (a mesma da NF-e)

O ERP chama `/licenca/conectar` a cada 5 minutos e guarda o token que voltar.
**Esse endpoint remoeda o token com os módulos do momento, ou devolve o mesmo
até `proximaValidacaoEm`?** Disso depende a contratação aparecer na loja em
~5 minutos ou em até 7 dias (contrato fiscal, §9). Vale responder uma vez e
servir para todos os módulos.

## 4. Texto comercial sugerido

> **Compras** — saiba o que comprar antes de faltar. O sistema aponta o que
> está abaixo do estoque mínimo, monta o pedido por fornecedor com o último
> preço pago, avisa quando outro fornecedor vende mais barato, e confere a
> mercadoria e a nota na chegada, lançando estoque e contas a pagar.

(Ajustar conforme as fases entregues: fase 1 = fornecedores do produto e
último preço; fase 2 = necessidades e pedido; fase 3 = recebimento e contas;
fase 4 = nota × pedido; fase 5 = sugestão por vendas e relatórios.)

## 5. Como testar quando for liberar

1. Na plataforma, conceder `COMPRAS` a **uma** licença (loja canário, com
   backup feito antes da atualização).
2. No ERP dessa loja, esperar a renovação do token (ver §3) — ou reconectar.
3. Conferir: menu **Compras** (Necessidades, Pedidos, Recebimento) aparece;
   Cadastro do produto → seção **Fornecedores (compras)** aparece;
   Configurações › Cargos → linhas **Compras** e **Recebimento** aparecem.
4. Numa licença **sem** `COMPRAS`: nada disso aparece (nem o menu), e
   `GET /api/v1/compras/fornecedores` responde 403 `MODULO_NAO_CONTRATADO`.
5. Revogar `COMPRAS` da licença canário e conferir que some após a renovação
   do token.

## 6. O que NÃO é preciso na web

- Nenhuma rota nova, nenhuma tabela nova, nenhuma mudança no formato do JWT
  (só um valor a mais no array que já existe).
- Nenhuma cota ou contagem de uso (diferente da NF-e, Compras não consome
  serviço da plataforma).
- Futuro, fora do escopo atual: baixar NF-e pela chave (DF-e/Manifestação),
  que **vai** passar pela plataforma fiscal — plano próprio.
