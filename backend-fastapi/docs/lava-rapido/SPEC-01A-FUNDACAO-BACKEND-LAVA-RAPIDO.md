# Spec 01A — Fundação do Lava-Rápido (Backend): Segmento, Tipos de Veículo, Status e Identificador

| Campo        | Valor                                                                     |
|--------------|---------------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026 — suíte 3.013 → 3.108 passando, 1 pulado (§7)  |
| Camada       | Backend (FastAPI) ⚠️ toca o registry, a criação de OS e a troca de status (por chave declarada) |
| Dependências | SPEC-00 (Revisão 2)                                                       |
| Bloqueia     | Spec 01B, 02A, 03, 04A, 08A, 10A                                          |
| Referência   | SPEC-00: F1, F2, F3, P3, P4, P4a, O2b, O5, O6, O10 · PR1, PR6, PR7, PR9   |

---

## 1. Objetivo

Fazer o sistema **conhecer** o segmento `lava_rapido`, sem nenhuma tabela nova:

1. O segmento existe e pode ser escolhido no cadastro da empresa.
2. A OS é sobre um **Veículo**, de um dos quatro tipos (Carro, Moto, Pesado, Outros), cada um com os seus campos.
3. A **placa** identifica o veículo; no tipo "Outros", se não houver placa, o sistema gera o código.
4. O segmento usa só os status **Aberta, Em Andamento, Pronto e Finalizada** (e Cancelada, pelo cancelamento de sempre); o backend recusa os outros.
5. Vistoria de avarias e fotos na entrada ligadas pelas capacidades que já existem.

## 2. Escopo

**Dentro do escopo**
- `app/core/segmentos/definicoes/lava_rapido.py` e o registro em `definicoes/__init__.py`.
- Duas chaves novas e **opcionais** no registry, com as funções que as leem: `status_usados` e `identificador.gerado_se_vazio`.
- `lava_rapido` em `SEGMENTOS_VALIDOS`.
- Criação da OS: gerar o identificador quando a placa vier vazia, só para quem declara `gerado_se_vazio`.
- Troca de status: recusar status que o segmento não usa, só para quem declara `status_usados`.
- Testes.

**Fora do escopo**
- Telas, onboarding e impressão (Spec 01B).
- Lista de portes editável e preço por porte (Specs 02A/02B). Aqui o porte é um campo de opção com a **lista inicial** da SPEC-00 P2a.
- Lavadores e comissão (Specs 10A/10B, separadas da 01A na Revisão 3 da SPEC-00).
- Capacidades novas (`preco_por_porte`, `quadro_patio`, `executores_os`, `agenda_servicos`): cada uma entra **na spec que a implementa**. Declarar antes seria metadado órfão — o guard do registry existe para impedir isso.

---

## 3. Arquivos afetados

```
backend-fastapi/
├── app/
│   ├── core/segmentos/
│   │   ├── __init__.py                        # ALTERAR — reexportar o novo
│   │   └── definicoes/
│   │       ├── __init__.py                    # ALTERAR — registrar LAVA_RAPIDO; status_usados_do_segmento(),
│   │       │                                  #           status_permitido(), identificador_gerado_se_vazio();
│   │       │                                  #           gerar_identificador() aceita gerado_se_vazio
│   │       └── lava_rapido.py                 # CRIAR — a definição (dado)
│   ├── schemas/acesso/auth.py                 # ALTERAR — 'lava_rapido' em SEGMENTOS_VALIDOS
│   └── services/
│       ├── sistema/segmentos.py               # ALTERAR — assert_status_usado_pelo_segmento()
│       └── ordem_servico/
│           ├── criacao.py                     # ALTERAR ⚠️ — gerar placa vazia (só gerado_se_vazio)
│           └── atualizacao.py                 # ALTERAR ⚠️ — recusar status não usado (só status_usados)
└── test/
    ├── core/test_registry_segmentos.py        # ALTERAR — guards das chaves novas e do lava-rápido
    └── api/v1/test_segmento_lava_rapido.py    # CRIAR — OS de ponta a ponta + não regressão
```

| Camada | Faz | Não faz |
|--------|-----|---------|
| `definicoes/lava_rapido.py` | Declara | Regra |
| `definicoes/__init__.py` | Responde perguntas sobre as declarações | Banco |
| `services/sistema/segmentos.py` | Aplica a regra do segmento atual (lê a empresa) | Saber o nome de um segmento |
| `services/ordem_servico/*` | Chama a regra no ponto certo | Conhecer o lava-rápido |

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Valor `lava_rapido`; constante `SEGMENTO_LAVA_RAPIDO` | F1 |
| D2 | Quatro `tipo_de_trabalho`: `carro`, `moto`, `pesado`, `outros`. Os **ids são contrato** com o frontend (teste próprio, como os da serigrafia) | F3, P4a |
| D3 | **Vistoria e fotos sem tipo**: `vistoria` fica no topo da definição (o guard só proíbe `veiculo`/`checkin` junto com `tipos`), e as capacidades `vistoria` e `imagem_na_entrada` ligam a aba e as fotos | O5. A avaria é do veículo, qualquer que seja o tipo |
| D4 | Identificador `placa`, rótulo "Placa", **`regex: None`** | Com o regex da placa, um código gerado (`VEI-…`) e placa estrangeira (caminhão do Mercosul) **não** valeriam como chave em `identificador_pesquisavel`, e cada visita criaria um veículo novo. A oficina continua com o regex dela |
| D5 | Chave nova **`identificador.gerado_se_vazio: True`** + `prefixo: "VEI"`: placa digitada é a chave; placa vazia → o sistema gera `VEI-AAAA-NNNNNN` do número da OS (mesma `gerar_identificador`) | P4a. Diferente de `gerado` (serigrafia, marcenaria), o campo **continua no formulário** e o usuário digita quando existe |
| D6 | No backend a placa é opcional em **todo** tipo do lava-rápido (vazia = gerada). A obrigatoriedade por tipo (Carro, Moto e Pesado pedem placa) é do formulário (Spec 01B), pelo `obrigatorio` do campo | O serviço da OS não conhece tipo de trabalho para o objeto; uma OS de carro sem placa ainda é uma OS válida, só não acha o carro na próxima visita |
| D7 | `marca` e `modelo` **continuam obrigatórios** (regra de hoje em `_exigir_campos_do_objeto`); o preenchimento automático de `marca`/`modelo` do `gerado` **não** vale para `gerado_se_vazio` | O veículo tem marca e modelo de verdade; no tipo "Outros" o modelo é a descrição ("Jet ski VX") |
| D8 | Chave nova **`status_usados`**: lista dos valores do enum que o segmento usa. Lava-rápido: `ABERTA`, `EM_ANDAMENTO`, `AGUARDANDO_RETIRADA`, `FINALIZADA`, `CANCELADA` | O2b |
| D9 | A troca de status pela **edição da OS** recusa (422) status fora de `status_usados`. Finalizar, cancelar e reabrir têm rotas próprias e não mudam | Tela e backend dizem a mesma coisa. Quem não declara a chave recebe exatamente a regra de hoje |
| D10 | `rotulos_status`: só `AGUARDANDO_RETIRADA` → **"Pronto"** (curto "Pronto"). ABERTA, EM_ANDAMENTO e FINALIZADA ficam com o texto padrão ("Aberta", "Em Andamento", "Finalizada") | "A OS está aberta/finalizada" é o texto que o sistema inteiro já usa; só "Aguardando Retirada" não é a palavra do pátio |
| D11 | `rotulo_defeito` = **"Pedido do cliente"** (placeholder: "Ex: lavagem completa, cuidado com o adesivo do capô"); `rotulo_responsavel` = "Responsável"; `rotulo_situacao` = "Situação do Serviço"; `rotulos_situacao`: REPARADO → "Concluído", SEM_REPARO → "Não realizado", CONDENADO → "Recusado" | O campo `defeito_relatado` é o pedido, como na serigrafia. O desfecho é o mesmo enum; SEM_REPARO/CONDENADO continuam dispensando o pagamento integral (o cliente desistiu, ou a loja recusou o veículo) |
| D12 | Capacidades: **`vistoria`** e **`imagem_na_entrada`**. Sem `diagnostico`, `garantia_prazo`, `garantia_itens`, `aprovacao_itens`, `revisoes` | O6 |
| D13 | Porte: campo `porte` (opção, **obrigatório**, escopo objeto, `dados_adicionais`) com a lista inicial do tipo (SPEC-00 P2a). Grava o **texto** do porte | P3. A Spec 02A troca a fonte das opções para a tabela da loja e decide a chave estável |

### 4.1. Campos por tipo

| Campo | Carro | Moto | Pesado | Outros | Onde grava |
|-------|:-----:|:----:|:------:|:------:|-----------|
| Placa | ✱ | ✱ | ✱ | opcional | coluna `numero_serie` |
| Marca | ✱ | ✱ | ✱ | ✱ | coluna `marca` |
| Modelo (Outros: "Descrição") | ✱ | ✱ | ✱ | ✱ | coluna `modelo` |
| Cor | | | | | coluna `cor` |
| Porte | ✱ | ✱ | ✱ | ✱ | `dados_adicionais.porte` |
| Carroceria | | | opção | | `dados_adicionais.carroceria` |
| Placa do implemento | | | texto | | `dados_adicionais.placa_implemento` |
| Pertences deixados no veículo | texto | texto | texto | texto | OS, `dados_adicionais.pertences` |

✱ obrigatório no formulário.

Portes iniciais — **Carro:** Hatch, Sedã, SUV, Picape, Van / utilitário · **Moto:** Até 300 cc, Acima de 300 cc · **Pesado:** Caminhão 2 eixos, Caminhão 3 eixos, Caminhão 4 eixos, Caminhão 5 eixos ou mais, Ônibus / micro-ônibus · **Outros:** Pequeno, Médio, Grande.

Carroceria: Baú, Sider, Graneleiro, Tanque, Cegonha, Basculante, Outra.

### 4.2. Vistoria

Estados de sempre (OK / N_OK / REPARAR).

- **Externa:** pintura (riscos), amassados, vidros e para-brisa, faróis e lanternas, rodas e aros, retrovisores, para-choques e carenagem, adesivos e envelopamento.
- **Interna:** bancos e estofados, painel, tapetes e assoalho, manchas e odores, objetos de valor.

---

## 5. Contrato

Nenhuma rota nova. O que muda é o que já sai em `GET /api/v1/ordens-servico/definicao-campos` quando a empresa é lava-rápido (a definição inteira, como nos outros segmentos), mais:

| Chave nova | Tipo | Quem declara | Quem não declara |
|------------|------|--------------|------------------|
| `status_usados` | `list[str]` (valores do enum) | lava-rápido | Usa todos os status, como hoje |
| `identificador.gerado_se_vazio` | `bool` | lava-rápido | `False` |

Erro novo (só no lava-rápido): `PUT /ordens-servico/{id}` com status fora da lista → **422** `"Status 'Aguardando Peças' não é usado neste segmento."`

---

## 6. Especificação técnica

### 6.1. Registry — funções novas (`definicoes/__init__.py`)

```python
def identificador_gerado_se_vazio(segmento):
    # True se o usuario PODE digitar o identificador e, em branco, o sistema gera.
    # Diferente de identificador_e_gerado (o sistema SEMPRE gera e nao pergunta).
    return bool((get_identificador_segmento(segmento) or {}).get("gerado_se_vazio"))

def gerar_identificador(segmento, numero_os):
    # Passa a valer tambem para gerado_se_vazio (antes: so `gerado`).
    identificador = get_identificador_segmento(segmento) or {}
    if not (identificador.get("gerado") or identificador.get("gerado_se_vazio")):
        return None
    ...  # resto igual

def status_usados_do_segmento(segmento):
    # Lista declarada, ou None = todos (o padrao de hoje).
    return (get_definicao_segmento(segmento) or {}).get("status_usados")

def status_permitido(segmento, status):
    usados = status_usados_do_segmento(segmento)
    return usados is None or status in usados
```

### 6.2. Criação da OS (`criacao.py`)

`_preencher_identificador_gerado` ganha um ramo **antes** do retorno de hoje:

```python
if reg.identificador_gerado_se_vazio(segmento):
    # Placa digitada vale; vazia, o sistema gera do numero da OS (D5).
    if not (objeto_data.get("numero_serie") or "").strip():
        objeto_data["numero_serie"] = reg.gerar_identificador(segmento, numero_os)
    return  # marca/modelo NAO sao preenchidos aqui (D7)
```

Oficina, informática, serigrafia e marcenaria não declaram a chave e passam pelo caminho de hoje.

### 6.3. Troca de status (`atualizacao.py` + `sistema/segmentos.py`)

```python
# services/sistema/segmentos.py
def assert_status_usado_pelo_segmento(db, novo_status):
    segmento = get_segmento_atual(db)
    valor = getattr(novo_status, "value", novo_status)
    if reg.status_permitido(segmento, valor):
        return
    raise HTTPException(422, detail=f"Status '{rotulo}' não é usado neste segmento.")
```

Chamada em `update_ordem_servico` logo depois da recusa de FINALIZADA/CANCELADA que já existe, e só quando o status muda.

---

## 7. Prova de não regressão (⚠️ PR1)

| O quê | Como |
|-------|------|
| Registry dos outros segmentos | Guard: nenhum outro segmento declara `status_usados` nem `gerado_se_vazio` (teste "diga em voz alta") |
| Criação de OS na oficina, informática e serigrafia | Suítes `test_os_identificador_gerado.py`, `test_ordem_servico_oficina.py`, `test_os_identificador_duplicado.py` sem mudança |
| Troca de status nos outros segmentos | Caso: oficina passa para AGUARDANDO_PECAS → 200, como hoje |
| Suíte inteira | Mesmo número de testes passando de antes + os novos |

**Resultado (12/11/2026).** Antes, em worktree limpo de `2dc12ccd`: 3.013 passando, 1 pulado. Depois: **3.108 passando, 1 pulado**. Diferença de +95 = 9 de API + 8 do guard + 78 casos parametrizados do guard que passaram a conferir os campos do lava-rápido (160 → 246 coletados em `test_registry_segmentos.py`). Nenhum teste existente mudou de resultado; o único teste existente alterado foi `test_so_a_marcenaria_renomeia_status_por_enquanto`, renomeado para `test_so_marcenaria_e_lava_rapido_renomeiam_status` (o "Pronto", dito em voz alta).

## 8. Limitações e observações

- Os estados da vistoria são OK / N_OK / REPARAR para todo segmento (`grupo_vistoria`). "Reparar" é estranho num lava-rápido; a Spec 01B decide o texto mostrado sem mudar o valor gravado.
- O porte grava o **texto**. Se a loja renomear um porte depois (Spec 02A), os veículos antigos mantêm o texto antigo; a 02A trata a chave estável.
- Placa vazia em Carro/Moto/Pesado só é barrada pela tela (D6).

## 9. Entrega (PR7)

Backend mudou → `npm run build:sidecar` antes do próximo instalador. O arquivo novo tem poucos KB; os alterados ficam longe do teto de 64 KB do PyArmor trial (`criacao.py` ≈ 12 KB).

## 10. Critérios de aceite

1. Empresa cadastrada com `segmento: "lava_rapido"` → 201.
2. A definição devolve os 4 tipos, a vistoria, as capacidades e as chaves novas.
3. OS de carro com placa → o veículo grava a placa; a segunda OS da mesma placa reaproveita o veículo.
4. OS de "Outros" sem placa → `numero_serie` = `VEI-AAAA-NNNNNN`.
5. Trocar para AGUARDANDO_PECAS no lava-rápido → 422; para AGUARDANDO_RETIRADA → 200.
6. Oficina e serigrafia idênticas (§7).

## 11. Casos de teste

### Registry — `test/core/test_registry_segmentos.py`
1. `status_usados` só tem valores do enum e inclui ABERTA, FINALIZADA e CANCELADA.
2. Só o lava-rápido declara `status_usados` e `gerado_se_vazio` (por enquanto).
3. `gerado` e `gerado_se_vazio` não convivem; `gerado_se_vazio` exige prefixo.
4. Ids dos tipos do lava-rápido são contrato (`carro`, `moto`, `pesado`, `outros`).
5. Todo tipo do lava-rápido declara `porte` obrigatório com opções.
6. Lava-rápido tem `vistoria` + `imagem_na_entrada` e não tem `garantia_prazo`.
7. `status_permitido` e `gerar_identificador` para lava-rápido, oficina e segmento nulo.
8. `test_so_a_marcenaria_renomeia_status_por_enquanto` passa a aceitar o lava-rápido (com o "Pronto"), dito em voz alta.

### API — `test/api/v1/test_segmento_lava_rapido.py`
1. Empresa com o segmento → 201.
2. OS de carro com placa → veículo com a placa.
3. Segunda OS, mesma placa e cliente → mesmo veículo.
4. OS de "Outros" sem placa → `VEI-…`.
5. Placa estrangeira ("AB123CD") vale como chave (reaproveita na segunda OS).
6. Status AGUARDANDO_PECAS → 422; AGUARDANDO_RETIRADA → 200.
7. Não regressão: oficina continua aceitando AGUARDANDO_PECAS.
