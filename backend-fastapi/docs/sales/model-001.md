# Documento de Especificação Técnica e Dicionário de Dados
**Módulo:** Ponto de Venda (PDV) - Gestão de Vendas e Carrinho
**Autor:** Carlos André Guedes de Almeida
**Data:** 09 de Abril de 2026
**Banco de Dados:** Relacional (SQL)
**Padrão Financeiro:** Todos os valores monetários são armazenados como `Integer` (representando centavos) para evitar erros de precisão flutuante. Exemplo: R$ 10,50 é salvo como 1050.
**Padrão de Chaves:** Todas as chaves primárias (PK) e estrangeiras (FK) utilizam o formato `Integer` (Auto-Incremental) para manter a consistência com a arquitetura do banco de dados legado.

---

## 1. Resumo Executivo
Este documento detalha a modelagem de dados para o módulo de PDV do ERP de Assistência Técnica. O modelo foi projetado para suportar salvamento contínuo (vendas em rascunho), rastreabilidade rigorosa de estoque, vendas anônimas e pagamentos múltiplos.

## 2. Mapa de Relacionamentos (Cardinalidade)
* **Cliente (1) ➔ (N) Vendas:** Um cliente pode ter várias vendas, mas uma venda pertence a um único cliente (ou a nenhum, caso seja venda de balcão).
* **Funcionário (1) ➔ (N) Vendas / Sessão de Caixa / Logs:** O funcionário é o ator responsável pelas transações e movimentações.
* **Venda (1) ➔ (N) Produtos_Venda:** Uma venda consolida múltiplos itens no carrinho.
* **Venda (1) ➔ (N) Pagamentos_Venda:** Uma venda suporta múltiplos métodos de pagamento coordenados.
* **Produto (1) ➔ (N) Logs_Produto:** Histórico de auditoria de vida de um item (entradas e saídas).

---

## 3. Estrutura das Tabelas

### Tabela: `vendas`
Entidade central do fluxo transacional. Gerencia o status do carrinho e consolida os valores financeiros.

| Coluna | Tipo | Restrições | Descrição / Regra de Negócio |
| :--- | :--- | :--- | :--- |
| `id` | `Integer` | **PK** | Identificador único da venda (Auto-Incremental). |
| `cliente_id` | `Integer` | **FK**, `NULL` | Cliente atrelado. Nulo para vendas rápidas. |
| `funcionario_id` | `Integer` | **FK**, `NOT NULL` | Vendedor responsável pelo caixa. |
| `sessao_caixa_id`| `Integer` | **FK**, `NULL` | Vínculo com o turno/caixa atual. |
| `status` | `String` / `Enum` | `NOT NULL` | `RASCUNHO`, `CONCLUIDA` ou `CANCELADA`. |
| `subtotal` | `Integer`| `NOT NULL`, Default `0` | Soma dos itens (em centavos, sem descontos e fretes). |
| `desconto` | `Integer`| `NOT NULL`, Default `0` | Desconto global aplicado no fechamento (em centavos). |
| `entrega` | `Integer`| `NOT NULL`, Default `0` | Valor do frete/motoboy (em centavos). |
| `adiantamento` | `Integer`| `NOT NULL`, Default `0` | Valor pago previamente/sinal (em centavos). |
| `total` | `Integer`| `NOT NULL`, Default `0` | `(subtotal + entrega) - (desconto + adiantamento)` (em centavos). |
| `criado_em` | `Timestamp` | `NOT NULL` | Data de criação do rascunho. |
| `atualizado_em`| `Timestamp` | `NOT NULL` | Última alteração no carrinho. |

### Tabela: `produtos_venda`
Tabela pivô do carrinho. Congela preços no momento da venda e aceita produtos avulsos.

| Coluna | Tipo | Restrições | Descrição / Regra de Negócio |
| :--- | :--- | :--- | :--- |
| `id` | `Integer` | **PK** | Identificador da linha do carrinho. |
| `venda_id` | `Integer` | **FK**, `NOT NULL` | Referência à venda matriz. |
| `produto_id` | `Integer` | **FK**, `NULL` | Item de estoque. **Nulo** se for item avulso. |
| `descricao_avulsa`| `String` | `NULL` | Obrigatório se `produto_id` for nulo. |
| `qtd` | `Integer` | `NOT NULL`, `> 0` | Quantidade do item vendido. |
| `valor_unitario`| `Integer`| `NOT NULL` | Preço unitário **congelado** no ato da inclusão (em centavos). |
| `desconto` | `Integer`| `NOT NULL`, Default `0` | Desconto específico deste item (em centavos). |
| `subtotal` | `Integer`| `NOT NULL` | Calculado: `(valor_unitario * qtd) - desconto` (em centavos). |

### Tabela: `pagamentos_venda`
Armazena múltiplas formas de pagamento para quitar uma única venda.

| Coluna | Tipo | Restrições | Descrição / Regra de Negócio |
| :--- | :--- | :--- | :--- |
| `id` | `Integer` | **PK** | Identificador único da transação. |
| `venda_id` | `Integer` | **FK**, `NOT NULL` | Venda correspondente. |
| `tipo_pagamento_id`| `Integer` | **FK**, `NOT NULL` | Tabela de domínio (PIX, Cartão, Dinheiro). |
| `valor` | `Integer`| `NOT NULL`, `> 0` | Fração financeira paga neste método (em centavos). |
| `parcelado` | `Boolean` | `NOT NULL`, Default `False`| Flag indicando compra a prazo. |
| `qtd_parcelas` | `Integer` | `NOT NULL`, Default `1` | Quantidade de parcelas (1 = à vista). |
| `data_pagamento` | `Timestamp` | `NOT NULL` | Momento exato do registro. |

### Tabela: `logs_produto`
Histórico de auditoria imutável para movimentações de estoque.

| Coluna | Tipo | Restrições | Descrição / Regra de Negócio |
| :--- | :--- | :--- | :--- |
| `id` | `Integer` | **PK** | Identificador do log. |
| `produto_id` | `Integer` | **FK**, `NOT NULL` | Produto movimentado. |
| `venda_id` | `Integer` | **FK**, `NULL` | Venda que causou saída ou estorno. |
| `funcionario_id` | `Integer` | **FK**, `NOT NULL` | Responsável pela ação. |
| `tipo_transacao` | `String` / `Enum` | `NOT NULL` | `ENTRADA`, `SAIDA_VENDA`, `ESTORNO`. |
| `qtd` | `Integer` | `NOT NULL` | Quantidade movimentada (+ ou -). |
| `data_registro` | `Timestamp` | `NOT NULL` | Data exata da movimentação no sistema. |

### Tabela: `sessao_caixa`
Garante a integridade do dinheiro físico e agrupamento de turnos.

| Coluna | Tipo | Restrições | Descrição / Regra de Negócio |
| :--- | :--- | :--- | :--- |
| `id` | `Integer` | **PK** | Identificador do turno de caixa. |
| `funcionario_id` | `Integer` | **FK**, `NOT NULL` | Usuário que assumiu o caixa. |
| `status` | `String` / `Enum` | `NOT NULL` | `ABERTO` ou `FECHADO`. |
| `saldo_inicial` | `Integer`| `NOT NULL` | Dinheiro de troco na abertura (em centavos). |
| `saldo_final_esperado`| `Integer`| `NULL` | Soma automática ao encerrar (em centavos). |
| `data_abertura` | `Timestamp` | `NOT NULL` | Início do expediente. |
| `data_fechamento`| `Timestamp` | `NULL` | Encerramento do expediente. |