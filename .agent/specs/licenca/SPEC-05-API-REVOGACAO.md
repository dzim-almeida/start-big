# Licença 05 — API: revogação, backup e contrato de recusa

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend da API (NestJS, Prisma), repositório `plataformaADM` |
| Repositório  | `dzim-almeida/plataformaADM` (outro repositório: fora do harness do `start-big`) |
| Dependências | Acesso de escrita ao repositório `plataformaADM` (ACORDO D-01). A SPEC-02 não depende desta spec para funcionar. |
| Bloqueia     | — |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-01, D-04, D-06; quadro F15, F23, F27, F28, F29, F32 |

> **Pré-requisito:** a implementação só começa com acesso de escrita ao `plataformaADM` e uma branch nova no próprio repositório. Esta spec fica no `start-big` para o planejamento ficar em um lugar só (D-01).

## 1. Objetivo

Fechar o acesso de uma máquina que já foi trocada. Hoje o token de uma máquina revogada ainda consegue baixar backup da empresa inteira. Também padronizar como a API recusa a licença, para o app saber o que fazer sem ler texto.

## 2. Escopo

**Dentro do escopo**
- O guard `ErpLicencaGuard` consulta a revogação da máquina antes de aceitar o token (D-04, F32).
- Upload e download de backup recusam máquina revogada e máquina que não é o servidor atual (F15).
- Token sem `hwid` não é aceito para backup (F29).
- Trial recebe um backup completo, sem incrementais (D-06).
- Recusa de vencimento em `/licenca/conectar` passa a ter `codigo` estável (F27, lado da API).
- Teste automatizado que trava o formato da recusa de `/licenca/conectar` e de `/licenca/validar` (F28).

**Fora do escopo**
- Lista de tokens por `jti` (ACORDO D-04, alternativa C).
- Redução da validade do token para 24 h (ACORDO D-04, alternativa B).
- Reenvio do link de primeiro acesso. Está na SPEC-06, junto dos outros itens de cadastro.

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `apps/server/src/core/guards/erp-licenca.guard.ts` | alterar | `canActivate` passa a ser `async` e consulta `hwidEstaRevogado(licencaId, hwid)`. Máquina revogada recebe `401 LICENCA_HWID_REVOGADO`. |
| `apps/server/src/features/erp/erp-backup.service.ts` | alterar | `urlUpload` e `urlDownload` recusam quando o HWID não é o servidor atual. Trial aceita um backup completo. |
| `apps/server/src/features/erp/erp-backup.controller.ts` | alterar | Sem mudança de rota. |
| `apps/server/src/features/dispositivos/dispositivo.service.ts` | alterar | `conectar` troca `BadRequestException('Licença vencida.')` por `HttpException` com `codigo: 'LICENCA_VENCIDA'` e status 402. |
| `apps/server/src/features/erp/erp-licenca.controller.ts` | alterar | Sem mudança de rota. |
| `packages/database/src/repositories/licenca-servidor.repository.ts` | usar | `hwidEstaRevogado`, sem mudança. |
| `apps/server/test/licenca/revogacao-backup.test.ts` | criar | Casos CT-01 a CT-06. |
| `apps/server/test/licenca/contrato-recusa.test.ts` | criar | Casos CT-07 a CT-10. |

Testes existentes que precisam continuar passando: `apps/server/test/licenca/licenca-troca-servidor.test.ts`, que cobre a troca de servidor e o comportamento dos caixas.

## 4. Contrato da API

### 4.1. Recusa de token de máquina revogada (todas as rotas com `ErpLicencaGuard`)

```json
{
  "statusCode": 401,
  "message": "Esta máquina não é mais o servidor desta licença.",
  "codigo": "LICENCA_HWID_REVOGADO"
}
```

### 4.2. Backup: recusa de máquina que não é o servidor (`url-upload` e `url-download`)

```json
{
  "statusCode": 403,
  "message": "Esta máquina não é mais o servidor desta licença. O backup só é aceito do servidor atual.",
  "codigo": "BACKUP_MAQUINA_REVOGADA"
}
```

### 4.3. Backup: token sem `hwid`

```json
{
  "statusCode": 403,
  "message": "O token não tem a identificação da máquina.",
  "codigo": "BACKUP_HWID_AUSENTE"
}
```

### 4.4. Backup de trial: segundo envio completo

```json
{
  "statusCode": 403,
  "message": "O período de teste permite um backup completo. Assine para ter backups completos e incrementais.",
  "codigo": "BACKUP_TRIAL_LIMITE"
}
```

### 4.5. Vencimento em `/licenca/conectar`

Hoje a resposta é `400` com texto "Licença vencida.". Passa a ser:

```json
{
  "statusCode": 402,
  "message": "Sua licença está vencida. Renove a assinatura para ativar o sistema neste computador.",
  "codigo": "LICENCA_VENCIDA"
}
```

O app já trata `402` como vencimento (`recusa.ts`, `_recusa_por_vencimento`). Por isso a mudança de status não quebra o cliente atual.

## 5. Schemas

Nenhum schema de entrada muda. A resposta de erro segue o `HttpExceptionFilter` existente, que já repassa `codigo` (api-contract, seção 3).

## 6. Especificação técnica

### 6.1. Guard consulta a revogação (D-04, F32)

O guard hoje só verifica a assinatura do token. Ele passa a consultar o banco. Como a consulta é assíncrona, `canActivate` vira `async`:

```typescript
// erp-licenca.guard.ts — recusa token de máquina que já foi trocada (D-04)
import { hwidEstaRevogado } from '@startbig/database/repositories/licenca-servidor.repository'

async canActivate(context: ExecutionContext): Promise<boolean> {
  const request = context.switchToHttp().getRequest()
  const payload = this.verificarAssinatura(request)        // código atual, sem mudança
  // Se o token traz uma máquina e ela foi revogada, a recusa é imediata.
  if (payload.hwid && await hwidEstaRevogado(payload.licencaId, payload.hwid)) {
    throw new UnauthorizedException({
      codigo: 'LICENCA_HWID_REVOGADO',
      message: 'Esta máquina não é mais o servidor desta licença.',
    })
  }
  request.erp = payload
  return true
}
```

A regra escolhida é só "não está revogada". Ela não exige que a máquina seja o servidor atual em todas as rotas, porque o login do ERP sem `hwid` gera um token com identificador próprio. A regra do servidor atual vale só para backup (6.2).

### 6.2. Backup só do servidor atual (F15, F29)

```typescript
// erp-backup.service.ts — o backup só entra e sai pelo servidor atual (F15, F29)
private async exigirServidorAtual(licencaId: string, hwidToken: string | null, hwidPedido: string) {
  if (!hwidToken)
    throw this.erro(HttpStatus.FORBIDDEN, 'BACKUP_HWID_AUSENTE',
                    'O token não tem a identificação da máquina.')   // F29
  const licenca = await findLicencaById(licencaId)
  if (hwidPedido !== hwidToken || licenca.hwidServidor !== hwidToken)
    throw this.erro(HttpStatus.FORBIDDEN, 'BACKUP_MAQUINA_REVOGADA',
                    'Esta máquina não é mais o servidor desta licença.')   // F15
}
```

`urlUpload` e `urlDownload` chamam esse método logo depois de `carregarLicencaLiberada`. Hoje a checagem de `hwid` é condicional (`if (hwidToken && ...)`), e a mudança a torna obrigatória.

### 6.3. Trial recebe um backup completo (D-06)

`motivoDeBloqueio` retorna `TRIAL` para toda licença de teste. A mudança libera um envio completo, e só um:

```typescript
// erp-backup.service.ts — trial tem um backup completo e nada mais (D-06)
if (licenca.isTrial) {
  const enviados = await contarBackupsCompletos(licencaId)   // quantos fulls já existem
  if (tipo !== 'FULL' || enviados >= 1)
    throw this.erro(HttpStatus.FORBIDDEN, 'BACKUP_TRIAL_LIMITE',
                    'O período de teste permite um backup completo. Assine para ter backups completos e incrementais.')
}
```

O motivo de bloqueio `TRIAL` deixa de recusar tudo, e passa a recusar só o segundo envio ou um incremental.

### 6.4. Vencimento com código (F27)

```typescript
// dispositivo.service.ts — vencimento sai com código e status 402 (F27)
if (licenca.dataVencimento && licenca.dataVencimento < new Date() && !emCarencia)
  throw new HttpException(
    { codigo: 'LICENCA_VENCIDA',
      message: 'Sua licença está vencida. Renove a assinatura para ativar o sistema neste computador.' },
    HttpStatus.PAYMENT_REQUIRED,   // 402: o app já trata este status como vencimento
  )
```

### 6.5. Contrato travado por teste (F28)

Hoje `/licenca/validar` responde `201` com `valida: false` em recusa, e `/licenca/conectar` responde `4xx`. O app depende do `201`. O teste trava o formato dos dois endpoints, para qualquer mudança de status quebrar o teste e não o app em produção.

## 7. Critérios de aceite

- **CA-01:** token de máquina revogada recebe `401 LICENCA_HWID_REVOGADO` em qualquer rota do guard.
- **CA-02:** backup de máquina que não é o servidor atual recebe `BACKUP_MAQUINA_REVOGADA`, nos dois sentidos (envio e download).
- **CA-03:** token sem `hwid` recebe `BACKUP_HWID_AUSENTE`.
- **CA-04:** trial envia um backup completo e recebe `BACKUP_TRIAL_LIMITE` no segundo.
- **CA-05:** vencimento em `/licenca/conectar` responde `402` com `codigo: LICENCA_VENCIDA`.
- **CA-06:** o app continua reconhecendo o vencimento sem mudança, porque `recusa.ts` já aceita o status `402`.

Verificável com `npm test` no `apps/server`, sem Postgres (banco fake de `test/apoio/prisma-falso.ts`).

## 8. Casos de teste

| ID | Caso | Esperado |
|----|------|----------|
| CT-01 | Token com `hwid` revogado | `401 LICENCA_HWID_REVOGADO` |
| CT-02 | Token com `hwid` não revogado | Passa |
| CT-03 | Upload de máquina que não é `hwidServidor` | `BACKUP_MAQUINA_REVOGADA` |
| CT-04 | Download de máquina que não é `hwidServidor` | `BACKUP_MAQUINA_REVOGADA` |
| CT-05 | Upload sem `hwid` no token | `BACKUP_HWID_AUSENTE` |
| CT-06 | Trial, primeiro full | Aceito |
| CT-07 | Trial, segundo full | `BACKUP_TRIAL_LIMITE` |
| CT-08 | `/licenca/conectar` com licença vencida | `402`, `codigo: LICENCA_VENCIDA` |
| CT-09 | `/licenca/validar` com recusa | `201`, `valida: false`, com os campos esperados |
| CT-10 | `/licenca/conectar` com recusa de transferência | `400`, `codigo: LICENCA_TRANSFERIDA` |

## 9. Testes existentes que a mudança afeta

- `apps/server/test/licenca/licenca-troca-servidor.test.ts`: cobre a troca de servidor e a revogação. Deve passar. Se algum teste esperava `400` no vencimento, a expectativa passa a ser `402`, com o motivo registrado no teste.
- `apps/server/test/financeiro/*` e `apps/server/test/erp/*`, se usarem `ErpLicencaGuard`: a guarda passa a ser `async`, então os testes que a chamam precisam ser `await`.

## 10. Perguntas antes da aprovação

- Nenhuma. D-04 e D-06 já estão fechadas no ACORDO.

## 11. Observações

- Repositório separado: a branch e o PR são do `plataformaADM`, e o padrão de commits dele é o do próprio repositório.
- O guard passa a fazer uma consulta ao banco por requisição autenticada. Medir o efeito no primeiro uso.
- O `start-big` não muda nesta spec. O app só passa a ver os códigos novos quando a SPEC-02 e a SPEC-06 forem entregues.
