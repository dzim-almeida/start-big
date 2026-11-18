# Licença 09 — API: vagas de computador (sessões)

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend da API (NestJS, Prisma), repositório `aalan-big/plataformaADM` |
| Repositório  | `aalan-big/plataformaADM` (público; outro repositório, fora do harness do `start-big`) |
| Dependências | Acesso de escrita ao `plataformaADM` (ACORDO D-01). Tarefa do comentário do heartbeat no `start-big` (ROTEIRO, passo 2) |
| Bloqueia     | — |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-01, D-10; risco R-02; quadro F6, F17, F21 |

> **Pré-requisito:** a implementação só começa com acesso de escrita ao `plataformaADM` e uma branch nova no próprio repositório.

> **Origem (2026-11-18):** esta spec nasceu da divisão da antiga SPEC-06 na revisão de conflitos (conflito 15). Ela leva a parte de vagas de computador. O F5 (`tokenSessao` no desconectar) **não** veio junto: virou o risco aceito R-02 (conflito 7). Os fatos da §1.1 foram conferidos no código do `plataformaADM` durante a revisão.

## 1. Objetivo

As vagas de computador da licença não podem ficar presas por sessões mortas, e dois caixas entrando juntos não podem passar do limite.

### 1.1. Como funciona hoje (conferido no código)

- Cada computador ocupa uma linha em `LicencaSessao` (`packages/database/src/repositories/licenca-sessao.repository.ts`).
- O `start-big` manda heartbeat de cada caixa a cada **100 segundos** (`backend-fastapi/app/core/tarefas.py:34`; o comentário da linha diz "5 minutos" e está errado).
- A sessão morta só é apagada por um **cron a cada 10 minutos**, que apaga quem está sem heartbeat há **35 minutos** (`apps/server/src/features/cron/cron.service.ts:94-98`, `deletarSessoesInativas(35)`).
- A constante `HEARTBEAT_TIMEOUT_MS` (`dispositivo.service.ts:104`) diz 35 minutos, mas não é ela que decide.
- `countSessoesAtivas` conta **todas** as linhas da licença, vivas ou mortas.
- Na troca de servidor, `assumirServidorDaLicenca` apaga só a sessão do servidor antigo (`licenca-servidor.repository.ts:34-52`).
- No `conectar`, a contagem e a gravação da sessão são dois passos separados (`dispositivo.service.ts:785-830`).

## 2. Escopo

**Dentro do escopo**
- Sessão sem heartbeat há mais de **10 minutos** deixa de contar como vaga, na hora (D-10, F21).
- O cron passa a apagar as sessões com mais de 10 minutos sem heartbeat.
- Na troca de servidor, as sessões dos caixas da loja antiga também são apagadas (F17).
- Contagem e gravação da sessão numa operação só, sem corrida (F6).

**Fora do escopo**
- `tokenSessao` no desconectar (F5): risco aceito R-02.
- Tela para o dono liberar vagas (ACORDO D-10, alternativa B).
- Cadastro, login e titular (LIC-06).

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `packages/database/src/repositories/licenca-sessao.repository.ts` | alterar | Constante única `MINUTOS_SESSAO_VIVA = 10`. `countSessoesAtivas` conta só sessões com heartbeat dentro desse prazo. Nova `ocuparVagaSeCouber`. |
| `apps/server/src/features/cron/cron.service.ts` | alterar | `deletarSessoesInativas(MINUTOS_SESSAO_VIVA)` no lugar de `35`. |
| `apps/server/src/features/dispositivos/dispositivo.service.ts` | alterar | `conectar` usa `ocuparVagaSeCouber`. A constante `HEARTBEAT_TIMEOUT_MS`, que não decide nada, sai. |
| `packages/database/src/repositories/licenca-servidor.repository.ts` | alterar | `assumirServidorDaLicenca` apaga, na troca, todas as sessões da licença menos a do servidor novo. |
| `apps/server/test/licenca/sessoes.test.ts` | criar | Casos CT-01 a CT-07. |

Teste existente que precisa continuar passando: `apps/server/test/licenca/licenca-troca-servidor.test.ts`. A expectativa de tempo muda de 35 para 10 minutos, e isso fica registrado no teste.

## 4. Contrato da API

Nenhuma rota nova. Os erros de limite continuam os de hoje (`400` com a mensagem de limite no `conectar`, `LIMITE_DISPOSITIVOS` no heartbeat).

## 5. Schemas

Nenhum campo novo. A contagem passa a usar o `ultimoHeartbeat`, que já existe em `LicencaSessao`.

## 6. Especificação técnica

### 6.1. Sessão viva = heartbeat nos últimos 10 minutos (D-10, F21)

```typescript
// licenca-sessao.repository.ts — uma regra só para "sessão viva" (D-10)
// O start-big manda heartbeat a cada 100 s: 10 minutos dão folga para várias falhas seguidas.
export const MINUTOS_SESSAO_VIVA = 10

function inicioDaJanela(): Date {
  return new Date(Date.now() - MINUTOS_SESSAO_VIVA * 60 * 1000)
}

export async function countSessoesAtivas(licencaId: string) {
  return prisma.licencaSessao.count({
    // Só conta quem deu sinal de vida dentro da janela. Uma sessão morta deixa de
    // ocupar vaga na hora, sem esperar o cron passar.
    where: { licencaId, ultimoHeartbeat: { gte: inicioDaJanela() } },
  })
}
```

O cron (`cron.service.ts`) continua rodando a cada 10 minutos, agora com `deletarSessoesInativas(MINUTOS_SESSAO_VIVA)`. Ele só faz a limpeza das linhas: quem decide a vaga é a contagem acima.

### 6.2. Troca de servidor apaga as sessões da loja antiga (F17)

A API não sabe quais caixas pertencem a qual servidor: as sessões guardam só o HWID. Na troca, a regra passa a ser: **todas as sessões da licença são apagadas, menos a do servidor novo**. Os caixas da loja nova entram de novo pelo login deles, que já acontece depois da troca (a SPEC-03 avisa: "os caixas precisarão apontar para este computador").

```typescript
// licenca-servidor.repository.ts — na troca, ninguém da loja antiga fica ocupando vaga (F17)
if (hwidAntigo && hwidAntigo !== hwidNovo) {
  operacoes.push(
    prisma.licencaHwidRevogado.upsert({ /* como hoje: revoga o servidor antigo */ }),
    // Antes: apagava só a sessão do servidor antigo. Agora: todas, menos a do novo.
    prisma.licencaSessao.deleteMany({ where: { licencaId, hwid: { not: hwidNovo } } }),
  )
}
```

### 6.3. Ocupar vaga numa operação só (F6)

```typescript
// licenca-sessao.repository.ts — conta e grava numa transação serializável (F6).
// Dois caixas entrando juntos não passam os dois pelo limite.
export async function ocuparVagaSeCouber(licencaId: string, hwid: string, limite: number, nome?: string) {
  return prisma.$transaction(async (tx) => {
    const jaTem = await tx.licencaSessao.findUnique({ where: { licencaId_hwid: { licencaId, hwid } } })
    const vivas = await tx.licencaSessao.count({
      where: { licencaId, ultimoHeartbeat: { gte: inicioDaJanela() } },
    })
    if (!jaTem && vivas >= limite) return false                 // sem vaga: nada gravado
    await tx.licencaSessao.upsert({ /* como upsertLicencaSessao */ })
    return true
  }, { isolationLevel: 'Serializable' })                        // o banco impede a corrida entre as duas
}
```

O `conectar` chama `ocuparVagaSeCouber`. Quando ela devolve `false`, segue o caminho de hoje: erro de limite, ou, no login autenticado, encerra a sessão mais antiga e tenta de novo.

## 7. Critérios de aceite

- **CA-01:** dois caixas ao mesmo tempo, com limite 1, só um entra.
- **CA-02:** uma sessão sem heartbeat há mais de 10 minutos não conta como vaga, mesmo antes do cron passar.
- **CA-03:** na troca de servidor, nenhuma sessão da loja antiga continua ocupando vaga.
- **CA-04:** um caixa com heartbeat em dia nunca perde a vaga.

Verificável com `npm test` no `apps/server`, sem Postgres (banco fake de `test/apoio/prisma-falso.ts`). O CA-01 depende do isolamento do banco real e também é conferido na verificação de integração (ROTEIRO, último passo).

## 8. Casos de teste

| ID | Arquivo | Caso | Esperado |
|----|---------|------|----------|
| CT-01 | `sessoes.test.ts` | Dois caixas simultâneos com limite 1 | Um entra, o outro recebe o erro de limite |
| CT-02 | `sessoes.test.ts` | Sessão sem heartbeat há 11 minutos | Fora da contagem |
| CT-03 | `sessoes.test.ts` | Sessão sem heartbeat há 9 minutos | Dentro da contagem |
| CT-04 | `sessoes.test.ts` | Cron com sessão de 11 minutos | Linha apagada; `totalUsuarios` atualizado |
| CT-05 | `sessoes.test.ts` | Troca de servidor com caixas da loja antiga | Todas as sessões apagadas, menos a do servidor novo |
| CT-06 | `sessoes.test.ts` | Reconexão do mesmo HWID com a licença no limite | Entra sem contar duas vezes |
| CT-07 | `sessoes.test.ts` | Caixa com heartbeat a cada 100 s por 30 minutos | Nunca perde a vaga |

## 9. Testes existentes que a mudança afeta

- `apps/server/test/licenca/licenca-troca-servidor.test.ts`: depende das sessões e da troca. Deve passar; a expectativa de tempo muda de 35 para 10 minutos, e a de sessões apagadas na troca passa a incluir os caixas.

## 10. Perguntas antes da aprovação

- Nenhuma. D-10 está fechada no ACORDO, e a regra de troca da §6.2 segue o F17.

## 11. Observações

- **Heartbeat do `start-big`:** o intervalo real é `INTERVALO_HEARTBEAT_SEGUNDOS = 100` (`backend-fastapi/app/core/tarefas.py:34`), e o comentário da linha diz "5 minutos". A correção do comentário é a tarefa do passo 2 do ROTEIRO, pré-requisito desta spec.
- **Lojas com versão antiga do app:** o heartbeat delas é o mesmo, então a mudança não as afeta.
