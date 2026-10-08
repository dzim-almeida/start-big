# Spec 06A — Orçamento de Marcenaria (Backend): Dados, Ciclo de Vida e API

| Campo        | Valor                                                                              |
|--------------|------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                    |
| Camada       | Backend (FastAPI)                                                                  |
| Dependências | Specs 04A (parâmetros, permissões, capacidade) e 05 (motor)                        |
| Bloqueia     | Specs 06B, 07, 08A                                                                 |
| Revisões     | 1 (06/10/2026): pedidos da Spec 06B · 2 (06/10/2026): pedidos da Spec 07 — ver o fim do documento |
| Referência   | SPEC-00: F1, F5, O1, O2, O3, O3a, O5, O6, C3, C4, C5a, C7, C9, T3c, T3d, T7, P4 · PR3, PR4, PR6, PR8 |

---

## 1. Objetivo

Criar o **orçamento de marcenaria** no backend: as tabelas, as regras de status e de versão, e a API que a tela da Spec 06B vai usar.

Ao final desta spec, pela API, é possível: criar um orçamento, montar ambientes e móveis com insumos, ver o cálculo completo (Spec 05), anexar fotos e PDFs da medição, enviar ao cliente, voltar a editar, recusar, renovar um vencido, criar nova versão, atualizar preços de insumo com aviso, e consultar o histórico. A **aprovação** (que gera a OS) é a Spec 08A.

## 2. Escopo

**Dentro do escopo**
- Tabelas `marcenaria_*` do orçamento e o histórico de eventos da marcenaria.
- Numeração `ORC-AAAA-NNNNNN` com versão.
- Status `RASCUNHO`, `ENVIADO`, `RECUSADO`, `VENCIDO`, `SUBSTITUIDO` (e o lugar de `APROVADO`, preenchido pela 08A).
- Cópia dos parâmetros (04A) e do custo do produto (O3a) no momento certo.
- Endpoints de leitura, escrita, transições, versões, preços, anexos e histórico.
- Recorte de custos por permissão (P4) e trava de edição concorrente.
- Permissões de orçamento.
- Migração e testes.

**Fora do escopo**
- Telas (Spec 06B) e proposta em PDF (Spec 07).
- Aprovar e gerar a OS, desfazer aprovação (Spec 08A).
- Conta a pagar do RT (Spec 09A).
- Reserva de estoque (Spec 10A): esta spec só deixa os índices necessários.

---

## 3. Arquivos afetados

```
backend-fastapi/
├── alembic/versions/
│   └── z9a0b1c2d3e4_orcamento_marcenaria.py        # CRIAR — tabelas novas (filha da 04A)
├── app/
│   ├── core/
│   │   ├── permissoes.py                           # ALTERAR — chaves de orçamento
│   │   └── imagem.py                               # ALTERAR — contexto "orcamento_anexo" + salvar PDF
│   ├── db/
│   │   ├── models/marcenaria/
│   │   │   ├── __init__.py                         # CRIAR
│   │   │   ├── orcamento.py                        # CRIAR — orçamento, RT, anexo
│   │   │   ├── ambiente.py                         # CRIAR — ambiente, móvel, insumo
│   │   │   └── evento.py                           # CRIAR — histórico da marcenaria
│   │   ├── models/__init__.py                      # ALTERAR — registrar os models
│   │   └── crud/marcenaria/
│   │       ├── __init__.py                         # CRIAR
│   │       ├── orcamento.py                        # CRIAR
│   │       └── evento.py                           # CRIAR
│   ├── schemas/marcenaria/
│   │   ├── __init__.py                             # CRIAR
│   │   └── orcamento.py                            # CRIAR — entrada e saída
│   ├── services/marcenaria/
│   │   ├── orcamento.py                            # CRIAR — regras, status, versões
│   │   ├── orcamento_calculo.py                    # CRIAR — tradução banco ↔ motor (Spec 05)
│   │   ├── orcamento_precos.py                     # CRIAR — custo do produto (O3a) e atualização
│   │   └── orcamento_anexos.py                     # CRIAR
│   └── api/v1/
│       ├── endpoints/marcenaria_orcamento.py       # CRIAR
│       └── api.py                                  # ALTERAR — prefixo /marcenaria/orcamentos
└── test/
    ├── services/marcenaria/test_orcamento_*.py     # CRIAR
    └── api/v1/marcenaria/test_orcamento_*.py       # CRIAR
```

| Camada | Faz | Não faz |
|--------|-----|---------|
| `endpoints/marcenaria_orcamento.py` | Lê token e parâmetros, aplica permissão, escolhe o recorte de custos | Regra, SQL |
| `services/marcenaria/orcamento.py` | Status, versões, travas, histórico, cópia de parâmetros, transação | SQL direto |
| `services/marcenaria/orcamento_calculo.py` | Monta a entrada do motor a partir do banco e devolve o resultado | Calcular (é o motor) |
| `crud/marcenaria/*` | Consultas e gravação | Regra |

---

## 4. Decisões

### 4.1. Estrutura

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Árvore: **orçamento → ambientes → móveis → insumos**, mais RT, anexos e eventos | F1, Figma |
| D2 | Insumo guarda **cópia** de: descrição, unidade, código, custo unitário, `sofre_perda` e a **origem do custo** (`ULTIMA_COMPRA`, `CUSTO_MEDIO`, `SEM_CUSTO`). Guarda também o `produto_id` | O3: mudar o produto (nome, preço, `sofre_perda`) nunca muda um orçamento sem aviso. O `produto_id` serve à atualização de preços e ao estoque (10A) |
| D3 | Custo copiado na **inclusão do insumo**: `estoque.valor_entrada`; sem ele, `estoque.custo_medio`; sem os dois, 0 com origem `SEM_CUSTO` | O3a |
| D4 | Parâmetros copiados na **criação** do orçamento: markup, perda, custo/hora, RT padrão e modo, validade e prazo de entrega (04A). Ficam editáveis no orçamento | T6. Mudar a configuração não altera orçamento existente |
| D5 | **Valores calculados não são a fonte da verdade**: a cada leitura, o motor (Spec 05) recalcula. O cabeçalho guarda só um **resumo** (bruto, total, margem, número de móveis) para a lista, atualizado a cada escrita | C8. A lista não pode rodar o motor para 200 orçamentos; o detalhe nunca usa o resumo |
| D6 | Projeto (O5): o orçamento guarda `objeto_id` (projeto existente do cliente) **ou** só nome e endereço da obra. O objeto é criado na aprovação (08A) se não existir | Evita objetos órfãos de orçamentos recusados. O cliente que volta escolhe o projeto que já tem |
| D7 | Arquiteto (C5a): tabela `marcenaria_orcamento_rt` com **N** linhas (fornecedor + %). O motor recebe a **soma** dos percentuais. A tela da fase 1 edita uma linha só | SPEC-00: "a tabela já aceita vários comissionados" |
| D8 | Instalação (C3): `instalacao_custo_centavos` no cabeçalho, opcional (vazio = sem linha de instalação) | C3 |
| D9 | Desconto e sinal: modo (`PERCENTUAL`/`VALOR`) + valor, no cabeçalho | C7, C9 |
| D10 | Unidades do banco iguais às do motor: centavos, bp, milésimos de insumo, centésimos de hora, milímetros de medida | PR4, Spec 05 D1 |

### 4.2. Ciclo de vida

| # | Decisão | Motivo |
|---|---------|--------|
| D11 | **Só `RASCUNHO` é editável.** Qualquer escrita em outro status responde `409`. Exceção: anexos (D31) | Uma regra só; o resto são transições |
| D12 | `ENVIADO → RASCUNHO` pela ação **"voltar a editar"**, registrada no histórico | T3c. A tela (06B) avisa "o cliente recebeu R$ X" antes |
| D13 | Ao **enviar**: exige cliente, nome do projeto e pelo menos um móvel; grava `data_envio` e `data_validade = hoje + validade_dias` | O cliente precisa receber algo completo; a validade conta do envio |
| D14 | **Vencimento preguiçoso:** ao ler (lista, detalhe), todo `ENVIADO` com `data_validade < hoje` passa a `VENCIDO`, com evento do usuário "Sistema" | Sem tarefa agendada nova. Ninguém vê um orçamento vencido marcado como enviado |
| D15 | **Renovar** um `VENCIDO` volta para `RASCUNHO` (mesma versão), limpando `data_validade`. A tela oferece atualizar preços antes de reenviar | O3 |
| D16 | **Nova versão** a partir de `ENVIADO`, `VENCIDO` ou `RECUSADO`: copia a árvore inteira (com os custos **copiados**, não os atuais) para a versão `n + 1` em `RASCUNHO`; a anterior vira `SUBSTITUIDO` (somente leitura) | O2. A tela oferece atualizar preços na versão nova (O3) |
| D17 | **Recusar** exige motivo (texto livre, até 500 caracteres) | Histórico útil para o dono ("preço", "prazo", "fechou com outro") |
| D18 | **Excluir** só a versão 1 em `RASCUNHO` que **nunca foi enviada**. Fora disso, o orçamento fica (pode ser recusado) | Proposta enviada é documento; o histórico não some |
| D19 | `APROVADO` é escrito só pela Spec 08A | Separação de responsabilidade |

### 4.3. Concorrência, permissão e histórico

| # | Decisão | Motivo |
|---|---------|--------|
| D20 | **Trava otimista:** o cabeçalho tem `revisao` (inteiro). Toda escrita manda a revisão que tem; se for diferente da gravada, `409` "Este orçamento foi alterado em outro computador. Recarregue para ver a versão atual." Cada escrita bem-sucedida soma 1 | O StartBig roda em vários computadores da loja; com salvamento automático (T3d), dois computadores no mesmo orçamento se sobrescreveriam em silêncio |
| D21 | Toda escrita responde com o **detalhe completo** (com a nova `revisao` e o cálculo) | A tela não precisa de uma segunda chamada para atualizar total e avisos |
| D22 | Permissões novas: `view_orcamentos_marcenaria`, `manage_orcamentos_marcenaria` (criar, editar, enviar, versões, recusar, anexos; aprovar na 08A), `delete_orcamentos_marcenaria` (excluir, D18). `manage` implica `view` | Padrão da matriz (ver/gerenciar/excluir); a linha entra na 06B |
| D23 | **Recorte de custos (P4):** sem `view_custos_marcenaria`, a resposta **não traz** custo de insumo, origem do custo, material, perda, mão de obra, custos, margens, RT (% e valores), markup, perda %, custo/hora. Traz preços, quantidades, medidas, desconto, total, sinal e saldo | P4. Mesmo padrão da 04A: chave ausente, não nula |
| D24 | Sem `view_custos_marcenaria`, as escritas desses campos são **recusadas** (`403`), e o insumo novo recebe o custo do produto normalmente | Quem não vê o custo não pode alterá-lo, mas pode montar o móvel |
| D24a | **(Revisão 1)** No `PUT` do móvel, chave de custo **ausente** (`mao_obra`, `terceirizado_centavos`, `custo_unit_centavos` de insumo com `id`) **mantém** o valor gravado; só o valor enviado muda. Vale para todos os usuários | O vendedor sem custos salva o móvel sem essas chaves (06B D16). Se ausência zerasse, ele apagaria em silêncio a mão de obra que o dono lançou |
| D25 | Histórico em `marcenaria_evento`, compartilhado com as próximas specs (OS, produção, entrega). Registra **transições e ações** (criar, enviar, voltar a editar, recusar, renovar, nova versão, preços atualizados, anexo incluído/removido, excluir), **não** cada edição de campo | T7. O salvamento automático geraria centenas de eventos inúteis por orçamento |
| D26 | Tudo responde **404** sem a capacidade `orcamento_tecnico` | 04A, D1 |

### 4.4. Anexos (medição, O1)

| # | Decisão | Motivo |
|---|---------|--------|
| D27 | Aceita **imagens** (JPG, PNG, WebP; pelo pipeline existente de `imagem.py`, até 5 MB) e **PDF** (até 10 MB, guardado como veio, conferido pelo início `%PDF`) | Planta e projeto do arquiteto chegam em PDF; foto do ambiente em imagem |
| D28 | Cada anexo tem uma **legenda** opcional (até 120 caracteres) e o tipo (`FOTO`, `PDF`) | "Parede da pia", "Planta baixa" |
| D29 | Campo de texto no cabeçalho, **"Medidas e observações da medição"** (até 4000 caracteres) | A medição tem números que não são foto |
| D30 | Anexos são do **código** do orçamento, não da versão: todas as versões veem os mesmos | A medição não muda entre versões; copiar arquivos a cada versão encheria o disco |
| D31 | **(Revisão 1)** Incluir, excluir e mudar a legenda de anexos é permitido em **qualquer status, exceto `SUBSTITUIDO` e `APROVADO`**, e **não** soma na `revisao` | A foto do ambiente muitas vezes chega depois do envio e não muda o preço. Não somar na revisão evita conflito falso com quem está editando o rascunho |

---

## 5. Modelo de dados

```sql
-- Cabeçalho. Uma linha por versão.
CREATE TABLE marcenaria_orcamentos (
  id                       INTEGER PRIMARY KEY,
  codigo                   VARCHAR(20)  NOT NULL,          -- ORC-2026-000084 (igual em todas as versões)
  versao                   INTEGER      NOT NULL DEFAULT 1,
  status                   VARCHAR(12)  NOT NULL,          -- RASCUNHO|ENVIADO|APROVADO|RECUSADO|VENCIDO|SUBSTITUIDO
  revisao                  INTEGER      NOT NULL DEFAULT 1, -- trava otimista (D20)
  cliente_id               INTEGER      REFERENCES clientes(id),           -- obrigatório para enviar
  funcionario_id           INTEGER      REFERENCES funcionarios(id),       -- vendedor
  objeto_id                INTEGER      REFERENCES objetos_servico(id),    -- projeto existente (D6)
  projeto_nome             VARCHAR(100),                                   -- obrigatório para enviar
  endereco_obra            VARCHAR(255),
  medicao_observacoes      TEXT,                                           -- D29
  -- parâmetros copiados (D4)
  markup_bp                INTEGER NOT NULL,
  perda_bp                 INTEGER NOT NULL,
  custo_hora_centavos      INTEGER NOT NULL,
  rt_modo                  VARCHAR(10) NOT NULL,                           -- MARGEM|PRECO
  validade_dias            INTEGER NOT NULL,
  prazo_entrega_dias       INTEGER NOT NULL,
  instalacao_custo_centavos INTEGER,                                       -- D8
  desconto_modo            VARCHAR(10) NOT NULL DEFAULT 'PERCENTUAL',
  desconto_valor           INTEGER NOT NULL DEFAULT 0,
  sinal_modo               VARCHAR(10) NOT NULL DEFAULT 'PERCENTUAL',
  sinal_valor              INTEGER NOT NULL DEFAULT 0,
  observacoes_proposta     TEXT,                                           -- sai na proposta (Spec 07)
  -- datas
  data_envio               DATETIME,
  data_validade            DATE,
  data_recusa              DATETIME,
  motivo_recusa            VARCHAR(500),
  data_aprovacao           DATETIME,                                       -- Spec 08A
  os_id                    INTEGER REFERENCES ordens_servico(id),          -- Spec 08A
  -- resumo para a lista (D5)
  resumo_bruto_centavos    INTEGER NOT NULL DEFAULT 0,
  resumo_total_centavos    INTEGER NOT NULL DEFAULT 0,
  resumo_margem_bp         INTEGER NOT NULL DEFAULT 0,
  resumo_qtd_moveis        INTEGER NOT NULL DEFAULT 0,
  data_criacao             DATETIME NOT NULL,
  data_atualizacao         DATETIME NOT NULL,
  CONSTRAINT uq_marcenaria_orcamentos_codigo_versao UNIQUE (codigo, versao)
);
CREATE INDEX ix_marcenaria_orcamentos_status ON marcenaria_orcamentos (status);
CREATE INDEX ix_marcenaria_orcamentos_cliente ON marcenaria_orcamentos (cliente_id);
CREATE INDEX ix_marcenaria_orcamentos_validade ON marcenaria_orcamentos (data_validade);

CREATE TABLE marcenaria_orcamento_rt (           -- D7
  id INTEGER PRIMARY KEY,
  orcamento_id  INTEGER NOT NULL REFERENCES marcenaria_orcamentos(id) ON DELETE CASCADE,
  fornecedor_id INTEGER NOT NULL REFERENCES fornecedores(id),
  rt_bp         INTEGER NOT NULL                 -- 0 a 3000
);

CREATE TABLE marcenaria_ambientes (
  id INTEGER PRIMARY KEY,
  orcamento_id INTEGER NOT NULL REFERENCES marcenaria_orcamentos(id) ON DELETE CASCADE,
  nome         VARCHAR(80) NOT NULL,
  ordem        INTEGER NOT NULL
);
CREATE INDEX ix_marcenaria_ambientes_orcamento ON marcenaria_ambientes (orcamento_id);

CREATE TABLE marcenaria_moveis (
  id INTEGER PRIMARY KEY,
  ambiente_id   INTEGER NOT NULL REFERENCES marcenaria_ambientes(id) ON DELETE CASCADE,
  nome          VARCHAR(120) NOT NULL,
  descricao     VARCHAR(500),                     -- sai na proposta (Spec 07)
  largura_mm    INTEGER, altura_mm INTEGER, profundidade_mm INTEGER,
  quantidade    INTEGER NOT NULL DEFAULT 1,
  tipo_producao VARCHAR(12) NOT NULL DEFAULT 'INTERNA',   -- INTERNA|TERCEIRIZADA
  central_fornecedor_id INTEGER REFERENCES fornecedores(id), -- obrigatório se TERCEIRIZADA (E6)
  terceirizado_centavos INTEGER NOT NULL DEFAULT 0,
  mao_obra_modo VARCHAR(8) NOT NULL DEFAULT 'NENHUMA',    -- FIXA|HORAS|NENHUMA
  mao_obra_centavos INTEGER NOT NULL DEFAULT 0,
  mao_obra_horas_centesimos INTEGER NOT NULL DEFAULT 0,
  aprovado      BOOLEAN,                          -- NULL até a aprovação (Spec 08A, O4)
  ordem         INTEGER NOT NULL
);
CREATE INDEX ix_marcenaria_moveis_ambiente ON marcenaria_moveis (ambiente_id);

CREATE TABLE marcenaria_movel_insumos (
  id INTEGER PRIMARY KEY,
  movel_id    INTEGER NOT NULL REFERENCES marcenaria_moveis(id) ON DELETE CASCADE,
  produto_id  INTEGER REFERENCES produtos(id) ON DELETE SET NULL,   -- D2
  descricao   VARCHAR(255) NOT NULL,                                -- cópia do nome
  codigo      VARCHAR(100),                                         -- cópia do SKU
  unidade     VARCHAR(10),                                          -- cópia da unidade
  quantidade_milesimos INTEGER NOT NULL,
  custo_unit_centavos  INTEGER NOT NULL,
  custo_origem VARCHAR(14) NOT NULL,                                -- ULTIMA_COMPRA|CUSTO_MEDIO|SEM_CUSTO|MANUAL
  sofre_perda BOOLEAN NOT NULL,
  ordem       INTEGER NOT NULL
);
CREATE INDEX ix_marcenaria_movel_insumos_movel ON marcenaria_movel_insumos (movel_id);
CREATE INDEX ix_marcenaria_movel_insumos_produto ON marcenaria_movel_insumos (produto_id);

CREATE TABLE marcenaria_orcamento_anexos (          -- D27, D30
  id INTEGER PRIMARY KEY,
  codigo_orcamento VARCHAR(20) NOT NULL,
  tipo        VARCHAR(4) NOT NULL,                  -- FOTO|PDF
  nome_arquivo VARCHAR(255) NOT NULL,
  url         VARCHAR(500) NOT NULL,
  legenda     VARCHAR(120),
  usuario_id  INTEGER,
  data_criacao DATETIME NOT NULL
);
CREATE INDEX ix_marcenaria_orcamento_anexos_codigo ON marcenaria_orcamento_anexos (codigo_orcamento);

CREATE TABLE marcenaria_eventos (                   -- D25 (T7), só inclusão
  id INTEGER PRIMARY KEY,
  orcamento_id INTEGER REFERENCES marcenaria_orcamentos(id),
  os_id        INTEGER REFERENCES ordens_servico(id),   -- usado a partir da Spec 08A
  tipo         VARCHAR(40) NOT NULL,                    -- ORCAMENTO_CRIADO, ORCAMENTO_ENVIADO, ...
  descricao    VARCHAR(500) NOT NULL,                   -- frase pronta para a tela
  dados        JSON,                                    -- ex.: {"status_anterior": "...", "motivo": "..."}
  usuario_id   INTEGER,
  usuario_nome VARCHAR(150) NOT NULL,                   -- cópia (o histórico sobrevive à troca de nome)
  ocorrido_em  DATETIME NOT NULL
);
CREATE INDEX ix_marcenaria_eventos_orcamento ON marcenaria_eventos (orcamento_id, ocorrido_em);
CREATE INDEX ix_marcenaria_eventos_os ON marcenaria_eventos (os_id, ocorrido_em);
```

- `custo_origem = MANUAL`: quando quem tem `view_custos` digita o custo à mão no orçamento.
- Este SQL é referência; a fonte da verdade são os models e a migração.
- Os índices de **reserva de estoque** (SPEC-00 E1a) dependem de colunas de separação que nascem na Spec 10A; `ix_marcenaria_movel_insumos_produto` já ajuda.

### 5.1. Limites de tamanho

| Item | Limite | Motivo |
|------|--------|--------|
| Ambientes por orçamento | 50 | Proteção; nenhum projeto real chega perto |
| Móveis por orçamento | 300 | Idem; o motor faz 100 em menos de 50 ms (Spec 05) |
| Insumos por móvel | 100 | Idem |
| Anexos por código | 60 | Disco |

---

## 6. Contrato da API

Prefixo: `/api/v1/marcenaria/orcamentos`. Todas as rotas exigem a capacidade (D26) e a permissão indicada. Toda escrita recebe `?revisao=N` (D20) e responde com o **detalhe** (§6.2).

### 6.1. Rotas

| Método e rota | Permissão | O que faz |
|---------------|-----------|-----------|
| `GET /` | view | Lista (§6.3) |
| `GET /contagens` | view | **(Revisão 1)** Quantos orçamentos por status, mais `vence_em_3_dias` (§6.8) |
| `GET /projetos?cliente_id=` | view | **(Revisão 1)** Projetos (objetos) do cliente para escolher (§6.7) |
| `POST /` | manage | Cria em `RASCUNHO`, com os parâmetros copiados (D4); corpo opcional `{cliente_id, objeto_id, projeto_nome, endereco_obra, funcionario_id}`. Sem `funcionario_id`, usa o funcionário ligado ao usuário logado, se houver (Revisão 1) |
| `GET /{id}` | view | Detalhe com cálculo (§6.2) |
| `PATCH /{id}` | manage | Cabeçalho: cliente, vendedor, projeto, medição, parâmetros, instalação, desconto, sinal, observações |
| `PUT /{id}/rt` | manage + view_custos | Lista de arquitetos `[{fornecedor_id, rt_bp}]` (substitui a lista) |
| `POST /{id}/ambientes` | manage | `{nome}`; entra no fim |
| `PATCH /{id}/ambientes/{aid}` | manage | `{nome}` |
| `DELETE /{id}/ambientes/{aid}` | manage | Remove com os móveis |
| `PUT /{id}/ambientes/ordem` | manage | `{ids: [...]}` na nova ordem |
| `POST /{id}/ambientes/{aid}/moveis` | manage | Móvel completo, com insumos (§6.4) |
| `PUT /{id}/moveis/{mid}` | manage | Móvel completo (substitui insumos); pode trocar `ambiente_id` |
| `DELETE /{id}/moveis/{mid}` | manage | |
| `POST /{id}/moveis/{mid}/duplicar` | manage | Cópia logo abaixo, nome com " (cópia)" (T4) |
| `POST /{id}/moveis/simular` | manage | **(Revisão 1)** Calcula um móvel sem gravar nada (§6.6) |
| `PUT /{id}/ambientes/{aid}/moveis/ordem` | manage | `{ids: [...]}` |
| `POST /{id}/enviar` | manage | `RASCUNHO → ENVIADO` (D13) |
| `POST /{id}/voltar-a-editar` | manage | `ENVIADO → RASCUNHO` (D12) |
| `POST /{id}/recusar` | manage | `{motivo}`; `ENVIADO`/`VENCIDO` → `RECUSADO` (D17) |
| `POST /{id}/renovar` | manage | `VENCIDO → RASCUNHO` (D15) |
| `POST /{id}/nova-versao` | manage | D16; responde o detalhe da **versão nova** |
| `GET /{id}/precos-desatualizados` | view + view_custos | §6.5 |
| `POST /{id}/atualizar-precos` | manage + view_custos | `{insumo_ids: [...]}` ou `{todos: true}`; só em `RASCUNHO` |
| `GET /{id}/versoes` | view | Todas as versões do mesmo código (número, status, total, datas) |
| `GET /{id}/anexos` · `POST` (multipart: arquivo, legenda) · `PATCH /{id}/anexos/{xid}` (`{legenda}`, Revisão 1) · `DELETE /{id}/anexos/{xid}` | view · manage · manage · manage | D27–D31 |
| `GET /{id}/historico` | view | Eventos do orçamento (todas as versões do código), do mais novo para o mais antigo |
| `DELETE /{id}` | delete | D18 |

As rotas estáticas (`/contagens`, `/projetos`) são declaradas **antes** de `/{id}`, como `/definicao-campos` na OS.

`view` = `view_orcamentos_marcenaria`; `manage` = `manage_orcamentos_marcenaria`; `delete` = `delete_orcamentos_marcenaria`; `view_custos` = `view_custos_marcenaria` (04A). Master e `all` passam em tudo.

### 6.2. Detalhe

```jsonc
{
  "id": 84, "codigo": "ORC-2026-000084", "versao": 2, "status": "RASCUNHO", "revisao": 17,
  "cliente": { "id": 12, "nome": "Studio Arquitetura & Interiores Ltda", "documento": "00360305000104",
               "telefone": "8533334444", "email": "contato@studio.com",                 // Revisão 2
               "endereco": "Rua X, 123 - Aldeota, Fortaleza - CE, CEP 60000-000" },      // Revisão 2
  "vendedor": { "id": 3, "nome": "Alan Alves de Amorim", "telefone": "85988887777" },   // Revisão 2
  "projeto": { "objeto_id": null, "nome": "Residencial Alpha Ville - Apto 802", "endereco_obra": "Av. das Américas, 4200" },
  "medicao_observacoes": "Pé-direito 2,70 m. Ponto de água a 60 cm do canto.",
  "parametros": { "markup_bp": 9000, "perda_bp": 1000, "custo_hora_centavos": 4500, "rt_modo": "MARGEM",
                  "validade_dias": 15, "prazo_entrega_dias": 30 },        // sem view_custos: só validade e prazo
  "arquitetos": [ { "fornecedor_id": 7, "nome": "Studio Renascer", "rt_bp": 800 } ], // sem view_custos: só nomes
  "instalacao_custo_centavos": 75000,                                       // sem view_custos: ausente
  "desconto": { "modo": "PERCENTUAL", "valor": 500 },
  "sinal": { "modo": "PERCENTUAL", "valor": 4000 },
  "ambientes": [
    { "id": 1, "nome": "Cozinha Gourmet", "ordem": 1, "subtotal_centavos": 830015, "custo_centavos": 444350,
      "moveis": [
        { "id": 10, "nome": "Torre Quente", "descricao": "...", "largura_mm": 700, "altura_mm": 2200,
          "profundidade_mm": 600, "quantidade": 1, "tipo_producao": "TERCEIRIZADA",
          "central": { "fornecedor_id": 9, "nome": "Madeiranit" }, "terceirizado_centavos": 38000,
          "mao_obra": { "modo": "FIXA", "centavos": 30000, "horas_centesimos": 0 },
          "insumos": [ { "id": 100, "produto_id": 55, "descricao": "MDF Branco TX 18mm", "unidade": "UN",
                         "quantidade_milesimos": 1400, "custo_unit_centavos": 28000,
                         "custo_origem": "ULTIMA_COMPRA", "sofre_perda": true } ],
          "calculo": { "material_centavos": 146000, "perda_centavos": 8250, "mao_obra_centavos": 30000,
                       "custo_unit_centavos": 222250, "preco_unit_centavos": 422275,
                       "preco_total_centavos": 422275, "rt_linha_centavos": 32093 } }
      ] }
  ],
  "calculo": { "bruto_centavos": 972515, "desconto_centavos": 48626, "total_centavos": 923889,
               "custo_total_centavos": 511850, "margem_bruta_centavos": 412039, "rt_total_centavos": 73911,
               "margem_liquida_centavos": 338128, "margem_liquida_bp": 3660,
               "sinal_centavos": 369556, "saldo_centavos": 554333,
               "instalacao": { "custo_centavos": 75000, "preco_centavos": 142500 } },
  "avisos": ["INSUMO_SEM_CUSTO"],
  "datas": { "criacao": "...", "envio": null, "validade": null, "recusa": null, "aprovacao": null },
  "motivo_recusa": null, "os": null,
  "inclui_custos": true,
  "acoes": { "editar": true, "enviar": true, "voltar_a_editar": false, "recusar": false,
             "renovar": false, "nova_versao": false, "excluir": true, "aprovar": false }
}
```

- `acoes` diz o que o usuário **pode fazer agora** (status + permissão). A tela só mostra botões a partir disso.
- Sem `view_custos`: saem todas as chaves de custo e margem (D23), inclusive dentro de `calculo` de móvel e de ambiente; ficam preços, quantidades, medidas, desconto, total, sinal e saldo.
- `subtotal_centavos` de ambiente e `preco_*` são **brutos** (antes do desconto), como na proposta (T5).

### 6.3. Lista

`GET /?status=&cliente=&vendedor_id=&vence_em_dias=&busca=&incluir_versoes_antigas=false&page=&limit=`

- Por padrão, mostra só a **versão mais recente** de cada código (sem `SUBSTITUIDO`).
- `vence_em_dias=N`: `ENVIADO` com `data_validade` entre hoje e hoje + N.
- `busca`: código, nome do projeto ou nome do cliente.
- Ordem: `data_atualizacao` decrescente.
- Item: `id, codigo, versao, status, cliente_nome, projeto_nome, vendedor_nome, resumo_total_centavos, resumo_qtd_moveis, data_validade, data_atualizacao` (+ `resumo_margem_bp` só com `view_custos`).
- Paginação no formato `PaginationBase` existente (`app/schemas/pagination.py`).

### 6.4. Móvel (entrada)

```jsonc
{
  "nome": "Torre Quente c/ Nicho p/ Forno e Micro-ondas",
  "descricao": "MDF Branco TX e Freijó, corrediças com amortecedor",
  "largura_mm": 700, "altura_mm": 2200, "profundidade_mm": 600,
  "quantidade": 1,
  "tipo_producao": "TERCEIRIZADA", "central_fornecedor_id": 9, "terceirizado_centavos": 38000,
  "mao_obra": { "modo": "FIXA", "centavos": 30000, "horas_centesimos": 0 },
  "insumos": [
    { "id": 100, "produto_id": 55, "quantidade_milesimos": 1400 },                   // existente: mantém o custo copiado
    { "produto_id": 61, "quantidade_milesimos": 26000 },                            // novo: custo pelo O3a
    { "produto_id": 70, "quantidade_milesimos": 2000, "custo_unit_centavos": 20000 } // custo manual (view_custos)
  ]
}
```

- Insumo **com `id`**: mantém custo, origem, descrição e `sofre_perda` gravados; só a quantidade e a ordem mudam (O3).
- Insumo **sem `id`**: copia do produto (D2, D3).
- `custo_unit_centavos` enviado: exige `view_custos` (D24); grava com origem `MANUAL`.
- Insumo que não veio na lista é removido.

### 6.5. Preços desatualizados (O3)

```jsonc
{
  "itens": [
    { "insumo_id": 100, "movel": "Torre Quente", "descricao": "MDF Branco TX 18mm",
      "custo_atual_orcamento": 28000, "custo_produto_hoje": 31500, "origem_hoje": "ULTIMA_COMPRA",
      "sofre_perda_orcamento": true, "sofre_perda_hoje": true }
  ],
  "total_atual_centavos": 923889,
  "total_com_precos_novos_centavos": 931204,
  "diferenca_centavos": 7315
}
```

- Lista os insumos com `produto_id` cujo custo pelo O3a **ou** `sofre_perda` mudou desde a cópia. Insumos com origem `MANUAL` também aparecem (o usuário decide).
- `total_com_precos_novos` vem do motor com os custos de hoje.
- `POST /atualizar-precos` grava os novos custos (e `sofre_perda`) nos itens escolhidos, com evento `PRECOS_ATUALIZADOS` (quantos itens e a diferença no total).

### 6.6. Simular um móvel (Revisão 1)

`POST /{id}/moveis/simular` recebe o **mesmo corpo** do móvel (§6.4) e, opcionalmente, `movel_id` (para os insumos com `id` manterem o custo copiado). Usa os parâmetros do orçamento (markup, perda, custo/hora, modo e soma do RT) e responde, **sem gravar** e **sem** mexer na `revisao`:

```jsonc
{
  "calculo": { "custo_unit_centavos": 222250, "preco_unit_centavos": 422275, "preco_total_centavos": 422275,
               "material_centavos": 146000, "perda_centavos": 8250, "mao_obra_centavos": 30000 },
  "insumos": [ { "produto_id": 61, "custo_unit_centavos": 0, "custo_origem": "SEM_CUSTO", "sofre_perda": true } ],
  "avisos": ["INSUMO_SEM_CUSTO"]
}
```

- O preço de um móvel depende só dele e dos parâmetros (Spec 05), então a simulação bate com o que será gravado. O RT por linha (`rt_linha_centavos`) **não** sai: depende do orçamento inteiro.
- `insumos` traz custo e origem dos insumos **sem** `id`, pela regra O3a, para a tela mostrar o selo antes de salvar.
- Mesmo recorte de custos da D23 (sem `view_custos`, só os preços). Funciona em qualquer status (não grava nada).

### 6.7. Projetos do cliente (Revisão 1)

`GET /projetos?cliente_id=12` → objetos de serviço **ativos** do cliente, do mais recente ao mais antigo:

```jsonc
[ { "objeto_id": 31, "identificador": "PRJ-000031", "nome": "Residencial Alpha Ville - Apto 802",
    "endereco_obra": "Av. das Américas, 4200", "ultimo_uso": "2026-09-14" } ]
```

O `GET /clientes/{id}/objetos` existente **não** serve: ele não devolve o `id` do objeto e é compartilhado com os outros segmentos (mexer nele seria PR1 sem necessidade).

### 6.8. Contagens para a lista (Revisão 1)

`GET /contagens` → `{ "RASCUNHO": 3, "ENVIADO": 5, "VENCIDO": 1, "RECUSADO": 2, "APROVADO": 1, "vence_em_3_dias": 2, "total": 12 }`. Conta só a versão mais recente de cada código (como a lista padrão) e roda o vencimento preguiçoso antes (D14).

### 6.9. Erros

| Status | `detail` | Quando |
|--------|----------|--------|
| `404` | "Orçamento não encontrado." | Id inexistente (ou segmento sem a capacidade, D26) |
| `409` | `REVISAO_DESATUALIZADA` · "Este orçamento foi alterado em outro computador. Recarregue para ver a versão atual." | `revisao` diferente (D20) |
| `409` | `STATUS_NAO_EDITAVEL` · "Só é possível editar orçamentos em rascunho." | Escrita fora de `RASCUNHO` (D11) |
| `409` | `TRANSICAO_INVALIDA` · "Ação não permitida para um orçamento {status}." | Transição inválida |
| `422` | "Para enviar, informe o cliente, o nome do projeto e pelo menos um móvel." | D13 (a mensagem lista só o que falta) |
| `422` | "Informe o motivo da recusa." | D17 |
| `422` | "Móvel terceirizado precisa da central parceira." | `TERCEIRIZADA` sem `central_fornecedor_id` |
| `422` | `CALCULO_INVALIDO` · mensagens do motor (Spec 05 §6.6), com `campo` | Desconto/sinal maior que o total, valores negativos etc. |
| `422` | "Limite de {n} {itens} atingido." | §5.1 |
| `422` | "Arquivo não suportado. Envie JPG, PNG, WebP ou PDF." / "Arquivo maior que {n} MB." | D27 |
| `403` | Mensagem padrão do `check_permission` | Permissão (D22, D24) |
| `409` | `EXCLUSAO_NAO_PERMITIDA` · "Só é possível excluir um orçamento em rascunho que nunca foi enviado." | D18 |

**Formato (Revisão 1).** Os `409` e o `422` do motor respondem `detail` como objeto, no formato que o `getErrorMessage` do frontend já entende (usado pelo módulo fiscal):

```jsonc
{ "detail": { "codigo": "REVISAO_DESATUALIZADA", "mensagem": "Este orçamento foi alterado em outro computador. Recarregue para ver a versão atual." } }
{ "detail": { "codigo": "CALCULO_INVALIDO", "campo": "desconto", "mensagem": "O desconto não pode ser maior que o total do orçamento." } }
```

A tela decide pelo `codigo` (dois `409` diferentes pedem reações diferentes) e mostra o erro do motor embaixo do `campo` certo. `campo` é `desconto`, `sinal`, `markup`, `perda`, `custo_hora` ou `null`; o serviço o deduz pela validação que falhou (o motor continua devolvendo só a frase). Os demais `422` (Pydantic, D13, D17, anexos, limites) seguem o formato de hoje.

---

## 7. Especificação técnica

### 7.1. Numeração

```python
def proximo_codigo(db: Session) -> str:
    """ORC-AAAA-NNNNNN: o próximo da sequência do ano (mesma lógica de get_next_numero da OS)."""
    ...

def criar_orcamento(db, dados, usuario_token):
    for tentativa in (1, 2):                     # dois computadores podem pedir o mesmo número
        try:
            codigo = proximo_codigo(db)
            ...                                  # insere com versao=1
            db.commit()
            return orcamento
        except IntegrityError:                   # uq_marcenaria_orcamentos_codigo_versao
            db.rollback()
            if tentativa == 2:
                raise
```

A OS gera o número da mesma forma ("último + 1") e **não** tem essa nova tentativa. Fica registrado (não é escopo daqui).

### 7.2. Tradução banco ↔ motor — `orcamento_calculo.py`

```python
def montar_entrada_motor(orc: OrcamentoModel, so_aprovados: bool = False) -> OrcamentoCalc:
    """Converte o orçamento do banco na entrada da Spec 05.

    so_aprovados=True é usado pela Spec 08A (aprovação parcial, O4): só entram os
    móveis com aprovado=True. Aqui (06A) é sempre False.
    """
    rt_total_bp = sum(rt.rt_bp for rt in orc.rts)               # D7: o motor recebe a soma
    ambientes = tuple(
        AmbienteCalc(
            id=str(amb.id),
            moveis=tuple(_movel_para_calc(m) for m in amb.moveis if not so_aprovados or m.aprovado),
        )
        for amb in sorted(orc.ambientes, key=lambda a: a.ordem)
    )
    return OrcamentoCalc(
        ambientes=ambientes,
        markup_bp=orc.markup_bp, perda_bp=orc.perda_bp, custo_hora_centavos=orc.custo_hora_centavos,
        rt_bp=rt_total_bp, rt_modo=orc.rt_modo,
        instalacao_custo_centavos=orc.instalacao_custo_centavos,
        desconto=AjusteCalc(orc.desconto_modo, orc.desconto_valor),
        sinal=AjusteCalc(orc.sinal_modo, orc.sinal_valor),
    )
```

Toda escrita termina com: carregar a árvore → montar a entrada → chamar o motor → atualizar o **resumo** do cabeçalho (D5) → somar 1 na `revisao` → commit. Se o motor levantar `ValueError` (ex.: desconto maior que o novo total), a escrita é **desfeita** e responde `422`.

### 7.3. Custo do produto (O3a) — `orcamento_precos.py`

```python
def custo_do_produto(produto: ProdutoModel) -> tuple[int, str]:
    """(centavos, origem) pela regra O3a: última compra, senão custo médio, senão zero."""
    estoque = produto.estoque
    if estoque and estoque.valor_entrada:                 # último preço de compra
        return estoque.valor_entrada, "ULTIMA_COMPRA"
    if estoque and estoque.custo_medio:                   # reserva: custo médio
        return estoque.custo_medio, "CUSTO_MEDIO"
    return 0, "SEM_CUSTO"                                 # o motor avisa INSUMO_SEM_CUSTO
```

Conferir se `valor_entrada = 0` deve contar como "sem custo" (proposta: sim, como acima).

### 7.4. Vencimento preguiçoso (D14)

```python
def marcar_vencidos(db: Session) -> None:
    """ENVIADO com validade no passado vira VENCIDO, com evento do 'Sistema'. Chamado pela lista e pelo detalhe."""
    hoje = date.today()                                    # data local da loja (conferir o helper de fuso do projeto)
    vencidos = crud.listar_enviados_vencidos(db, hoje)     # usa ix_marcenaria_orcamentos_validade
    for orc in vencidos:
        orc.status = "VENCIDO"
        registrar_evento(db, orc, "ORCAMENTO_VENCIDO", f"Validade terminou em {orc.data_validade:%d/%m/%Y}.",
                         usuario_nome="Sistema")
    if vencidos:
        db.commit()
```

O vencimento **não** soma na `revisao` (não é edição de quem está com a tela aberta).

### 7.5. Nova versão (D16)

1. Confere status (`ENVIADO`, `VENCIDO` ou `RECUSADO`) e `revisao`.
2. Cria o cabeçalho `versao + 1` com os mesmos campos (parâmetros, projeto, desconto, sinal, observações), `status = RASCUNHO`, `revisao = 1`, datas de envio/validade/recusa vazias.
3. Copia RT, ambientes, móveis e insumos **com os custos copiados** (não os atuais). `aprovado` volta a `NULL`.
4. A versão anterior vira `SUBSTITUIDO`.
5. Eventos `NOVA_VERSAO` nas duas.
6. Tudo numa transação.

### 7.6. Permissões — `permissoes.py`

```python
VER_ORCAMENTOS_MARCENARIA = "view_orcamentos_marcenaria"
GERIR_ORCAMENTOS_MARCENARIA = "manage_orcamentos_marcenaria"
EXCLUIR_ORCAMENTOS_MARCENARIA = "delete_orcamentos_marcenaria"
PERMISSOES_VER_ORCAMENTOS = [VER_ORCAMENTOS_MARCENARIA, GERIR_ORCAMENTOS_MARCENARIA]   # gerir implica ver
```

### 7.7. Anexos

- Imagem: novo contexto `"orcamento_anexo"` em `CONTEXTO_IMAGEM` (`max_dimensao (1920, 1920)`, `qualidade 80`, `diretorio_base "static/uploads/marcenaria/orcamentos"`), pasta por **código**.
- PDF: função nova `salvar_pdf(arquivo, pasta) -> str` no mesmo módulo: confere o início `%PDF` e o tamanho, grava com nome `uuid4().pdf`, devolve o caminho relativo. Sem processamento.
- Excluir anexo apaga o arquivo do disco (`deletar_imagem` já faz isso para o caminho dado).

### 7.8. Migração

`z9a0b1c2d3e4_orcamento_marcenaria.py`, filha da migração da 04A. Só **cria tabelas que faltam** (o `create_all()` do startup costuma criá-las antes; PR8). `downgrade` remove as tabelas na ordem inversa.

---

## 8. Limitações conhecidas

- **Numeração da OS sem nova tentativa:** a OS usa "último + 1" sem tratar dois computadores criando ao mesmo tempo. O orçamento trata (§7.1); a OS fica como está (não é escopo).
- **Anexos compartilhados entre versões (D30):** excluir um anexo numa versão some de todas. É o comportamento esperado para a medição, mas a tela deve dizer "este anexo é usado por todas as versões".
- **Edição concorrente:** a trava otimista avisa, mas não junta as alterações. O segundo computador recarrega e refaz.
- **Vencimento preguiçoso:** um orçamento vencido só muda de status quando alguém abre a lista ou o detalhe. Relatórios futuros que leiam a tabela direto devem considerar `data_validade`.

## 9. Entrega (PR7)

`npm run build:sidecar`. Arquivos novos de backend e uma migração: medir o teto do PyArmor (o pacote de serviços cresce).

---

## 10. Critérios de aceite

- [ ] Criar orçamento copia os parâmetros da configuração; mudar a configuração depois não altera o orçamento.
- [ ] Incluir insumo copia descrição, unidade, código, `sofre_perda` e custo pela regra O3a, com a origem certa.
- [ ] Alterar o preço ou o `sofre_perda` do produto não muda nenhum orçamento; `precos-desatualizados` mostra a diferença e `atualizar-precos` aplica, com evento.
- [ ] O detalhe sempre traz o cálculo da Spec 05; o resumo da lista bate com o total do detalhe.
- [ ] Sem `view_custos`, nenhuma chave de custo ou margem aparece no detalhe nem na lista, e escritas de custo respondem `403`.
- [ ] Só `RASCUNHO` aceita edição; todas as transições da §6.1 seguem D11–D19.
- [ ] Enviar exige cliente, projeto e um móvel, e grava envio e validade.
- [ ] Um `ENVIADO` com validade no passado aparece como `VENCIDO` na primeira leitura, com evento do "Sistema".
- [ ] Nova versão copia a árvore com os custos antigos, deixa a anterior `SUBSTITUIDO` e aparece em `/versoes`.
- [ ] Revisão desatualizada responde `409` e não grava nada.
- [ ] Anexos de imagem e PDF entram, saem e aparecem em todas as versões do código.
- [ ] Histórico registra as transições e ações da D25, não as edições de campo.
- [ ] Tudo responde `404` fora do segmento com `orcamento_tecnico`.
- [ ] Dois orçamentos criados ao mesmo tempo recebem códigos diferentes.
- [ ] Revisão 1: `409`/`422` com `codigo`, simulação, projetos, contagens, D24a e D31 conforme a §11.
- [ ] Código comentado (PR6); suíte inteira verde.

## 11. Casos de teste

### Serviço (sem HTTP)

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Criar com a configuração padrão | markup 9000, perda 1000, validade 15, prazo 30, `RASCUNHO`, `revisao 1`, código `ORC-<ano>-000001` |
| 02 | Mudar o markup da configuração e reler o orçamento | Markup do orçamento inalterado |
| 03 | Insumo de produto com `valor_entrada` | Custo = `valor_entrada`, origem `ULTIMA_COMPRA` |
| 04 | Produto sem `valor_entrada`, com `custo_medio` | Origem `CUSTO_MEDIO` |
| 05 | Produto sem os dois | Custo 0, `SEM_CUSTO`; detalhe com aviso `INSUMO_SEM_CUSTO` |
| 06 | Montar o exemplo da Spec 05 §11.1 (cenário B) | Detalhe com os mesmos números da Spec 05 |
| 07 | Salvar o móvel reenviando insumo com `id` depois de mudar o preço do produto | Custo antigo mantido |
| 08 | Mudar o `sofre_perda` do produto | Orçamento inalterado; aparece em `precos-desatualizados` |
| 09 | `atualizar-precos` com `todos` | Custos novos; evento com a diferença; total igual ao `total_com_precos_novos` |
| 10 | Duplicar móvel | Cópia logo abaixo, " (cópia)", insumos com os mesmos custos copiados |
| 11 | Excluir ambiente | Móveis e insumos removidos (cascade) |
| 12 | Desconto em R$ maior que o novo total ao remover um móvel | `422` com a mensagem do motor; nada gravado |
| 13 | Nova versão de um `RECUSADO` | v2 `RASCUNHO` com a árvore copiada; v1 `SUBSTITUIDO`; `aprovado` nulo |
| 14 | Renovar `VENCIDO` | `RASCUNHO`; validade limpa; evento |
| 15 | Vencimento: `ENVIADO` com validade ontem, chamar a lista | `VENCIDO`; um evento; `revisao` inalterada |
| 16 | Dois `criar_orcamento` disputando o mesmo número (simular `IntegrityError` na 1ª) | Segundo recebe o número seguinte |
| 17 | Enviar sem cliente | `422` dizendo só o que falta |

### API

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 18 | Segmento serigrafia, qualquer rota | `404` |
| 19 | Cargo sem `view_orcamentos_marcenaria` | `403` |
| 20 | Cargo com `manage_orcamentos` e **sem** `view_custos`, `GET /{id}` | Sem `custo_unit_centavos`, `custo_origem`, `margem_*`, `rt_*`, `markup_bp`, `perda_bp`, `custo_hora_centavos`, `instalacao_custo_centavos`; com preços, total, sinal, saldo |
| 21 | Mesmo cargo, insumo novo sem custo informado | `200`; custo copiado do produto |
| 22 | Mesmo cargo, insumo com `custo_unit_centavos` | `403` |
| 23 | `PATCH` com `revisao` antiga | `409` com a mensagem da D20; nada gravado |
| 24 | `PATCH` num `ENVIADO` | `409` "Só é possível editar orçamentos em rascunho." |
| 25 | `voltar-a-editar` num `ENVIADO` | `RASCUNHO`; evento |
| 26 | `recusar` sem motivo / com motivo | `422` / `RECUSADO` com motivo e data |
| 27 | `DELETE` de v1 rascunho nunca enviado / de um já enviado | `204` / `409` |
| 28 | Lista padrão com v1 `SUBSTITUIDO` e v2 `RASCUNHO` | Só v2; com `incluir_versoes_antigas=true`, as duas |
| 29 | `vence_em_dias=3` | Só `ENVIADO` com validade em até 3 dias |
| 30 | Anexo PDF válido / arquivo `.exe` renomeado para `.pdf` / imagem de 6 MB | `201` / `422` / `422` |
| 31 | Anexo incluído na v1 | Aparece em `GET /{v2}/anexos` |
| 32 | `GET /{id}/historico` depois de criar, enviar, voltar a editar | 3 eventos, do mais novo ao mais antigo, com nome do usuário |
| 33 | `acoes` em cada status | Coerente com a §6.1 e com a permissão |

### Revisão 1

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 34 | `PATCH` com `revisao` antiga | `detail.codigo = "REVISAO_DESATUALIZADA"` |
| 35 | `PATCH` com desconto em R$ maior que o bruto | `422`, `detail = {codigo: "CALCULO_INVALIDO", campo: "desconto", ...}` |
| 36 | Cargo sem `view_custos` faz `PUT` de móvel sem `mao_obra` | Mão de obra gravada antes continua igual (D24a) |
| 37 | `simular` com insumo novo de produto sem custo | Origem `SEM_CUSTO`, aviso `INSUMO_SEM_CUSTO`; nada gravado; `revisao` igual |
| 38 | `simular` e depois salvar o mesmo móvel | `preco_unit_centavos` iguais |
| 39 | `GET /projetos?cliente_id=` | Só objetos ativos desse cliente, com `objeto_id` |
| 40 | `GET /contagens` com v1 `SUBSTITUIDO` e v2 `ENVIADO` | Conta só a v2 |
| 41 | Anexo incluído e legenda alterada num `ENVIADO` | `201`/`200`; `revisao` igual; num `SUBSTITUIDO`, `409` |
| 42 | `POST /` sem `funcionario_id`, usuário ligado a um funcionário | Vendedor = esse funcionário |

---

## Revisão 1 (06/10/2026) — pedidos da tela (Spec 06B)

Escrever a 06B mostrou o que faltava para a tela funcionar bem:

1. **`409` e `422` do motor com `codigo`** (§6.9): a tela precisa distinguir "outro computador mudou" (recarregar) de "não está em rascunho" (mostrar a faixa), e mostrar o erro do desconto embaixo do desconto.
2. **`GET /projetos`** (§6.7): o endpoint de objetos do cliente que existe não devolve o `id`.
3. **`POST /moveis/simular`** (§6.6): o preço do móvel aparece enquanto o usuário monta, sem cálculo em TypeScript (C8).
4. **D24a:** chave de custo ausente no `PUT` do móvel mantém o valor. Sem isso, o vendedor sem custos apagaria a mão de obra.
5. **`GET /contagens`** (§6.8): os chips da lista.
6. **D31:** anexos fora do rascunho, sem somar na `revisao`, e `PATCH` da legenda.
7. **Vendedor padrão** no `POST /`.


## Revisão 2 (06/10/2026) — pedidos da proposta (Spec 07)

1. **Contato no detalhe:** `cliente` ganha `telefone` (celular, senão o fixo), `email` e `endereco` (uma linha, no formato de `getClienteEndereco` do frontend); `vendedor` ganha `telefone` (celular, senão o fixo). Não são custo: saem para todos. Motivo: a proposta precisa deles, e buscar o cliente à parte exigiria a permissão de clientes, que o vendedor pode não ter.
2. **Evento de envio com os valores:** `ORCAMENTO_ENVIADO` grava em `dados` `{total_centavos, sinal_centavos, data_validade, qtd_moveis}` e a frase "Enviado com total de R$ 9.238,89, válido até 21/10/2026.". É o registro do que o cliente recebeu, mesmo depois de "voltar a editar" (a proposta não é guardada como arquivo; Spec 07 D1).

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 43 | Detalhe sem `view_custos` | `cliente.telefone`, `email`, `endereco` e `vendedor.telefone` presentes |
| 44 | Enviar, voltar a editar, mudar o desconto, enviar de novo | Dois eventos de envio, cada um com o total daquele momento |