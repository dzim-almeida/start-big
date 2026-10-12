# Spec 03A — Ajuste do Segmento Marcenaria (Backend)

| Campo        | Valor                                                                    |
|--------------|--------------------------------------------------------------------------|
| Status       | Implementada em 09/10/2026                                               |
| Camada       | Backend (FastAPI) · toca `services/ordem_servico.py` (compartilhado) ⚠️  |
| Dependências | Spec 01A                                                                 |
| Bloqueia     | Spec 03B, Spec 08A                                                       |
| Referência   | SPEC-00 (Revisão 4): O4, E0, E0a, E0b · SPEC-00 (Revisão 15): FB1 · PR1, PR6, PR7 |

> **Revisão 3 (08/10/2026) — FB1, aposentadoria da fábrica.** A branch recebeu em 08/10 o módulo "fábrica" (`docs/marcenaria-fabrica-plano.md`, F1–F5), que liga um trilho de 10 fases nas OS de Planejados quando a chave `configuracoes_os.modo_fabrica` está ligada. A trava desta spec (OS só nasce do orçamento) e o trilho (status travado) não convivem. Esta spec passa a **aposentar a fábrica no backend** antes de qualquer código novo da marcenaria: nenhuma OS nova entra no trilho, o cancelamento deixa de devolver a separação fora do trilho, e os testes que exigiam o trilho ligado dão lugar a um teste que prova que ele ficou inerte. O banco não muda. Novas seções: D13–D18, §6.5, casos 20–28.
>
> **Revisão 2 (06/10/2026) — Reforma de móveis fora da fase 1 (decisão do usuário):** spec reescrita. A marcenaria fica com **um tipo só** (Planejados), toda OS nasce do orçamento, e `aprovacao_itens` sai do segmento (O4 original). A Revisão 1 (manter a aprovação por causa da Reforma) perdeu o objeto. A referência da Reforma, para a volta, está na SPEC-00 §7.1.

---

## 1. Objetivo

Adaptar a definição do segmento marcenaria ao orçamento técnico (opção 3 da SPEC-00):

1. A marcenaria passa a ter **um tipo de trabalho só, "Móveis planejados"**, com os dados do projeto (nome e endereço da obra). Ambiente, módulos, material, acabamento, ferragens, montagem e etapa saem: passam a viver no orçamento e na produção.
2. **Toda OS da marcenaria nasce da aprovação de um orçamento.** O caminho comum de criação (`POST /ordens-servico/`) recusa a criação, e a OS não pode trocar de tipo depois.
3. A **Reforma de móveis** sai do registry (fica para uma fase seguinte).
4. A capacidade **`aprovacao_itens`** sai da marcenaria: os móveis são aprovados no orçamento.
5. **A fábrica é aposentada** (Revisão 3, FB1): nenhuma OS nova entra no trilho de 10 fases, e o cancelamento só devolve separação de OS do trilho antigo.

## 2. Escopo

**Dentro do escopo**
- `marcenaria.py`: só o tipo Planejados, enxuto, com `criacao_manual=False`; sem Reforma; sem `aprovacao_itens`.
- `tipo_de_trabalho()` ganha o parâmetro opcional `criacao_manual` (padrão `True`).
- Funções de registry `tipo_permite_criacao_manual()` e `label_do_tipo()`.
- Trava em `create_ordem_servico` e `update_ordem_servico`, com o parâmetro `origem_orcamento` reservado para a Spec 08A.
- Testes de registry, de serviço e de API.
- **Aposentadoria da fábrica no backend** (Revisão 3): `modo_fabrica_ligado()` sempre `False`; `devolver_tudo` no cancelamento só para OS com `fase_fabrica`; testes da fábrica que exigiam o trilho ligado trocados por um teste de inércia.

**Fora do escopo**
- Frontend: botão "Criar OS", tipo travado, textos de impressão, fallback de capacidades (Spec 03B).
- A criação da OS pela aprovação do orçamento (Spec 08A, que usa `origem_orcamento=True`).
- Novas capacidades das abas Orçamento, Separação, Produção e Entrega: cada uma entra na spec que a implementa (08B, 10A, 12A, 13A). Declarar antes criaria uma aba vazia.
- Reforma de móveis (SPEC-00 §7.1).
- Telas da fábrica (Spec 03B, Revisão 3) e remoção do código inerte da fábrica (spec de limpeza, depois do piloto).
- Qualquer mudança no banco: tabelas e colunas da fábrica ficam (FB1).

---

## 3. Arquivos afetados

```
backend-fastapi/
├── app/
│   ├── core/segmentos/
│   │   ├── campos.py                          # ALTERAR — tipo_de_trabalho(..., criacao_manual=True)
│   │   ├── __init__.py                        # ALTERAR — exportar as funções novas
│   │   └── definicoes/
│   │       ├── __init__.py                    # ALTERAR — tipo_permite_criacao_manual(), label_do_tipo()
│   │       └── marcenaria.py                  # ALTERAR — só Planejados; sem Reforma; sem aprovacao_itens
│   └── services/
│       ├── ordem_servico.py                   # ALTERAR ⚠️ — trava na criação e na edição; cancelamento (FB1)
│       └── fabrica/modo.py                    # ALTERAR — modo_fabrica_ligado() sempre False (FB1)
└── test/
    ├── core/test_registry_segmentos.py        # ALTERAR — guardas novos; remove os testes da Reforma
    ├── api/v1/
    │   ├── test_os_identificador_gerado.py    # ALTERAR — caso PRJ passa a criar pelo serviço
    │   ├── test_os_tipo_criacao_manual.py     # CRIAR — trava de criação e edição
    │   └── fabrica/
    │       ├── test_orcamento_api.py          # REMOVER — exige o trilho ligado (FB1, D17)
    │       ├── test_trilho_api.py             # REMOVER — idem
    │       ├── test_separacao_api.py          # REMOVER — idem
    │       ├── test_insumo_api.py             # MANTER — a rota de insumo continua (sem tela)
    │       ├── test_migracao_fabrica.py       # MANTER — as migrações ficam na cadeia
    │       └── test_fabrica_aposentada.py     # CRIAR — a fábrica ficou inerte (D17)
    └── services/fabrica/test_calculo.py       # MANTER — funções puras que continuam no código
```

**Regra que não pode ser quebrada:** a trava lê a **marcação do tipo** no registry, nunca o nome "marcenaria" ou "planejados".

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | A marcenaria declara **um tipo só**: `planejados`, com `nome_projeto` (obrigatório, coluna `modelo`) e `endereco_obra` | Dados do **objeto Projeto** (O5), que o cliente reutiliza quando volta. O resto é do orçamento |
| D2 | Saem de Planejados: `ambiente`, `modulos`, `material`, `acabamento`, `ferragens`, `montagem_incluida`, `etapa` | Repetiriam o orçamento: um orçamento tem **vários** ambientes; módulos e materiais viram móveis e insumos; montagem vira a linha de instalação (C3); etapa vira etapa por móvel (P1) |
| D3 | O tipo `reforma_moveis` **sai** do registry, junto com `ETAPAS_REFORMA` e `servico_reforma` | Fora da fase 1 (E0). A referência para a volta está na SPEC-00 §7.1 |
| D4 | Marcação **`criacao_manual`** no tipo de trabalho, padrão `True`. Planejados declara `False` | Regra genérica: serve a qualquer segmento futuro com um tipo que só nasce de outro documento |
| D5 | A criação manual é recusada quando: (a) o tipo informado tem `criacao_manual=False`; **ou** (b) o tipo está ausente/desconhecido **e** o segmento declara tipos e **nenhum** deles é criável à mão | Sem (b), bastaria omitir o tipo para criar uma OS de marcenaria pelo caminho comum. Para a serigrafia (tipos criáveis) e para segmentos sem tipos, nada muda |
| D6 | A trava é no **backend**, além de o frontend esconder o botão (03B) | Esconder na tela não impede uma chamada direta à API nem uma tela antiga |
| D7 | `create_ordem_servico(..., *, origem_orcamento: bool = False)`. Só a Spec 08A passa `True`. O endpoint **nunca** recebe esse valor do cliente | O caminho legítimo fica aberto, sem expor um "pular trava" na API |
| D8 | Na edição, a OS **não troca de tipo** quando o tipo antigo **ou** o novo não é criável à mão | Uma OS de Planejados virando outra coisa perderia o vínculo com o orçamento |
| D9 | O tipo é lido de `dados_adicionais.tipo_trabalho` **da OS** (onde o frontend grava) | Mesmo lugar do frontend (`OSObjetoDinamicoTab.vue`, `CHAVE_TIPO`) |
| D10 | `aprovacao_itens` **sai** das capacidades da marcenaria. Ficam `imagem_na_entrada` e `garantia_prazo` | O4: os móveis são aprovados no orçamento. A capacidade só ficaria por causa da Reforma, que saiu |
| D11 | As listas `AMBIENTES`, `ETAPAS_PLANEJADOS` e `ETAPAS_REFORMA` saem do arquivo | Sem uso. Se a Spec 06B quiser sugerir nomes de ambiente, ela decide onde a lista mora |
| D12 | Sem migração de dados | Nenhuma loja usa a marcenaria (SPEC-00 §3). Em bancos de desenvolvimento, OS antigas de Reforma ficam com o tipo gravado e os campos em `dados_adicionais`, sem quebrar nada |

### 4.1. Aposentadoria da fábrica (Revisão 3, FB1)

| # | Decisão | Motivo |
|---|---------|--------|
| D13 | `services/fabrica/modo.modo_fabrica_ligado()` passa a devolver **sempre `False`**, com um comentário que aponta para a SPEC-00 FB1. Com isso `fase_inicial()` devolve `None` e nenhuma OS nova recebe `fase_fabrica` | Um ponto só desliga tudo: todo o resto da fábrica pergunta pela **fase** da OS (`modo.py`, docstring) |
| D14 | A chave `configuracoes_os.modo_fabrica` (e `fabrica_travar_etapas`) **continua** no schema e no banco; o valor gravado é ignorado | Mudar o contrato de Configurações de OS mexeria numa tela de todos os segmentos (PR1). A tela da chave sai na 03B |
| D15 | No `cancelar_ordem_servico`, `separacao_fabrica.devolver_tudo(...)` só é chamado quando `os_in_db.fase_fabrica` não é nulo | Hoje ele é "no-op fora da fábrica" só porque nenhuma outra OS separa. A Spec 10A faz a OS da marcenaria separar pela mesma coluna, e a regra dela é **não** devolver sozinho (E2a). Para os outros segmentos nada muda (nenhum item deles tem `quantidade_separada`) |
| D16 | O resto do código da fábrica (rotas `/fabrica`, trilho, separação, central de corte) **fica**, inerte: todas as funções que ele expõe à OS (`assert_status_manual`, `assert_pode_finalizar`, `ao_finalizar`, `ao_cancelar`, `ao_reabrir`) saem cedo sem `fase_fabrica` (conferido em 08/10). O Compras chama `pode_comprar(None, …)`, que responde `True` | Remover código que o serviço da OS e o Compras importam é uma mudança maior do que esta spec. Inerte, ele não muda comportamento; sai numa spec de limpeza depois do piloto |
| D17 | Testes: `test_orcamento_api.py`, `test_trilho_api.py` e `test_separacao_api.py` (pasta `test/api/v1/fabrica/`) **saem**, porque montam o cenário ligando o modo fábrica e criando a OS pelo `POST`, que esta spec recusa. Entra `test_fabrica_aposentada.py`, que prova a inércia (casos 20–26). `test_migracao_fabrica.py`, `test_insumo_api.py` e `test/services/fabrica/test_calculo.py` **ficam** | Teste de comportamento que não existe mais não protege nada; o que importa agora é provar que o trilho não liga e que a OS e o Compras seguem iguais. A saída fica registrada aqui, com o motivo (nenhum teste é apagado em silêncio) |
| D18 | A base de testes de referência (08/10/2026, `53e5d81`): **2.334 passando, 1 pulado**. Depois desta spec: 2.334 − 50 (removidos, D17) + os casos novos, todos passando | Prova de que a saída dos testes é só a da D17 |

> **Resultado (09/10/2026).** Depois da Spec 01A a suíte estava em 2.347. Depois desta spec: **2.287 passando, 1 pulado**, sem falhas. A conta: 2.347 − 50 (D17) − 1 (`test_marcenaria_reforma_nao_tem_montagem_externa`, caso 05) − 39 + 30 novos. Os **39** não estavam previstos aqui: são casos **gerados por campo** em `test_registry_segmentos.py` (cada campo declarado é conferido por vários testes parametrizados), e os 13 campos que saíram da marcenaria (D2, D3) levaram os seus casos junto. Nenhum teste de outro segmento mudou (lista de ids comparada antes × depois).

---

## 5. Contrato da API

### 5.1. `GET /api/v1/ordens-servico/definicao-campos` (marcenaria)

```json
{
  "capacidades": ["imagem_na_entrada", "garantia_prazo"],
  "tipos": [
    {
      "id": "planejados",
      "label": "Móveis planejados",
      "criacao_manual": false,
      "campos": [
        { "nome": "nome_projeto", "label": "Nome do projeto", "tipo": "texto", "obrigatorio": true, "escopo": "objeto", "coluna": "modelo" },
        { "nome": "endereco_obra", "label": "Endereço da obra", "tipo": "texto", "escopo": "objeto" }
      ]
    }
  ]
}
```

(Outras chaves da definição omitidas.) Na **serigrafia**, cada tipo ganha `"criacao_manual": true`. É a única diferença no contrato dela, e o frontend atual ignora chaves que não conhece (o tipo do contrato é uma `interface` TypeScript, sem zod).

### 5.2. `POST /api/v1/ordens-servico/` — erro novo

| Status | `detail` | Quando |
|--------|----------|--------|
| `422` | "OS de Móveis planejados é criada pela aprovação de um orçamento. Use a tela Orçamentos." | Regra D5. O nome vem do `label` do tipo informado; se o tipo foi omitido, do primeiro tipo do segmento |

### 5.3. `PUT /api/v1/ordens-servico/{numero}` — erro novo

| Status | `detail` | Quando |
|--------|----------|--------|
| `422` | "O tipo de trabalho desta OS não pode ser alterado." | `tipo_trabalho` enviado diferente do gravado, e um dos dois não é criável à mão (D8) |

Reenviar o **mesmo** tipo (o formulário costuma reenviar tudo) **não** é erro.

---

## 6. Especificação técnica

### 6.1. `campos.py`

```python
def tipo_de_trabalho(
    id: str,
    label: str,
    campos: List[Dict[str, Any]],
    criacao_manual: bool = True,     # False = a OS deste tipo so nasce de outro documento (Spec 03A, D4)
) -> Dict[str, Any]:
    """(docstring atual mantida) ..."""
    return {"id": id, "label": label, "campos": campos, "criacao_manual": criacao_manual}
```

### 6.2. `definicoes/marcenaria.py`

- Remover `AMBIENTES`, `ETAPAS_PLANEJADOS`, `ETAPAS_REFORMA`, `_REFORMA` e, se ficarem sem uso, `GRUPO_ESPECIFICACAO` e `GRUPO_PRODUCAO`.
- Planejados:

```python
# Unico tipo da fase 1 (SPEC-00, E0). A OS nasce da aprovacao de um orcamento
# (Spec 03A): ambiente, modulos, materiais, montagem e etapa vivem no orcamento
# e na producao por movel. Aqui ficam so os dados do PROJETO, que o cliente
# reutiliza quando volta.
_PLANEJADOS = tipo_de_trabalho(
    "planejados",
    "Móveis planejados",
    [
        *_campos_do_projeto("Nome do projeto"),               # ex.: "Cozinha apto 302"
        # Onde o movel vai ser instalado -- nao e o endereco do cliente.
        campo("endereco_obra", "Endereço da obra", "texto",
              escopo="objeto", grupo=GRUPO_PROJETO, largura="inteira"),
    ],
    criacao_manual=False,   # so pela aprovacao do orcamento (Spec 08A)
)
```

- `"tipos": [_PLANEJADOS]`.
- `"capacidades": [CAP_IMAGEM_NA_ENTRADA, CAP_GARANTIA_PRAZO]` (D10). Remover o import de `CAP_APROVACAO_ITENS` se ficar sem uso.
- `_campos_do_projeto(label_nome)` pode perder o parâmetro (só há um rótulo agora); manter a docstring.
- **Reescrever o cabeçalho do arquivo**: hoje ele descreve as "duas metades" (Planejados e Reforma) e "o que este arquivo não faz: preço; produção", que é a decisão de 16/09. Trocar por um parágrafo curto: fase 1 = só Planejados, OS nasce do orçamento, referência da Reforma na SPEC-00 §7.1.
- **Não mexer** em `rotulos_status` (Spec 01A), `rotulos_situacao`, `identificador` (PRJ).

### 6.3. `definicoes/__init__.py`

```python
def tipo_permite_criacao_manual(segmento: Optional[str], tipo_id: Optional[str]) -> bool:
    """Uma OS deste segmento/tipo pode ser criada pelo caminho comum? (Spec 03A, D5)

    - Tipo conhecido: vale a marcacao dele (padrao True).
    - Tipo ausente ou desconhecido: so e recusado se o segmento declara tipos e
      NENHUM deles e criavel a mao (senao omitir o tipo furaria a trava).
    - Segmento sem definicao ou sem tipos: sempre True (nada muda).
    """
    definicao = get_definicao_segmento(segmento)               # None para segmento generico
    tipos = (definicao or {}).get("tipos") or []               # [] para oficina/informatica
    if not tipos:                                              # sem tipos: comportamento de hoje
        return True
    for tipo in tipos:                                         # tipo informado e conhecido?
        if tipo["id"] == tipo_id:
            return tipo.get("criacao_manual", True)
    # Tipo ausente/desconhecido: permitido se existir ALGUM tipo criavel a mao.
    return any(t.get("criacao_manual", True) for t in tipos)


def label_do_tipo(segmento: Optional[str], tipo_id: Optional[str]) -> str:
    """Nome do tipo para mensagens; sem tipo informado, o primeiro do segmento."""
    tipos = (get_definicao_segmento(segmento) or {}).get("tipos") or []
    for tipo in tipos:
        if tipo["id"] == tipo_id:
            return tipo["label"]
    return tipos[0]["label"] if tipos else (tipo_id or "")
```

Exportar as duas em `app/core/segmentos/__init__.py` (import e `__all__`).

### 6.4. `services/ordem_servico.py`

O arquivo já importa `reg` (`app.core.segmentos`) e `get_segmento_atual` (`app.services.segmentos`).

```python
CHAVE_TIPO_TRABALHO = "tipo_trabalho"   # mesma chave que o frontend grava na OS


def _assert_tipo_pode_ser_criado(db: Session, dados_adicionais_os: dict | None, origem_orcamento: bool) -> None:
    """Recusa OS que so nasce de outro documento (Spec 03A, D5-D7)."""
    if origem_orcamento:                                   # caminho legitimo da Spec 08A
        return
    tipo_id = (dados_adicionais_os or {}).get(CHAVE_TIPO_TRABALHO)
    segmento = get_segmento_atual(db)
    if reg.tipo_permite_criacao_manual(segmento, tipo_id):
        return
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=(
            f"OS de {reg.label_do_tipo(segmento, tipo_id)} é criada pela aprovação "
            "de um orçamento. Use a tela Orçamentos."
        ),
    )


def create_ordem_servico(
    db: Session,
    os_to_create: OrdemServicoCreate,
    *,
    origem_orcamento: bool = False,     # so a Spec 08A passa True; o endpoint nao expoe
) -> OSModel:
    # Primeira linha: nada e gravado se a OS nao puder nascer por aqui.
    _assert_tipo_pode_ser_criado(db, os_to_create.dados_adicionais, origem_orcamento)
    ...  # resto sem mudanca
```

Em `update_ordem_servico`, **antes** de mesclar `dados_adicionais`:

```python
    tipo_antigo = (os_in_db.dados_adicionais or {}).get(CHAVE_TIPO_TRABALHO)
    tipo_novo = (update_data.get("dados_adicionais") or {}).get(CHAVE_TIPO_TRABALHO, tipo_antigo)
    if tipo_novo != tipo_antigo:                                   # reenviar o mesmo tipo nao e erro
        segmento = get_segmento_atual(db)
        if not (reg.tipo_permite_criacao_manual(segmento, tipo_antigo)
                and reg.tipo_permite_criacao_manual(segmento, tipo_novo)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="O tipo de trabalho desta OS não pode ser alterado.",
            )
```

`get_segmento_atual(db)` roda uma vez na criação e só quando o tipo muda na edição.

### 6.5. Aposentadoria da fábrica (Revisão 3, FB1)

**`services/fabrica/modo.py`** (D13):

```python
def modo_fabrica_ligado(db: Session) -> bool:
    """Sempre False: a fábrica foi APOSENTADA (SPEC-00 da marcenaria, Revisão 15, FB1).

    A marcenaria segue as specs de docs/marcenaria/ (orçamento técnico). A chave
    `configuracoes_os.modo_fabrica` continua no banco e no contrato, mas não liga
    mais nada: nenhuma OS nova entra no trilho. O código da fábrica fica inerte
    (tudo pergunta pela `fase_fabrica` da OS, que nenhuma OS nova recebe) e sai
    numa limpeza depois do piloto.
    """
    return False  # `db` fica na assinatura: quem chama não muda
```

**`services/ordem_servico.py`, `cancelar_ordem_servico`** (D15):

```python
    os_in_db.status = OrdemServicoStatus.CANCELADA
    # Fábrica APOSENTADA (SPEC-00 FB1): só a OS que ainda está no trilho antigo
    # devolve sozinha a separação ao cancelar. A OS da marcenaria nova também
    # separa (Spec 10A), mas a regra dela é a contrária: chapa cortada não volta
    # à prateleira por um clique (E2a). Nos outros segmentos nada muda: nenhum
    # item deles tem `quantidade_separada`.
    if os_in_db.fase_fabrica is not None:
        from app.services.fabrica import separacao as separacao_fabrica
        separacao_fabrica.devolver_tudo(db, os_in_db, usuario_token or {})
    trilho_fabrica.ao_cancelar(db, os_in_db, (usuario_token or {}).get("nome") or "Sistema", data.motivo)
```

Nada mais muda no serviço da OS: as outras chamadas à fábrica (criação, edição, finalização, reabertura) já saem cedo sem `fase_fabrica` (D16).

**Testes (D17).** Remover os três arquivos da D17 no mesmo commit da mudança, com a mensagem de commit citando a SPEC-00 FB1 e esta D17. O arquivo novo segue o padrão de `test/api/v1/fabrica/conftest.py`: `TestClient(app)` **sem** `with` (com `with`, o lifespan roda `create_all()` e as migrações no banco real da máquina).

---

## 7. Prova de não regressão (⚠️ PR1)

1. `pytest test/` inteiro antes e depois. Oficina, assistência, serigrafia e PDV sem mudança de resultado.
2. **Serigrafia:** criar OS de camisa, de sacola **e sem tipo**; editar trocando camisa ↔ sacola. Tudo como hoje (D5: a serigrafia tem tipos criáveis à mão).
3. **Informática e oficina** (sem tipos): criação e edição iguais.
4. `/definicao-campos` da serigrafia: a única diferença é `"criacao_manual": true` em cada tipo.
5. **Cancelamento de OS** em informática, oficina e serigrafia: mesmo resultado de antes, inclusive o estoque (nenhuma devolução nova).
6. **Compras:** `demanda_os` e o painel "Compras desta OS" iguais para OS de qualquer segmento (`pode_comprar` continua `True` para OS sem fase).
7. Contagem da suíte: referência de 08/10 (2.334 passando, 1 pulado) menos os 50 da D17, mais os casos novos, todos passando (D18).

## 8. Limitações conhecidas

- **Sem OS manual na marcenaria.** Até a Spec 08A existir, a marcenaria não cria OS nenhuma pela tela; em desenvolvimento, criar pelo serviço (`origem_orcamento=True`) ou por teste. Nenhuma loja é afetada.
- **Conserto rápido de móvel** não tem caminho próprio na fase 1: vira orçamento de um móvel só, ou espera a Reforma voltar.

## 9. Entrega (PR7)

`npm run build:sidecar` depois do merge. A definição **encolhe** bastante: sem risco para o teto de bytecode do PyArmor.

---

## 10. Critérios de aceite

- [ ] A marcenaria declara só `planejados`, com `nome_projeto` e `endereco_obra` e `criacao_manual = false`.
- [ ] `reforma_moveis`, `ETAPAS_*`, `AMBIENTES` e `aprovacao_itens` não existem mais na marcenaria.
- [ ] `POST /ordens-servico/` na marcenaria responde `422` com tipo `planejados`, **sem tipo** e com tipo desconhecido; nada é gravado.
- [ ] `create_ordem_servico(..., origem_orcamento=True)` cria a OS de Planejados e gera o código `PRJ-…`.
- [ ] `PUT` trocando o tipo de uma OS de Planejados responde `422`; reenviar o mesmo tipo funciona.
- [ ] Serigrafia cria e troca de tipo como hoje; informática e oficina iguais.
- [ ] Nenhum `if` com o nome do segmento ou do tipo.
- [ ] Com `configuracoes_os.modo_fabrica = true` gravado no banco, uma OS nova de Planejados (criada pelo serviço) nasce com `fase_fabrica` nula.
- [ ] Cancelar uma OS sem `fase_fabrica` não registra nenhuma entrada de estoque nova; com `fase_fabrica`, devolve a separação como antes.
- [ ] Os 50 testes da D17 removidos, `test_fabrica_aposentada.py` criado, e o restante da suíte igual à referência de 08/10.
- [ ] Suíte inteira verde; código novo comentado (PR6).

## 11. Casos de teste

### Registry — `test/core/test_registry_segmentos.py`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Todo tipo de todo segmento | Tem `criacao_manual` booleano |
| 02 | Tipos da serigrafia | `criacao_manual = True` |
| 03 | Marcenaria | Um tipo só, `planejados`, `criacao_manual = False`, campos `{nome_projeto, endereco_obra}` |
| 04 | Capacidades da marcenaria | `{imagem_na_entrada, garantia_prazo}`; **sem** `aprovacao_itens` |
| 05 | **Remover** `test_marcenaria_reforma_nao_tem_montagem_externa` | Substituído pelo caso 03 |
| 06 | `test_ids_dos_tipos_da_marcenaria_sao_contrato_com_o_frontend` | Passa a esperar `{"planejados"}` (atualizar a docstring: só Planejados na fase 1) |
| 07 | `tipo_permite_criacao_manual("marcenaria", x)` para `x` = `"planejados"`, `None`, `"inexistente"`, `"reforma_moveis"` | `False` em todos |
| 08 | `tipo_permite_criacao_manual` para `("serigrafia", "camisa")`, `("serigrafia", None)`, `("serigrafia", "inexistente")`, `("assistencia_tecnica", None)`, `(None, None)` | `True` em todos |
| 09 | `label_do_tipo("marcenaria", None)` | `"Móveis planejados"` |
| 10 | Guarda nova: segmento cujos tipos são **todos** não criáveis à mão | Permitido, mas o teste lista quais são (hoje só a marcenaria), para a Spec 03B saber onde esconder "Criar OS" |

### API e serviço — `test/api/v1/test_os_tipo_criacao_manual.py`

Mesmo setup de `test_os_identificador_gerado.py` (`_autenticar_e_criar_empresa`, `_criar_cliente`), com o tipo em `dados_adicionais` **da OS**. Os casos de serviço usam a mesma sessão de banco do `client` (fixture `db_session`).

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 11 | Marcenaria, `POST` com `tipo_trabalho = "planejados"` | `422` com "Móveis planejados" e "Orçamentos"; nenhuma OS nem objeto gravado |
| 12 | Marcenaria, `POST` **sem** `tipo_trabalho` | `422` (D5-b) |
| 13 | Marcenaria, `POST` com `tipo_trabalho = "reforma_moveis"` | `422` (tipo desconhecido; nenhum tipo criável) |
| 14 | Serviço: `create_ordem_servico(db, dados_planejados, origem_orcamento=True)` | OS criada com `PRJ-…` |
| 15 | `PUT` na OS do caso 14 mudando o tipo para `"outro"` | `422` "não pode ser alterado" |
| 16 | `PUT` na OS do caso 14 reenviando `planejados` e mudando a observação | `200` |
| 17 | Serigrafia: `POST` sem tipo; `POST` com `camisa`; `PUT` `camisa` → `sacola` | `201`, `201`, `200` (como hoje) |
| 18 | `POST` com `"origem_orcamento": true` no corpo | Ignorado (o schema não tem o campo): `422` igual ao caso 11 |

### `test/api/v1/test_os_identificador_gerado.py`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 19 | `test_marcenaria_abre_os_de_planejados_sem_o_usuario_informar_codigo`: hoje cria por `POST`. Passa a criar pelo **serviço** com `origem_orcamento=True` (o `POST` agora é recusado) | Código `PRJ-…` gerado como antes |

### Fábrica aposentada — `test/api/v1/fabrica/test_fabrica_aposentada.py` (Revisão 3)

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 20 | `modo_fabrica_ligado(db)` com a chave gravada como `true` na marcenaria | `False` |
| 21 | Marcenaria, chave `true`, OS de Planejados criada pelo serviço (`origem_orcamento=True`) | `fase_fabrica` nula |
| 22 | Mesma OS: `PUT` trocando o status | `200` (o trilho não trava o status) |
| 23 | Mesma OS com um item de produto com `quantidade_separada` preenchida, cancelada | Nenhuma movimentação de entrada criada; `quantidade_separada` intacta |
| 24 | OS com `fase_fabrica` gravada à mão no teste (cenário do trilho antigo), cancelada | `devolver_tudo` devolve como antes (entrada no livro) |
| 25 | `compras.demanda_os.demandas_por_produto` com a OS do caso 21 | `pode_comprar = True` |
| 26 | Informática: criar, finalizar e cancelar OS com item de produto | Mesmo estoque e mesmo livro de antes (comparação com a OS equivalente sem a mudança) |
| 27 | `test_migracao_fabrica.py`, `test_insumo_api.py`, `test_calculo.py` | Continuam passando sem mudança |
| 28 | Contagem da suíte | Referência − 50 + novos (D18) |
