# Licença 09 — API: vagas de computador (sessões e heartbeat)

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend da API (NestJS, Prisma) |
| Repositório  | Trabalho no fork `dzim-almeida/plataformaADM`; entrega por PR ao `aalan-big/plataformaADM` (D-01) |
| Dependências | SPEC-05 (helper `lerTokenDaLicenca` e a consulta de revogação). Tarefa do comentário do heartbeat no `start-big` (ROTEIRO). Integração com a SPEC-02 (o app passa a mandar o token no heartbeat) |
| Bloqueia     | — |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-01, D-10, D-37, D-38; [ADR-004](../../docs/licenca/adr/ADR-004-compatibilidade-api-app-instalado.md); risco R-02; quadro F6, F17, F21 |

> **Origem (2026-11-18):** dividida da antiga SPEC-06 na revisão de conflitos (conflito 15). O F5 não veio junto (R-02).

> **Revisão 2 (2026-11-19):** conferência linha a linha no código da plataforma (fork no commit `981fa71`).
> - **Conflito 19 (D-01 revista):** trabalho no fork, entrega por PR.
> - **Conflito 27 (D-37):** o heartbeat só pedia o `licencaId`. Quem o soubesse ocupava as vagas da loja com HWIDs inventados. Ele passa a ser autenticado pelo token da licença, com transição: sem token, só renova sessão existente e nunca cria; a resposta é `404`, nunca `400` (o app instalado bloqueia a licença quando todos os caixas recebem `400`).
> - **Conflito 28 (D-38):** a contagem sem corrida usa a licença trancada (`SELECT ... FOR UPDATE`) em vez de uma transação serializável, que falharia com erro 500 em vez de "limite atingido". O banco falso ganha o que falta, e a corrida real é testada por script contra um PostgreSQL de desenvolvimento.
> - **Documentação (D16 a D18, D20):** rotas em dobro (`/licenca/heartbeat` e `/erp/heartbeat`); como os testes rodam; padrão de arquivos.

## 1. Objetivo

As vagas de computador da licença não podem ficar presas por sessões mortas, nem ser ocupadas por quem não é da loja, e dois caixas entrando juntos não podem passar do limite.

### 1.1. Como funciona hoje (conferido no código)

- Cada computador ocupa uma linha em `LicencaSessao` (`packages/database/src/repositories/licenca-sessao.repository.ts`).
- O `start-big` manda heartbeat de cada caixa a cada **100 segundos** (`backend-fastapi/app/core/tarefas.py:34`; o comentário diz "5 minutos" e está errado).
- O heartbeat (`/licenca/heartbeat`, usado pelo app, e a gêmea `/erp/heartbeat`) só pede `licencaId` e `hwid` (`packages/schemas/src/licenca/licenca.schema.ts:43-47`). Sem sessão, ele **cria** uma, se couber (`dispositivo.service.ts:865-878`).
- O app instalado, ao receber `400` no heartbeat, remove o caixa da tabela; se **todos** recebem `400`, **marca a licença como bloqueada** (`backend-fastapi/app/services/licenca/sincronizacao.py:57-67`).
- A sessão morta só é apagada por um cron a cada 10 minutos, com 35 minutos sem heartbeat (`apps/server/src/features/cron/cron.service.ts:94-98`). A constante `HEARTBEAT_TIMEOUT_MS` (`dispositivo.service.ts:104`) não decide nada.
- `countSessoesAtivas` conta **todas** as linhas da licença, vivas ou mortas.
- Na troca de servidor, `assumirServidorDaLicenca` apaga só a sessão do servidor antigo.
- No `conectar`, a contagem e a gravação são dois passos separados (`dispositivo.service.ts:785-830`).

## 2. Escopo

**Dentro do escopo**
- Sessão sem heartbeat há mais de **10 minutos** deixa de contar como vaga, na hora (D-10, F21), e o cron passa a usar o mesmo prazo.
- Na troca de servidor, as sessões dos caixas da loja antiga também são apagadas (F17).
- Ocupar vaga com a licença trancada, sem corrida (F6, D-38).
- Heartbeat autenticado pelo token, com transição (D-37).

**Fora do escopo**
- `tokenSessao` no desconectar (F5): risco aceito R-02.
- Recusar o heartbeat sem token: fica para quando as lojas tiverem atualizado (ACORDO §7, ADR-004).
- Tela para o dono liberar vagas (ACORDO D-10, alternativa B).
- Mandar o token no heartbeat, do lado do app: SPEC-02.

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `packages/database/src/repositories/licenca-sessao.repository.ts` | alterar | Constante `MINUTOS_SESSAO_VIVA = 10`. `countSessoesAtivas` conta só sessões vivas. Nova `ocuparVagaSeCouber` (§6.3). |
| `apps/server/src/features/cron/cron.service.ts` | alterar | `deletarSessoesInativas(MINUTOS_SESSAO_VIVA)` no lugar de `35`. |
| `apps/server/src/features/dispositivos/dispositivo.service.ts` | alterar | `conectar` usa `ocuparVagaSeCouber`. `heartbeat` aplica a tabela da §6.4. Sai a constante `HEARTBEAT_TIMEOUT_MS`. |
| `packages/database/src/repositories/licenca-servidor.repository.ts` | alterar | `assumirServidorDaLicenca` apaga, na troca, todas as sessões da licença menos a do servidor novo. |
| `apps/server/src/core/guards/erp-licenca.guard.ts` | alterar | Novo `ErpLicencaGuardOpcional`: confere o token quando ele vem (com `lerTokenDaLicenca`, da SPEC-05, e a revogação) e deixa passar sem token, marcando `request.erp = null`. |
| `apps/server/src/features/dispositivos/dispositivo.controller.ts` | alterar | `POST /licenca/heartbeat` (usado pelo app) com `@UseGuards(ErpLicencaGuardOpcional)`, mantendo o `@Public()` da rota. |
| `apps/server/src/features/erp/erp-licenca.controller.ts` | alterar | A gêmea `POST /erp/heartbeat`, com o mesmo guard. |
| `apps/server/test/apoio/prisma-falso.ts` | alterar | `$transaction` aceita também uma função (recebe o próprio banco falso), `$queryRaw` que não faz nada, e o operador `lt`. |
| `scripts/testar-corrida-vagas.ts` | criar | Dispara conexões simultâneas contra um PostgreSQL de desenvolvimento e confere que só cabem `limite` sessões (mesmo padrão dos `scripts/testar-*.ts`). |
| `apps/server/test/licenca/sessoes.test.ts` | criar | Casos CT-01 a CT-06. |
| `apps/server/test/licenca/heartbeat-autenticado.test.ts` | criar | Casos CT-07 a CT-12. |

Os testes rodam com `npm test` em `apps/server`. Arquivos novos seguem o padrão do repositório (comentários em PT-BR e cabeçalho `NOME DO ARQUIVO / MÓDULO / O QUE ESTE ARQUIVO FAZ`).

Teste existente que precisa continuar passando: `apps/server/test/licenca/licenca-troca-servidor.test.ts`. A expectativa de tempo muda de 35 para 10 minutos, e a de sessões apagadas na troca passa a incluir os caixas.

## 4. Contrato da API

### 4.1. Heartbeat (`POST /licenca/heartbeat` e `POST /erp/heartbeat`)

O corpo não muda (`licencaId`, `hwid`, `totalUsuarios`). Passa a aceitar o cabeçalho `Authorization: Bearer <token da licença>`.

| Pedido | Sessão existe | Sessão não existe |
|---|---|---|
| Com token válido, do mesmo `licencaId` | Renova | Cria, se couber (como hoje) |
| Com token de máquina revogada | `401 LICENCA_HWID_REVOGADO` | `401 LICENCA_HWID_REVOGADO` |
| Com token de outra licença | `403 HEARTBEAT_LICENCA_DIVERGENTE` | `403 HEARTBEAT_LICENCA_DIVERGENTE` |
| Sem token (versões instaladas) | Renova | **Não cria**: `404 SESSAO_INEXISTENTE` |

**Nenhuma recusa nova é `400`.** O app instalado trata `400` como "caixa bloqueado" e, se todos os caixas receberem `400`, bloqueia a licença da loja. As recusas que já existem com `400` (`LICENCA_TRANSFERIDA`, `LIMITE_DISPOSITIVOS`, licença inativa) continuam como estão.

### 4.2. Conectar

Sem mudança de contrato. Os erros de limite continuam os de hoje.

## 5. Schemas

Nenhum campo novo no banco (sem `db push`). A contagem usa o `ultimoHeartbeat`, que já existe e tem índice em `LicencaSessao`.

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
    // Só conta quem deu sinal de vida dentro da janela: uma sessão morta deixa de
    // ocupar vaga na hora, sem esperar o cron passar.
    where: { licencaId, ultimoHeartbeat: { gte: inicioDaJanela() } },
  })
}
```

O cron continua rodando a cada 10 minutos, com `deletarSessoesInativas(MINUTOS_SESSAO_VIVA)`. Ele só limpa as linhas: quem decide a vaga é a contagem acima.

### 6.2. Troca de servidor apaga as sessões da loja antiga (F17)

A API não sabe quais caixas pertencem a qual servidor: as sessões guardam só o HWID. Na troca, **todas as sessões da licença são apagadas, menos a do servidor novo**. Os caixas da loja nova entram de novo pelo login deles, que já acontece depois da troca (a SPEC-03 avisa: "os caixas precisarão apontar para este computador").

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

### 6.3. Ocupar vaga com a licença trancada (F6, D-38)

```typescript
// licenca-sessao.repository.ts — tranca a licença enquanto conta e grava a vaga (F6).
// O segundo caixa ESPERA o primeiro terminar (milissegundos) e recebe "limite atingido":
// não há erro 500 nem nova tentativa, como haveria numa transação serializável.
export async function ocuparVagaSeCouber(licencaId: string, hwid: string, limite: number, nome?: string) {
  return prisma.$transaction(async (tx) => {
    await tx.$queryRaw`SELECT id FROM licencas WHERE id = ${licencaId} FOR UPDATE`   // fila por licença
    const jaTem = await tx.licencaSessao.findUnique({ where: { licencaId_hwid: { licencaId, hwid } } })
    const vivas = await tx.licencaSessao.count({
      where: { licencaId, ultimoHeartbeat: { gte: inicioDaJanela() } },
    })
    if (!jaTem && vivas >= limite) return false                                       // sem vaga: nada gravado
    await tx.licencaSessao.upsert({ /* como upsertLicencaSessao */ })
    return true
  })
}
```

O `conectar` chama `ocuparVagaSeCouber`. Quando ela devolve `false`, segue o caminho de hoje: erro de limite, ou, no login autenticado, encerra a sessão mais antiga e tenta de novo. O heartbeat com token, quando precisa criar a sessão, usa a mesma função.

### 6.4. Heartbeat autenticado, com transição (D-37)

```typescript
// dispositivo.service.ts — o heartbeat confia no token; sem token, nunca cria vaga (D-37)
async heartbeat(body: unknown, erp: { licencaId: string; hwid: string } | null) {
  const dados = this.parseBody(heartbeatSchema, body)
  if (erp && erp.licencaId !== dados.licencaId)
    throw this.erro(HttpStatus.FORBIDDEN, 'HEARTBEAT_LICENCA_DIVERGENTE', 'O token não é desta licença.')

  // ... checagens de hoje (licença existe, status, carência, HWID revogado → 400 LICENCA_TRANSFERIDA) ...

  const sessao = await findLicencaSessao(dados.licencaId, dados.hwid)
  if (!sessao) {
    // Sem token (versão instalada): não cria. 404, e NUNCA 400: o app antigo bloqueia
    // a licença da loja quando todos os caixas recebem 400.
    if (!erp)
      throw this.erro(HttpStatus.NOT_FOUND, 'SESSAO_INEXISTENTE', 'Sessão não encontrada. Conecte o caixa de novo.')
    if (!(await ocuparVagaSeCouber(dados.licencaId, dados.hwid, this.limiteDe(licenca))))
      throw this.erro(HttpStatus.BAD_REQUEST, 'LIMITE_DISPOSITIVOS', '...')          // igual a hoje
    return { ok: true }
  }
  await upsertLicencaSessao(dados.licencaId, dados.hwid)                               // renova
  return { ok: true }
}
```

O app instalado recebe o `404` e só registra no log: o caixa continua funcionando, e a sessão volta no próximo login dele. O app novo (SPEC-02) reconecta o caixa na hora.

## 7. Critérios de aceite

- **CA-01:** dois caixas ao mesmo tempo, com limite 1, só um entra, e o outro recebe "limite atingido" (não erro 500).
- **CA-02:** uma sessão sem heartbeat há mais de 10 minutos não conta como vaga, mesmo antes do cron passar.
- **CA-03:** na troca de servidor, nenhuma sessão da loja antiga continua ocupando vaga.
- **CA-04:** um caixa com heartbeat em dia nunca perde a vaga.
- **CA-05:** heartbeat sem token nunca cria sessão, e a resposta é `404 SESSAO_INEXISTENTE`.
- **CA-06:** heartbeat com token de máquina revogada recebe `401`; com token de outra licença, `403`.
- **CA-07:** uma loja com a versão instalada do app continua funcionando depois do deploy (nenhuma licença bloqueada por `400` novo).

Os casos CT rodam com `npm test` em `apps/server`. O CA-01 é conferido pelo `scripts/testar-corrida-vagas.ts` contra um PostgreSQL de desenvolvimento, e de novo na verificação de integração. O CA-07 também é conferido na verificação de integração.

## 8. Casos de teste

| ID | Arquivo | Caso | Esperado |
|----|---------|------|----------|
| CT-01 | `sessoes.test.ts` | `ocuparVagaSeCouber` com limite 1, chamada duas vezes com HWIDs diferentes | A primeira grava; a segunda devolve `false` |
| CT-02 | `sessoes.test.ts` | Sessão sem heartbeat há 11 minutos | Fora da contagem |
| CT-03 | `sessoes.test.ts` | Sessão sem heartbeat há 9 minutos | Dentro da contagem |
| CT-04 | `sessoes.test.ts` | Cron com sessão de 11 minutos | Linha apagada; `totalUsuarios` atualizado |
| CT-05 | `sessoes.test.ts` | Troca de servidor com caixas da loja antiga | Todas as sessões apagadas, menos a do servidor novo |
| CT-06 | `sessoes.test.ts` | Reconexão do mesmo HWID com a licença no limite | Entra sem contar duas vezes |
| CT-07 | `heartbeat-autenticado.test.ts` | Com token, sessão inexistente, com vaga | Sessão criada |
| CT-08 | `heartbeat-autenticado.test.ts` | Sem token, sessão inexistente | `404 SESSAO_INEXISTENTE`; nada criado |
| CT-09 | `heartbeat-autenticado.test.ts` | Sem token, sessão existente | Renovada |
| CT-10 | `heartbeat-autenticado.test.ts` | Token de máquina revogada | `401 LICENCA_HWID_REVOGADO` |
| CT-11 | `heartbeat-autenticado.test.ts` | Token de outra licença | `403 HEARTBEAT_LICENCA_DIVERGENTE` |
| CT-12 | `heartbeat-autenticado.test.ts` | Nenhuma recusa nova do heartbeat usa `400` | Verdadeiro (lista as recusas e confere os status) |

## 9. Testes existentes que a mudança afeta

- `apps/server/test/licenca/licenca-troca-servidor.test.ts`: depende das sessões e da troca. Deve passar com as expectativas de 10 minutos e das sessões dos caixas apagadas na troca.

## 10. Perguntas antes da aprovação

- Nenhuma. D-10, D-37 e D-38 estão fechadas no ACORDO.

## 11. Observações

- **Entrega:** branch no fork `dzim-almeida/plataformaADM`, PR para o `aalan-big/plataformaADM`. Esta spec não muda o banco (sem `db push`).
- **Heartbeat do `start-big`:** o comentário de `tarefas.py:34` diz "5 minutos" e o valor é 100 s. A correção é a tarefa do ROTEIRO, pré-requisito desta spec.
- **Transição:** quando as lojas tiverem atualizado (o app novo manda o token, SPEC-02), o heartbeat sem token passa a ser recusado com `401`. Isso fica para uma spec futura, seguindo a ADR-004.
