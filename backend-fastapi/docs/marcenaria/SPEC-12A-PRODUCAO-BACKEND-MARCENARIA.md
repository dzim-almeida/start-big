# Spec 12A — Produção: Etapas por Móvel (Backend)

| Campo        | Valor                                                                                 |
|--------------|---------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                       |
| Camada       | Backend (FastAPI)                                                                     |
| Dependências | Specs 04A (`etapas_producao`), 08A (aprovação), 09A (ganchos), 11A (terceirizado conferido) |
| Bloqueia     | Spec 12B                                                                              |
| Referência   | SPEC-00: P1, P1a, P2, P2a, P2b, P3, P4, E6a, E6b, O8, T7, FB1, R15-MIG · PR1, PR6, PR7, PR8 |

> **Revisão 1 (08/10/2026) — convergência com a branch (SPEC-00 Revisão 15).** (1) Migração `072437088f6c`, filha de `642b2e8f79fa` (11A). (2) **Trilho da fábrica aposentado (FB1):** ele recusava troca manual de status em OS com `fase_fabrica`; as OS da marcenaria nascem sem fase (03A D13), então a troca de status depois da pergunta (D16, 12B D13) passa pelo `PUT` de OS de sempre, sem bloqueio. (3) **Terceirizado pronto** = `CONFERIDO` pela função `_situacao` da 11A, nos dois modos (pedido do Compras ou manual).

---

## 1. Objetivo

Acompanhar a fabricação de cada móvel produzido na fábrica:

1. Na aprovação, cada móvel interno recebe uma **cópia** das etapas padrão (Corte → Borda → Furação → Montagem → Embalagem), que pode ser **editada** naquele móvel (P1).
2. Cada etapa passa por **Pendente → Em execução → Concluída**, com quem fez e quando.
3. Quando **todos** os móveis da OS estão prontos (internos com todas as etapas concluídas e terceirizados conferidos), o sistema **sugere** mover a OS para o próximo status — nunca muda sozinho (P2).
4. Um resumo de **todas as OS em produção**, para o quadro da fábrica.

## 2. Escopo

**Dentro do escopo**
- Etapas por móvel: criação na aprovação, edição da lista, transições, ações em lote.
- Progresso por móvel e por OS, e a sugestão de status.
- Resumo das OS em produção.
- Bloqueio do "desfazer aprovação" quando a produção começou.

**Fora do escopo**
- Telas (12B).
- Tempo gasto por etapa, produtividade por funcionário, apontamento de horas (fase 2).
- Etapas por **peça** (só com plano de corte, fase 2).

---

## 3. Arquivos afetados

```
backend-fastapi/
├── alembic/versions/072437088f6c_producao_marcenaria.py   # CRIAR — filha da 11A (642b2e8f79fa; Revisão 1)
├── app/
│   ├── db/models/marcenaria/etapa.py                       # CRIAR
│   ├── db/crud/marcenaria/etapa.py                         # CRIAR
│   ├── schemas/marcenaria/producao.py                      # CRIAR
│   ├── services/marcenaria/producao.py                     # CRIAR
│   ├── services/marcenaria/aprovacao.py                    # ALTERAR — cria as etapas na aprovação (08A)
│   ├── services/marcenaria/__init__.py                     # ALTERAR — bloqueio do desfazer
│   └── api/v1/endpoints/marcenaria_producao.py             # CRIAR
└── test/services/marcenaria/test_producao.py               # CRIAR
```

Nenhum arquivo compartilhado muda: a troca de status da OS continua pelo endpoint de OS que já existe (a tela chama, depois da pergunta).

---

## 4. Decisões

### 4.1. Etapas

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Na **aprovação** (dentro da transação da 08A), cada móvel aprovado `INTERNA` recebe as etapas de `configuracoes_marcenaria.etapas_producao` **daquele momento**, todas `PENDENTE` | P1 e 04A D7: cópia. Mudar a configuração depois não mexe em OS aprovada |
| D2 | Móvel com quantidade maior que 1 (3 aéreos iguais) tem **um** conjunto de etapas: a etapa vale para as 3 unidades | O marceneiro corta e monta os iguais juntos; etapas por unidade triplicariam o trabalho de marcar |
| D3 | A lista de etapas do móvel é **editável** enquanto a OS estiver aberta: incluir (no fim ou depois de uma etapa), renomear, remover e reordenar. Etapa **concluída** não pode ser removida nem renomeada (só reaberta antes) | P1: um móvel com pintura ganha a etapa "Pintura"; um painel simples perde "Furação". O que já foi feito não some do histórico |
| D4 | Limites: 1 a 20 etapas por móvel, nomes de 1 a 60 caracteres sem repetir no móvel (as mesmas regras da configuração, 04A) | Mesmas regras dos dois lados |
| D5 | Móvel **terceirizado** não tem etapas: para a produção, está pronto quando `CONFERIDO` (11A, `_situacao`, com pedido do Compras ou manual) | E6: a fábrica não o produz |
| D6 | Móvel aprovado sem etapas (configuração vazia na época, ou removidas todas): a resposta marca `sem_etapas: true`, e `POST /aplicar-padrao` cria as etapas atuais da configuração | Nunca deixa o móvel sem caminho para ficar "pronto" |

### 4.2. Transições

| # | Decisão | Motivo |
|---|---------|--------|
| D7 | **Iniciar** (`PENDENTE → EM_EXECUCAO`) grava o responsável (padrão: o funcionário do usuário logado; pode escolher outro funcionário ativo) e a data | P1 |
| D8 | **Concluir** a partir de `PENDENTE` ou `EM_EXECUCAO`: grava quem concluiu, a data e, se não houver, o responsável (mesmo padrão do D7) | Na prática, muita etapa é marcada no fim do dia, sem ter sido "iniciada" no sistema |
| D9 | **Reabrir** (`CONCLUIDA → PENDENTE` ou `EM_EXECUCAO → PENDENTE`): limpa datas e conclusão; mantém o histórico no evento | Corrigir o marcado errado |
| D10 | A ordem das etapas **não** é imposta: dá para concluir Montagem antes de Borda. A resposta indica a **próxima** etapa pendente de cada móvel (a primeira pendente na ordem) | Fábrica real tem exceções; travar a ordem obrigaria a "marcar mentira" para seguir |
| D11 | Ações **em lote**: concluir (ou iniciar) uma lista de etapas de uma vez, inclusive de móveis diferentes. Atalho: "concluir a etapa {nome} em todos os móveis da OS" | O corte das chapas de uma obra inteira acontece de uma vez; marcar 20 móveis um a um é o que faz a fábrica abandonar o sistema |
| D12 | **Idempotente:** concluir uma etapa já concluída responde `200` sem mudar nada (não sobrescreve quem concluiu). Sem trava de revisão | Duas pessoas marcando a mesma etapa no mesmo minuto querem o mesmo resultado; um `409` aqui seria só atrito |
| D13 | Só com a OS aberta; OS finalizada ou cancelada: somente leitura | Como separação e terceirizados |
| D14 | Cada transição grava evento (06A D25); o lote grava **um** evento com a lista ("Corte concluído em 6 móveis por João") | T7, sem encher o histórico |

### 4.3. Prontidão e status da OS (P2)

| # | Decisão | Motivo |
|---|---------|--------|
| D15 | **Móvel pronto:** interno com todas as etapas concluídas; terceirizado `CONFERIDO`. **Produção concluída:** todos os móveis aprovados prontos | P2, E6a |
| D16 | Toda resposta de escrita traz `sugestao_status`: quando a OS está `ABERTA` e a primeira etapa é iniciada ou concluída → `{de: "ABERTA", para: "EM_ANDAMENTO"}` ("Em Produção", P2a); quando a produção fica concluída e a OS está em `EM_ANDAMENTO` ou `AGUARDANDO_PECAS` → `{para: "AGUARDANDO_RETIRADA"}` ("Aguardando Entrega"). Nada é mudado pelo backend | P2: decisão sempre do usuário. A primeira sugestão é o mesmo princípio aplicado ao começo da produção |
| D17 | A sugestão de "Aguardando Entrega" **não** aparece se a OS já está em `AGUARDANDO_RETIRADA` ou além, e só aparece **uma vez** por conclusão (reabrir uma etapa e concluir de novo volta a sugerir) | Pergunta repetida vira clique automático sem ler |

### 4.4. Resumo e outras regras

| # | Decisão | Motivo |
|---|---------|--------|
| D18 | `GET /producao` lista as OS abertas da marcenaria com: número, cliente, projeto, status, previsão de entrega, progresso (etapas concluídas / total, e móveis prontos / total), móveis atrasados em relação à previsão, e a próxima etapa mais comum ("Montagem em 4 móveis") | O quadro da fábrica (P3): o que está em cada estágio, sem abrir OS por OS |
| D19 | Permissão: **OS** (`servico`), como separação e terceirizados. **Nenhum preço** em nenhuma resposta (P4) | P4: a tela de produção é do marceneiro |
| D20 | **Desfazer aprovação** (08A §7.6) bloqueado com alguma etapa iniciada ou concluída: "A produção já começou (Corte concluído em 3 móveis)." | O8 |

---

## 5. Modelo de dados

```sql
CREATE TABLE marcenaria_etapas (
  id INTEGER PRIMARY KEY,
  movel_id      INTEGER NOT NULL REFERENCES marcenaria_moveis(id) ON DELETE CASCADE,
  nome          VARCHAR(60) NOT NULL,
  ordem         INTEGER NOT NULL,
  status        VARCHAR(12) NOT NULL DEFAULT 'PENDENTE',   -- PENDENTE|EM_EXECUCAO|CONCLUIDA
  responsavel_funcionario_id INTEGER REFERENCES funcionarios(id),
  responsavel_nome VARCHAR(150),                          -- cópia (sobrevive à troca de nome)
  iniciada_em   DATETIME,
  concluida_em  DATETIME,
  concluida_por_nome VARCHAR(150),
  CONSTRAINT uq_marcenaria_etapas_movel_nome UNIQUE (movel_id, nome)
);
CREATE INDEX ix_marcenaria_etapas_movel ON marcenaria_etapas (movel_id, ordem);
CREATE INDEX ix_marcenaria_etapas_status ON marcenaria_etapas (status);
```

A unicidade do nome no móvel é sem diferenciar maiúsculas na validação do serviço (o índice do SQLite diferencia; o serviço confere antes).

Migração `072437088f6c`, filha de `642b2e8f79fa` (11A): só cria a tabela se faltar (PR8; Revisão 1).

---

## 6. Contrato da API

Prefixo `/api/v1/marcenaria`. Permissão `servico`. `404` sem a capacidade ou numa OS sem orçamento aprovado.

| Método e rota | O que faz |
|---------------|-----------|
| `GET /os/{numero_os}/producao` | Móveis com etapas, progresso, `producao_concluida` (§6.1) |
| `POST /os/{numero_os}/producao/etapas/iniciar` | `{etapa_ids, responsavel_funcionario_id?}` (D7, D11) |
| `POST /os/{numero_os}/producao/etapas/concluir` | `{etapa_ids, responsavel_funcionario_id?}` (D8, D11, D12) |
| `POST /os/{numero_os}/producao/etapas/concluir-em-todos` | `{nome}` — a etapa com esse nome em todos os móveis internos (D11) |
| `POST /os/{numero_os}/producao/etapas/{etapa_id}/reabrir` | D9 |
| `PUT /os/{numero_os}/producao/moveis/{movel_id}/etapas` | Lista editada `[{id?, nome}]` na nova ordem (D3, D4) |
| `POST /os/{numero_os}/producao/moveis/{movel_id}/aplicar-padrao` | D6 |
| `GET /producao` | Resumo das OS em produção (D18) |

Toda escrita responde o `GET /os/{n}/producao` atualizado mais `sugestao_status` (D16).

### 6.1. Produção da OS

```jsonc
{
  "os": { "numero_os": "OS-2026-000512", "status": "EM_ANDAMENTO", "editavel": true, "previsao": "2026-11-05" },
  "progresso": { "etapas_concluidas": 14, "etapas_total": 25, "moveis_prontos": 2, "moveis_total": 6 },
  "producao_concluida": false,
  "moveis": [
    { "movel_id": 10, "nome": "Armário aéreo", "ambiente": "Cozinha Gourmet", "quantidade": 3,
      "medidas": { "largura_mm": 800, "altura_mm": 700, "profundidade_mm": 350 },
      "tipo_producao": "INTERNA", "pronto": false, "sem_etapas": false,
      "proxima_etapa": "Montagem",
      "etapas": [
        { "id": 501, "nome": "Corte", "ordem": 1, "status": "CONCLUIDA",
          "responsavel": "João Silva", "concluida_em": "2026-10-09T10:12:00", "concluida_por": "João Silva" },
        { "id": 502, "nome": "Borda", "ordem": 2, "status": "EM_EXECUCAO", "responsavel": "Pedro", "iniciada_em": "…" }
      ] },
    { "movel_id": 11, "nome": "Torre Quente", "tipo_producao": "TERCEIRIZADA", "pronto": false,
      "terceirizado": { "situacao": "ENVIADO", "previsao": "2026-10-20", "atrasado": false } }
  ],
  "sugestao_status": null      // { "de": "EM_ANDAMENTO", "para": "AGUARDANDO_RETIRADA", "rotulo": "Aguardando Entrega" }
}
```

O `rotulo` vem de `rotulo_status(segmento, status)` (01A): a tela mostra "Aguardando Entrega", não o enum.

### 6.2. Erros

| Status | `detail` | Quando |
|--------|----------|--------|
| `409` | `{codigo: "OS_FECHADA"}` | D13 |
| `409` | "A etapa Corte está concluída: reabra antes de remover ou renomear." | D3 |
| `422` | Mensagens dos limites (04A §4.1, em "etapa") | D4 |
| `422` | "Escolha pelo menos uma etapa." | Lote vazio |
| `404` | "Etapa não encontrada nesta OS." | Id de outra OS |

---

## 7. Especificação técnica

```python
def concluir(db, numero_os, etapa_ids, responsavel_id, usuario) -> ProducaoResposta:
    os_, orc = _os_editavel(db, numero_os)                             # D13
    status_antes = _situacao_producao(orc)                             # para decidir a sugestão (D16, D17)
    etapas = crud.etapas_da_os(db, orc.id, etapa_ids)                  # 404 se alguma não for desta OS
    responsavel = _responsavel(db, responsavel_id, usuario)            # padrão: funcionário do usuário (D7)
    concluidas_agora = []
    for etapa in etapas:
        if etapa.status == "CONCLUIDA":
            continue                                                   # D12: idempotente
        etapa.status = "CONCLUIDA"
        etapa.concluida_em = agora_utc()
        etapa.concluida_por_nome = _nome(usuario)
        if not etapa.responsavel_funcionario_id:                        # D8
            etapa.responsavel_funcionario_id, etapa.responsavel_nome = responsavel.id, responsavel.nome
        concluidas_agora.append(etapa)
    if concluidas_agora:
        registrar_evento(db, orc, "ETAPAS_CONCLUIDAS", _frase_lote(concluidas_agora, usuario), os_id=os_.id)  # D14
    resposta = montar_producao(db, os_, orc)
    resposta.sugestao_status = _sugestao(os_, status_antes, resposta)  # D16, D17
    return resposta
```

- `_situacao_producao` devolve `NAO_INICIADA`, `EM_ANDAMENTO` ou `CONCLUIDA`; a sugestão só aparece na **mudança** (`NAO_INICIADA → …` ou `… → CONCLUIDA`), o que cumpre D17 sem coluna nova.
- A **conferência** e o **voltar** de terceirizado (11A) também mudam a prontidão: as duas respostas da 11A passam a trazer `sugestao_status`, calculado pela mesma função (`_sugestao`). Sem isso, a OS cujo último móvel a ficar pronto é o terceirizado nunca receberia a pergunta.
- A criação na aprovação (D1) é uma chamada `producao.criar_etapas_da_aprovacao(db, orc)` no fim de `aprovar` (08A §7.1), antes do evento. O desfazer (08A §7.5) apaga as etapas dos móveis (todas pendentes, garantido pelo D20).
- `GET /producao` (D18): uma consulta agrupada por OS (contagens por status), mais uma para a "próxima etapa" por móvel; nunca uma por OS em laço.

---

## 8. Limitações conhecidas

- Sem tempo gasto nem produtividade (fase 2); as datas de início e conclusão ficam gravadas para isso.
- Etapas por móvel, não por unidade (D2) nem por peça.
- A sugestão de status não considera a separação (material todo retirado): a produção pode terminar com sobra não devolvida; a separação mostra isso à parte.

## 9. Entrega (PR7)

`npm run build:sidecar`.

---

## 10. Critérios de aceite

- [ ] Aprovar cria as 5 etapas padrão em cada móvel interno; terceirizados sem etapas; mudar a configuração depois não altera a OS.
- [ ] Editar as etapas de um móvel (incluir "Pintura", remover "Furação", reordenar); etapa concluída não pode ser removida.
- [ ] Iniciar, concluir (direto de pendente), reabrir; lote e "concluir em todos"; concluir de novo não muda nada.
- [ ] Progresso por móvel e OS; terceirizado conferido conta como pronto.
- [ ] Sugestão "Em Produção" na primeira etapa de uma OS aberta e "Aguardando Entrega" quando tudo fica pronto; nunca muda o status sozinho.
- [ ] Resumo de produção de todas as OS abertas.
- [ ] Desfazer aprovação bloqueado com produção iniciada. Nenhum preço. Código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Aprovar com 2 internos e 1 terceirizado | 10 etapas pendentes; terceirizado sem etapas |
| 02 | Mudar a configuração e reler a OS | Etapas iguais |
| 03 | Aprovar com a configuração de etapas vazia (forçada no banco) | `sem_etapas: true`; `aplicar-padrao` cria as atuais |
| 04 | Incluir "Pintura" depois de "Montagem" | Ordem atualizada |
| 05 | Remover etapa concluída | `409` |
| 06 | Nome repetido ("corte" com "Corte") | `422` |
| 07 | Concluir etapa pendente direto | Concluída; responsável = funcionário do usuário |
| 08 | Concluir a mesma etapa duas vezes | Segunda sem mudança; `concluida_por` da primeira |
| 09 | `concluir-em-todos` "Corte" | Corte concluído em todos os internos; um evento |
| 10 | Primeira etapa numa OS `ABERTA` | `sugestao_status` para `EM_ANDAMENTO`, rótulo "Em Produção" |
| 11 | Última etapa com terceirizado `CONFERIDO` | `producao_concluida: true`; sugestão "Aguardando Entrega" |
| 12 | Mesmo, com terceirizado só `RECEBIDO` | Sem conclusão nem sugestão |
| 13 | Reabrir e concluir de novo | Sugere de novo (D17) |
| 14 | OS já em `AGUARDANDO_RETIRADA` | Sem sugestão |
| 15 | OS finalizada | Escritas `409 OS_FECHADA` |
| 16 | Desfazer aprovação com uma etapa concluída | Motivo do D20 |
| 17 | `GET /producao` com 3 OS abertas | Progresso e próxima etapa de cada; sem preço |
| 18 | Etapa de outra OS no lote | `404`; nada concluído |
