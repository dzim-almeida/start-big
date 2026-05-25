# Documentação de API: Módulo de Vendas (PDV)

Esta especificação define os contratos e rotas para o módulo de Vendas. O fluxo padrão consiste na criação de um "rascunho" de venda, seguido pela adição/edição de itens no carrinho e, por fim, a consolidação financeira com a finalização da transação.

## 1. Modelos de Dados (Schemas)

Abaixo estão os principais schemas de entrada (Payloads) extraídos das regras de negócio para a comunicação com a API.

### 1.1. Vendas (Geral)
* **`VendaCreate`** (Usado para abrir a venda)
  * `cliente_id` (int, opcional): Identificador do cliente.
  * `funcionario_id` (int, obrigatório): Identificador do funcionário que está abrindo a venda.
* **`VendaUpdate`** (Usado para atualizar cabeçalhos/totais)
  * `cliente_id`, `funcionario_id` (int, opcionais).
  * `entrega`, `adiantamento`, `desconto` (int, opcionais): Valores financeiros acessórios.
  * `observacao` (str, opcional): Limite de 500 caracteres.

### 1.2. Itens do Carrinho (Produtos)
* **`ProdutoVendaCreate`** (Usado para adicionar ao carrinho)
  * `tipo_produto` (Enum: CADASTRADO ou AVULSO, obrigatório).
  * `produto_id` (int, opcional): Obrigatório se tipo for CADASTRADO.
  * `descricao_avulsa` (str, opcional): Obrigatório se tipo for AVULSO.
  * `quantidade` (int, obrigatório, > 0).
  * `valor_unitario` (int, obrigatório, >= 0).
  * `desconto` (int, obrigatório, >= 0).
* **`ProdutoVendaUpdate`** (Usado para editar itens no carrinho)
  * `quantidade`, `descricao_avulsa`, `valor_unitario`, `desconto` (opcionais). 

### 1.3. Pagamentos
* **`PagamentoVendaCreate`** (Usado na finalização)
  * `forma_pagamento_id` (int, obrigatório).
  * `parcelado` (bool, opcional, default=False).
  * `qtd_parcelas` (int, opcional): Obrigatório se parcelado for `true`.
  * `valor` (int, obrigatório, >= 0).

---

## 2. Endpoints (Rotas)

A estrutura de rotas segue um padrão RESTful aninhado, garantindo que as manipulações de carrinho pertençam estritamente ao recurso da venda "pai".

### `POST /vendas`
* **Resumo:** Cria o rascunho inicial da venda.
* **Descrição:** Inicia uma nova transação de forma leve no banco de dados, gerando o ID identificador do carrinho.
* **Payload de Request:** `VendaCreate`
* **Response Esperado:** `VendaRead` (Retorna o `id` da venda e status inicial, ex: `RASCUNHO`).

### `PATCH /vendas/{venda_id}`
* **Resumo:** Atualiza dados gerais transacionais da venda.
* **Descrição:** Permite vincular/alterar o cliente no decorrer do atendimento, aplicar descontos globais, registrar frete (entrega) ou valores de adiantamento.
* **Parâmetros de Path:** `venda_id` (int).
* **Payload de Request:** `VendaUpdate`
* **Response Esperado:** `VendaRead` (Retorna a venda com os totais recalculados).

### `POST /vendas/{venda_id}/itens`
* **Resumo:** Adiciona um item ao carrinho.
* **Descrição:** Insere um produto (cadastrado ou avulso) na venda. Neste estágio, valida-se o estoque disponível sem efetuar a baixa definitiva.
* **Parâmetros de Path:** `venda_id` (int).
* **Payload de Request:** `ProdutoVendaCreate`
* **Response Esperado:** `AddProdutoVendaRead` (Retorna o produto inserido junto com o resumo financeiro atualizado da venda).

### `PATCH /vendas/{venda_id}/itens/{item_id}`
* **Resumo:** Edita um item existente no carrinho.
* **Descrição:** Rota dedicada para alterar propriedades de um produto já adicionado, como incrementar/decrementar a quantidade, aplicar um desconto específico no item ou alterar a descrição de produtos avulsos.
* **Parâmetros de Path:** `venda_id` (int), `item_id` (int).
* **Payload de Request:** `ProdutoVendaUpdate`
* **Response Esperado:** `AddProdutoVendaRead` (Retorna o produto atualizado junto com o resumo financeiro atualizado da venda)

### `DELETE /vendas/{venda_id}/itens/{item_id}`
* **Resumo:** Remove um item específico do carrinho.
* **Descrição:** Exclui o produto do rascunho da venda e recalcula o valor total.
* **Parâmetros de Path:** `venda_id` (int), `item_id` (int).
* **Payload de Request:** *Nenhum.*
* **Response Esperado:** HTTP `204 No Content`.

### `POST /vendas/{venda_id}/cancelar`
* **Resumo:** Cancela o rascunho ou a venda.
* **Descrição:** Transação que invalida o rascunho, interrompe o fluxo do caixa e descarta qualquer reserva de estoque provisória associada a este ID.
* **Parâmetros de Path:** `venda_id` (int).
* **Payload de Request:** *Opcional (pode receber um motivo de cancelamento).*
* **Response Esperado:** `VendaRead` (Retorna a venda com status alterado para `CANCELADA`).

### `POST /vendas/{venda_id}/finalizar`
* **Resumo:** Transação Principal (Checkout).
* **Descrição:** Recebe o array de pagamentos acordados no PDV. Valida se a soma dos pagamentos cobre o total financeiro (considerando adiantamentos, descontos e juros). Caso positivo, desconta o estoque definitivamente e muda o status da transação.
* **Parâmetros de Path:** `venda_id` (int).
* **Payload de Request:** Objeto contendo uma lista (`Array`) de `PagamentoVendaCreate`.
* **Response Esperado:** `VendaRead` (Retorna a venda consolidada com status `CONCLUIDA`, com pagamentos anexados).