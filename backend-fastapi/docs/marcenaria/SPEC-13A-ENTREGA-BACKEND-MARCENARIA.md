# Spec 13A — Entrega e Instalação (Backend)

| Campo        | Valor                                                                                    |
|--------------|------------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                          |
| Camada       | Backend (FastAPI)                                                                        |
| Dependências | Specs 04A (`checklist_vistoria`), 08A (aprovação, bloqueios), 12A (padrão de cópia na aprovação) |
| Bloqueia     | Specs 13B, 14                                                                            |
| Referência   | SPEC-00: I1, I2, I3, I4, I5, I5a, I5b, I6, T7, T8, T8a, P3, P4, O8, R15-MIG · PR1, PR6, PR7, PR8 |

> **Revisão 1 (08/10/2026) — convergência com a branch (SPEC-00 Revisão 15).** (1) Migração `2c4df92b1412`, filha de `072437088f6c` (12A). (2) **I5b:** a OS guarda em `ordens_servico.data_instalacao` a data do próximo agendamento com ambiente ainda não entregue (D20). A coluna já existe (fábrica F3) e só o Compras a lê, para a fila de material atender primeiro quem instala primeiro (`demanda_os.DemandaOS.na_fila`). A Lista de OS continua igual (T8a).

---

## 1. Objetivo

Fechar a obra:

1. **Agendar** a instalação: data, hora, quais ambientes e quais montadores (I4, I5). Uma obra pode ter vários agendamentos (a cozinha numa semana, o closet na outra, I6).
2. Dar os dados do **Termo de Entrega A4 por ambiente** (I1): móveis, checklist (I2), espaço para pendências e assinaturas. O montador leva o papel; o sistema não vai à obra (P3).
3. **Registrar** o resultado de cada ambiente quando o termo volta: "Conforme" ou "Com ressalvas" com as pendências, a data, quem montou, e as fotos (termo assinado e montagem).
4. Acompanhar e **resolver** as pendências; avisar (sem travar) ao finalizar a OS com pendência aberta (I3).

## 2. Escopo

**Dentro do escopo**
- Entrega por ambiente (criada na aprovação), checklist editável, resultado, pendências.
- Agendamentos de instalação.
- Fotos ligadas à entrega, guardadas como fotos da OS.
- Resumo para a finalização da OS e para a lista de instalações.
- Bloqueio do "desfazer aprovação".

**Fora do escopo**
- Telas e a impressão do termo (13B).
- Pagamento de montador (I4: sempre funcionário, sem conta a pagar).
- Cobrança por ambiente (I6).
- Agenda semanal em calendário (I5: fase 2).

---

## 3. Arquivos afetados

```
backend-fastapi/
├── alembic/versions/2c4df92b1412_entrega_marcenaria.py    # CRIAR — filha da 12A (072437088f6c; Revisão 1)
├── app/
│   ├── db/models/marcenaria/entrega.py                     # CRIAR — entrega, pendência, foto, agendamento
│   ├── db/crud/marcenaria/entrega.py                       # CRIAR
│   ├── schemas/marcenaria/entrega.py                       # CRIAR
│   ├── services/marcenaria/entrega.py                      # CRIAR
│   ├── services/marcenaria/agenda.py                       # CRIAR
│   ├── services/marcenaria/aprovacao.py                    # ALTERAR — cria as entregas na aprovação
│   ├── services/marcenaria/__init__.py                     # ALTERAR — bloqueio do desfazer
│   └── api/v1/endpoints/marcenaria_entrega.py              # CRIAR
└── test/services/marcenaria/test_entrega.py, test_agenda.py    # CRIAR
```

Nenhum arquivo compartilhado muda: as fotos usam `upload_foto_os`/`delete_foto_os` como são.

---

## 4. Decisões

### 4.1. Entrega por ambiente

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Na **aprovação**, cada ambiente com pelo menos um móvel aprovado recebe uma **entrega** `PENDENTE`, com a **cópia** do `checklist_vistoria` da configuração (I2; mesmo padrão das etapas, 12A D1) | I6: o termo é por ambiente |
| D2 | O checklist da entrega é **editável** enquanto ela estiver pendente (incluir, renomear, remover, reordenar; 1 a 30 itens, até 120 caracteres, sem repetir — as regras da 04A) | I2: "copiado para cada ambiente e editável ali". A cozinha tem "cooktop nivelado"; o closet não |
| D3 | A instalação, quando aprovada, **não** tem entrega própria: ela acontece dentro dos ambientes | A instalação é o serviço de montar os móveis dos ambientes, não um ambiente |
| D4 | **Registrar resultado:** situação `CONFORME` ou `COM_RESSALVAS`; data da entrega (padrão hoje); montadores que fizeram (funcionários, I4); recebido por (nome de quem assinou na obra, opcional); marcações do checklist (opcional: `ok`, `nao_ok` ou em branco, copiadas do papel); observações; e, com ressalvas, **pelo menos uma pendência** | I1. O checklist é opcional porque o papel assinado (foto) é a prova; digitar cada item vale para quem quiser os dados |
| D5 | **Corrigir** um resultado registrado (mudar a situação, a data, as marcações): permitido enquanto a OS estiver aberta, com evento "Entrega da Cozinha corrigida: Conforme → Com ressalvas" | Erro de digitação de quem passou o papel a limpo |
| D6 | **Pendência:** descrição (até 300), situação `ABERTA`/`RESOLVIDA`; resolver pede como foi resolvido (até 300) e a data, e guarda quem resolveu. Pendência pode ser criada depois do registro (cliente ligou na semana seguinte), mesmo com a OS finalizada | I3. A assistência pós-entrega acontece depois da finalização |
| D7 | **Fotos:** o upload vai para as fotos da OS (`upload_foto_os`, mesmo pipeline e limites) e a entrega guarda o vínculo com o **tipo**: `TERMO` (foto do termo assinado) ou `MONTAGEM`. Excluir pela entrega exclui a foto da OS | I1: "mecanismo de fotos da OS". A foto aparece na galeria da OS, como todas; o vínculo diz de que ambiente e de que tipo ela é |
| D8 | Registrar o resultado **sem** foto do termo é permitido, com o aviso na resposta (`avisos: ["SEM_FOTO_TERMO"]`) | Travar o registro porque a câmera estava sem bateria seria pior que o aviso |

### 4.2. Agendamento (I5)

| # | Decisão | Motivo |
|---|---------|--------|
| D9 | **Agendamento:** data (obrigatória), hora de início (opcional), ambientes da OS que serão instalados (um ou mais, entre os ainda não entregues), montadores (um ou mais funcionários ativos) e observação (até 300). Uma OS pode ter **vários** | I6: a cozinha antes do closet. I4: montador é funcionário |
| D10 | Agendamento pode ser editado e excluído enquanto a entrega dos ambientes dele não foi registrada. Depois, fica como histórico | O agendamento muda com a chuva; o que aconteceu não muda |
| D11 | **Conflito de montador** (mesmo funcionário em dois agendamentos na mesma data): permitido, com aviso na resposta (`avisos: ["MONTADOR_OCUPADO"]`, com quem e onde) | Uma equipe pode fazer duas obras pequenas no mesmo dia; o aviso evita o engano, sem travar |
| D12 | **Agendamento atrasado:** data no passado com algum ambiente dele ainda `PENDENTE` | O que foi marcado e não foi registrado |
| D13 | **Lista de instalações** (`GET /instalacoes?de=&ate=&montador_id=&atrasadas=`): agendamentos ordenados por data e hora, com OS, cliente, endereço da obra, ambientes, montadores e situação das entregas | ⚠️ **Revisão de T8:** a lista e o filtro ficam numa **aba própria** (13B), e não na Lista de OS compartilhada. Ver D14 |
| D14 | Nada muda na tabela nem na lista de OS: o agendamento vive na marcenaria | T8 pedia coluna e filtro na Lista de OS. Para isso a lista **compartilhada** teria de ler uma tabela da marcenaria (ou a tabela de OS ganharia colunas novas): mexer na tela mais usada das 3 lojas em produção por uma informação que só a marcenaria tem. A aba própria entrega o mesmo "quem instala onde amanhã" sem esse risco (PR1) |

### 4.3. Fechamento

| # | Decisão | Motivo |
|---|---------|--------|
| D15 | `GET /os/{n}/entrega/resumo` devolve: ambientes entregues / total, pendências abertas (com a descrição) e `todos_entregues`. A tela de finalização (13B) usa para **avisar** — sem travar — quando há ambiente não entregue ou pendência aberta | I3 e I6. O backend da finalização de OS não muda |
| D16 | Quando o último ambiente é registrado, a resposta traz `todos_entregues: true`; a tela oferece "Finalizar a OS" (o fluxo de finalização de sempre, com os pagamentos) | P2: o sistema sugere; o usuário decide, e a finalização tem as regras de dinheiro dela |
| D17 | **Desfazer aprovação** (08A §7.6) bloqueado com alguma entrega registrada: "Já há entrega registrada (Cozinha Gourmet)." Agendamentos sem registro não bloqueiam e são apagados junto | O8 |
| D18 | Permissão: **OS** (`servico`). Nenhum preço nas respostas (P4) | Montador e atendente lidam com a entrega |
| D19 | Cada registro, correção, pendência, resolução e agendamento grava evento (06A D25) | T7 |
| D20 | **Revisão 1 (I5b):** depois de criar, editar ou excluir um agendamento, e depois de registrar uma entrega, `ordens_servico.data_instalacao` recebe a **menor data** entre os agendamentos que ainda têm algum ambiente `PENDENTE` (ou nula, se não houver). A conta é da marcenaria (`agenda.sincronizar_data_instalacao(db, os_)`); a coluna é a que já existe | O Compras ordena a fila de material por essa data (RC12): a chapa da obra que instala amanhã sai antes da que instala no mês que vem. Nada na Lista de OS lê a coluna (T8a) |

---

## 5. Modelo de dados

```sql
CREATE TABLE marcenaria_entregas (
  id INTEGER PRIMARY KEY,
  os_id        INTEGER NOT NULL REFERENCES ordens_servico(id),
  ambiente_id  INTEGER NOT NULL REFERENCES marcenaria_ambientes(id),
  checklist    JSON NOT NULL,                     -- [{"texto": "...", "marcacao": null|"ok"|"nao_ok"}]
  situacao     VARCHAR(14) NOT NULL DEFAULT 'PENDENTE',   -- PENDENTE|CONFORME|COM_RESSALVAS
  data_entrega DATE,
  montadores   JSON,                              -- [{"funcionario_id": 4, "nome": "Carlos"}] (cópia dos nomes)
  recebido_por VARCHAR(150),
  observacoes  VARCHAR(1000),
  registrado_por_nome VARCHAR(150),
  registrado_em DATETIME,
  CONSTRAINT uq_marcenaria_entregas_os_ambiente UNIQUE (os_id, ambiente_id)
);

CREATE TABLE marcenaria_pendencias (
  id INTEGER PRIMARY KEY,
  entrega_id   INTEGER NOT NULL REFERENCES marcenaria_entregas(id) ON DELETE CASCADE,
  descricao    VARCHAR(300) NOT NULL,
  situacao     VARCHAR(10) NOT NULL DEFAULT 'ABERTA',      -- ABERTA|RESOLVIDA
  criada_em    DATETIME NOT NULL,  criada_por_nome VARCHAR(150),
  resolucao    VARCHAR(300), resolvida_em DATE, resolvida_por_nome VARCHAR(150)
);
CREATE INDEX ix_marcenaria_pendencias_aberta ON marcenaria_pendencias (situacao);

CREATE TABLE marcenaria_entrega_fotos (
  id INTEGER PRIMARY KEY,
  entrega_id   INTEGER NOT NULL REFERENCES marcenaria_entregas(id) ON DELETE CASCADE,
  os_foto_id   INTEGER NOT NULL REFERENCES ordem_servico_fotos(id) ON DELETE CASCADE,
  tipo         VARCHAR(10) NOT NULL                          -- TERMO|MONTAGEM
);

CREATE TABLE marcenaria_agendamentos (
  id INTEGER PRIMARY KEY,
  os_id        INTEGER NOT NULL REFERENCES ordens_servico(id),
  data         DATE NOT NULL,
  hora_inicio  VARCHAR(5),                                   -- "08:00"
  ambiente_ids JSON NOT NULL,                                -- [1, 3]
  montadores   JSON NOT NULL,                                -- [{"funcionario_id": 4, "nome": "Carlos"}]
  observacao   VARCHAR(300),
  criado_por_nome VARCHAR(150), criado_em DATETIME NOT NULL
);
CREATE INDEX ix_marcenaria_agendamentos_data ON marcenaria_agendamentos (data);
```

- Montadores em JSON com o nome copiado: a lista é curta, não é filtrada pelo banco por pessoa em volume (o filtro por montador da lista de instalações é feito em Python sobre os agendamentos do período, que são poucos) e o nome sobrevive à troca de nome.
- Migração `2c4df92b1412`, filha de `072437088f6c` (12A): só cria o que faltar (PR8; Revisão 1).

---

## 6. Contrato da API

Prefixo `/api/v1/marcenaria`. Permissão `servico`. `404` sem a capacidade ou em OS sem orçamento aprovado.

| Método e rota | O que faz |
|---------------|-----------|
| `GET /os/{n}/entrega` | Entregas por ambiente com móveis, checklist, situação, pendências, fotos e agendamentos (§6.1) |
| `GET /os/{n}/entrega/resumo` | D15 |
| `PUT /os/{n}/entrega/{entrega_id}/checklist` | Lista de textos editada (D2) |
| `POST /os/{n}/entrega/{entrega_id}/registrar` | Resultado (D4); também corrige (D5) |
| `POST /os/{n}/entrega/{entrega_id}/pendencias` · `POST …/pendencias/{pid}/resolver` · `…/reabrir` | D6 |
| `POST /os/{n}/entrega/{entrega_id}/fotos` (multipart: arquivo, tipo) · `DELETE …/fotos/{fid}` | D7 |
| `POST /os/{n}/agendamentos` · `PUT …/{aid}` · `DELETE …/{aid}` | D9, D10 |
| `GET /instalacoes?de=&ate=&montador_id=&atrasadas=` | D13 |

### 6.1. Entrega da OS

```jsonc
{
  "os": { "numero_os": "OS-2026-000512", "status": "AGUARDANDO_RETIRADA", "editavel": true },
  "projeto": { "codigo": "PRJ-000031", "nome": "Residencial Alpha Ville - Apto 802", "endereco_obra": "Av. das Américas, 4200" },
  "cliente": { "nome": "Studio Arquitetura & Interiores Ltda", "telefone": "8533334444" },
  "entregas": [
    { "id": 31, "ambiente": "Cozinha Gourmet", "situacao": "PENDENTE",
      "moveis": [ { "nome": "Torre Quente", "quantidade": 1, "medidas": { "largura_mm": 700, "altura_mm": 2200, "profundidade_mm": 600 } } ],
      "checklist": [ { "texto": "Alinhamento de portas e gavetas", "marcacao": null } ],
      "data_entrega": null, "montadores": [], "recebido_por": null, "observacoes": null,
      "pendencias": [], "fotos": [],
      "agendamento": { "id": 7, "data": "2026-11-03", "hora_inicio": "08:00", "montadores": ["Carlos", "Davi"] } }
  ],
  "agendamentos": [ { "id": 7, "data": "2026-11-03", "hora_inicio": "08:00", "ambientes": ["Cozinha Gourmet"],
                      "montadores": [ { "funcionario_id": 4, "nome": "Carlos" } ], "atrasado": false } ],
  "resumo": { "entregues": 0, "total": 2, "pendencias_abertas": 0, "todos_entregues": false }
}
```

`agendamento` da entrega é o mais recente que inclui o ambiente.

### 6.2. Registrar (entrada)

```jsonc
{
  "situacao": "COM_RESSALVAS",
  "data_entrega": "2026-11-03",
  "montadores": [4, 6],
  "recebido_por": "Ana (síndica)",
  "checklist": [ "ok", "nao_ok", null ],          // na ordem do checklist; opcional
  "observacoes": "Cliente pediu para voltar na sexta.",
  "pendencias": [ "Porta do aéreo 2 desalinhada" ]   // obrigatório com ressalvas (D4)
}
```

### 6.3. Erros

| Status | `detail` | Quando |
|--------|----------|--------|
| `422` | "Com ressalvas, informe pelo menos uma pendência." | D4 |
| `422` | "Escolha pelo menos um ambiente e um montador." | D9 |
| `422` | "O ambiente Cozinha Gourmet já foi entregue." | Agendar ambiente entregue |
| `409` | "Este agendamento já tem entrega registrada e não pode mais ser alterado." | D10 |
| `409` | `{codigo: "OS_FECHADA"}` | Registrar, agendar ou editar checklist com a OS fechada (pendências seguem abertas a qualquer tempo, D6) |
| `422` | Mensagens dos limites do checklist (04A) | D2 |

---

## 7. Especificação técnica

```python
def registrar(db, numero_os, entrega_id, dados: RegistroEntrega, usuario) -> EntregaResposta:
    os_, orc = _os_editavel(db, numero_os)                                    # D5: só com a OS aberta
    entrega = _entrega_da_os(db, os_, entrega_id)
    if dados.situacao == "COM_RESSALVAS" and not dados.pendencias and not entrega.pendencias:
        raise HTTPException(422, "Com ressalvas, informe pelo menos uma pendência.")   # D4
    anterior = entrega.situacao
    entrega.situacao = dados.situacao
    entrega.data_entrega = dados.data_entrega or hoje_local()
    entrega.montadores = _montadores(db, dados.montadores)                    # cópia dos nomes (I4)
    entrega.recebido_por, entrega.observacoes = dados.recebido_por, dados.observacoes
    _aplicar_marcacoes(entrega, dados.checklist)                              # opcional (D4)
    for texto in dados.pendencias or []:
        entrega.pendencias.append(PendenciaModel(descricao=texto, criada_em=agora_utc(), criada_por_nome=_nome(usuario)))
    entrega.registrado_por_nome, entrega.registrado_em = _nome(usuario), agora_utc()
    tipo_evento = "ENTREGA_REGISTRADA" if anterior == "PENDENTE" else "ENTREGA_CORRIGIDA"   # D5
    registrar_evento(db, orc, tipo_evento, _frase(entrega, anterior), os_id=os_.id, usuario=usuario)
    resposta = montar_entrega(db, os_, orc)
    resposta.avisos = [] if _tem_foto_termo(entrega) else ["SEM_FOTO_TERMO"]  # D8
    return resposta                                                           # resumo.todos_entregues (D16)
```

- A criação na aprovação (D1) entra junto com a das etapas (12A §7), no fim de `aprovar`. O desfazer apaga entregas pendentes e agendamentos (D17 garante que nenhuma foi registrada).
- `GET /instalacoes`: uma consulta pelos agendamentos do período (índice em `data`) com as OS e as entregas dos ambientes; filtro por montador em Python.

---

## 8. Limitações conhecidas

- **Sem agenda em calendário** (I5): a lista por data atende "quem instala onde amanhã".
- **Montador não registra na obra** (P3): o resultado é passado a limpo na fábrica.
- **Garantia** continua a da OS (capacidade `garantia_prazo`); não há garantia por ambiente.

## 9. Entrega (PR7)

`npm run build:sidecar`.

---

## 10. Critérios de aceite

- [ ] Aprovar cria uma entrega pendente por ambiente aprovado, com a cópia do checklist; o checklist é editável por ambiente.
- [ ] Agendar com data, hora, ambientes e montadores; vários agendamentos por OS; aviso de montador ocupado; atrasado quando a data passa sem registro.
- [ ] Registrar Conforme ou Com ressalvas (exige pendência), com data, montadores, recebido por, marcações e observações; corrigir depois com evento.
- [ ] Fotos de termo e de montagem entram na galeria da OS e ficam ligadas ao ambiente; registro sem foto do termo avisa.
- [ ] Pendências criadas, resolvidas e reabertas, mesmo com a OS finalizada.
- [ ] Resumo para a finalização com ambientes não entregues e pendências abertas; `todos_entregues` no último registro.
- [ ] Lista de instalações por período, montador e atrasadas.
- [ ] Desfazer aprovação bloqueado com entrega registrada. Nenhum preço. Código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Aprovar com 2 ambientes (um sem móvel aprovado) | Uma entrega, com o checklist padrão |
| 02 | Mudar o checklist na configuração | Entrega existente igual |
| 03 | Agendar a cozinha para amanhã com Carlos e Davi | Agendamento; evento |
| 04 | Agendar Carlos em outra OS no mesmo dia | Aceito com `MONTADOR_OCUPADO` |
| 05 | Agendar ambiente já entregue | `422` |
| 06 | Registrar Conforme | Situação, data, montadores; `SEM_FOTO_TERMO` sem foto |
| 07 | Registrar Com ressalvas sem pendência | `422` |
| 08 | Registrar Com ressalvas com 2 pendências | 2 pendências abertas |
| 09 | Corrigir de Conforme para Com ressalvas | Evento `ENTREGA_CORRIGIDA` |
| 10 | Foto tipo `TERMO` | Aparece em `GET /ordens-servico/{n}` (galeria) e na entrega |
| 11 | Excluir a foto pela entrega | Some da galeria da OS |
| 12 | Último ambiente registrado | `todos_entregues: true` |
| 13 | Resumo com pendência aberta | Lista a pendência |
| 14 | Resolver pendência com a OS finalizada | Aceito |
| 15 | Registrar com a OS finalizada | `409 OS_FECHADA` |
| 16 | Agendamento de ontem sem registro | `atrasado: true`; aparece em `?atrasadas=true` |
| 17 | Editar agendamento com entrega registrada | `409` |
| 18 | Desfazer aprovação com uma entrega registrada / só com agendamento | Bloqueado / permitido (agendamento apagado) |
| 19 | `GET /instalacoes?montador_id=4` | Só agendamentos com Carlos |

### Revisão 1 — casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 20 | Agendar a cozinha para 03/11 e o closet para 10/11 | `data_instalacao` = 03/11 |
| 21 | Registrar a entrega da cozinha | `data_instalacao` = 10/11 |
| 22 | Excluir o agendamento do closet | `data_instalacao` nula |
| 23 | Duas OS precisando da mesma chapa, a mais nova instala antes | Em `demanda_os.demandas_por_produto`, a mais nova vem primeiro na fila |
| 24 | Lista de OS (informática e marcenaria) | Igual a antes (nenhuma coluna nova) |

