# Plano: Marcenaria-fábrica (projeto → orçamento → produção → compra → instalação)

Escrito em 04/10/2026 e **revisado em 05/10/2026 contra o código** (branch
`feat/compras`, em cima de `529fc34`). Esta versão é para implementar: cada
fase diz o que muda no banco, na API, nas telas e o que os testes provam.

Fontes: o resumo do Alan ("Módulo de Compras para Marcenaria", RC01–RC20,
DC1–DC7), o plano do segmento (`docs/segmento-marcenaria-plano.md`, 16/09), o
módulo de Compras (`docs/compras-plano.md`, §12–§17) e o código.

---

## O que mudou na revisão de 05/10

| Versão de 04/10 | Revisão (05/10) | Por quê |
|---|---|---|
| Tabela nova `projetos` (PRJ-000123) | **Não existe.** O projeto é o `ObjetoServico` da OS | Na marcenaria, o objeto da OS **já é** o Projeto ("Cozinha apto 302", `rotulo_objeto_singular = "Projeto"`), e o código PRJ já é gerado do número da OS (`identificador`) |
| A OS nasce na aprovação do orçamento, mas as 4 primeiras etapas ficavam na OS | **A OS nasce no primeiro contato** (como hoje) e o orçamento pendura nela | Resolvia uma contradição: a etapa "Medição" estava numa OS que ainda não existia |
| "Aprovado" como etapa | **Evento** (vai para o log), não etapa parada | Ninguém fica em "Aprovado": aprovar já reserva e passa para "Aguardando sinal". Ficam **10 etapas guardadas** |
| D0 (travar ou só mostrar) bloqueava o plano | **Duas chaves**: `modo_fabrica` e `fabrica_travar_etapas`. A segunda vem **desligada** (só avisa) | O dono responde ligando ou desligando a chave; o código é o mesmo |
| Item da OS = cada linha da lista de material | Item da OS = **um por móvel** (o que o cliente compra) + **um por insumo somado** (o que sai do estoque) | O cliente compra a cozinha, não a chapa; e a chapa é dividida entre os móveis no corte (arredondar por móvel compraria chapa demais) |
| Baixa "na separação", sem dizer como | `quantidade_separada` no item; a baixa e a reserva usam **quantidade − separada** | Uma regra só para baixa, reserva, cancelamento e reabertura. Nulo nos outros segmentos = conta de hoje |
| Sinal "liquidado no financeiro" | Recebido = **mesma soma da finalização** (`valor_entrada` + `adiantamentos_anteriores` + pagamentos) | Já é o que a OS conta como dinheiro recebido; nenhum lugar novo |

**Nada disso depende do dono para começar.** As perguntas da §12 ajustam
valores padrão (sinal de 50%, travas ligadas ou não), não o desenho.

---

## Resumo em uma página

A marcenaria de hoje é uma **OS de balcão bem vestida**: tipos Planejados e
Reforma, ambiente, módulos em texto, endereço da obra, adiantamento, aprovação
por item e um campo **Etapa** só informativo. Continua assim para quem não
ligar o modo fábrica.

O **modo fábrica** (chave da loja, só no segmento Marcenaria, só para OS do tipo
*Planejados*) acrescenta à mesma OS:

1. **Insumo** no produto: chapa em m², fita em metro, e a marca "sofre perda" (F1).
2. **Orçamento por móvel** com versões: ambiente → móvel → lista de material.
   Aprovar uma versão **escreve os itens na OS**, já com a perda e o custo
   congelados (F2).
3. **Trilho de 10 etapas** com travas (ou avisos), log e o **sinal** liberando
   a compra (F3).
4. **Separação bipada** que dá a baixa na hora e grava o **custo real**, e a
   **margem orçada × real** (F4).
5. **Central de corte** como pedido de serviço do móvel (F5).

Compras (fases 1–6) já faz o resto: reserva calculada, necessidade por OS,
pedido ligado à OS, recebimento, contas e o painel "Compras desta OS".

**Custo: 4 a 5 semanas**, em fases que já servem uma de cada vez. A primeira
entrega útil (orçamento por móvel que gera a OS) sai em ~2 semanas (F1 + F2).

---

## 0. O que "pronto" significa

| # | Critério de aceite | Fase |
|---|---|---|
| F1 | Cadastrar insumo: chapa 2750×1850 em m², fita em rolo de 50 m, ferragem em unidade, com "sofre perda" | F1 |
| F2 | Na OS de Planejados (modo fábrica), montar o orçamento: ambientes → móveis (LxAxP) → material, com o custo puxado do cadastro | F2 |
| F3 | Ter versões do orçamento, enviar, aprovar uma só; recusar ou vencer as outras | F2 |
| F4 | Aprovar escreve na OS os móveis (preço) e os insumos somados com a perda, arredondados para cima, custo congelado | F2 |
| F5 | As Necessidades de Compras pedem **chapas inteiras** para a OS aprovada | F2 (de graça, via fase 6) |
| F6 | A OS segue as 10 etapas; o botão de avançar diz o que falta; tudo vai para o log | F3 |
| F7 | Sem sinal, a OS **não gera compra**; o gestor libera antes, com motivo | F3 |
| F8 | A fila de Compras atende primeiro quem **instala primeiro** | F3 |
| F9 | O almoxarife separa bipando, no PC ou no celular; a baixa acontece ali e o fechamento não baixa de novo | F4 |
| F10 | A OS mostra margem orçada × real | F4 |
| F11 | O móvel terceirizado tem pedido de serviço à central de corte | F5 |
| **F12** | **Oficina, assistência, serigrafia, PDV, a marcenaria de bairro e a Reforma de móveis continuam idênticos** | todas |

F12 manda em todo o resto: tudo entra por **coluna nula, tabela nova e chave
desligada**.

---

## 1. Onde estamos (05/10/2026), conferido no código

**Segmento** (`app/core/segmentos/definicoes/marcenaria.py`): tipos `planejados`
e `reforma_moveis`, gravados em `ordens_servico.dados_adicionais.tipo_trabalho`;
campos `nome_projeto` (→ `objetos_servico.modelo`), `endereco_obra`, `ambiente`,
`modulos`, `material`, `acabamento`, `ferragens`, `montagem_incluida`, `etapa`
(lista do dono). Capacidades: aprovação por item, imagem na entrada, garantia.
Código do projeto gerado: `PRJ-…` a partir do número da OS.

**OS** (`app/db/models/ordem_servico.py`, `services/ordem_servico.py`):
- 7 status; `update_ordem_servico` deixa trocar livremente, menos para
  FINALIZADA/CANCELADA (têm endpoint próprio).
- Item (`ordem_servico_item.py`): `tipo` PRODUTO/SERVICO, `produto_id` ou
  `servico_id` **ou nenhum** (item avulso), `quantidade` float, `valor_unitario`,
  `custo_unitario` congelado, `status_aprovacao`, `visivel_cliente` (peça
  embutida que não sai na via do cliente).
- Baixa: `_itens_de_produto` + `_movimentar_estoque_os`, **só ao finalizar**;
  estorno ao cancelar uma finalizada e ao reabrir.
- Recebido: `sum(pagamentos) + adiantamentos_anteriores + valor_entrada`.
- Fotos: `ordem_servico_foto.py`.

**Configuração da OS** (`configuracoes_os`, 1:1 com a empresa): prazos,
garantia, vias. É onde entra a chave do modo fábrica (padrão de
`configuracoes_produtos.usar_embalagens`).

**Compras** (`services/compras/demanda_os.py`, `necessidades.py`): reserva
calculada pela **mesma regra** da baixa (`_itens_de_produto`); fila por
`data_criacao` da OS; pedido ligado à OS por `pedido_compra_origens`; painel
"Compras desta OS".

**Produto**: `unidade_medida` texto (UN, M2, M…). Custo: `estoque.custo_medio`
(média ponderada), caindo para `estoque.valor_entrada` (último preço) quando
nulo — é o `custo_atual` de `services/movimentacao_estoque.py`, e é ele que o
orçamento copia e a separação grava como custo real. Não sabe converter m² em chapa.

---

## 2. A ideia

```
 OS PRJ-2026-000123  (já existe: cliente, Projeto "Cozinha apto 302",
 │                    endereço da obra, fotos)  tipo Planejados, modo fábrica
 │
 ├─ fase_fabrica: MEDICAO → ELABORACAO → … (§6)
 │
 ├─ ORÇAMENTO v1, v2, v3…  (fabrica_orcamentos: perda %, sinal %, validade)
 │    └─ AMBIENTE (Cozinha, Suíte…)
 │         └─ MÓVEL (Armário aéreo 1800×700×350, preço de venda, terceirizado?)
 │              └─ MATERIAL (insumo, consumo em m²/m/un, custo copiado)
 │
 └─ APROVAR v2 ──► escreve os ITENS DA OS (congelados):
        • 1 item por MÓVEL: SERVICO avulso, valor = preço do móvel,
          visível ao cliente  → é o que soma no total da OS
        • 1 item por INSUMO (somado em todos os móveis): PRODUTO,
          quantidade = ⌈ consumo total com perda ÷ consumo por chapa ⌉,
          valor 0, invisível ao cliente, custo_unitario congelado
                                   → é o que reserva, compra e baixa
    ──► Compras faz o resto (fase 6): reserva, necessidade em chapas,
        pedido ligado à OS, recebimento, contas, painel
```

**Por que um item por insumo somado, e não por móvel:** o corte divide a chapa
entre móveis. Três móveis que gastam 1 m² cada cabem em uma chapa;
arredondando por móvel, o sistema compraria três. A divisão por móvel continua
guardada no orçamento (`fabrica_materiais`), e a margem por móvel usa a fração
de chapa, sem arredondar. A sobra (o que o arredondamento comprou a mais) volta
ao saldo livre depois da separação (DC7).

**Por que o móvel é item avulso de SERVIÇO:** `servico_id` e `produto_id`
nulos já são aceitos ("itens customizados"), o item SERVIÇO não mexe no
estoque, e a via do cliente lista exatamente o que ele comprou ("Armário aéreo
1800×700×350 — R$ 2.400"). O insumo com `visivel_cliente = False` é o
mecanismo que a oficina já usa para a peça embutida no serviço.

---

## 3. Decisões

### 3.1 Do resumo do Alan (DC1–DC7)

| # | Decisão | Como fica |
|---|---|---|
| DC1 | Compra antes do sinal | **Bloqueada por padrão**; o gestor libera por OS, com motivo no log (RC04) |
| DC2 | Alocação do que chega | Pela **data de instalação**; sem ela, pela abertura da OS (como hoje) (RC12) |
| DC3 | Perda na quantidade | **Sim**, para reserva e compra, só em insumo que "sofre perda" (RC01) |
| DC4 | Título a pagar | No recebimento, proporcional — já é assim em Compras (D8) |
| DC5 | Custo para o almoxarife | Oculto — já é assim em Compras (D14); a tela de separação não mostra custo |
| DC6 | Montador terceirizado | Fica para depois do piloto (§12, pergunta 7) |
| DC7 | Sobra de chapa | Volta ao saldo livre: separa-se a quantidade arredondada, a sobra física fica na prateleira e é contada no próximo inventário. Sem "retalho" no sistema nesta versão |

### 3.2 Deste plano

| # | Decisão | Como fica |
|---|---|---|
| D0 | Modo fábrica | `configuracoes_os.modo_fabrica` (bool, padrão **false**). Só tem efeito se `empresa.segmento == "marcenaria"`. Ligado, toda OS **nova** do tipo *Planejados* nasce com `fase_fabrica = MEDICAO`. Reforma e as OS antigas não mudam |
| D0b | Travar ou avisar | `configuracoes_os.fabrica_travar_etapas` (bool, padrão **false**). Desligado: a trava vira aviso e o usuário avança confirmando um motivo, que vai para o log. Ligado: não avança. A resposta do dono à pergunta D0 é só o valor desta chave |
| D0c | Desligar o modo depois | OS que já têm `fase_fabrica` continuam no trilho até fechar; só as novas deixam de nascer nele. Nunca apagar `fase_fabrica` |
| D1 | Onde mora o orçamento | Pendurado na OS (`fabrica_orcamentos.os_id`). Uma OS, várias versões, **uma aprovada** |
| D2 | Insumo | Produto do catálogo + 3 colunas: `unidade_consumo` (M2, M, UN), `consumo_por_unidade` (inteiro: mm² por chapa, mm por rolo, 1 por unidade), `sofre_perda` |
| D3 | Unidade do estoque | A **de compra** (chapa, rolo, unidade). O orçamento fala em m²/m; a conversão é na aprovação, **arredondando para cima** |
| D4 | Inteiros | Dentro do orçamento: mm, mm², centavos, pontos-base (1000 = 10%). O estoque continua decimal |
| D5 | Etapas | Coluna `fase_fabrica` na OS. O **status de sempre é derivado** dela (§6) e não pode ser trocado à mão nessas OS |
| D6 | Baixa na separação | `quantidade_separada` (float, nulo) no item. Separar baixa **a diferença**; finalizar baixa `quantidade − separada`; cancelar estorna o separado; a reserva conta `quantidade − separada` |
| D7 | Custo real | `custo_real` (centavos, nulo) no item: custo médio do estoque no momento da separação. O `custo_unitario` congelado nunca muda (RC11) |
| D8 | Central de corte | Pedido de compra `tipo = SERVICO` (já existe desde a fase 2) ligado ao **móvel** (`fabrica_moveis.pedido_compra_id`) |
| D9 | Medição | Fotos da OS (já existem) + medidas do móvel no orçamento. Checklist de vistoria fica fora (§10) |
| D10 | Preço do móvel | Digitado por móvel. O sistema mostra o custo e **sugere** custo × (1 + `margem_lucro_padrao` de Produtos). Não há tabela de preço por m² |
| D11 | Aprovação por item | Na OS da fábrica, quem aprova é a **versão**. "Aprovou a cozinha, deixou o closet" = nova versão sem o closet. Os itens já nascem APROVADO |
| D12 | Mudar depois de aprovado | Permitido até a primeira separação: aprovar outra versão **troca** os itens gerados pela anterior. Depois de separar, só com estorno da separação |
| D13 | Licença | Nesta versão, sem módulo pago próprio: a chave basta. Orçamento, trilho e separação funcionam **sem** o módulo COMPRAS; necessidade/pedido/painel exigem COMPRAS, como hoje. Se o Alan quiser cobrar, vira `requer_modulo("FABRICA")` no router — uma linha |

---

## 4. Modelo de dados

Tudo aditivo. Tabelas novas nascem pelo `create_all()`; colunas novas vão em
migration que decide pela **ausência da coluna** (modelo `965c71a2da9a`). Os
nomes levam o prefixo `fabrica_` porque `orcamentos` já é o orçamento de venda
do PDV.

```
produtos (+3, F1)
├── unidade_consumo      VARCHAR(4)  nulo     M2 | M | UN
├── consumo_por_unidade  INTEGER     nulo     mm² por chapa (2750×1850 = 5.087.500),
│                                             mm por rolo (50 m = 50.000), 1 por unidade
└── sofre_perda          BOOLEAN     false    MDF e fita sim, ferragem não

configuracoes_os (+2, F2/F3)
├── modo_fabrica            BOOLEAN false
└── fabrica_travar_etapas   BOOLEAN false

fabrica_orcamentos (nova, F2) — as versões
├── id, os_id FK (CASCADE), versao INT  (única por OS)
├── situacao   RASCUNHO | ENVIADO | APROVADO | RECUSADO | VENCIDO
├── perda_bp INT (1000 = 10%), sinal_bp INT (5000 = 50%), validade DATE nulo
├── total INT (centavos, soma dos preços), custo_total INT (centavos)
├── observacao TEXT nulo
├── enviado_em, aprovado_em, aprovado_por (nome), recusado_motivo
└── criado_em, atualizado_em

fabrica_ambientes (nova, F2): id, orcamento_id FK (CASCADE), nome, ordem
fabrica_moveis (nova, F2):    id, ambiente_id FK (CASCADE), nome,
                              largura_mm, altura_mm, profundidade_mm (nulos),
                              preco_venda INT, terceirizado BOOL,
                              custo_terceiro INT (centavos, nulo), ordem,
                              pedido_compra_id FK nulo (F5)
fabrica_materiais (nova, F2): id, movel_id FK (CASCADE), produto_id FK,
                              consumo INT (na unidade de consumo: mm², mm, un),
                              custo_unitario INT (centavos POR UNIDADE DE COMPRA,
                                                  copiado do cadastro ao incluir)

ordens_servico (+, nulos)
├── fase_fabrica            VARCHAR(30)   F3 (F2 já grava MEDICAO/ELABORACAO/…)
├── data_instalacao         DATE          F3
├── compra_liberada_em      DATETIME      F3
├── compra_liberada_por     VARCHAR(100)  F3
└── compra_liberada_motivo  TEXT          F3

ordem_servico_itens (+, nulos)
├── fabrica_orcamento_id   FK nulo   F2  ← marca o item GERADO pela aprovação
├── fabrica_movel_id       FK nulo   F2  ← no item do móvel
├── quantidade_separada    FLOAT     F4
└── custo_real             INTEGER   F4

fabrica_fases_log (nova, F3) — só INSERT (RC18)
└── id, os_id, fase_anterior, fase_nova, evento (AVANCO, RETROCESSO,
    APROVACAO, LIBERACAO_COMPRA, AVISO_IGNORADO), motivo, usuario, ocorrido_em
```

**Migrations (uma por fase):** F1 `produtos`; F2 `configuracoes_os.modo_fabrica`,
`ordens_servico.fase_fabrica`, `ordem_servico_itens.fabrica_*`; F3 o resto da
OS e `fabrica_travar_etapas`; F4 `quantidade_separada` e `custo_real`.

---

## 5. Cálculos (`app/services/fabrica/calculo.py`, funções puras)

```python
def consumo_com_perda(consumo: int, perda_bp: int, sofre_perda: bool) -> int:
    # ⌈ consumo × (10000 + perda_bp) ÷ 10000 ⌉, em inteiro (sem float)
    if not sofre_perda: return consumo
    return -(-consumo * (10000 + perda_bp) // 10000)

def quantidade_de_compra(consumo_total: int, consumo_por_unidade: int) -> int:
    # ⌈ consumo_total ÷ consumo_por_unidade ⌉  — chapas, rolos, unidades
    return -(-consumo_total // consumo_por_unidade)

def custo_do_material(consumo: int, perda_bp, sofre_perda, consumo_por_unidade,
                      custo_unitario: int) -> int:
    # fração de chapa, sem arredondar a chapa — é o custo do MÓVEL
    # round_half_up(consumo_com_perda × custo_unitario ÷ consumo_por_unidade)

def itens_da_aprovacao(orcamento) -> list[ItemGerado]:
    # móveis → 1 item SERVICO cada; insumos → somar consumo_com_perda por
    # produto em TODOS os móveis, depois quantidade_de_compra UMA vez
```

**Exemplos que viram teste (RNC04):**

| Caso | Entrada | Resultado |
|---|---|---|
| Resumo | 12 m² MDF, perda 10%, chapa 2750×1850 | 13,2 m² → 2,59 → **3 chapas** |
| Soma antes de arredondar | 3 móveis × 1 m², perda 10%, mesma chapa | 3,3 m² → 0,65 → **1 chapa** (não 3) |
| Sem perda | 24 dobradiças, perda 10%, `sofre_perda = false` | **24** |
| Fita | 37,5 m, perda 10%, rolo 50 m | 41,25 m → **1 rolo** |
| Exato | 2 chapas exatas, perda 0 | **2** (não 3) |
| Custo do móvel | 1 m² de chapa de R$ 300,00 (5,0875 m²), perda 10% | R$ 64,86 |

**Validações:** insumo sem `unidade_consumo`/`consumo_por_unidade` não entra
na lista de material (o erro aponta o produto e leva ao cadastro);
`consumo_por_unidade > 0`; `perda_bp` entre 0 e 5000; `sinal_bp` entre 0 e 10000.

---

## 6. As 10 etapas

| `fase_fabrica` | Rótulo | Status derivado | Trava para avançar | Quem avança |
|---|---|---|---|---|
| `MEDICAO` | Medição | ABERTA | ≥ 1 foto na OS | manual |
| `ELABORACAO` | Em elaboração | ABERTA | versão com ≥ 1 móvel e preço > 0 | **enviar a versão** move sozinho |
| `AGUARDANDO_APROVACAO` | Aguardando aprovação | AGUARDANDO_APROVACAO | uma versão aprovada | **aprovar** move sozinho (evento APROVACAO) |
| `AGUARDANDO_SINAL` | Aguardando sinal | AGUARDANDO_APROVACAO | recebido ≥ sinal exigido **ou** compra liberada | manual (o botão mostra "faltam R$ X") |
| `SEPARACAO_COMPRA` | Separação e compra | AGUARDANDO_PECAS | todo insumo com `quantidade_separada == quantidade` (RC20) | manual |
| `EM_PRODUCAO` | Em produção | EM_ANDAMENTO | — (o campo `etapa` de hoje vira a sub-etapa: Corte, Montagem interna) | manual |
| `PRONTO_EXPEDICAO` | Pronto para expedição | EM_ANDAMENTO | `data_instalacao` preenchida | manual |
| `EM_INSTALACAO` | Em instalação | EM_ANDAMENTO | — | manual |
| `VISTORIA_FINAL` | Vistoria final | AGUARDANDO_RETIRADA | — | manual |
| `ENTREGUE` | Entregue | FINALIZADA | o `/finalizar` de sempre (saldo coberto) | **finalizar** move sozinho |

- **Sinal exigido** = ⌈ total da versão aprovada × `sinal_bp` ÷ 10000 ⌉.
  **Recebido** = `valor_entrada + adiantamentos_anteriores + Σ pagamentos`
  (a soma da finalização).
- **Avançar** só para a próxima. **Retroceder** para qualquer anterior, sempre
  com motivo; não volta para antes de `SEPARACAO_COMPRA` se houver item separado
  (estorne a separação antes). Voltar para `ELABORACAO` com versão aprovada
  "desaprova" (D12).
- **Cancelar** é o `/cancelar` de sempre; a fase fica onde estava e o log
  registra. **Reabrir** uma ENTREGUE volta para `VISTORIA_FINAL`.
- Com `fabrica_travar_etapas = false`, a trava vira aviso: o usuário confirma
  com motivo e o log grava `AVISO_IGNORADO`. As automáticas (enviar, aprovar,
  finalizar) não têm aviso, são sempre verdade.
- `update_ordem_servico` passa a **recusar** `status` em OS com `fase_fabrica`
  (o status vem da fase). Nas outras, nada muda.

---

## 7. API — router `/api/v1/fabrica` (`endpoints/fabrica.py`)

Todas as rotas checam: segmento marcenaria, modo fábrica ligado (exceto
leitura de OS que já tem fase) e a OS ser de fábrica. Erros em português, no
padrão dos `*_exce` do projeto.

| Método e rota | Faz | Fase |
|---|---|---|
| `GET /fabrica/os/{numero_os}/orcamentos` | lista as versões (resumo) | F2 |
| `POST /fabrica/os/{numero_os}/orcamentos` | nova versão vazia ou **copiando** `{copiar_de: id}` | F2 |
| `GET /fabrica/orcamentos/{id}` | a árvore inteira, com custos e totais calculados | F2 |
| `PUT /fabrica/orcamentos/{id}` | **salva a árvore inteira** (só RASCUNHO); devolve com totais | F2 |
| `POST /fabrica/orcamentos/{id}/enviar` | RASCUNHO → ENVIADO; OS → AGUARDANDO_APROVACAO | F2 |
| `POST /fabrica/orcamentos/{id}/aprovar` | ENVIADO → APROVADO; escreve os itens; as outras ENVIADAS → RECUSADO | F2 |
| `POST /fabrica/orcamentos/{id}/recusar` | `{motivo}` | F2 |
| `GET /fabrica/os/{numero_os}/trilho` | fase, próxima, travas (`[{codigo, texto, ok}]`), sinal exigido/recebido, log | F3 |
| `POST /fabrica/os/{numero_os}/fase` | `{fase, motivo?}`; 409 com a lista de travas se travado | F3 |
| `POST /fabrica/os/{numero_os}/liberar-compra` | `{motivo}` obrigatório; só gestor | F3 |
| `GET /fabrica/os/{numero_os}/separacao` | insumos: a separar, separado, local no estoque (sem custo) | F4 |
| `POST /fabrica/os/{numero_os}/separacao` | `{codigo \| item_id, quantidade}` — bipe; baixa a diferença | F4 |
| `POST /fabrica/os/{numero_os}/separacao/estornar` | `{item_id, quantidade, motivo}` | F4 |
| `GET /fabrica/os/{numero_os}/margem` | por móvel e total: orçado × real (só quem vê custo) | F4 |
| `POST /fabrica/moveis/{id}/pedido-servico` | cria o pedido SERVICO à central de corte | F5 |

O "salvar a árvore inteira" (em vez de uma rota por ambiente/móvel/material)
é de propósito: a tela edita a árvore em memória e salva de uma vez, o backend
recalcula tudo e não há estado parcial. A árvore de uma cozinha tem dezenas de
linhas, não milhares.

`PUT /configuracoes/os` (já existe) ganha `modo_fabrica` e
`fabrica_travar_etapas`. O schema da OS devolve `fase_fabrica` e
`data_instalacao` (nulos para quem não usa).

**Permissões** (linha "Fábrica" em Cargos, no padrão de
`services/compras/permissoes.py`, fora da conta do nível do cargo):
`orcar` (montar/enviar), `aprovar` (aprovar versão, liberar compra),
`separar` (tela de separação), `avancar` (mudar fase). Ver custo e margem
segue a regra de custo que já existe (D14 de Compras).

---

## 8. Telas (frontend)

Pasta nova `frontend/src/modules/order-service/fabrica/` (components,
composables, services, types, schemas), no padrão de `ordens/`. Tudo
aparece **só** quando a OS tem `fase_fabrica`.

| Tela | Onde | Fase |
|---|---|---|
| **Seção "Insumo de marcenaria"** no cadastro do produto: unidade de consumo; para M2, largura × altura da chapa em mm (o front calcula mm²); para M, comprimento do rolo; "sofre perda". Só no segmento marcenaria | `modules/products` | F1 |
| **Chave "Modo fábrica"** e "Travar etapas" em Configurações › Ordens de Serviço, com texto explicando | `modules/configuracoes` | F2/F3 |
| **Aba "Orçamento"** na OS: seletor de versão; árvore ambiente → móvel → material; consumo em m²/m/un (o front converte para inteiro); custo e preço sugerido por móvel; totais; botões Nova versão, Copiar, Enviar, Aprovar, Recusar | `fabrica/components/OrcamentoFabricaTab.vue` | F2 |
| **Impressão do orçamento** (proposta ao cliente): ambientes, móveis com medidas e preço, total, sinal, validade. Sem material e sem custo | `fabrica/components/OrcamentoFabricaPrint.vue` | F2 |
| **Trilho** no topo da OS: as 10 etapas, a atual destacada, botão "Avançar" que lista as travas, "Voltar" com motivo, log recolhível; sinal exigido × recebido; data de instalação | `fabrica/components/TrilhoFabrica.vue` | F3 |
| **Separação** (`/fabrica/separacao/:numero_os`): lista de insumos com local na prateleira, campo do leitor sempre focado (o mesmo do Recebimento de Compras), barra de progresso, funciona no celular na rede da loja | `fabrica/views/SeparacaoView.vue` | F4 |
| **Margem** na Visão Geral da OS: por móvel e total, orçado × real | `fabrica/components/MargemFabrica.vue` | F4 |

Na OS de fábrica, a aba "Serviços e Peças" mostra os itens gerados **somente
leitura** (editar é pelo orçamento) e o campo `etapa` do segmento passa a ser
a sub-etapa de produção.

---

## 9. Fases de entrega

Cada fase termina com: testes novos, a **suíte inteira do backend** passando
(F12), `vue-tsc --noEmit`, `vite build`, a tela vista no app rodando,
`build:sidecar` e uma seção "Entrega da fase" neste documento (como §12–§17 do
plano de Compras).

### F1 — Insumo (2–3 dias)
- Migration + model + schema do produto (3 colunas); a seção no cadastro.
- `services/fabrica/calculo.py` com os exemplos da §5 como teste.
- **Prova F12:** produto sem as colunas sai idêntico no GET/PUT; PDV, XML e
  Compras não mudam.

### F2 — Orçamento que gera a OS (1,5–2 semanas)
- Chave `modo_fabrica`; OS nova de Planejados nasce com `fase_fabrica = MEDICAO`
  (em `create_ordem_servico`, só se modo ligado + segmento + tipo).
- Tabelas `fabrica_*`, `services/fabrica/orcamentos.py`, router das versões.
- Aprovar: gera os itens (§2), recalcula o total da OS
  (`_recalcular_valor_total_os`), marca os itens com `fabrica_orcamento_id`;
  aprovar outra versão troca os itens (D12).
- Enviar/aprovar já movem `fase_fabrica` (sem travas ainda — elas vêm na F3).
- Aba Orçamento + impressão.
- **Testes:** os exemplos da §5 de ponta a ponta (aprovar → item com 3 chapas);
  versão aprovada única; re-aprovação troca e não duplica; RASCUNHO só;
  Necessidades pedem chapas inteiras para a OS; Reforma e OS sem modo não
  ganham fase; modo desligado = 403 nas rotas.
- **Já serve sozinha:** a fábrica orça por móvel, imprime a proposta e compra
  pelas Necessidades.

### F3 — Trilho (1 semana)
- Colunas restantes da OS, `fabrica_fases_log`, `fabrica_travar_etapas`.
- `services/fabrica/trilho.py`: tabela da §6 como dado; `travas(os)`,
  `avancar`, `retroceder`, `status_derivado`; `update_ordem_servico` recusa
  status manual em OS de fábrica; finalizar/cancelar/reabrir gravam log e fase.
- **Sinal (RC04):** `demanda_os` ganha "pode comprar?" — OS em fase anterior a
  `SEPARACAO_COMPRA` sem `compra_liberada_em` **reserva mas não gera
  necessidade**. Liberar compra grava log.
- **Fila (RC12):** `demandas_por_produto` ordena por
  `coalesce(data_instalacao, data_criacao)`; o aviso do painel compara com
  `data_instalacao` quando houver.
- Trilho na tela.
- **Testes:** a tabela da §6 inteira (cada trava, aviso × trava, retroceder,
  motivo obrigatório); status derivado em cada fase; dashboard/lista de OS
  contam certo; sem sinal = sem necessidade, liberado = com; OS sem
  `data_instalacao` mantém a ordem de hoje (prova F12 da fila).

### F4 — Separação e margem (1 semana)
- Colunas `quantidade_separada` e `custo_real`.
- `services/fabrica/separacao.py`: bipe → acha o item pelo código do produto
  (o mesmo achador do Recebimento) → registra SAÍDA da diferença
  (`registrar_movimentacao`, origem ORDEM_SERVICO) → grava `custo_real`.
- **Regra única (D6):** `_itens_de_produto` passa a usar
  `quantidade − coalesce(quantidade_separada, 0)` na baixa e no estorno;
  `demanda_os` idem na reserva. Cancelar estorna também o separado.
- Tela de separação e margem.
- **Testes:** separou tudo e finalizou = **uma baixa só**; separou metade =
  finaliza baixando a outra metade; cancelar devolve o separado; reabrir não
  devolve o separado; reserva cai ao separar; **oficina e assistência:
  baixa idêntica** (item sem `quantidade_separada`); separar mais que a
  quantidade = 409.

### F5 — Terceirizados (3–5 dias)
- Móvel `terceirizado`: botão gera pedido SERVICO ao fornecedor (central de
  corte), ligado em `fabrica_moveis.pedido_compra_id`; a trava de
  `SEPARACAO_COMPRA` passa a exigir esse pedido **recebido**; o custo real do
  móvel usa o valor recebido do pedido.
- O que o pedido guarda depende da pergunta 4 da §12 (arquivo do plano de
  corte? só texto?). Detalhar quando houver a resposta.

### F6 — Depois do piloto
Cotação, retalho de chapa, relatório de margem por projeto, retrabalho,
montador (DC6), checklist de medição. Só com pedido da loja piloto.

---

## 10. O que NÃO entra

- **Projeto 3D / importar do Promob** — outro produto.
- **Plano de corte otimizado** (encaixar peças na chapa) — Promob Cut e Corte
  Certo fazem; aqui a perda é o fator %.
- **Retalho de chapa** como estoque próprio — sobra volta ao saldo (DC7).
- **Kanban/PCP por peça** — a etapa é por OS.
- **Offline no celular** — a separação funciona no celular na rede da loja.
- **Orçamento por m² na marcenaria de bairro** — continua pelo catálogo
  (decisão de 16/09).
- **Aprovação por móvel** — aprova-se a versão (D11).

---

## 11. Riscos

| Risco | Defesa |
|---|---|
| Código da OS compartilhado com três segmentos em produção | Colunas nulas, chave desligada, `if os.fase_fabrica` como única porta; suíte inteira em cada fase |
| Baixa em dois lugares | Uma fórmula só (`quantidade − separada`) usada na baixa, estorno e reserva; teste "separou e finalizou = uma baixa" |
| Status derivado errado tira a OS do filtro certo | A tabela da §6 vira teste, fase por fase |
| Conversão m² → chapa compra a mais ou a menos em silêncio | Cálculo puro, inteiro, com os exemplos da §5 |
| Re-aprovar duplica itens | Itens gerados marcados por `fabrica_orcamento_id`; aprovar apaga os da versão anterior antes de gravar; teste |
| Total da OS muda e o adiantamento fica maior que o total | Aprovar versão mais barata com adiantamento acima do total: aviso na tela; o crédito segue a regra de hoje da finalização |
| Sidecar e PyArmor | `build:sidecar` no fim de cada fase |

---

## 12. Perguntas para o dono da fábrica (piloto)

Nenhuma bloqueia a F1 ou a F2. Cada uma diz o que ajusta.

1. **Travar ou só mostrar** as etapas? → valor de `fabrica_travar_etapas`.
2. **Prazo** do fornecedor de chapa? → se a liberação antes do sinal vai ser
   exceção ou rotina.
3. Compra o mesmo insumo de **mais de um fornecedor**? → o que Compras mostra
   primeiro.
4. O pedido à **central de corte** vai pelo software de corte ou por
   e-mail/WhatsApp? → detalhe da F5.
5. Alguém **confere a nota** na chegada? → se a XML × pedido vai ser usada.
6. **Sobra de chapa** é reaproveitada? → confirma DC7 (ou puxa o retalho para
   F6).
7. **Montador:** funcionário ou contratado por instalação? → DC6.
8. O **sinal** padrão é 50%? Muda por cliente? → padrão de `sinal_bp`
   (editável por versão de qualquer jeito).
9. Quem **mede** e quem **orça** são pessoas diferentes? → permissões.
10. A lista de **ambientes** está certa? → `AMBIENTES` no segmento.
11. **Perda** padrão é 10%? Muda por material? → padrão de `perda_bp`
    (por versão nesta entrega; por insumo, se ele pedir).

---

## 13. Do resumo ao código (RC01–RC20)

| RC | O que é | Onde | Situação |
|---|---|---|---|
| RC01 | Reserva com perda | Aprovação gera itens com perda | F2 |
| RC02 | Consumo × compra, arredonda para cima | Produto + `calculo.py` | F1 |
| RC03 | Necessidade por insumo, todas as OS | Compras fase 6 | ✅ |
| RC04 | Compra só após o sinal | `demanda_os` + liberação | F3 |
| RC05 | Pedido por fornecedor, último preço | Compras fase 2 | ✅ |
| RC06 | Pedido × itens da OS | Compras fase 6 | ✅ |
| RC07 | Status de compra no item | Painel "Compras desta OS" | ✅ |
| RC08 | Previsão × instalação | Painel usa `data_instalacao` | F3 |
| RC09 | Cancelar libera reserva | Reserva calculada | ✅ |
| RC10 | Recebimento bipado e parcial | Compras fase 3 | ✅ |
| RC11 | Custo real no livro, OS congelada | Compras fase 3 + `custo_real` à parte | ✅ / F4 |
| RC12 | Alocação por instalação | Fila por `data_instalacao` | F3 |
| RC13 | Título a pagar no recebimento | Compras fase 3 | ✅ |
| RC14 | Margem orçada × real | `custo_real` na separação | F4 |
| RC15 | Central de corte = pedido de serviço | `fabrica_moveis.pedido_compra_id` | F5 |
| RC16 | Custo real do serviço × orçado | Idem | F5 |
| RC17 | Montador terceirizado | — | depois do piloto |
| RC18 | Log de pedido, alocação, liberação | `compras_log` ✅ + `fabrica_fases_log` | F3 |
| RC19 | Almoxarife/marceneiro sem preço | Cargos + separação sem custo | F3–F4 |
| RC20 | Trava em "Separação e compra" | Trilho | F3 |

---

## 14. Entrega da F1 — Insumo (05/10/2026)

**Banco:** `produtos.unidade_consumo`, `consumo_por_unidade`, `sofre_perda`
(migration `f1c7a2d9e3b4`, `ADD COLUMN` coluna a coluna pela ausência; sem
`batch_alter_table`, porque `produtos` é alvo de FK e o batch recria a tabela).

**Rota própria, fora do cadastro do produto:** `GET/PUT
/fabrica/produtos/{id}/insumo` (`endpoints/fabrica.py`,
`services/fabrica/insumo.py`). O router inteiro responde 403
`SEGMENTO_SEM_FABRICA` fora da marcenaria; cada rota pede a permissão
`produto`. `unidade_consumo` nulo desliga e limpa rendimento e perda. O
`ProdutoRead` não ganhou campo: o payload de `/produtos` é o mesmo para todos.

**Cálculo puro** (`services/fabrica/calculo.py`): `consumo_com_perda`,
`quantidade_de_compra`, `custo_do_material`, `quantidades_por_insumo` (soma
antes de arredondar). Só inteiros. Os exemplos da §5 são os testes.

**Tela:** seção "Insumo da fábrica" no modal do produto (só com
`isMarcenaria`, carregada sob demanda — chunk próprio no build): tipo (chapa
m², fita metro, ferragem unidade), medidas da chapa em mm (o front calcula a
área), metros por rolo ou unidades por embalagem, "sofre perda". Pasta nova
`frontend/src/modules/order-service/fabrica/`.

**Verificado:** 11 testes do cálculo, 15 da rota (trava por segmento em 5
segmentos, permissão, gravar, desligar, 422 de dado inválido, 404, cadastro
do produto idêntico antes × depois e PUT do produto não apaga o insumo), 2 da
migration (com `PRAGMA foreign_keys=ON`, idempotente, base sem produtos);
front: 4 testes das conversões, `vue-tsc` limpo, `vite build`.
**Não verificado:** a seção num app rodando; sidecar não regerado.

---

## 15. Entrega da F2 — Orçamento que gera a OS (05/10/2026)

**Banco** (migration `a2d8b3e5f107`): tabelas `fabrica_orcamentos`,
`fabrica_ambientes`, `fabrica_moveis` (já com `pedido_compra_id` para a F5),
`fabrica_materiais`; colunas `configuracoes_os.modo_fabrica`,
`ordens_servico.fase_fabrica`, `ordem_servico_itens.fabrica_orcamento_id` e
`fabrica_movel_id`. As FKs do item entram como INTEGER simples na migration
(o SQLite não acrescenta constraint a tabela existente); valem em banco novo.

**Quem entra no trilho** (`services/fabrica/modo.py`): marcenaria + chave
ligada + tipo Planejados. Achado: a tela só grava `tipo_trabalho` quando o
atendente MEXE no seletor — OS sem o campo vale o primeiro tipo do segmento,
como a tela mostra. Desligar a chave não tira ninguém do trilho.

**Rotas** (`/fabrica`): `GET /insumos` (busca só o que é insumo),
`GET|POST /os/{n}/orcamentos`, `GET|PUT /orcamentos/{id}`,
`POST /orcamentos/{id}/enviar|aprovar|recusar`. Permissão: a da OS
(`servico`). Config: `modo_fabrica` no PUT de configurações de OS que já existia.

**Aprovar** (`services/fabrica/orcamentos.py`): item SERVIÇO por móvel
(preço, visível) + item PRODUTO por insumo somado (chapas inteiras, valor 0,
invisível, custo congelado); troca só os itens com `fabrica_orcamento_id`;
recalcula o total da OS; a outra versão aprovada/enviada vira RECUSADO com
o motivo. O item do móvel só leva custo quando é terceirizado — o material já
entra no custo pela baixa do estoque, e contaria duas vezes.

**OS:** item gerado não se edita nem se apaga pela OS (409; cadeado na aba
Serviços e Peças). Item lançado à mão continua livre.

**Tela:** aba **Orçamento** na OS (só com `fase_fabrica`, sob demanda):
versões, ambientes (sugestões da lista do segmento), móveis com medidas,
material pelo seletor de insumo, terceirizado, preço com sugestão
(custo + margem padrão de Produtos), totais/margem/sinal em prévia
(`utils/calculo.ts` espelha o backend, com os mesmos exemplos nos testes),
"material que vai para a OS", enviar/aprovar (com confirmação)/recusar (com
motivo), **proposta A4** sem material e sem custo. Chave "Modo fábrica" em
Configurações › Ordens de Serviço (só marcenaria).

**Decidido na implementação (rever na F3):**
- Criar a primeira versão move MEDICAO → ELABORACAO sem trava (a trava da
  foto vem com o trilho).
- O **status** da OS ainda não é derivado da fase — é a F3. Até lá, fase e
  status andam separados.
- Custo e margem aparecem para quem tem a permissão da OS; esconder do
  marceneiro/almoxarife vem com a linha "Fábrica" em Cargos (F3).

**Verificado:** 22 testes do orçamento (quem entra no trilho em 4 casos,
desligar depois, 403 fora da marcenaria, versões, custos e chapas, produto
que não é insumo, custo copiado × de hoje, cópia de versão, enviar, aprovar
escreve itens e reserva para Compras, re-aprovação troca sem duplicar e
mantém o item manual, item gerado travado, vencido, recusar, busca de
insumo, OS comum continua editando) + 2 da migration. Suíte do backend:
2119 passaram + 1 que só falhou por eu ter rodado sem o plugin de log (passa
normal). Front: 153 testes, `vue-tsc` limpo, `vite build` (aba em chunk
próprio).
**Não verificado:** as telas num app rodando; impressão real da proposta;
sidecar não regerado.

---

## 16. Entrega da F3 — Trilho (05/10/2026)

**Banco** (migration `b4e9c1a7d2f3`): `ordens_servico.data_instalacao`,
`compra_liberada_em/_por/_motivo`; `configuracoes_os.fabrica_travar_etapas`;
tabela `fabrica_fases_log` (só INSERT).

**Trilho** (`services/fabrica/trilho.py`): a tabela da §6 como dado
(`ROTULOS`, `STATUS_DA_FASE`, `AVANCO_POR_ACAO`). `mudar_fase` é a única
porta: muda a fase, **deriva o status** e grava o log. Travas para SAIR:
- Medição: ao menos uma foto;
- Aguardando sinal: recebido (a soma da finalização) ≥ sinal da versão
  aprovada, ou compra liberada pelo gestor;
- Separação e compra: **todo o material no estoque para esta OS** (a fila do
  painel "Compras desta OS"). A F4 troca por "tudo separado/bipado";
- Pronto para expedição: data de instalação marcada.
Enviar, aprovar e finalizar não passam pelo "Avançar" (409 com a instrução).
Com a trava desligada (padrão), pendência devolve 422 `MOTIVO_OBRIGATORIO`;
com motivo, avança e o log guarda `AVISO_IGNORADO`. Ligada, 409
`TRAVA_PENDENTE`. Voltar exige motivo e, com orçamento aprovado, não passa
de "Aguardando sinal" (mudar o aprovado = nova versão).

**OS de sempre** (`services/ordem_servico.py`, só ganchos, no-op fora da
fábrica): status manual recusado (409) na OS da fábrica; finalizar com a
trava ligada só a partir da Vistoria final; finalizar leva a ENTREGUE;
cancelar grava no log; reabrir volta para a etapa (ENTREGUE → Vistoria
final) com o status dela. O orçamento (F2) agora move a fase pelo trilho
(log de AVANCO/APROVACAO/RETROCESSO); com a trava ligada e sem foto, criar a
versão não tira a OS da Medição e enviar é recusado.

**Compras:** `DemandaOS` ganhou `data_instalacao` e `pode_comprar`.
- RC04: OS da fábrica antes do sinal (sem liberação) **reserva** (aparece em
  `reservado_os`, marcada `aguardando_sinal`) mas **não pesa na compra** —
  nem pelo mínimo — e o pedido gerado não é ligado a ela; o painel da OS
  avisa (`compra_bloqueada`).
- RC12: a fila ordena por instalação; sem data, pela abertura (OS comum:
  igual a antes).
- RC08: o aviso de atraso do painel compara com a instalação quando houver.

**Cargos:** linha **Fábrica** (só marcenaria, fora da conta do nível):
Visualizar = ver custo e margem; Gerenciar = orçar, enviar, responder pelo
cliente, liberar compra. Avançar/voltar/instalação = permissão de Serviços.
Sem a permissão de custo, o orçamento e a busca de insumo vêm com custo
nulo e a tela esconde custo, margem e preço sugerido.

**Rotas:** `GET /fabrica/os/{n}/trilho`, `POST .../avancar`, `.../voltar`,
`.../liberar-compra`, `PUT .../instalacao`. Config: `fabrica_travar_etapas`.

**Tela:** trilho no topo da OS (etapas, o que falta, sinal, instalação,
Avançar com motivo quando há pendência, Liberar compra, Voltar com motivo,
histórico); seletor de status travado na OS da fábrica; "Travar etapas" em
Configurações › Ordens de Serviço; aviso de sinal no painel de Compras.

**Verificado:** 15 testes do trilho (status acompanha o orçamento, status
manual 409 × OS comum livre, aviso com motivo, trava, sinal pago, avanço
por ação, instalação, foto, voltar, finalizar/reabrir, sem sinal não compra
e liberar compra, fila por instalação, Cargos sem custo e com custo) + 1 da
migration. Suíte do backend: **2137 passaram**, 1 pulado. Front: 156 testes
(+3 da linha de Cargos), `vue-tsc` limpo, `vite build`.
**Não verificado:** as telas num app rodando; sidecar não regerado.

---

## Fontes

- Resumo do Alan: "Módulo de Compras para Marcenaria — Especificação de
  Requisitos" (RC01–RC20, RNC01–RNC05, DC1–DC7).
- `docs/segmento-marcenaria-plano.md` (16/09/2026) — fluxo e decisões do dono.
- `docs/compras-plano.md` — módulo de Compras, fases 1–6 (§12–§17).
- Código conferido em 05/10: `core/segmentos/definicoes/marcenaria.py`,
  `db/models/ordem_servico*.py`, `db/models/objeto_servico.py`,
  `db/models/configuracao_os.py`, `services/ordem_servico.py`
  (`_itens_de_produto`, `_movimentar_estoque_os`, `finalizar_ordem_servico`,
  `update_ordem_servico`), `services/compras/demanda_os.py`,
  `services/compras/necessidades.py`.
- Mercado (pesquisa de 16/09): Calcme, GestorMarceneiro, Planejados Pro,
  WoodOrça+, Promob (ERP/MRP, Cut Pro), Corte Certo.
