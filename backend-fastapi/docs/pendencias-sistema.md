# Pendências do Sistema

Registro de problemas e lacunas encontrados durante outros trabalhos, que **não** cabem no escopo de quem os achou e precisam de spec própria. Cada item diz onde foi achado, o impacto e uma proposta inicial. Não é lista de desejos: só entra o que afeta uma loja real.

| ID | Título | Gravidade | Achado em | Status |
|----|--------|-----------|-----------|--------|
| PEND-001 | CNPJ alfanumérico não é aceito em nenhum cadastro | Alta | Spec 02 da marcenaria (06/10/2026) | Aberta |
| PEND-002 | Comissão da OS ignora o desconto da OS | Média | Spec 08A da marcenaria (06/10/2026) | Aberta |
| PEND-003 | Conta do recebimento de Compras nasce sem categoria e o material sai do lucro duas vezes | Média | Revisão 15 da SPEC-00 da marcenaria (08/10/2026) | Aberta |

**Gravidade:** Alta = impede uma operação real da loja · Média = obriga contorno manual · Baixa = incômodo.

---

## PEND-001 — CNPJ alfanumérico não é aceito em nenhum cadastro

| Campo | Valor |
|-------|-------|
| Gravidade | **Alta** |
| Status | Aberta |
| Achado em | `docs/marcenaria/SPEC-02-CNPJ-CLIENTE-MARCENARIA.md` §9 (06/10/2026) |
| Afeta | Todos os segmentos |

### O problema

Desde **julho de 2026**, a Receita Federal emite CNPJ **alfanumérico** (IN RFB nº 2.229/2024): as 12 primeiras posições aceitam letras e números, e os 2 dígitos verificadores continuam numéricos. Exemplo oficial: `12.ABC.345/01DE-35`. Os CNPJs antigos, só numéricos, continuam válidos.

O StartBig trata CNPJ como **14 dígitos numéricos** em todas as camadas. Uma empresa aberta depois de julho de 2026 **não consegue ser cadastrada** como cliente PJ, fornecedor ou como a própria empresa do sistema, e não pode ser destinatária de NF-e.

### Onde está a restrição (levantamento de 06/10/2026, branch `feat/segmento-marcenaria`)

| Camada | Onde | Restrição |
|--------|------|-----------|
| Backend — validação | `app/core/validators.py::validar_cnpj` | Remove tudo que não é dígito e exige 14 dígitos; o cálculo do DV é só numérico |
| Backend — fiscal | `services/fiscal/validators.py`, `services/verificacao_fiscal.py`, `schemas/venda_nota_fiscal.py` | Usam `validar_cnpj` (emitente e destinatário) |
| Backend — schemas | `schemas/cliente.py`, `fornecedor.py`, `empresa.py`, `auth.py`, `emissao_fiscal.py`, `perfil_tributario.py`, `forma_pagamento.py`, `configuracao_clientes.py` | Conferir cada um: padrões de 14 dígitos e chamadas a `validar_cnpj` |
| Banco | `cliente.cnpj`, `fornecedor.cnpj` | `String(14)` (o tamanho serve; o problema é o que se grava e se valida) |
| Frontend — máscara | `customers/.../CompanyDataSection.vue`, `enterprise/.../IdentificationSection.vue`, `sign-in/.../ResponsavelStep.vue`, `sales/.../FiscalFechamentoSection.vue` | `##.###.###/####-##` (só números) |
| Frontend — validação | `customer.schema.ts`, `empresa.schema.ts`, `employee.schema.ts`, `sign-in.schema.ts` | `cpf-cnpj-validator` (numérico) e regex `^\d{14}$` |
| Frontend — normalização | `replace(/\D/g, '')` em vários pontos (ex.: `buscarDadosCNPJ`) | Apaga as letras |
| Externo | BrasilAPI (consulta de CNPJ) | Suporte ao formato alfanumérico **não confirmado** |
| Externo | Plataforma fiscal / SEFAZ (NF-e) | O leiaute da NF-e já prevê o CNPJ alfanumérico; **confirmar** o suporte na plataforma usada pelo StartBig |

### Impacto

- **Cadastro:** cliente PJ, fornecedor e empresa com CNPJ novo não passam da validação.
- **Fiscal:** NF-e para um destinatário com CNPJ novo é bloqueada antes do envio.
- **Onboarding:** uma loja aberta depois de julho de 2026 não consegue criar a empresa no sistema com o próprio CNPJ.
- O problema **cresce com o tempo**: toda empresa nova a partir de julho de 2026 recebe o formato novo.

### Proposta inicial (para a spec própria)

1. **Um validador único** por lado, com o algoritmo oficial: cada caractere vale `código ASCII − 48` (`'0'` = 0 … `'9'` = 9, `'A'` = 17 … `'Z'` = 42), pesos `5,4,3,2,9,8,7,6,5,4,3,2` (1º DV) e `6,5,4,3,2,9,8,7,6,5,4,3,2` (2º DV), módulo 11. Para CNPJ só numérico, o resultado é idêntico ao cálculo atual.
2. **Normalizar** para 14 caracteres `[0-9A-Z]`, em maiúsculas, sem pontuação. Trocar `replace(/\D/g, '')` por remover só `.`, `/`, `-` e espaços.
3. **Máscara** que aceita letras nas 12 primeiras posições e só números nas 2 últimas, convertendo para maiúsculas; `inputmode="text"` (com teclado numérico não há como digitar letras).
4. **Banco:** `String(14)` já comporta. Não há migração de dados: CNPJs gravados continuam válidos.
5. **Fiscal:** confirmar com a plataforma de emissão antes de liberar NF-e para destinatário alfanumérico.
6. **Consulta de CNPJ:** confirmar o suporte da BrasilAPI; sem suporte, a consulta automática não roda para CNPJ com letras, e o cadastro segue manual.
7. **Testes:** os casos oficiais (`12.ABC.345/01DE-35` válido; `11.222.333/0001-81` válido; letra nos DVs, minúsculas normalizadas, sequência repetida inválida) nos dois lados, com os mesmos resultados.

### Por que não entra na marcenaria

Toca cadastro, onboarding e fiscal, em todos os segmentos e nas lojas em produção. A Spec 02 da marcenaria mantém a consulta de CNPJ só para o formato numérico e aponta para esta pendência.


---

## PEND-002 — Comissão da OS ignora o desconto da OS

| Campo | Valor |
|-------|-------|
| Gravidade | **Média** |
| Status | Aberta |
| Achado em | `docs/marcenaria/SPEC-08A-APROVACAO-OS-BACKEND-MARCENARIA.md` §9 (06/10/2026) |
| Afeta | Todos os segmentos com OS (informática, oficina, serigrafia, marcenaria) |

### O problema

A base da comissão de OS (`db/crud/relatorio.py`, `get_comissao_base`) soma, por funcionário, `valor_total − quantidade × custo_unitario` **de cada item de serviço**. O `desconto` fica no cabeçalho da OS (`ordens_servico.desconto`) e **não entra** nessa conta. A docstring de `services/relatorio.get_comissao` diz o contrário ("OS.valor_total já é pós-desconto"), o que esconde o problema de quem lê.

Exemplo: OS com serviço de R$ 1.000,00 (custo R$ 400,00) e desconto de R$ 100,00. O cliente paga R$ 900,00 e a loja ganha R$ 500,00, mas a comissão é calculada sobre R$ 600,00.

### Impacto

- Hoje: pequeno, porque descontos de OS costumam ser baixos.
- Com a marcenaria: o desconto global (C9) é parte normal da negociação (5% de R$ 9.725 = R$ 486). O vendedor ganha comissão sobre o desconto que ele mesmo deu, o que incentiva o desconto.

### Proposta inicial (para a spec própria)

1. Repartir o desconto da OS entre os itens **pelo valor** (mesmo critério de maior resto do motor da marcenaria) e subtrair a parte de cada item de serviço na base.
2. Corrigir a docstring de `get_comissao`.
3. Prova de não regressão: relatório de comissão das lojas atuais antes × depois, com a diferença explicada OS por OS (só mudam as OS com desconto).
4. Avisar o dono: a comissão de OS com desconto vai diminuir; pode ser preciso recalibrar o percentual (mesmo aviso da troca de base de 05/09/2026).

### Por que não entra na marcenaria

Muda um número que três lojas em produção já usam para pagar funcionário (PR1). Precisa de decisão do dono e de comunicação, não de um ajuste escondido dentro de outra spec.


---

## PEND-003 — Conta do recebimento de Compras nasce sem categoria e o material sai do lucro duas vezes

| Campo | Valor |
|-------|-------|
| Gravidade | **Média** |
| Status | Aberta |
| Achado em | `docs/marcenaria/SPEC-00-DECISOES-MARCENARIA.md`, Revisão 15 (08/10/2026) |
| Afeta | Toda loja que usar o módulo Compras para comprar mercadoria (qualquer segmento) |

### O problema

O resultado do mês é `receita − CMV − despesas pagas` (`services/financeiro_analise.py` e `financeiro_visao.py`). As despesas pagas vêm de `crud/financeiro._total_pago`, que conta como **despesa** toda conta paga cuja categoria não é do tipo `CUSTO` — **inclusive a conta sem categoria** (decisão de 02/09/2026: "o lado seguro do erro").

O recebimento de um pedido de compra (`services/compras/recebimentos.lancar_contas`) cria as contas a pagar **sem `plano_conta_id`**. Para mercadoria, isso desconta a mesma chapa duas vezes:

1. quando a conta do fornecedor é paga (despesa sem categoria);
2. quando a chapa sai do estoque (CMV, pelo livro de estoque).

Exemplo: 10 chapas de R$ 300,00 compradas pelo Compras, conta paga em outubro, chapas usadas em OS finalizadas em outubro. O resultado de outubro cai R$ 6.000,00, quando o custo real foi R$ 3.000,00.

Para pedido de **serviço** (`tipo = SERVICO`, central de corte), a conta sem categoria está **certa**: serviço não passa pelo estoque, então só a despesa o leva ao resultado.

### Impacto

- O lucro do mês aparece menor do que é, na proporção do que foi comprado pelo Compras e pago no período.
- Contorno de hoje: o dono reclassifica a conta para "Fornecedores / Mercadoria" (tipo `CUSTO`) em Contas a Pagar.

### Proposta inicial (para a spec própria)

1. No recebimento de pedido `MATERIAL`, lançar as contas na categoria padrão de tipo `CUSTO` ("Fornecedores / Mercadoria", achada pelo tipo, não pelo nome); pedido `SERVICO` continua sem categoria (ou numa categoria `DESPESA`).
2. Permitir escolher a categoria no recebimento, com esse padrão.
3. Prova: resultado do mês antes × depois numa loja com compras recebidas; só mudam os meses com contas de compra pagas.

### Por que não entra na marcenaria

É regra do módulo Compras, que prevalece sobre as specs da marcenaria (SPEC-00, FB2), e afeta todos os segmentos. A marcenaria só a registra.

