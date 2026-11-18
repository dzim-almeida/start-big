# Produtos e Estoque (`products`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

A tela **Produtos** (`/produtos`, nome `products`) tem três abas: **Estoque** (cadastro e saldo dos produtos), **Fornecedores** e **Etiquetas** (central de etiquetas de estoque e envio). Cobre cadastro de produto, embalagens (fardo/caixa), regras de preço, movimentação de estoque, importação por planilha e entrada de mercadoria pela XML da NF-e.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/products/` — `views/ProductsView.vue` (abas), `inventory/`, `suppliers/`, `labels/`, `shared/` |
| Backend (endpoints) | `produto.py` (11 rotas), `produto_embalagem.py`, `produto_regra_preco.py`, `movimentacao_estoque.py`, `produto_importacao.py` (`/estoque/importar-planilha`), `nfe_entrada.py` (`/estoque/nfe-entrada`), `etiquetas.py` (`/api/v1/etiquetas`), `fornecedor.py` (`/api/v1/fornecedores`) |
| Backend (regras) | `app/services/produto/` (`cadastro`, `embalagem`, `estoque`, `fotos`, `importacao_planilha`, `movimentacao`) · `services/etiquetas/` (`modelo`, `envio`) · `services/fornecedor/` · `services/precificacao/` (`regras`, `quantidade`, `custo_mercadoria`) |
| Backend (banco) | `models/produto.py`, `estoque.py`, `produto_embalagem.py`, `produto_fiscal.py`, `produto_regra_preco.py`, `produto_fotos.py`, `movimentacao_estoque.py`, `log_produto.py`, `nota_entrada.py`, `modelo_etiqueta.py`, `fornecedor.py`, `produto_fornecedor.py`, `produto_codigo_fornecedor.py` |
| Permissões | `produto` · `fornecedor` · `etiqueta` · `manage_labels` · `delete_labels` |
| Impressão de etiqueta | feita no **Tauri** (`frontend/src-tauri/src/impressao/`), não no backend |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Movimentação de estoque** | Entrada, saída ou ajuste que muda o saldo e fica registrado. |
| **Embalagem** | Fardo/caixa que contém N unidades (com código DUN-14); o PDV pode vender por embalagem. |
| **Regra de preço** | Preço por quantidade/atacado (`produto_regra_preco`). |
| **Venda fracionada** | Quantidade quebrada (ex.: 3,5 kg). |
| **Modelo de etiqueta** | Layout neutro em mm, traduzido para a linguagem de cada impressora. |
| **Perfil tributário** | Dados fiscais do produto (NCM, CST...) usados na NF-e. |

## 4. Fluxos principais

1. **Cadastrar produto:** formulário "inteligente" (padrão de mercado) com foto, preço, fiscal e embalagens → `/produtos/`.
2. **Entrada por XML:** sobe o XML da NF-e do fornecedor e confere itens → `/estoque/nfe-entrada`.
3. **Importar planilha:** carga em lote → `/estoque/importar-planilha`.
4. **Ajustar estoque:** `movimentacao_estoque` registra o motivo.
5. **Etiquetas:** escolhe modelo e imprime direto da máquina (Tauri).

## 5. Decisões de arquitetura

- **Quem imprime etiqueta é o Tauri**, porque a impressora fica plugada no terminal e o backend pode estar em outra máquina.
- **Dinheiro e quantidade em `Decimal`/`Numeric`**, nunca `float`; quantidade fracionada tem regra própria (`precificacao/quantidade.py`).
- Campos fiscais do produto só aparecem quando a licença traz o módulo `NFE` (`lojaFiscal`).
- Aba **Etiquetas** exige permissão própria (`etiqueta`); editar/apagar modelo tem permissão separada.

## 6. Integração com outros módulos

- **`sales`/`order-service`:** consomem o produto (preço, estoque) e geram baixa de estoque.
- **`compras`:** pedidos e recebimento alimentam entrada de estoque e `produto_fornecedor`.
- **`fiscal`:** perfil tributário e NCM.
- **`financeiro`:** a entrada por XML pode lançar contas a pagar (`lancar_contas_pagar`, em `services/compras/nfe_entrada.py`).
- **`home`:** widget de estoque baixo.

## 7. Referências

- `backend-fastapi/docs/cadastro-produto-plano.md` · `produto-embalagens-plano.md` · `entrada-xml-nfe-plano.md` · `etiquetas-plano.md` · `venda-fracionada-plano.md`
