# Licença 05 — API: revogação, backup e contrato de recusa

| Campo        | Valor |
|--------------|-------|
| Status       | Concluída (2026-11-19) |
| Camada       | Backend da API (NestJS, Prisma) |
| Repositório  | Trabalho no fork `dzim-almeida/plataformaADM`; entrega por PR ao `aalan-big/plataformaADM` (D-01) |
| Dependências | — |
| Bloqueia     | LIC-06 e LIC-09 (usam a verificação do token deste guard) |
| Referência   | [acordo](../../../docs/licenca/ACORDO.md) decisões D-01, D-04, D-06, D-33; quadro F15, F27, F28, F29, F32 |

> **Revisão 1 (2026-11-18):** o repositório é o `plataformaADM`, não `dzim-almeida` (corrigido na época para `aalan-big`). O F23 saiu das referências. Os códigos novos no app ficam na LIC-08. As claims do token já existem.

> **Revisão 2 (2026-11-19):** conferência linha a linha no código da plataforma (fork no commit `981fa71`).
> - **Conflito 19 (D-01 revista):** trabalho no fork, entrega por PR. A spec deixou de estar "bloqueada por acesso".
> - **Conflito 21 (D-33):** licenças antigas têm `hwidServidor` vazio. A primeira chamada de backup grava o servidor, de forma condicional, em vez de recusar.
> - **Conflito 22 (D-06 revista):** o trial é tratado na regra única `motivoDeBloqueio`, que vale para o `/status`, o envio e o download. O start-big lê o `/status` antes de enviar e para em silêncio quando ele diz "não"; liberar o trial só no envio não funcionaria, e o download continuaria bloqueado. Código novo `TRIAL_BACKUP_USADO`.
> - **Documentação (D14 a D17, D20):** os exemplos usam o guard real (`jsonwebtoken` + `getPublicKey()`), o import `@startbig/database` e funções que existem (`findUltimoFullConfirmado`). Os tipos de backup são `full` e `fragmento`. Os testes rodam com `npm test` em `apps/server`.

> **Revisão 3 (2026-11-19, implementação):** fork `dzim-almeida/plataformaADM`, branch `fix/licenca-seguranca` (uma branch para as três specs da API, pedido do usuário), commit `b735773`.
> - **Vencimento no `conectar`:** a licença que o cron já marcou como `VENCIDA` (sem carência) também responde `402 LICENCA_VENCIDA`. Antes ela caía no `400 "Licença vencida. Acesso negado."` da checagem de status, antes da data (CT-14b).
> - **`hwidServidor` vazio:** `assumirServidorSeVazio` trata `null` e texto vazio como "sem servidor".
> - **Ordem no backup:** licença existe → servidor atual (`exigirServidorAtual`) → regra do plano. `carregarLicencaLiberada` passou a receber o hwid do token, o do pedido e a operação. O `urlUpload` do trial recusa `fragmento` com `BACKUP_TRIAL_LIMITE` antes de olhar o ciclo.
> - **Banco falso:** `prisma-falso.ts` ganhou a tabela `backup`, `licenca.updateMany` e o operador `lt`.
> - **Verificação:** CT-01 a CT-16 com `node --test` (pasta `test/licenca`, 44 testes). `tsc --noEmit` sem erro. CA-07 (start-big atual faz o full do trial sozinho) fica para a verificação de integração (passo 11 do roteiro), não verificado nesta sessão.

## 1. Objetivo

Fechar o acesso de uma máquina que já foi trocada. Hoje o token de uma máquina revogada ainda consegue baixar o backup da empresa inteira. Também dar ao trial o seu único backup (D-06) e padronizar como a API recusa a licença, para o app saber o que fazer sem ler texto.

## 2. Escopo

**Dentro do escopo**
- O `ErpLicencaGuard` consulta a revogação da máquina antes de aceitar o token (D-04, F32).
- `/erp/backup/status`, `url-upload` e `url-download` recusam máquina que não é o servidor atual da licença (F15).
- Licença com `hwidServidor` vazio: a primeira chamada de backup grava o servidor (D-33).
- Token sem `hwid` não é aceito no backup (F29).
- Trial: um backup completo; o `/status` diz "não" depois dele; o download sempre segue as regras das licenças pagas (D-06).
- Vencimento em `/licenca/conectar` com código estável e status `402` (F27, lado da API).
- Testes que travam o formato da recusa de `/licenca/conectar` e de `/licenca/validar` (F28).

**Fora do escopo**
- Lista de tokens por `jti` (ACORDO D-04, alternativa C).
- Redução da validade do token para 24 h (ACORDO D-04, alternativa B).
- Reenvio de link: LIC-06. Heartbeat autenticado: LIC-09 (usa o helper de token criado aqui).

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `apps/server/src/core/guards/erp-licenca.guard.ts` | alterar | Extrai o helper `lerTokenDaLicenca(request)` (assinatura e validade). `canActivate` vira `async` e consulta `hwidEstaRevogado`. Máquina revogada → `401 LICENCA_HWID_REVOGADO`. |
| `apps/server/src/features/erp/erp-backup.service.ts` | alterar | `motivoDeBloqueio` passa a receber a operação (`envio` ou `download`) e se o trial já tem full. Novo `exigirServidorAtual`. `status`, `urlUpload` e `urlDownload` chamam os dois. |
| `apps/server/src/features/erp/erp-backup.controller.ts` | alterar | `status` passa a receber `req.erp.hwid`. Sem rota nova. |
| `packages/database/src/repositories/licenca-servidor.repository.ts` | alterar | Nova `assumirServidorSeVazio(licencaId, hwid)`: grava só se o campo ainda estiver vazio. |
| `apps/server/src/features/dispositivos/dispositivo.service.ts` | alterar | `conectar` troca `BadRequestException('Licença vencida.')` por `HttpException` com `codigo: 'LICENCA_VENCIDA'` e status 402. O serviço atende `/licenca/conectar` (usado pelo app) e `/erp/conectar`. |
| `apps/server/test/apoio/prisma-falso.ts` | alterar | Acrescenta o que faltar para os casos novos (por exemplo, `licenca.updateMany` com condição). |
| `apps/server/test/licenca/revogacao-backup.test.ts` | criar | Casos CT-01 a CT-08. |
| `apps/server/test/licenca/backup-trial.test.ts` | criar | Casos CT-09 a CT-13. |
| `apps/server/test/licenca/contrato-recusa.test.ts` | criar | Casos CT-14 a CT-16. |

Arquivos novos seguem o padrão do repositório: comentários em PT-BR e o cabeçalho `NOME DO ARQUIVO / MÓDULO / O QUE ESTE ARQUIVO FAZ` (exemplo: `core/filters/http-exception.filter.ts`).

Teste existente que precisa continuar passando: `apps/server/test/licenca/licenca-troca-servidor.test.ts`.

## 4. Contrato da API

O `HttpExceptionFilter` (`core/filters/http-exception.filter.ts`) responde `{ statusCode, path, message, codigo? }`. Os exemplos abaixo mostram só `statusCode`, `message` e `codigo`.

### 4.1. Recusa de token de máquina revogada (todas as rotas com `ErpLicencaGuard`)

```json
{ "statusCode": 401, "message": "Esta máquina não é mais o servidor desta licença.", "codigo": "LICENCA_HWID_REVOGADO" }
```

### 4.2. Backup: máquina que não é o servidor atual (`status`, `url-upload` e `url-download`)

```json
{ "statusCode": 403, "message": "Esta máquina não é mais o servidor desta licença. O backup só é aceito do servidor atual.", "codigo": "BACKUP_MAQUINA_REVOGADA" }
```

### 4.3. Backup: token sem `hwid`

```json
{ "statusCode": 403, "message": "O token não tem a identificação da máquina.", "codigo": "BACKUP_HWID_AUSENTE" }
```

### 4.4. Backup do trial (D-06)

| Situação do trial | `GET /erp/backup/status` | `url-upload` | `url-download` |
|---|---|---|---|
| Ainda não tem full confirmado | `planoPermiteBackup: true` | Aceita **só** `full` | Mesmas regras das licenças pagas |
| Já tem full confirmado | `planoPermiteBackup: false`, `codigoBloqueio: "TRIAL_BACKUP_USADO"` | `403 BACKUP_TRIAL_LIMITE` | Mesmas regras das licenças pagas |

"Mesmas regras das licenças pagas" quer dizer: liberado enquanto a licença estiver ativa e dentro do prazo; bloqueado se vencida, suspensa, bloqueada ou revogada (como hoje). O código antigo `TRIAL` deixa de existir.

```json
{ "statusCode": 403, "message": "O período de teste permite um backup completo. Assine para ter backups contínuos.", "codigo": "BACKUP_TRIAL_LIMITE" }
```

### 4.5. Vencimento em `/licenca/conectar`

Hoje a resposta é `400` com texto "Licença vencida.". Passa a ser:

```json
{ "statusCode": 402, "message": "Sua licença está vencida. Renove a assinatura para ativar o sistema neste computador.", "codigo": "LICENCA_VENCIDA" }
```

O app já trata `402` como vencimento (`backend-fastapi/app/services/licenca/recusa.py`, `_recusa_por_vencimento`, linha 172). Por isso a mudança não quebra as versões instaladas (ADR-004).

## 5. Schemas

Nenhum schema de entrada muda. Nenhum campo novo no banco: o `hwidServidor` já existe (`prisma/schema.prisma:302`).

## 6. Especificação técnica

### 6.1. Guard consulta a revogação (D-04, F32)

```typescript
// erp-licenca.guard.ts — recusa token de máquina que já foi trocada (D-04)
import { hwidEstaRevogado } from '@startbig/database'
import jwt from 'jsonwebtoken'

/** Confere assinatura e validade do token. Usado por este guard e pelo do heartbeat (LIC-09). */
export function lerTokenDaLicenca(request: any, publicKey: string): any | null {
  const authHeader: string | undefined = request.headers.authorization
  if (!authHeader?.startsWith('Bearer ')) return null          // sem token
  try {
    return jwt.verify(authHeader.slice(7), publicKey, { algorithms: ['RS256'] })
  } catch {
    throw new UnauthorizedException('Token de licença inválido ou expirado.')
  }
}

@Injectable()
export class ErpLicencaGuard implements CanActivate {
  constructor(private readonly dispositivoService: DispositivoService) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest()
    const payload = lerTokenDaLicenca(request, this.dispositivoService.getPublicKey())
    if (!payload) throw new UnauthorizedException('Token de licença não fornecido.')
    // Se o token traz uma máquina e ela foi revogada, a recusa é imediata.
    if (payload.hwid && await hwidEstaRevogado(payload.licencaId, payload.hwid))
      throw new UnauthorizedException({
        codigo:  'LICENCA_HWID_REVOGADO',
        message: 'Esta máquina não é mais o servidor desta licença.',
      })
    request.erp = payload
    return true
  }
}
```

A regra é só "não está revogada". Ela não exige ser o servidor atual em todas as rotas: o login sem `hwid` gera um token com identificador próprio (`login-<uuid>`). A regra do servidor atual vale só para o backup (§6.2).

### 6.2. Backup só do servidor atual (F15, F29, D-33)

```typescript
// erp-backup.service.ts — o backup só entra e sai pelo servidor atual (F15, F29)
private async exigirServidorAtual(licenca: { id: string; hwidServidor: string | null },
                                  hwidToken: string | null, hwidPedido?: string) {
  if (!hwidToken)
    throw this.erro(HttpStatus.FORBIDDEN, 'BACKUP_HWID_AUSENTE',
                    'O token não tem a identificação da máquina.')            // F29
  if (hwidPedido !== undefined && hwidPedido !== hwidToken)
    throw this.erro(HttpStatus.FORBIDDEN, 'BACKUP_HWID_DIVERGENTE',
                    'HWID informado não corresponde ao da sessão autenticada.')  // já existe hoje

  // Licença antiga, sem servidor registrado: quem chama a rota de backup É o servidor
  // (os caixas não fazem backup), com identidade assinada pela API. Grava só se ainda
  // estiver vazio; se duas chamadas chegarem juntas, a primeira vence (D-33).
  let servidor = licenca.hwidServidor
  if (!servidor) servidor = await assumirServidorSeVazio(licenca.id, hwidToken)

  if (servidor !== hwidToken)
    throw this.erro(HttpStatus.FORBIDDEN, 'BACKUP_MAQUINA_REVOGADA',
                    'Esta máquina não é mais o servidor desta licença. O backup só é aceito do servidor atual.')
}
```

```typescript
// licenca-servidor.repository.ts — grava o servidor só se o campo ainda estiver vazio (D-33)
export async function assumirServidorSeVazio(licencaId: string, hwid: string): Promise<string | null> {
  // updateMany com condição: o banco garante que só a primeira gravação acontece.
  await prisma.licenca.updateMany({ where: { id: licencaId, hwidServidor: null }, data: { hwidServidor: hwid } })
  const licenca = await prisma.licenca.findUnique({ where: { id: licencaId }, select: { hwidServidor: true } })
  return licenca?.hwidServidor ?? null                      // devolve quem ficou gravado
}
```

`status`, `urlUpload` e `urlDownload` chamam `exigirServidorAtual` logo depois de carregar a licença. Hoje a checagem de `hwid` é condicional (`if (hwidToken && ...)`), e a mudança a torna obrigatória.

### 6.3. Trial com um backup completo (D-06)

A regra única passa a receber o contexto:

```typescript
// erp-backup.service.ts — uma regra para status, envio e download (D-06)
private motivoDeBloqueio(
  licenca: { status: string; isTrial: boolean; dataVencimento: Date | null },
  contexto: { operacao: 'envio' | 'download'; trialJaTemFull: boolean },
): { codigo: string; mensagem: string } | null {
  // Trial: um full, e nada mais. O download não tem regra de trial.
  if (licenca.isTrial && contexto.operacao === 'envio' && contexto.trialJaTemFull)
    return { codigo: 'TRIAL_BACKUP_USADO',
             mensagem: 'O período de teste permite um backup completo. Assine para ter backups contínuos.' }

  // Daqui para baixo, igual a hoje, para trial e pago.
  if (licenca.status !== 'ATIVA')
    return { codigo: `LICENCA_${licenca.status}`, mensagem: `Licença ${licenca.status.toLowerCase()} — backup em nuvem indisponível.` }
  if (licenca.dataVencimento && licenca.dataVencimento < new Date())
    return { codigo: 'LICENCA_VENCIDA', mensagem: 'Licença vencida — backup em nuvem indisponível até a renovação.' }
  return null
}
```

- `trialJaTemFull` = `licenca.isTrial && !!(await findUltimoFullConfirmado(licencaId))`. Para licença paga, a consulta não roda.
- O `status` usa `operacao: 'envio'` para preencher `planoPermiteBackup` e `codigoBloqueio`. O start-big (`backend-fastapi/app/services/cloud/flow.py:26-27`) já para em silêncio quando `planoPermiteBackup` é `false`, e envia `full` quando `fullDoCicloConfirmado` é `false`. Por isso o trial ganha o seu backup até nas versões instaladas.
- O `urlUpload` usa `operacao: 'envio'` e, além disso, recusa `fragmento` no trial sem full (`BACKUP_TRIAL_LIMITE`), como segunda barreira.
- O `urlDownload` usa `operacao: 'download'`.

### 6.4. Vencimento com código (F27)

```typescript
// dispositivo.service.ts — vencimento sai com código e status 402 (F27)
if (licenca.dataVencimento && licenca.dataVencimento < new Date() && !emCarencia) {
  await updateLicenca(licenca.id, { status: 'VENCIDA' })        // como hoje
  throw new HttpException(
    { codigo: 'LICENCA_VENCIDA',
      message: 'Sua licença está vencida. Renove a assinatura para ativar o sistema neste computador.' },
    HttpStatus.PAYMENT_REQUIRED,                                  // 402: o app já trata como vencimento
  )
}
```

### 6.5. Contrato travado por teste (F28)

Hoje `/licenca/validar` responde `201` com `valida: false` em recusa, e `/licenca/conectar` responde `4xx`. O app depende do `201`. Os testes travam o formato dos dois endpoints, para qualquer mudança de status quebrar o teste e não o app em produção.

## 7. Critérios de aceite

- **CA-01:** token de máquina revogada recebe `401 LICENCA_HWID_REVOGADO` em qualquer rota do guard.
- **CA-02:** máquina que não é o servidor atual recebe `BACKUP_MAQUINA_REVOGADA` no `/status`, no envio e no download.
- **CA-03:** token sem `hwid` recebe `BACKUP_HWID_AUSENTE`.
- **CA-04:** licença antiga com `hwidServidor` vazio continua fazendo backup, e passa a ter servidor registrado.
- **CA-05:** trial envia um full; depois o `/status` responde `TRIAL_BACKUP_USADO`; o download do trial funciona.
- **CA-06:** vencimento em `/licenca/conectar` responde `402` com `codigo: LICENCA_VENCIDA`.
- **CA-07:** o start-big atual, sem mudança, faz o full do trial sozinho e para depois dele.

Verificável com `npm test` em `apps/server` (`node --test` com `tsx`, banco falso de `test/apoio/prisma-falso.ts`). O CA-07 é conferido na verificação de integração.

## 8. Casos de teste

| ID | Arquivo | Caso | Esperado |
|----|---------|------|----------|
| CT-01 | `revogacao-backup.test.ts` | Token com `hwid` revogado | `401 LICENCA_HWID_REVOGADO` |
| CT-02 | `revogacao-backup.test.ts` | Token com `hwid` não revogado | Passa |
| CT-03 | `revogacao-backup.test.ts` | Envio de máquina que não é `hwidServidor` | `BACKUP_MAQUINA_REVOGADA` |
| CT-04 | `revogacao-backup.test.ts` | Download de máquina que não é `hwidServidor` | `BACKUP_MAQUINA_REVOGADA` |
| CT-05 | `revogacao-backup.test.ts` | `/status` de máquina que não é `hwidServidor` | `BACKUP_MAQUINA_REVOGADA` |
| CT-06 | `revogacao-backup.test.ts` | Envio sem `hwid` no token | `BACKUP_HWID_AUSENTE` |
| CT-07 | `revogacao-backup.test.ts` | `hwidServidor` vazio: primeira chamada, depois chamada de outra máquina | A primeira grava o servidor e passa; a outra recebe `BACKUP_MAQUINA_REVOGADA` |
| CT-08 | `revogacao-backup.test.ts` | Duas chamadas simultâneas com `hwidServidor` vazio | Só uma grava; a outra é tratada pela regra normal |
| CT-09 | `backup-trial.test.ts` | Trial sem full: `/status` e envio de `full` | `planoPermiteBackup: true`; envio aceito |
| CT-10 | `backup-trial.test.ts` | Trial com full: `/status` | `planoPermiteBackup: false`, `codigoBloqueio: TRIAL_BACKUP_USADO` |
| CT-11 | `backup-trial.test.ts` | Trial com full: envio | `403 BACKUP_TRIAL_LIMITE` |
| CT-12 | `backup-trial.test.ts` | Trial com full: download | Liberado |
| CT-13 | `backup-trial.test.ts` | Licença paga ativa | `/status`, envio e download como hoje |
| CT-14 | `contrato-recusa.test.ts` | `/licenca/conectar` com licença vencida | `402`, `codigo: LICENCA_VENCIDA` |
| CT-15 | `contrato-recusa.test.ts` | `/licenca/validar` com recusa | `201`, `valida: false`, com os campos esperados |
| CT-16 | `contrato-recusa.test.ts` | `/licenca/conectar` de máquina transferida | `400`, `codigo: LICENCA_TRANSFERIDA` (já existe hoje) |

## 9. Testes existentes que a mudança afeta

- `apps/server/test/licenca/licenca-troca-servidor.test.ts`: cobre a troca de servidor e a revogação. Deve passar. Se algum teste esperava `400` no vencimento, a expectativa passa a ser `402`, com o motivo registrado no teste.
- Testes que chamam o guard diretamente (se houver): `canActivate` passa a ser `async` e precisa de `await`.

## 10. Perguntas antes da aprovação

- Nenhuma. D-04, D-06 (revista) e D-33 estão fechadas no ACORDO.

## 11. Observações

- **Entrega:** branch no fork `dzim-almeida/plataformaADM`, PR para o `aalan-big/plataformaADM`. Esta spec não muda o banco (sem `db push`).
- O guard passa a fazer uma consulta ao banco por requisição autenticada. Medir o efeito no primeiro uso.
- O `start-big` não muda nesta spec. O app mostra os códigos novos pela LIC-08 e trata o vencimento pela SPEC-02, as duas com rede de segurança para a API antiga.
