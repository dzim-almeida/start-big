# Plano: Central de Etiquetas (estoque e envio)

Escrito em 27/09/2026, na branch `feat/segmento-marcenaria` (HEAD `f040e8d`).
Nasceu de um relatório do Alan ("Central de Etiquetas — Estoque & Expedição"),
debatido em conversa e confrontado com o código e com o mercado (§3).

Esse debate mudou três coisas no relatório original:

1. **Quem imprime é o Tauri, não o FastAPI.** O backend roda no servidor da loja,
   e a impressora de etiqueta está plugada no terminal de quem imprime. O caminho
   de impressão direta já existe (`src-tauri/src/impressao/local.rs`, usado
   pelo cupom).
2. **Não sabemos que impressora o cliente tem**, então o layout não pode
   pertencer a uma linguagem de impressora. Vira um **modelo neutro em mm**, e
   cada linguagem tem um tradutor (§5).
3. **Fardo/caixa não é feature de etiqueta, é feature de produto.** Mexe em PDV,
   estoque e NF-e, e ganha plano próprio (§8).

Escopo: a aba **Etiquetas** dentro do Estoque, com duas sub-abas (Estoque e
Envio) e o motor que as duas usam. Fora de escopo: etiqueta oficial de
transportadora, com rastreio (§10); etiqueta de peça de marcenaria, que é
gerada pelo software da seccionadora/CNC a partir do código `PRJ`
(`segmento-marcenaria-plano.md`).

**Nada começa a ser codado antes de as decisões da §4 estarem aceitas.**

> **Status (27/09/2026, branch `etiquetas`):** decisões aceitas pelo Alan, e as
> **fases 1 e 2 estão implementadas** — ver §12 para o que foi entregue, o que
> mudou em relação a este plano e o que falta conferir na loja.

---

## 0. O que "pronto" significa

| # | Critério de aceite | Hoje |
|---|---|---|
| E1 | Imprimir etiqueta em **qualquer** impressora que tenha driver no Windows | não existe etiqueta |
| E2 | Com Zebra, Elgin, Argox ou TSC, imprimir **sem diálogo** e rápido | só o cupom (ESC/POS) usa impressão direta |
| E3 | Deu entrada de 40 unidades? **Um clique** gera as 40 etiquetas | não existe |
| E4 | O lojista ajusta o layout **arrastando campos**, sem saber o que é ZPL | não existe |
| E5 | O que aparece no preview é o que sai no papel, na posição certa | — |
| E6 | Folha Pimaco meio usada: **pular as N primeiras** posições | — |
| E7 | Etiqueta de volume de entrega ("Volume 2/5") a partir da OS ou da Venda | não existe |
| E8 | Quem emite NF-e imprime o **DANFE Simplificado – Etiqueta** da nota | não existe |
| E9 | Um modelo criado num terminal **aparece em todos** os terminais da loja | — |
| E10 | Quem não usa etiqueta **não vê nada mudar** no Estoque além da aba nova | cláusula de não-regressão |

---

## 1. O que já existe e o plano aproveita

| Peça | Onde | Uso aqui |
|---|---|---|
| Impressão crua no spooler | `src-tauri/src/impressao/local.rs` → `imprimir_raw`, `listar_impressoras` | Linguagens nativas (ZPL, TSPL, PPLA…) |
| Servidor de impressão em rede | `src-tauri/src/impressao/rede.rs` | Terminal sem impressora de etiqueta usa a de outro |
| Config de impressão por terminal | `shared/stores/impressao.store.ts` (localStorage) | Ganha os campos da impressora de etiqueta (§6) |
| Impressão via driver com `@page` forçado | `shared/utils/print.utils.ts` → `imprimirComPagina` | Saída "driver do Windows" e A4 Pimaco |
| QR Code | `qrcode` (já é dependência) | Elemento QR do modelo |
| Abas do Estoque | `products/shared/constants/tabs.constants.ts` + `BaseTab2` | Terceira aba |
| Movimentação de entrada | `MovimentacaoModal.vue`, `movimentacao_estoque.py` | "Etiquetas desta entrada" |

O que falta: um produto tem **um** código de barras só (`produto.codigo_barras`,
mais `produto_fiscal.gtin_tributavel`). Não há NF-e de entrada importada por XML,
então a origem das "etiquetas da entrada" é a movimentação de estoque.

---

## 2. Onde a aba mora (arquitetura de pastas)

A aba é a **terceira do Estoque** (`Estoque | Fornecedores | Etiquetas`) e segue
o visual das outras duas: `PageReview` no topo, `BaseTab2`, `BaseSearchInput`,
`BaseFilter`, tabela no estilo da `FornecedorTable` e modais no padrão do
`ProductModal`.

Como ficou (fases 1 e 2). O que ainda não existe está marcado com *(fase N)*.

```
frontend/src/modules/products/labels/          ← a tela (padrão de inventory/ e suppliers/)
├── components/
│   ├── EtiquetasTab.vue                        catálogo na largura toda (sub-aba Envio: fase 5)
│   ├── estoque/ProdutosEtiquetaTable.vue       catálogo, com a situação do código de cada produto
│   ├── estoque/FilaEtiquetasDrawer.vue         painel pela direita: modelo, preview, pular, quantidades, imprimir
│   ├── estoque/EntradasRecentesModal.vue       "etiquetas desta entrada" (E3)
│   ├── estoque/CalibracaoEtiquetaModal.vue     deslocamento do terminal + página de teste
│   ├── modelo/ModelosEtiquetaModal.vue         modelos da loja: listar, criar, editar, excluir
│   ├── modelo/ModeloEtiquetaForm.vue           medidas + o que imprimir + preview ao vivo
│   └── envio/                                  (fase 5)
├── composables/useModelosEtiqueta.ts           presets + modelos da loja num só seletor
├── services/modeloEtiqueta.service.ts
├── store/filaEtiquetas.store.ts                a fila (o card do produto também alimenta)
└── types/etiquetas.types.ts

frontend/src/shared/etiquetas/                 ← o motor (Venda e OS também chamam)
├── modelo.ts             tipos do modelo neutro (§5.1) + geometria do papel
├── codigoBarras.ts       escolha e validação da simbologia (§5.2)
├── campos.ts             catálogo de variáveis e resolução a partir do produto (§5.3)
├── layoutAuto.ts         gera os elementos a partir do tamanho + blocos escolhidos
├── presets.ts            presets de fábrica (rolos, gôndola, Pimaco Carta, A4)
├── paginacao.ts          distribui nas páginas, "pular N posições"
├── teste.ts              página de teste (contorno + cruz)
├── useImpressaoEtiquetas.ts   monta o trabalho, injeta o @page e abre o diálogo
├── components/           EtiquetaView (render HTML em mm), BarrasSvg, QrSvg,
│                         EtiquetaPreview, EtiquetasImpressao
├── styles/print-etiquetas.css
├── render/zpl.ts  tspl.ts  ppla.ts  pplb.ts  epl.ts  bitmap.ts   (fase 4)
└── editor/                                                         (fase 3)

backend-fastapi/app/
├── db/models/modelo_etiqueta.py
├── schemas/modelo_etiqueta.py
├── db/crud/modelo_etiqueta.py
└── api/v1/endpoints/etiquetas.py
```

**Por que o motor fica em `shared/`:** a etiqueta de envio também terá atalho
na Venda e na OS ("Imprimir etiquetas de volume"). Com o motor dentro de
`products/`, vendas e OS importariam código de outro módulo.

**Ajuste obrigatório na `ProductsView.vue`:** título, descrição e botão do topo
decidem a aba com ternário de duas opções (`activeTab === 'product' ? … : …`).
Com três abas isso vira um mapa por aba, e a aba entra como componente próprio
(`<EtiquetasTab />`), sem inchar mais a view.

---

## 3. O que o mercado faz

| Sistema | Como resolve | Lição para nós |
|---|---|---|
| **Bling** | **Não tem** configuração de impressora: imprime pelo navegador, e a pessoa acerta tamanho e papel **no driver** | A saída via driver é o mínimo que todo mundo aceita, e funciona em qualquer impressora |
| **Tiny / Olist** | Cadastro de etiqueta com **medidas exatas** (largura, altura, margem, espaço entre colunas, nº de colunas), modo **Página** (folha) ou **Bobina** (térmica), campos posicionados **arrastando num preview**. Na expedição, etiquetas em **PDF ou ZPL** | O editor por arrastar é o padrão do mercado, e o suporte gira em torno de calibração (medir o rolo com régua, ajustar o driver) |
| **VR (varejo/supermercado)** | Mais de **25 modelos prontos** para Argox, Zebra e jato de tinta, com gôndola simples, gôndola com promoção ("de/por") e ofertas em A4, mais um **Report Designer** para quem quer criar do zero | **Presets bons resolvem a maioria**, e o editor fica para o resto |
| **Softwares de marcenaria** (CorteCloud etc.) | Etiqueta de **peça** com QR, gerada no plano de corte | Não é nosso papel: o StartBig entrega o código `PRJ` ao software de corte |

Também vale para o nosso caso:

- **DUN-14** identifica a caixa ou fardo com várias unidades iguais e é impresso
  em **ITF-14**. O **`cEANTrib` da NF-e deve ser o GTIN da menor unidade vendida
  no varejo, e GTIN-14 não é aceito nesse campo**. Isso define a regra fiscal do
  plano de embalagens (§8).
- **DANFE Simplificado – Etiqueta** (NT 2020.004): pode ser impresso em papel
  menor que A4, com **no mínimo 55 mm de largura** (por causa do código de
  barras) e fonte de pelo menos 6 pt. É aceito no transporte no lugar do DANFE
  normal, nas vendas a consumidor final por e-commerce, telefone e similares.

---

## 4. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | **O layout é um modelo neutro em mm**, e cada impressora recebe uma tradução dele | Não sabemos a impressora do cliente; é a única forma de "todas as possibilidades" |
| D2 | **A saída pelo driver do Windows existe sempre** e é a padrão | É a rede de segurança (lição do Bling): qualquer impressora com driver imprime |
| D3 | As linguagens nativas (ZPL, TSPL, PPLA, PPLB, EPL) são uma **opção por terminal** | Velocidade e impressão sem diálogo para quem tem térmica |
| D4 | **Os presets de fábrica ficam no código** (`presets.ts`); os modelos do cliente ficam no banco | Preset novo chega com a atualização, sem migration de dados; modelo do cliente é compartilhado na loja (E9) |
| D5 | **A impressora de etiqueta e a calibração ficam por terminal**, no `impressao.store` | É por terminal que a impressora está plugada, como a do cupom |
| D6 | **O editor visual vem logo depois da aba de estoque**, antes das linguagens nativas | O Alan pediu "configuração visual fácil", e o Tiny prova que é o padrão. Como o motor já nasce no modelo neutro, o editor só edita esse JSON |
| D7 | **Embalagens (fardo/caixa) ganham plano próprio** e andam em paralelo | Mexe em PDV, estoque e NF-e de lojas em produção; a etiqueta só **consome** a embalagem quando ela existir |
| D8 | **As fontes do envio são OS, Venda e Avulsa** (destinatário digitado) | OS: a marcenaria tem a etapa "Embalado & Pronto para Transporte". Venda: loja que entrega. Avulsa: casos que não passam pelo sistema. Não temos "pedido" |
| D9 | **Etiqueta oficial de transportadora fica fora** deste plano | Exige contrato e API de cada transportadora (Correios, Melhor Envio); é outro projeto |
| D10 | **Etiqueta de peça de marcenaria fica fora** | O software da seccionadora/CNC gera essa etiqueta a partir do `PRJ` |
| D11 | **O backend não imprime nem gera PDF** para etiqueta | Ele guarda modelos e resolve dados; quem renderiza e imprime é o terminal |

---

## 5. O motor

### 5.1 O modelo

```jsonc
{
  "nome": "Gôndola 60×40",
  "fonte": "produto",             // produto | embalagem | volume | danfe
  "pagina": {
    "tipo": "bobina",              // bobina | folha
    "largura_mm": 60, "altura_mm": 40,
    "colunas": 1, "espaco_colunas_mm": 0, "espaco_linhas_mm": 2,
    "margem_esq_mm": 0, "margem_topo_mm": 0,
    "folha": null                  // para folha: { "largura_mm": 210, "altura_mm": 297, "linhas": 10 }
  },
  "elementos": [
    { "tipo": "texto",  "x": 2, "y": 2,  "w": 56, "h": 8, "campo": "produto.nome", "fonte_pt": 9, "negrito": true, "linhas_max": 2 },
    { "tipo": "texto",  "x": 2, "y": 12, "w": 30, "h": 10, "campo": "preco.varejo", "fonte_pt": 18, "negrito": true },
    { "tipo": "barras", "x": 2, "y": 24, "w": 56, "h": 12, "campo": "produto.codigo_barras", "simbologia": "auto", "legenda": true },
    { "tipo": "linha",  "x": 0, "y": 22, "w": 60, "h": 0, "espessura_mm": 0.3 }
  ]
}
```

Tipos de elemento: `texto` (fixo ou campo), `barras`, `qr`, `linha`, `caixa` e
`imagem` (logo da empresa). Coordenadas em mm, com origem no canto superior
esquerdo **de uma etiqueta**. As colunas e linhas da folha são responsabilidade
da página, não do elemento.

### 5.2 Códigos de barras

| Simbologia | Quando |
|---|---|
| EAN-13 / EAN-8 | Código do produto com 13 ou 8 dígitos e dígito verificador válido |
| ITF-14 | DUN-14 da embalagem (§8) |
| Code 128 | Todo o resto: código interno, `PRJ`, número de pedido |
| QR | Chave da NF-e, link, `PRJ` |

`"simbologia": "auto"` escolhe pela forma do valor. Um EAN com dígito
verificador inválido **não** vira EAN errado: cai para Code 128 e o preview
avisa. Um produto sem código nenhum usa o `codigo_produto`, e sem os dois o item
fica marcado na fila, sem impressão silenciosa de etiqueta vazia.

### 5.3 Campos (variáveis)

| Fonte | Campos |
|---|---|
| `produto` | nome, codigo_produto, codigo_barras, marca, categoria, unidade_medida, localizacao_estoque, fornecedor, preço de varejo, preço de atacado, data de impressão |
| `embalagem` | os campos do produto + tipo (CX/FD…), fator ("Contém 12 un"), código da embalagem, preço da embalagem |
| `volume` | remetente (Empresa: nome, CNPJ, endereço, telefone), destinatário (cliente + endereço de entrega), nº da OS ou Venda, `PRJ`, volume N/M, peso, observação, nº da NF |
| `danfe` | layout **fixo**, conforme a NT (não é editável; só escolhe o tamanho) |

O remetente vem **sempre** do cadastro da Empresa. Nada de cidade escrita no
modelo.

### 5.4 Saídas

| Saída | Atende | Diálogo? |
|---|---|---|
| **Driver do Windows** (HTML + `imprimirComPagina` com `@page` no tamanho da etiqueta ou da folha) | Qualquer impressora com driver | Sim (limitação do `window.print`) |
| **ZPL** | Zebra; Elgin e várias outras emulam | Não, via `imprimir_raw` |
| **TSPL** | TSC, e boa parte das térmicas chinesas e nacionais | Não |
| **PPLA / PPLB** | Argox | Não |
| **EPL** | Zebras antigas | Não |

As linguagens nativas têm dois modos:

- **Texto nativo:** texto e código de barras são comandos da própria
  impressora. É o mais rápido e o mais nítido, mas a fonte é a da impressora, e
  o resultado fica **próximo** do preview, não idêntico.
- **Modo imagem:** a etiqueta é renderizada inteira como bitmap monocromático na
  resolução da impressora (203 ou 300 dpi) e enviada como gráfico (`^GF` no ZPL,
  `BITMAP` no TSPL…). Sai **idêntica ao preview**, com logo e fonte, em
  impressora que não conhecemos bem, e é mais lenta em lotes grandes. Os
  códigos de barras continuam nativos para não perderem leitura.

**Imprimir teste** e **página de calibração** (régua em mm com bordas) existem
desde a fase 1: a calibração é o maior assunto de suporte do mercado (§3).

### 5.5 Editor visual

- Canvas com a etiqueta em escala, zoom e grade em mm.
- Arrastar e redimensionar elementos, com os valores numéricos (x, y, w, h) editáveis ao lado.
- Painel de campos: arrastar "Preço" para dentro da etiqueta cria o elemento.
- Preview com um produto real escolhido na hora.
- Sempre parte de um preset ("Duplicar e editar"); ninguém começa de uma folha em branco.

---

## 6. Configuração por terminal (`impressao.store`)

**Entregue (fase 1/2)** — campos planos no `ConfigImpressao`, como os do cupom:

```ts
etiqueta_deslocamento_x_mm: number   // calibração
etiqueta_deslocamento_y_mm: number
etiqueta_modelo: string | null       // último modelo usado na fila (`preset:…` ou `loja:<id>`)
```

**Fase 4** acrescenta: saída (`driver | zpl | tspl | ppla | pplb | epl`), modo
nativo (`texto | imagem`), impressora, dpi e escuridão.

**Mudou em relação ao plano:** a calibração ficou **na própria aba** (botão da
régua na fila), e não em Configurações › Impressão. Enquanto a única saída é o
driver, não há impressora a escolher lá — o ajuste de deslocamento faz sentido
ao lado do "Imprimir teste". Quando a fase 4 trouxer a escolha de impressora e
linguagem, essa parte vai para Configurações.

---

## 7. Backend

- **`modelo_etiqueta`**: `id`, `nome`, `fonte`, `definicao` (JSON do §5.1),
  `ativo`, datas. É tabela nova, então o `create_all` a cria, e a migration de
  referência segue a regra do CLAUDE.md (decidir pelo schema antigo).
- **Endpoints** (`/api/v1/etiquetas`), permissão `produto` (a mesma do Estoque):
  - `GET/POST/PUT/DELETE /modelos` — **entregue**. Nome único por empresa (409),
    folha que não comporta as colunas/linhas e elemento fora da etiqueta (422).
    A definição guarda também `layout_auto` (os blocos que geraram os elementos).
  - ~~`POST /dados/produtos`~~ e ~~`GET /dados/movimentacao/{id}`~~ — **não foram
    necessários**: a fila lê a listagem de `/produtos` que a tela já carrega, e as
    entradas vêm de `/produtos/movimentacoes`. Voltam a ser avaliados com as
    embalagens (§8), se o dado não estiver na listagem.
  - `GET /dados/volume?os_id= | venda_id=` → remetente, destinatário e NF *(fase 5)*
  - `GET /dados/danfe/{documento_fiscal_id}` → dados do DANFE Simplificado *(fase 5)*
- **Não tem** `/imprimir` (D11), e o relatório original tinha.
- **Regerar o sidecar** ao final de cada fase que mexer no backend (`npm run build:sidecar`).

---

## 8. Embalagens: plano próprio (resumo do contrato)

Arquivo: `produto-embalagens-plano.md`, a escrever. O que a etiqueta precisa dele:

```
produto_embalagens: produto_id, tipo (CX, FD, PCT…), fator (12),
                    codigo_barras (EAN-13 ou DUN-14), preco (opcional), ativo
```

Regras que esse plano precisa fechar, com base na pesquisa:

- **O estoque fica sempre na unidade base.** Vender 1 FD baixa 12 UN.
- **PDV:** bipar o código da embalagem lança a embalagem com o fator.
- **NF-e:** `cEAN`, `uCom` e `qCom` recebem a embalagem vendida; `cEANTrib`,
  `uTrib` e `qTrib` recebem a **menor unidade de varejo**, e **nunca um GTIN-14**
  (NT 2017.001).
- **Entrada:** receber 3 CX lança 36 UN.

Enquanto esse plano não sai, a fonte `embalagem` do motor não aparece, e o
restante da Central funciona sem ela.

---

## 9. Fases

### Fase 1 — Motor + saída pelo driver
Modelo neutro, presets (rolos 40×25, 50×30, 60×40, 33×22 em 3 colunas,
100×150; Pimaco A4 mais comuns; gôndola), render HTML, "pular N posições" na
folha, imprimir teste e página de calibração, tabela `modelo_etiqueta`.
**Entrega E1, E5, E6 e E9.**

### Fase 2 — Aba Estoque
Aba no `ProductsView`, fila com busca e filtros, quantidade por item, "Etiquetas
desta entrada" na movimentação, "Imprimir etiqueta" no card do produto, config
por terminal. **Entrega E3 e E10.**

### Fase 3 — Editor visual
§5.5. **Entrega E4.**

### Fase 4 — Linguagens nativas
ZPL primeiro (maior cobertura), depois TSPL, PPLA/PPLB e EPL. Modo texto e modo
imagem. Uso do servidor de impressão em rede. **Entrega E2.**

### Fase 5 — Aba Envio
Etiquetas de volume a partir de OS, Venda e Avulsa, atalhos na OS
("Embalado & Pronto para Transporte") e na Venda, e o DANFE Simplificado –
Etiqueta para quem tem NF-e autorizada. **Entrega E7 e E8.**

### Em paralelo — Embalagens (§8)
Quando entrar, a fonte `embalagem` e a simbologia ITF-14 ficam disponíveis nas
fases já entregues.

---

## 10. Fora de escopo (por enquanto)

- Etiqueta oficial de transportadora com rastreio (Correios, Melhor Envio, marketplaces).
- Etiqueta de peça de marcenaria (é da CNC).
- Gerar EAN-13 interno (prefixo 2) para produto sem código: **risco de colisão
  com código de balança**, se algum dia o PDV ler balança. Fica para depois de
  verificar isso.
- Etiqueta de preço "de/por" com promoção: não temos preço promocional no produto.

---

## 11. Perguntas em aberto

1. ~~**Permissão:** a aba Etiquetas segue a mesma permissão do Estoque, ou ganha uma própria?~~
   Decidido na implementação: a mesma (`produto`). Quem cuida do estoque cuida das etiquetas.
2. **Loja piloto:** qual loja testa a fase 1, e qual impressora (e rolo) ela tem? Serve de primeiro caso de calibração.
3. **Envio na Venda:** hoje a venda guarda endereço de entrega, ou só o endereço do cadastro do cliente?

---

## 12. Entrega das fases 1 e 2 (27/09/2026)

**O que funciona:**
- Aba **Etiquetas** no Estoque, com o cabeçalho da `ProductsView` virando um mapa por aba.
- Catálogo com busca, filtro de categoria e a **situação do código** de cada produto
  (EAN-13/EAN-8/UPC/ITF-14 válido, código interno, EAN inválido, sem código).
- Fila (store Pinia) alimentada pelo catálogo, pelo botão **Etiqueta** do card do
  produto (que troca de aba) e por **Entradas recentes** (E3).
- 12 presets (5 rolos/gôndola, 4 Pimaco Carta, 3 A4) e modelos da loja no banco (E9),
  criados pelo formulário de medidas + blocos, com **layout automático** e preview ao vivo.
- Impressão pelo driver do Windows (E1, E5), "pular N posições" na folha (E6),
  página de teste e calibração por terminal.
- Um EAN com dígito verificador errado nunca sai como EAN: cai para Code 128.

**Testes:** `test/api/v1/etiquetas/` (12, contrato REST) e
`src/shared/etiquetas/__tests__/` (29: códigos, geometria, paginação, presets,
e a renderização montada em jsdom).

**Não foi visto num app rodando.** O backend de dev desta máquina aponta para o
banco da loja (ver `test/api/v1/fiscal/conftest.py`), e subir o backend rodaria
a migration nele. Falta conferir, com impressora de verdade:
1. **Térmica pelo driver:** se o `@page` no tamanho do rolo é respeitado e se o
   driver não solta etiqueta em branco entre uma e outra (a página tem 0,5 mm a
   menos por isso — `EtiquetasImpressao.vue`).
2. **Folha Pimaco:** alinhar com a página de teste; as medidas das A4 vieram da
   geometria Avery equivalente e podem precisar de ajuste fino.
3. **Leitura:** bipar no PDV um EAN-13 impresso em 40 × 25 mm.

**Migration:** `y8z9a0b1c2d3_modelo_etiqueta` (só cria tabela, decide pela
ausência dela). **Regerar o sidecar** antes de gerar instalador.

---

## Fontes

- Bling — impressão pelo navegador, configuração no driver: <https://ajuda.bling.com.br/hc/pt-br/articles/360035600834-Como-criar-etiquetas-customizadas>
- Olist/Tiny — configuração de etiqueta de produto: <https://ajuda.olist.com/produtos/como-cadastrar-a-etiqueta-de-um-produto>
- Olist/Tiny — PDF ou ZPL: <https://ajuda.olist.com/etiquetas/-escolha-o-formato-de-arquivo-da-sua-etiqueta>
- VR System — layout de etiquetas: <https://vrsystem.info/publico/post/layout-de-etiquetas-modelos/8befdc57-ea95-4ce1-92db-bfb54a212206>
- GS1 Brasil — ITF-14 / DUN-14: <https://www.gs1br.org/itf-14>
- Maxiprod — EAN, GTIN, DUN e cEANTrib: <https://maxiprod.com.br/ajuda/cadastros/codigos-de-produtos-e-unitizadores-ean-gtin-dun/>
- Conta Azul — conversão de unidade de medida: <https://ajuda.contaazul.com/hc/pt-br/articles/27381110462349-Produtos-convers%C3%A3o-de-unidade-de-medida>
- NT 2020.004 (DANFE Simplificado – Etiqueta): <https://focusnfe.com.br/blog/nota-tecnica-2020-004/>, <https://blog.tecnospeed.com.br/nota-tecnica-2020-004-da-nf-e/>
- `Plano_Marcenaria.pdf` e `segmento-marcenaria-plano.md` (etapa "Embalado & Pronto para Transporte", código `PRJ`)
