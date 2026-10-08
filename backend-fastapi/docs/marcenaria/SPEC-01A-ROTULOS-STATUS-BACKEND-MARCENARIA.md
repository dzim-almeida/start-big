# Spec 01A — Rótulos de Status por Segmento (Backend)

| Campo        | Valor                                                             |
|--------------|-------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                   |
| Camada       | Backend (FastAPI) ⚠️ código compartilhado                         |
| Dependências | Spec 00                                                           |
| Bloqueia     | Spec 01B (frontend), Spec 03A                                     |
| Referência   | SPEC-00: P2a, PR1, PR4, PR6, PR7                                  |

> **Revisão 3 (06/10/2026) — Reforma fora da fase 1:** a SPEC-00 (Revisão 4) tirou a Reforma de móveis da fase 1. O rótulo **"Aguardando Entrega" continua**: serve ao Planejados (a entrega é a instalação) e já fica pronto para quando a Reforma voltar. Onde esta spec cita a Reforma (§8), leia-se "quando ela voltar". Nada mais muda.
>
> **Revisão 2 (06/10/2026) — maiúsculas:** o texto **completo** segue o padrão da tela de OS, que escreve cada palavra com maiúscula ("Aguardando Aprovação", "Em Andamento"); sem isso, a lista da marcenaria misturaria "Aguardando Aprovação" com "Aguardando entrega". O texto **curto** segue o padrão do dashboard, que escreve só a primeira ("Aguard. retirada"). Os valores da §4.1, §5.1, §6.1 e do caso 05 foram atualizados.

> **Revisão 1 (06/10/2026) — decisão do usuário:** "Aguardando entrega" aprovado no lugar de "Aguardando instalação" (§8). O rótulo é do **segmento**, e o tipo "Reforma de móveis" também usa esse status, mas nele o cliente **retira** o móvel. A SPEC-00 (P2a) recebeu a Revisão 1. O **valor gravado** continua `AGUARDANDO_RETIRADA` (D2, D5): só o texto exibido muda.

---

## 1. Objetivo

Permitir que um segmento **renomeie os status da OS** sem mudar o status em si. A definição do segmento no registry ganha uma chave opcional, `rotulos_status`, e o backend passa a usá-la no único lugar onde escreve texto de status: o widget "OS por status" do dashboard.

A marcenaria é o primeiro segmento a declarar a chave. Oficina, informática, serigrafia e PDV **não declaram** e continuam exatamente como hoje.

Ao final desta spec, `GET /ordens-servico/definicao-campos` já entrega os rótulos novos ao frontend, mas nenhuma tela muda ainda: isso é a Spec 01B.

## 2. Escopo

**Dentro do escopo**
- Chave opcional `rotulos_status` na definição de segmento.
- Função `rotulo_status()` no registry.
- Declaração dos rótulos da marcenaria.
- Dashboard `GET /dashboard/os-por-status` usando o rótulo curto do segmento.
- Testes de guarda do registry e testes de API.

**Fora do escopo**
- Telas, badges, filtros, impressão e cupom (Spec 01B).
- Título do widget "Aguardando Retirada" do dashboard (texto do frontend; Spec 01B).
- Qualquer mudança no enum `OrdemServicoStatus`, nas transições ou nas regras de negócio da OS. **Só o texto muda.**
- Rótulo de status **por tipo de trabalho** (ver §8, alternativa recusada).

---

## 3. Arquivos afetados

```
backend-fastapi/
├── app/
│   ├── core/
│   │   └── segmentos/
│   │       ├── __init__.py                   # ALTERAR — exportar rotulo_status
│   │       └── definicoes/
│   │           ├── __init__.py               # ALTERAR — criar rotulo_status()
│   │           └── marcenaria.py             # ALTERAR — declarar rotulos_status
│   └── services/
│       ├── dashboard.py                      # ALTERAR — get_os_por_status usa o segmento
│       └── segmentos.py                      # CONFERIR — o contrato já devolve a definição inteira
└── test/
    ├── core/
    │   └── test_registry_segmentos.py        # ALTERAR — guardas novos
    └── api/v1/
        └── test_rotulos_status_segmento.py   # CRIAR — API (contrato e dashboard)
```

**Responsabilidade de cada camada:**

| Camada | Faz | Não faz |
|--------|-----|---------|
| `definicoes/marcenaria.py` | Declara os textos (dado) | Lógica |
| `definicoes/__init__.py` | `rotulo_status()`: procura o texto declarado | Decidir o texto padrão |
| `services/dashboard.py` | Escolhe: rótulo do segmento **ou** a tabela padrão de hoje | Conhecer o nome "marcenaria" |
| `services/segmentos.py` | Nada muda: já devolve a definição inteira no contrato | — |

**Regra que não pode ser quebrada:** nenhum arquivo ganha `if segmento == "marcenaria"`. O segmento declara; o motor lê.

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | `rotulos_status` é **opcional**. Segmento sem a chave usa os textos de hoje | Garante PR1: oficina, informática, serigrafia e PDV não mudam |
| D2 | **Só o rótulo** muda. Enum, ordem, transições, filtros, relatórios e regras são os mesmos para todos | Mesma regra do `rotulos_situacao` que já existe: o valor gravado é o mesmo em todo segmento |
| D3 | Cada rótulo declara **dois tamanhos**: `rotulo` (completo, para tela e impressão) e `curto` (para o dashboard, que hoje usa "Aguard. retirada") | A abreviação não é derivável com segurança ("Aguard. entrega" × "Aguardando entrega"). Declarar é mais barato que acertar uma regra |
| D4 | O segmento declara **só os status que quer renomear**. Os demais caem no padrão | Menos texto repetido; o padrão continua num lugar só |
| D5 | As chaves só podem ser valores do enum `OrdemServicoStatus` | Chave inventada nunca casaria com o valor salvo, e o erro seria silencioso (o padrão apareceria) |
| D6 | O texto padrão continua onde está hoje (`_STATUS_LABELS` no dashboard; constantes no frontend). `rotulo_status()` devolve `None` quando não há rótulo próprio | Não mover o padrão evita mexer em código dos outros segmentos |
| D7 | O contrato `/definicao-campos` não muda de forma: a chave aparece dentro de `definicao` porque o serviço já devolve o dicionário inteiro | Zero mudança no endpoint |
| D8 | Rótulo por **segmento**, não por tipo de trabalho | O dashboard soma OS de todos os tipos num mesmo status; um rótulo por tipo não teria como ser exibido ali |

### 4.1. Textos da marcenaria

| Status (enum) | `rotulo` | `curto` | Hoje (padrão) |
|---------------|----------|---------|---------------|
| `EM_ANDAMENTO` | Em Produção | Em produção | Em Andamento / Em andamento |
| `AGUARDANDO_PECAS` | Aguardando Material | Aguard. material | Aguardando Peças / Aguard. peças |
| `AGUARDANDO_RETIRADA` | Aguardando Entrega | Aguard. entrega | Aguardando Retirada / Aguard. retirada |

`ABERTA`, `AGUARDANDO_APROVACAO`, `FINALIZADA` e `CANCELADA` não são declarados: usam o padrão.

---

## 5. Contrato da API

Nenhum endpoint novo. Dois endpoints existentes passam a refletir o segmento.

### 5.1. `GET /api/v1/ordens-servico/definicao-campos`

Sem mudança de código. Para uma empresa de marcenaria, a resposta passa a trazer a chave nova dentro de `definicao`:

```json
{
  "segmento": "marcenaria",
  "tem_definicao": true,
  "definicao": {
    "segmento": "marcenaria",
    "rotulos_status": {
      "EM_ANDAMENTO": { "rotulo": "Em Produção", "curto": "Em produção" },
      "AGUARDANDO_PECAS": { "rotulo": "Aguardando Material", "curto": "Aguard. material" },
      "AGUARDANDO_RETIRADA": { "rotulo": "Aguardando Entrega", "curto": "Aguard. entrega" }
    }
  }
}
```

(Os demais campos da definição foram omitidos.) Para os outros segmentos, a resposta é **idêntica à de hoje**.

### 5.2. `GET /api/v1/dashboard/os-por-status`

O campo `status_label` de cada item passa a usar o rótulo **curto** do segmento, quando houver:

| Segmento | `status` | `status_label` |
|----------|----------|----------------|
| marcenaria | `AGUARDANDO_RETIRADA` | `Aguard. entrega` |
| marcenaria | `ABERTA` | `Aberta` (padrão) |
| assistencia_tecnica | `AGUARDANDO_RETIRADA` | `Aguard. retirada` (igual a hoje) |

**Erros:** nenhum novo.

---

## 6. Especificação técnica

### 6.1. Declaração — `definicoes/marcenaria.py`

Acrescentar ao dicionário `MARCENARIA`, logo depois de `rotulos_situacao`:

```python
    # Rotulos de STATUS da OS (nao confundir com rotulos_situacao, que e o
    # desfecho). O status gravado continua o mesmo enum de todos os segmentos;
    # so o texto mostrado muda. Spec 01A, decisoes D1-D8.
    "rotulos_status": {
        # Quando a OS sai de "aberta", o movel esta sendo fabricado.
        "EM_ANDAMENTO": {"rotulo": "Em Produção", "curto": "Em produção"},
        # Na marcenaria, o que se espera e chapa, fita e ferragem.
        "AGUARDANDO_PECAS": {"rotulo": "Aguardando Material", "curto": "Aguard. material"},
        # Pronto: em Planejados vai ser instalado; em Reforma, o cliente retira.
        # "Entrega" serve aos dois tipos (ver §8 da Spec 01A).
        "AGUARDANDO_RETIRADA": {"rotulo": "Aguardando Entrega", "curto": "Aguard. entrega"},
    },
```

### 6.2. Leitura — `definicoes/__init__.py`

```python
def rotulo_status(
    segmento: Optional[str],      # segmento da empresa (ex.: "marcenaria"), ou None
    status: str,                  # valor do enum, ex.: "AGUARDANDO_RETIRADA"
    curto: bool = False,          # True = versao abreviada (dashboard)
) -> Optional[str]:
    """Texto que o SEGMENTO declarou para um status da OS.

    Devolve None quando o segmento nao renomeia aquele status: quem chama usa
    o texto padrao que ja tem. Nunca inventa um texto padrao aqui (Spec 01A, D6).
    """
    definicao = get_definicao_segmento(segmento)      # dicionario do segmento, ou None
    if not definicao:                                  # empresa sem segmento ou segmento generico
        return None                                    # -> quem chamou usa o padrao
    rotulos = definicao.get("rotulos_status") or {}    # chave opcional: ausente vira {}
    rotulo = rotulos.get(status)                       # so existe para os status renomeados
    if not rotulo:                                     # status que o segmento nao renomeou
        return None
    return rotulo["curto"] if curto else rotulo["rotulo"]  # escolhe o tamanho pedido
```

Exportar em `app/core/segmentos/__init__.py` (import e `__all__`), como as outras funções do registry.

### 6.3. Dashboard — `services/dashboard.py`

```python
from app.core import segmentos as reg                      # registry (dado dos segmentos)
from app.services import segmentos as segmentos_service    # descobre o segmento da empresa


def get_os_por_status(db: Session, empresa_id: int) -> OSPorStatusResponse:
    rows = dashboard_crud.get_os_por_status(db, empresa_id)    # contagem por status (sem mudanca)
    segmento = segmentos_service.get_segmento_atual(db)        # uma consulta, fora do laco
    items = [
        OSPorStatusItem(
            status=row.status.value,
            # 1o: o texto curto que o segmento declarou; 2o: a tabela padrao de hoje;
            # 3o: o proprio codigo, como ja era antes desta spec.
            status_label=(
                reg.rotulo_status(segmento, row.status.value, curto=True)
                or _STATUS_LABELS.get(row.status.value, row.status.value)
            ),
            count=row.count,
        )
        for row in rows
    ]
    return OSPorStatusResponse(items=items, total_ativas=sum(i.count for i in items))
```

- `get_segmento_atual` é chamado **uma vez**, antes do laço.
- `_STATUS_LABELS` **não muda**. É o padrão dos outros segmentos.
- Conferir se `dashboard.py` já importa `segmentos_service` com outro nome antes de acrescentar o import (evitar import circular: o serviço de segmentos não importa o dashboard).

---

## 7. Prova de não regressão (⚠️ PR1)

1. `pytest test/` inteiro, **antes** e **depois**: nenhum teste existente muda de resultado.
2. Para cada segmento sem `rotulos_status` (oficina, assistência, serigrafia, PDV): a resposta de `/definicao-campos` é **byte a byte igual** antes e depois (caso 09).
3. `/dashboard/os-por-status` em informática devolve os mesmos `status_label` de hoje (caso 11).

## 8. Limitações conhecidas e alternativa recusada

**"Aguardando instalação" × "Aguardando entrega".** A SPEC-00 (P2a) combinou "Aguardando instalação". Ao especificar, apareceu um problema: o rótulo é **do segmento**, e a marcenaria tem dois tipos de trabalho. Em "Reforma de móveis", o móvel não é instalado; o cliente o **retira** (ou a loja entrega). Com "Aguardando instalação", toda OS de reforma pronta mostraria um texto falso.

| Opção | Efeito |
|-------|--------|
| **A) "Aguardando entrega"** (escolhida em 06/10) | Serve aos dois tipos: em Planejados, a entrega é a instalação; em Reforma, é a retirada |
| B) Manter "Aguardando instalação" | Texto errado em toda OS de reforma |
| C) Rótulo por tipo de trabalho | O dashboard soma OS dos dois tipos no mesmo status e não teria qual texto mostrar. Exige um mecanismo novo em código compartilhado |

**Rótulo no relatório.** `services/relatorio.py` devolve só o **código** do status; quem escreve o texto é o frontend (Spec 01B). Nada a fazer aqui.

## 9. Entrega (PR7)

Depois do merge: `npm run build:sidecar`. A definição cresce algumas linhas; não deve encostar no teto de bytecode do PyArmor, mas medir antes do instalador.

---

## 10. Critérios de aceite

- [ ] `rotulo_status()` existe, é exportada pelo pacote `app.core.segmentos` e devolve `None` quando não há rótulo próprio.
- [ ] A marcenaria declara exatamente os três status da §4.1, com `rotulo` e `curto`.
- [ ] Nenhum outro segmento declara `rotulos_status`.
- [ ] `/definicao-campos` da marcenaria traz `definicao.rotulos_status`; a dos outros segmentos é idêntica à de antes.
- [ ] `/dashboard/os-por-status` usa o rótulo curto na marcenaria e o texto de hoje nos outros segmentos.
- [ ] Nenhum `if segmento == "marcenaria"` foi escrito.
- [ ] Enum, transições e regras da OS sem nenhuma alteração (`git diff` não toca `core/enum.py` nem `services/ordem_servico.py`).
- [ ] Suíte inteira verde, com o mesmo número de testes passando antes (mais os novos).
- [ ] Trechos de código novos comentados (PR6).

## 11. Casos de teste

### Registry — `test/core/test_registry_segmentos.py`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `test_rotulos_de_status_nao_inventam_valor_de_enum`: chaves de `rotulos_status` de todos os segmentos | Todas pertencem a `OrdemServicoStatus` |
| 02 | Cada rótulo declarado | Tem `rotulo` e `curto`, ambos não vazios |
| 03 | `curto` de todos os rótulos | No máximo 20 caracteres (cabe no widget; o maior padrão hoje é "Aguard. aprovação", 17) |
| 04 | `test_so_a_marcenaria_renomeia_status_por_enquanto` | Oficina, assistência, serigrafia e PDV **não** têm a chave (o teste existe para dizer isso em voz alta, como o de imagem na entrada) |
| 05 | `rotulo_status("marcenaria", "AGUARDANDO_RETIRADA")` | `"Aguardando Entrega"` |
| 06 | `rotulo_status("marcenaria", "AGUARDANDO_RETIRADA", curto=True)` | `"Aguard. entrega"` |
| 07 | `rotulo_status("marcenaria", "ABERTA")` | `None` |
| 08 | `rotulo_status(None, "ABERTA")`, `rotulo_status("outros", "ABERTA")`, `rotulo_status("assistencia_tecnica", "AGUARDANDO_RETIRADA")` | `None` nos três |

### API — `test/api/v1/test_rotulos_status_segmento.py`

Mesmo setup de `test_ordem_servico_oficina.py` (`_autenticar_e_criar_empresa(client, segmento)`), com SQLite em memória.

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 09 | `/definicao-campos` em cada segmento sem rótulo próprio | Sem a chave `rotulos_status`; resto da resposta inalterado |
| 10 | `/definicao-campos` na marcenaria | `definicao.rotulos_status` igual à §5.1 |
| 11 | Informática, uma OS em `AGUARDANDO_RETIRADA`, `/dashboard/os-por-status` | `status_label = "Aguard. retirada"` |
| 12 | Marcenaria, OS em `AGUARDANDO_RETIRADA`, `EM_ANDAMENTO`, `AGUARDANDO_PECAS` e `ABERTA` | `"Aguard. entrega"`, `"Em produção"`, `"Aguard. material"`, `"Aberta"` |
| 13 | Marcenaria — conferir o `status` dos itens | Continua o código do enum (`"AGUARDANDO_RETIRADA"`), nunca o texto |

Para colocar a OS no status desejado, usar o mesmo caminho dos testes de OS existentes (`PUT /ordens-servico/{numero}` com o campo `status`).
