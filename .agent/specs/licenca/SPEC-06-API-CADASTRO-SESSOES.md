# Licença 06 — API: cadastro, login e sessões

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend da API (NestJS, Prisma), repositório `plataformaADM` |
| Repositório  | `dzim-almeida/plataformaADM` (outro repositório: fora do harness do `start-big`) |
| Dependências | Acesso de escrita ao `plataformaADM` (ACORDO D-01). Decisão da seção 10 sobre o fluxo de confirmação. |
| Bloqueia     | — (mas o fluxo de cadastro do `start-big` depende da seção 10) |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-01, D-09, D-10; quadro F2, F3, F4, F5, F6, F12, F13, F17, F21, F23 |

> **Pré-requisito:** a implementação só começa com acesso de escrita ao `plataformaADM` e uma branch nova no próprio repositório.

## 1. Objetivo

Fechar a porta de entrada da licença na API: quem cadastra precisa provar que é dono do e-mail, a chave só vai para quem confirmou, o login não entrega dados por tentativa, e as vagas de computador não ficam presas por sessões mortas.

## 2. Escopo

**Dentro do escopo**
- Cadastro idempotente: o mesmo e-mail e a mesma senha devolvem a licença existente, em vez de erro (F3).
- Confirmação de e-mail antes de criar o trial e antes de devolver a chave (F2, F13).
- Chave de ativação nunca na resposta do cadastro (F2).
- Limite progressivo de tentativas de login por e-mail (D-09, F4).
- Resposta genérica no login, sem revelar o estado da conta (F12).
- Reenvio do link de primeiro acesso, com limite de frequência (F23).
- Sessões sem heartbeat expiram em 10 minutos (D-10, F21).
- Troca de servidor apaga as sessões dos terminais do servidor antigo (F17).
- Desconexão exige o token da sessão (F5).
- Contagem de sessões em operação atômica (F6).
- Atualização dos dados do titular pela nuvem, antes do setup local (D-22, `PUT /erp/cadastro/titular`).

**Fora do escopo**
- Tela para o dono liberar vagas (ACORDO D-10, alternativa B). Fica para depois de medir o efeito do expurgo automático.
- Mudanças no guard e nos backups (SPEC-05).

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `apps/server/src/features/dispositivos/dispositivo.service.ts` | alterar | `autoCadastro` idempotente e com confirmação. `conectar` com contador atômico. `desconectar` exige token de sessão. `HEARTBEAT_TIMEOUT_MS` passa de 35 para 10 minutos. |
| `apps/server/src/features/dispositivos/dispositivo.controller.ts` | alterar | Novas rotas de confirmação; `desconectar` recebe o token de sessão. |
| `apps/server/src/features/erp/erp-auth.service.ts` | alterar | Bloqueio progressivo por e-mail e resposta genérica. |
| `apps/server/src/features/erp/erp-auth.controller.ts` | alterar | Rota de reenvio de primeiro acesso. |
| `apps/server/src/features/cliente/cliente.service.ts` | alterar | Reenvio com limite de frequência, reaproveitando o envio de primeiro acesso (linha ~199). |
| `apps/server/src/features/dispositivos/dispositivo.service.ts` (`cron`) | alterar | Expurgo de sessões a cada 10 minutos. |
| `packages/database/prisma/schema.prisma` | alterar | Campos novos em `Cliente`: `emailConfirmadoEm`, `falhasLogin`, `bloqueadoAte`, `tokenConfirmacaoEmail`, `tokenConfirmacaoExpiraEm`. Campo `tokenSessao` em `LicencaSessao`. |
| `packages/database/prisma/migrations/` | criar | Migração Prisma, decidindo pela presença do campo antigo. |
| `apps/server/test/licenca/cadastro-confirmacao.test.ts` | criar | Casos CT-01 a CT-05. |
| `apps/server/test/erp/login-bloqueio.test.ts` | criar | Casos CT-06 a CT-09. |
| `apps/server/test/licenca/sessoes.test.ts` | criar | Casos CT-10 a CT-14. |

Testes existentes que precisam continuar passando: `apps/server/test/licenca/licenca-troca-servidor.test.ts` e `apps/server/test/cripto/segredo-fiscal.test.ts`.

## 4. Contrato da API

### 4.1. `POST /erp/auto-cadastro` (muda)

Antes, a resposta trazia `chaveAtivacao` e `token`. Agora responde `202`, e a chave só sai depois da confirmação (F2).

```json
{
  "statusCode": 202,
  "message": "Enviamos um link de confirmação para o seu e-mail. Confirme para ativar o período de teste."
}
```

Se o e-mail já tem licença e a senha confere, a resposta é a licença existente, sem reenviar a chave (F3). Quando a senha não confere: `409 E_MAIL_JA_CADASTRADO`.

### 4.2. `GET /erp/auto-cadastro/confirmar?token=...` (nova)

Confirma o e-mail pelo link. Não devolve a chave na resposta: manda a chave e o login por e-mail.

| Status | Corpo | Quando |
|--------|-------|--------|
| 200 | `{ "message": "E-mail confirmado. Verifique sua caixa de entrada." }` | Token válido |
| 400 | `{ "codigo": "TOKEN_CONFIRMACAO_INVALIDO", "message": "Este link não é válido." }` | Token inexistente ou já usado |
| 410 | `{ "codigo": "TOKEN_CONFIRMACAO_EXPIRADO", "message": "Este link expirou. Peça um novo cadastro." }` | Token vencido |

### 4.3. `POST /erp/auth/login` (muda o erro)

| Situação | Status | `codigo` |
|----------|--------|----------|
| E-mail não existe, senha errada ou conta sem senha | 401 | `CREDENCIAIS_INVALIDAS` (mesma resposta nos três casos, F12) |
| Muitas tentativas | 429 | `MUITAS_TENTATIVAS`, com `message` dizendo para tentar em alguns minutos |
| Login certo com licença vencida | 402 | `LICENCA_VENCIDA` (sem mudança) |
| Login certo, mas o e-mail ainda não foi confirmado (sem licença criada) | 403 | `AGUARDANDO_CONFIRMACAO_EMAIL`, com `message` pedindo a confirmação |

### 4.4. `POST /erp/auth/reenviar-primeiro-acesso` (nova, F23)

Corpo `{ "email": "..." }`. Responde sempre `202`, com a mesma mensagem, existindo ou não o e-mail (sem enumeração). Só envia de novo se passou 60 segundos desde o último envio.

### 4.5. `POST /licenca/desconectar` (muda, F5)

O corpo passa a exigir `tokenSessao`, o token devolvido pelo `conectar` daquela sessão. Sem ele: `401 TOKEN_SESSAO_INVALIDO`.

### 4.6. `PUT /erp/cadastro/titular` (nova, D-22)

Atualiza os dados da empresa do titular na nuvem, antes de o setup criar a empresa local. Protegida por `ErpLicencaGuard`, com o token da licença (como `erp-backup.controller.ts`).

**Corpo**

```json
{
  "nomeOuRazao": "Loja Exemplo Ltda",
  "nomeFantasia": "Loja Exemplo",
  "telefone": "(85) 3000-0000",
  "celular": "(85) 99999-0000",
  "endereco": { "cep": "63000-000", "logradouro": "Rua A", "numero": "10", "bairro": "Centro", "cidade": "Iguatu", "estado": "CE" }
}
```

O **documento não vem no corpo**. Se vier, a API recusa com `DOCUMENTO_TRAVADO`, porque o documento do titular não muda por este caminho (D-22).

| Status | `codigo` | Quando |
|--------|----------|--------|
| 200 | — | Dados atualizados; corpo com o cadastro salvo |
| 401 | `LICENCA_HWID_REVOGADO` | Token de máquina revogada (SPEC-05) |
| 403 | `DOCUMENTO_TRAVADO` | Corpo trouxe documento |
| 422 | — | Campo inválido (texto do Zod, como hoje) |

## 5. Schemas

```prisma
// schema.prisma — campos novos (Prisma, não Pydantic)
model Cliente {
  emailConfirmadoEm          DateTime?  // quando o dono confirmou o e-mail
  falhasLogin                Int        @default(0)  // tentativas erradas seguidas
  bloqueadoAte               DateTime?  // até quando o login fica bloqueado
  tokenConfirmacaoEmail      String?    // token do link de confirmação (guardado em hash)
  tokenConfirmacaoExpiraEm   DateTime?  // validade do link
}

model LicencaSessao {
  tokenSessao  String?  // token devolvido pelo conectar, para desconectar com prova
}
```

Guardar o `tokenConfirmacaoEmail` em hash, não em texto puro, como a senha.

## 6. Especificação técnica

### 6.1. Cadastro idempotente e com confirmação (F2, F3, F13)

```typescript
// dispositivo.service.ts — o mesmo e-mail e a mesma senha devolvem o que já existe (F3)
const existente = await prisma.cliente.findFirst({ where: { email: dados.email } })
if (existente) {
  const senhaConfere = existente.senhaHash && await bcrypt.compare(dados.senha, existente.senhaHash)
  if (!senhaConfere)
    throw new ConflictException({ codigo: 'E_MAIL_JA_CADASTRADO',
      message: 'Este e-mail já tem cadastro. Use a opção Já tenho conta.' })
  // Mesma pessoa tentando de novo: não cria nada, só informa.
  return { message: 'Este e-mail já tem cadastro. Entre com a sua senha.', jaCadastrado: true }
}
// Sem cadastro: cria a conta, mas o trial só começa depois da confirmação (F13).
const tokenBruto = randomBytes(32).toString('hex')           // token do link, aleatório
await prisma.cliente.create({ data: { /* dados do cadastro */
  tokenConfirmacaoEmail: sha256(tokenBruto),                  // guarda o hash, nunca o token
  tokenConfirmacaoExpiraEm: addHours(new Date(), 24) } })
await this.emailService.enviarConfirmacao(dados.email, tokenBruto)
return { statusCode: 202, message: 'Enviamos um link de confirmação para o seu e-mail.' }
```

A confirmação cria a licença de teste, e só então envia a chave de ativação por e-mail. A chave nunca aparece na resposta HTTP.

### 6.2. Bloqueio progressivo por e-mail (D-09, F4, F12)

```typescript
// erp-auth.service.ts — espera de 1, 5 e 15 minutos depois de falhas seguidas (D-09)
const ESPERAS_MIN = [1, 5, 15]                  // minutos de espera, por nível de falha
if (cliente.bloqueadoAte && cliente.bloqueadoAte > new Date())
  throw new HttpException({ codigo: 'MUITAS_TENTATIVAS',
    message: 'Muitas tentativas. Tente de novo em alguns minutos.' }, 429)
const senhaOk = cliente.senhaHash && await bcrypt.compare(dados.senha, cliente.senhaHash)
if (!senhaOk) {
  const falhas = cliente.falhasLogin + 1
  const nivel = Math.min(falhas - 5, ESPERAS_MIN.length - 1)
  await prisma.cliente.update({ where: { id: cliente.id }, data: {
    falhasLogin: falhas,
    bloqueadoAte: falhas >= 5 ? addMinutes(new Date(), ESPERAS_MIN[nivel]) : null } })
  throw new UnauthorizedException({ codigo: 'CREDENCIAIS_INVALIDAS',
    message: 'E-mail ou senha incorretos.' })   // mesma mensagem para qualquer caso (F12)
}
await prisma.cliente.update({ where: { id: cliente.id }, data: { falhasLogin: 0, bloqueadoAte: null } })
```

A mensagem de senha não configurada também passa a ser `CREDENCIAIS_INVALIDAS`. O app orienta o reenvio do primeiro acesso pela rota da seção 4.4.

### 6.3. Sessões: expiração e troca (D-10, F17, F21)

```typescript
// dispositivo.service.ts — sessão sem heartbeat por 10 minutos já está morta (D-10)
const HEARTBEAT_TIMEOUT_MS = 10 * 60 * 1000   // antes: 35 minutos
```

Na troca de servidor (`assumirServidorDaLicenca`), as sessões dos terminais do servidor antigo também são apagadas (F17). Ao reconectar o servidor, as sessões sem heartbeat são expiradas antes da contagem (F21).

### 6.4. Desconexão com prova (F5)

O `conectar` devolve um `tokenSessao` aleatório, guardado em `LicencaSessao`. O `desconectar` só apaga a sessão se o token confere:

```typescript
// dispositivo.service.ts — só quem tem o token da sessão pode derrubá-la (F5)
const sessao = await findLicencaSessao(licenca.id, dados.hwid)
if (!sessao || sessao.tokenSessao !== dados.tokenSessao)
  throw new UnauthorizedException({ codigo: 'TOKEN_SESSAO_INVALIDO',
    message: 'Não foi possível encerrar esta sessão.' })
await deletarSessao(licenca.id, dados.hwid)
```

### 6.6. Atualização do titular (D-22)

Grava os dados no `Cliente` (`pf` ou `pj`, conforme o tipo que a nuvem já tem) e em `enderecos`. O tipo de documento não muda aqui.

```typescript
// atualizar-titular.ts — grava os dados da empresa do titular; o documento nunca muda aqui (D-22)
async atualizarTitular(licencaId: string, dados: AtualizarTitularDto) {
  if ('documento' in dados)
    throw this.erro(HttpStatus.FORBIDDEN, 'DOCUMENTO_TRAVADO',
                    'O documento do titular não pode ser alterado pelo app. Fale com o suporte.')
  const cliente = await findClienteDaLicenca(licencaId)      // o titular da licença
  await prisma.cliente.update({ where: { id: cliente.id }, data: {
    pj: { update: { nomeFantasia: dados.nomeFantasia, telefone: dados.telefone, celular: dados.celular,
                    razaoSocial: dados.nomeOuRazao } },      // para PF, o campo é nomeCompleto
  } })
  return { ok: true }
}
```

Para titular PF, o nome vai para `pf.nomeCompleto`, no mesmo formato. Se a nuvem não tiver o endereço, ele é criado em `enderecos`.

### 6.5. Contador atômico (F6)

A contagem de sessões e a gravação passam a ser uma única operação com condição, para dois caixas não passarem juntos pelo limite:

```sql
-- Só grava a sessão se ainda couber no limite. Uma instrução, sem janela de corrida.
INSERT INTO "LicencaSessao" (...)
SELECT ...
WHERE (SELECT COUNT(*) FROM "LicencaSessao" WHERE "licencaId" = $1) < $2;
```

Se nenhuma linha for gravada, a resposta é o mesmo erro de limite de hoje.

## 7. Critérios de aceite

- **CA-01:** cadastro novo responde `202` sem `chaveAtivacao` na resposta.
- **CA-02:** clicar no link de confirmação cria a licença de teste e envia a chave por e-mail.
- **CA-03:** cadastro repetido com a mesma senha não cria nada e não envia chave.
- **CA-04:** cinco senhas erradas seguidas bloqueiam o login por 1 minuto, e a mensagem é a mesma para qualquer falha.
- **CA-05:** dois caixas ao mesmo tempo, com limite 1, só um entra.
- **CA-06:** desconectar sem o `tokenSessao` recebe `TOKEN_SESSAO_INVALIDO`.
- **CA-07:** sessão sem heartbeat por 10 minutos some da contagem.
- **CA-08:** `PUT /erp/cadastro/titular` com `documento` no corpo recebe `403 DOCUMENTO_TRAVADO` e não altera nada.
- **CA-09:** login de cliente que ainda não confirmou o e-mail recebe `403 AGUARDANDO_CONFIRMACAO_EMAIL`, e nenhuma chave é devolvida.

Verificável com `npm test` no `apps/server`. CA-02 precisa de SMTP real ou de um envio simulado, e fica marcado conforme o caso.

## 8. Casos de teste

| ID | Caso | Esperado |
|----|------|----------|
| CT-01 | Cadastro novo | `202`, sem chave na resposta |
| CT-02 | Confirmação com token válido | Licença de teste criada, chave enviada |
| CT-03 | Confirmação com token já usado | `400 TOKEN_CONFIRMACAO_INVALIDO` |
| CT-04 | Confirmação com token vencido | `410 TOKEN_CONFIRMACAO_EXPIRADO` |
| CT-05 | Cadastro repetido com senha certa | Mensagem de "entre com a senha", sem novo cadastro |
| CT-06 | Cinco falhas seguidas | `bloqueadoAte` gravado, 1 minuto |
| CT-07 | Login durante o bloqueio | `429 MUITAS_TENTATIVAS` |
| CT-08 | E-mail inexistente ou sem senha | `401 CREDENCIAIS_INVALIDAS`, mesma resposta |
| CT-09 | Reenvio de primeiro acesso dentro de 60 s | `202`, sem novo envio |
| CT-10 | Dois caixas simultâneos com limite 1 | Um entra, um recebe limite |
| CT-11 | Sessão sem heartbeat por 11 minutos | Fora da contagem |
| CT-12 | Desconectar com `tokenSessao` certo | Sessão apagada |
| CT-13 | Desconectar com `tokenSessao` errado | `401 TOKEN_SESSAO_INVALIDO` |
| CT-14 | Troca de servidor com terminais do antigo | Sessões dos terminais apagadas |
| CT-15 | `PUT /erp/cadastro/titular` com dados válidos | `200`, cadastro atualizado |
| CT-16 | `PUT` com `documento` no corpo | `403 DOCUMENTO_TRAVADO`, nada alterado |
| CT-17 | `PUT` com token de máquina revogada | `401 LICENCA_HWID_REVOGADO` |
| CT-18 | Login antes da confirmação do e-mail | `403 AGUARDANDO_CONFIRMACAO_EMAIL`, sem chave |
| CT-19 | Login depois da confirmação | `200`, com a chave de ativação (D-23) |

## 9. Testes existentes que a mudança afeta

- `apps/server/test/licenca/licenca-troca-servidor.test.ts`: depende de sessões e da troca. Deve passar; a expectativa de tempo de heartbeat muda de 35 para 10 minutos, e isso fica registrado no teste.
- `apps/server/test/cripto/segredo-fiscal.test.ts`: não muda.

## 10. Perguntas antes da aprovação

- **1. Como o app recebe a chave depois da confirmação de e-mail (F2). Resolvida em 2026-11-18: opção B (D-23).** Depois de confirmar, o dono entra com e-mail e senha pelo re-login (SPEC-03). A API já devolve a chave nesse login. A B não cria confirmação própria: a confirmação é a do cadastro (F2), e sem ela não há licença nem chave.
  - Sub-decisão de código: o login de quem ainda não confirmou responde `AGUARDANDO_CONFIRMACAO_EMAIL` (seção 4.3), para o app mostrar a mensagem certa em vez de "sem licença ativa".
  - *Opções originais, mantidas para registro:* A. copiar a chave do e-mail; B. entrar com e-mail e senha (escolhida); C. consultar a API até a confirmação.

- **2. Trial só depois da confirmação (F13).** Com a confirmação, o cadastro some do app até o e-mail chegar. Quer confirmar que isso é aceitável para a loja?
  - **A.** Sim, o trial começa só depois da confirmação. É a proteção pedida.
  - **B.** Não, o trial começa na hora, e a confirmação só libera a chave. Menos atrito, mas o trial continua disponível para quem não é dono do e-mail.
  - **Recomendação: A.** É o que a análise pediu, e o custo é o tempo de espera do e-mail.

## 11. Observações

- **Impacto no `start-body` (`start-big`).** `registrar_licenca` (em `cadastro.py`) passa a receber `202` em vez de uma licença. O tratamento desse caso, e o caminho para o re-login depois da confirmação, entram na SPEC-03. Esta spec não muda o `start-big`, mas o fluxo de cadastro só funciona no app depois da SPEC-03.
- **Migração Prisma:** campos novos em `Cliente` e `LicencaSessao`. A migração decide pela presença do campo, como a regra de migração pede.
- **Tempo de heartbeat:** a mudança de 35 para 10 minutos depende de o `start-big` enviar heartbeat com folga. O intervalo real é `INTERVALO_HEARTBEAT_SEGUNDOS = 100` (`backend-fastapi/app/core/tarefas.py:34`), ou seja, cerca de 100 segundos. **Divergência registrada:** o comentário dessa linha diz "5 minutos", mas o valor é 100 segundos. A correção do comentário é uma linha no `start-big`, e entra no `ROTEIRO-IMPLEMENTACAO.md` como tarefa separada.
- **Rotas do desconectar:** `POST /licenca/desconectar` no controlador `dispositivo.controller.ts`. Não é `DELETE`.
