# Licença 06 — API: conta e cadastro

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend da API (NestJS, Prisma), repositório `aalan-big/plataformaADM` |
| Repositório  | `aalan-big/plataformaADM` (público; outro repositório, fora do harness do `start-big`) |
| Dependências | Acesso de escrita ao `plataformaADM` (ACORDO D-01). SPEC-05 (as rotas do titular usam a recusa de máquina revogada do guard) |
| Bloqueia     | — (a SPEC-03 usa esta spec, mas funciona sem ela pela rede de segurança do `404`) |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-01, D-09, D-22, D-23, D-24, D-28, D-31; risco R-01; quadro F2, F3, F4, F12, F13, F23 |

> **Pré-requisito:** a implementação só começa com acesso de escrita ao `plataformaADM` e uma branch nova no próprio repositório.

> **Revisão 1 (2026-11-18):** revisão de conflitos com o usuário, antes da aprovação. O arquivo se chamava `SPEC-06-API-CADASTRO-SESSOES.md`.
> - **Conflito 15:** a spec foi dividida. As **vagas de computador** (sessões de 10 minutos, troca apaga sessões, contagem atômica) foram para a **LIC-09**. Esta spec fica com conta e cadastro, e a §3 lista todos os arquivos e testes.
> - **Conflito 7:** o F5 (`tokenSessao` no desconectar) saiu. Virou o risco aceito R-02, mitigado pela SPEC-01.
> - **Conflito 8 (D-28):** entra o `GET /erp/cadastro/titular`.
> - **Conflito 14 (D-31):** o cadastro sempre responde `202`, sem revelar se o e-mail existe. A rota de reenvio vira `reenviar-link` e escolhe o link pelo estado da conta. A chave de ativação nunca vai por e-mail. Sai o código `E_MAIL_JA_CADASTRADO`.
> - **Documentação:** repositório `aalan-big/plataformaADM`; schema do Prisma em `prisma/schema.prisma`, na raiz. As perguntas da §10 estavam resolvidas.

## 1. Objetivo

Fechar a porta de entrada da licença na API: quem cadastra precisa provar que é dono do e-mail, a chave só vai para quem confirmou e entrou com a senha, e nenhuma resposta revela se um e-mail é cliente.

## 2. Escopo

**Dentro do escopo**
- Cadastro com resposta única (`202`) para qualquer caso: e-mail novo, já cadastrado, senha certa ou errada (F3, D-31).
- Confirmação de e-mail antes de criar o trial (F13, D-24). Nenhum e-mail leva a chave de ativação (F2, D-23).
- Login devolve a chave só a quem já confirmou (D-23); antes disso, `AGUARDANDO_CONFIRMACAO_EMAIL`.
- Limite progressivo de tentativas de login por e-mail (D-09, F4).
- Resposta genérica no login, sem revelar o estado da conta (F12).
- Rota `reenviar-link`, que manda o link certo pelo estado da conta, com limite de frequência (F23, D-31). Ela também permite ao dono definir uma nova senha, que é a mitigação do R-01.
- Leitura e atualização dos dados do titular (`GET` e `PUT /erp/cadastro/titular`, D-22 e D-28).

**Fora do escopo**
- Sessões, vagas e troca de servidor (LIC-09).
- Guard e backups (SPEC-05).
- `tokenSessao` no desconectar (F5): risco aceito R-02 (conflito 7).

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `apps/server/src/features/dispositivos/dispositivo.service.ts` | alterar | `autoCadastro` (linha ~962): resposta única `202`, sem criar licença nem mandar chave; cria a conta com o token de confirmação. Remove o envio da chave por e-mail (linhas ~444 e ~1139). Novo `confirmarCadastro(token)`, que cria a licença de teste. |
| `apps/server/src/features/dispositivos/dispositivo.controller.ts` | alterar | `POST /erp/auto-cadastro` responde `202`. Nova rota `GET /erp/auto-cadastro/confirmar`. |
| `apps/server/src/features/erp/erp-auth.service.ts` | alterar | `login` (linha 48): bloqueio progressivo, `SENHA_NAO_CONFIGURADA` vira `CREDENCIAIS_INVALIDAS`, `AGUARDANDO_CONFIRMACAO_EMAIL`. Novo `reenviarLink(email)`. `primeiroAcesso` passa a aceitar quem já tem senha (R-01) e muda a mensagem de link expirado. |
| `apps/server/src/features/erp/erp-auth.controller.ts` | alterar | Nova rota `POST /erp/auth/reenviar-link`. |
| `apps/server/src/features/erp/erp-cadastro.controller.ts` | criar | `GET` e `PUT /erp/cadastro/titular`, protegidas por `ErpLicencaGuard`. |
| `apps/server/src/features/erp/erp-cadastro.service.ts` | criar | `lerTitular(licencaId)` e `atualizarTitular(licencaId, dados)`. |
| `apps/server/src/features/erp/erp.module.ts` | alterar | Registra o controller e o service novos. |
| `apps/server/src/core/email/email.service.ts` | alterar | Modelos novos: `enviarConfirmacaoCadastro`, `enviarAvisoJaCadastrado`. O `enviarPrimeiroAcesso` passa a servir também à nova senha. |
| `prisma/schema.prisma` | alterar | Campos novos em `Cliente`: `emailConfirmadoEm`, `falhasLogin`, `bloqueadoAte`, `tokenConfirmacaoEmail`, `tokenConfirmacaoExpiraEm`, `ultimoEnvioLinkEm`. |
| `prisma/migrations/` | criar | Migração Prisma dos campos novos. |
| `apps/server/test/licenca/cadastro-confirmacao.test.ts` | criar | Casos CT-01 a CT-06. |
| `apps/server/test/erp/login-bloqueio.test.ts` | criar | Casos CT-07 a CT-11. |
| `apps/server/test/erp/reenviar-link.test.ts` | criar | Casos CT-12 a CT-16 e CT-22. |
| `apps/server/test/erp/cadastro-titular.test.ts` | criar | Casos CT-17 a CT-21. |

Testes existentes que precisam continuar passando: `apps/server/test/licenca/licenca-troca-servidor.test.ts` e `apps/server/test/cripto/segredo-fiscal.test.ts`.

## 4. Contrato da API

### 4.1. `POST /erp/auto-cadastro` (muda)

Antes, a resposta trazia `chaveAtivacao` e `token`. Agora responde **sempre** `202`, com a mesma mensagem, em qualquer caso:

```json
{
  "statusCode": 202,
  "message": "Enviamos as instruções para o seu e-mail. Se este e-mail já tiver conta, enviamos as instruções para entrar."
}
```

| Situação | O que a API faz por trás | Resposta |
|----------|--------------------------|----------|
| E-mail novo | Cria a conta sem licença e manda o link de confirmação | `202` |
| E-mail já cadastrado (senha certa ou errada) | Não cria nada; manda um e-mail "Este e-mail já tem cadastro. Entre com a sua senha ou crie uma nova pelo link abaixo" | `202` |

### 4.2. `GET /erp/auto-cadastro/confirmar?token=...` (nova)

Confirma o e-mail pelo link e cria a licença de teste (D-24). Não devolve nem envia a chave: o dono a recebe ao entrar no app com e-mail e senha (D-23).

| Status | Corpo | Quando |
|--------|-------|--------|
| 200 | `{ "message": "Conta confirmada. Volte ao StartBig e entre com o seu e-mail e senha." }` | Token válido |
| 400 | `{ "codigo": "TOKEN_CONFIRMACAO_INVALIDO", "message": "Este link não é válido." }` | Token inexistente ou já usado |
| 410 | `{ "codigo": "TOKEN_CONFIRMACAO_EXPIRADO", "message": "Este link expirou. Peça um novo link no StartBig." }` | Token vencido (24 h) |

### 4.3. `POST /erp/auth/login` (muda os erros)

| Situação | Status | `codigo` |
|----------|--------|----------|
| E-mail não existe, senha errada ou conta sem senha | 401 | `CREDENCIAIS_INVALIDAS` (mesma resposta nos três casos, F12). Hoje a conta sem senha responde `400 SENHA_NAO_CONFIGURADA` |
| Muitas tentativas | 429 | `MUITAS_TENTATIVAS`, com `message` pedindo para tentar em alguns minutos |
| Senha certa, e-mail ainda não confirmado (sem licença) | 403 | `AGUARDANDO_CONFIRMACAO_EMAIL` |
| Senha certa com licença vencida | 402 | `LICENCA_VENCIDA` (já existe hoje) |
| Senha certa, confirmado | 200 | Igual a hoje, com `chaveAtivacao` (D-23) |

### 4.4. `POST /erp/auth/reenviar-link` (nova, F23, D-31)

Corpo `{ "email": "..." }`. Responde **sempre** `202`, com a mesma mensagem, exista ou não o e-mail. Só envia de novo se passaram 60 segundos desde o último envio (`ultimoEnvioLinkEm`).

| Estado da conta | Link enviado |
|-----------------|--------------|
| Não existe | Nenhum (mesma resposta `202`) |
| Não confirmada | Um link de confirmação novo (o anterior deixa de valer) |
| Confirmada | Link para definir uma nova senha, mesmo que já exista uma (mitigação do R-01) |

O link de nova senha usa os campos que já existem, `tokenEmail` e `tokenEmailExpiraEm`, e a rota `primeiroAcesso` (`erp-auth.service.ts:120`). A mensagem de link expirado dela passa de "Entre em contato com o suporte" para "Peça um novo link no StartBig".

Definir a senha por esse link também grava `emailConfirmadoEm`, se estiver vazio: o link chegou ao e-mail, então prova que o dono o controla. Sem isso, as contas criadas pelo administrador da plataforma (`cliente.service.ts`, que manda o link de primeiro acesso) ficariam presas em `AGUARDANDO_CONFIRMACAO_EMAIL`.

### 4.5. `GET /erp/cadastro/titular` (nova, D-28)

Devolve os dados da empresa do titular, para pré-preencher o setup do app (SPEC-03 §6.6). Protegida por `ErpLicencaGuard`, com o token da licença (como `erp-backup.controller.ts`).

```json
{
  "tipoPessoa": "PJ",
  "nomeOuRazao": "Loja Exemplo Ltda",
  "documento": "00.000.000/0001-00",
  "nomeFantasia": "Loja Exemplo",
  "telefone": "(85) 3000-0000",
  "celular": "(85) 99999-0000",
  "endereco": { "cep": "63000-000", "logradouro": "Rua A", "numero": "10", "bairro": "Centro", "cidade": "Iguatu", "estado": "CE" }
}
```

| Status | `codigo` | Quando |
|--------|----------|--------|
| 200 | — | Dados do titular |
| 401 | `LICENCA_HWID_REVOGADO` | Token de máquina revogada (SPEC-05) |

### 4.6. `PUT /erp/cadastro/titular` (nova, D-22)

Atualiza os dados da empresa do titular, antes de o setup criar a empresa local. Mesma proteção do `GET`.

**Corpo:** os mesmos campos do `GET`, **sem** `tipoPessoa` e **sem** `documento`.

| Status | `codigo` | Quando |
|--------|----------|--------|
| 200 | — | Dados atualizados; corpo com o cadastro salvo |
| 401 | `LICENCA_HWID_REVOGADO` | Token de máquina revogada (SPEC-05) |
| 403 | `DOCUMENTO_TRAVADO` | O corpo trouxe `documento`. O documento do titular não muda por este caminho |
| 422 | — | Campo inválido (texto do Zod, como hoje) |

## 5. Schemas

```prisma
// prisma/schema.prisma — campos novos em Cliente (Prisma, não Pydantic)
model Cliente {
  emailConfirmadoEm          DateTime?               // quando o dono confirmou o e-mail
  falhasLogin                Int        @default(0)  // tentativas erradas seguidas
  bloqueadoAte               DateTime?               // até quando o login fica bloqueado
  tokenConfirmacaoEmail      String?                 // hash do token do link de confirmação
  tokenConfirmacaoExpiraEm   DateTime?               // validade do link (24 h)
  ultimoEnvioLinkEm          DateTime?               // controla o limite de 60 s do reenvio
}
```

Guardar o `tokenConfirmacaoEmail` em hash, nunca o token em texto puro.

Contas que já existem antes desta spec: a migração preenche `emailConfirmadoEm` com a data da migração para quem **já tem licença**. Assim nenhum cliente de hoje passa a receber `AGUARDANDO_CONFIRMACAO_EMAIL`. A migração decide pela presença de licença, que é o dado do schema antigo.

## 6. Especificação técnica

### 6.1. Cadastro com resposta única (F3, F13, D-31)

```typescript
// dispositivo.service.ts — o cadastro nunca diz se o e-mail já existe (D-31)
const RESPOSTA_CADASTRO = {
  statusCode: 202,
  message: 'Enviamos as instruções para o seu e-mail. Se este e-mail já tiver conta, enviamos as instruções para entrar.',
}

const existente = await prisma.cliente.findFirst({ where: { email: dados.email } })
if (existente) {
  // Não cria nada e não diz nada na resposta: o aviso vai só para a caixa do dono do e-mail.
  await this.emailService.enviarAvisoJaCadastrado(dados.email)
  return RESPOSTA_CADASTRO
}

// Conta nova: sem licença até a confirmação (D-24).
const tokenBruto = randomBytes(32).toString('hex')            // token do link, aleatório
await prisma.cliente.create({ data: { /* dados do cadastro */
  tokenConfirmacaoEmail: sha256(tokenBruto),                   // guarda o hash, nunca o token
  tokenConfirmacaoExpiraEm: addHours(new Date(), 24),
  ultimoEnvioLinkEm: new Date() } })
await this.emailService.enviarConfirmacaoCadastro(dados.email, tokenBruto)
return RESPOSTA_CADASTRO
```

A confirmação (`confirmarCadastro`) confere o hash e a validade, grava `emailConfirmadoEm`, apaga o token e cria a licença de teste. Nenhum e-mail leva a chave de ativação.

### 6.2. Bloqueio progressivo por e-mail (D-09, F4, F12)

```typescript
// erp-auth.service.ts — espera de 1, 5 e 15 minutos depois de 5 falhas seguidas (D-09)
const ESPERAS_MIN = [1, 5, 15]                  // minutos de espera, por nível de falha
if (cliente.bloqueadoAte && cliente.bloqueadoAte > new Date())
  throw new HttpException({ codigo: 'MUITAS_TENTATIVAS',
    message: 'Muitas tentativas. Tente de novo em alguns minutos.' }, 429)

// Conta sem senha cai no mesmo erro de senha errada (F12).
const senhaOk = !!cliente.senhaHash && await bcrypt.compare(dados.senha, cliente.senhaHash)
if (!senhaOk) {
  const falhas = cliente.falhasLogin + 1
  const nivel = Math.min(falhas - 5, ESPERAS_MIN.length - 1)   // 5ª falha = 1 min, 6ª = 5 min, 7ª em diante = 15 min
  await prisma.cliente.update({ where: { id: cliente.id }, data: {
    falhasLogin: falhas,
    bloqueadoAte: falhas >= 5 ? addMinutes(new Date(), ESPERAS_MIN[nivel]) : null } })
  throw new UnauthorizedException({ codigo: 'CREDENCIAIS_INVALIDAS',
    message: 'E-mail ou senha incorretos.' })                  // mesma mensagem para qualquer caso
}
await prisma.cliente.update({ where: { id: cliente.id }, data: { falhasLogin: 0, bloqueadoAte: null } })

// Senha certa, mas o e-mail não foi confirmado: não há licença, e a chave não sai (D-23).
if (!cliente.emailConfirmadoEm)
  throw new ForbiddenException({ codigo: 'AGUARDANDO_CONFIRMACAO_EMAIL',
    message: 'Confirme o link enviado ao seu e-mail antes de entrar.' })
```

E-mail inexistente responde `CREDENCIAIS_INVALIDAS` sem gravar nada, porque não há conta onde contar as falhas.

### 6.3. Reenviar link (F23, D-31, R-01)

```typescript
// erp-auth.service.ts — um botão só no app; a API escolhe o link pelo estado da conta
async reenviarLink(email: string) {
  const resposta = { statusCode: 202, message: 'Se este e-mail tiver conta, enviamos um link.' }
  const cliente = await prisma.cliente.findFirst({ where: { email } })
  if (!cliente) return resposta                                        // não revela que não existe
  if (cliente.ultimoEnvioLinkEm && Date.now() - cliente.ultimoEnvioLinkEm.getTime() < 60_000)
    return resposta                                                    // limite de 60 s
  if (!cliente.emailConfirmadoEm)
    await this.enviarNovoLinkDeConfirmacao(cliente)                    // invalida o anterior
  else
    await this.enviarLinkDeNovaSenha(cliente)                          // R-01: vale mesmo com senha cadastrada
  await prisma.cliente.update({ where: { id: cliente.id }, data: { ultimoEnvioLinkEm: new Date() } })
  return resposta
}
```

### 6.4. Leitura e atualização do titular (D-22, D-28)

```typescript
// erp-cadastro.service.ts — o documento é só leitura: nunca muda por este caminho (D-22)
async atualizarTitular(licencaId: string, dados: AtualizarTitularDto) {
  if ('documento' in dados)
    throw this.erro(HttpStatus.FORBIDDEN, 'DOCUMENTO_TRAVADO',
                    'O documento do titular não pode ser alterado pelo app. Fale com o suporte.')
  const cliente = await findClienteDaLicenca(licencaId)          // o titular da licença
  // PJ: razão social e nome fantasia em `pj`. PF: o nome vai para `pf.nomeCompleto`.
  // O tipo de pessoa (PF ou PJ) não muda aqui.
  await gravarDadosDoTitular(cliente, dados)
  return this.lerTitular(licencaId)
}
```

O `lerTitular` monta o corpo da §4.5 a partir do `Cliente` (`pf` ou `pj`) e de `enderecos`. Se a nuvem não tiver endereço, o `PUT` cria um.

## 7. Critérios de aceite

- **CA-01:** o cadastro responde `202`, com a mesma mensagem, para e-mail novo e para e-mail já cadastrado (com senha certa ou errada), sem `chaveAtivacao`.
- **CA-02:** clicar no link de confirmação cria a licença de teste, e nenhum e-mail leva a chave de ativação.
- **CA-03:** nenhuma resposta de cadastro, reenvio ou login com senha errada revela se o e-mail existe.
- **CA-04:** cinco senhas erradas seguidas bloqueiam o login por 1 minuto.
- **CA-05:** login de quem ainda não confirmou recebe `403 AGUARDANDO_CONFIRMACAO_EMAIL`, sem chave.
- **CA-06:** o reenvio manda o link de confirmação para conta não confirmada e o link de nova senha para conta confirmada.
- **CA-07:** o dono define uma nova senha pelo link, mesmo com uma senha já cadastrada, e a antiga deixa de valer (R-01).
- **CA-08:** `GET /erp/cadastro/titular` devolve os dados do titular; `PUT` atualiza.
- **CA-09:** `PUT /erp/cadastro/titular` com `documento` no corpo recebe `403 DOCUMENTO_TRAVADO` e não altera nada.
- **CA-10:** clientes que já tinham licença antes desta spec continuam entrando normalmente.

Verificável com `npm test` no `apps/server`, sem Postgres (banco fake de `test/apoio/prisma-falso.ts`). Os e-mails são verificados por envio simulado.

## 8. Casos de teste

| ID | Arquivo | Caso | Esperado |
|----|---------|------|----------|
| CT-01 | `cadastro-confirmacao.test.ts` | Cadastro novo | `202`; conta sem licença; e-mail de confirmação enviado, sem chave |
| CT-02 | `cadastro-confirmacao.test.ts` | Cadastro com e-mail existente e senha certa | `202` com a mesma mensagem; nada criado; e-mail "já tem cadastro" |
| CT-03 | `cadastro-confirmacao.test.ts` | Cadastro com e-mail existente e senha errada | `202` com a mesma mensagem; nada criado |
| CT-04 | `cadastro-confirmacao.test.ts` | Confirmação com token válido | Licença de teste criada; `emailConfirmadoEm` gravado; nenhum e-mail com chave |
| CT-05 | `cadastro-confirmacao.test.ts` | Confirmação com token já usado | `400 TOKEN_CONFIRMACAO_INVALIDO` |
| CT-06 | `cadastro-confirmacao.test.ts` | Confirmação com token vencido | `410 TOKEN_CONFIRMACAO_EXPIRADO`, mensagem "Peça um novo link no StartBig" |
| CT-07 | `login-bloqueio.test.ts` | Cinco falhas seguidas | `bloqueadoAte` gravado, 1 minuto |
| CT-08 | `login-bloqueio.test.ts` | Login durante o bloqueio | `429 MUITAS_TENTATIVAS` |
| CT-09 | `login-bloqueio.test.ts` | E-mail inexistente, senha errada e conta sem senha | `401 CREDENCIAIS_INVALIDAS`, mesma resposta nos três |
| CT-10 | `login-bloqueio.test.ts` | Login antes da confirmação | `403 AGUARDANDO_CONFIRMACAO_EMAIL`, sem chave |
| CT-11 | `login-bloqueio.test.ts` | Login depois da confirmação, e login de cliente antigo já com licença | `200` com a chave de ativação (D-23) |
| CT-12 | `reenviar-link.test.ts` | Conta não confirmada | `202`; link de confirmação novo; o anterior deixa de valer |
| CT-13 | `reenviar-link.test.ts` | Conta confirmada | `202`; link de nova senha |
| CT-14 | `reenviar-link.test.ts` | E-mail inexistente | `202` com a mesma mensagem; nada enviado |
| CT-15 | `reenviar-link.test.ts` | Segundo pedido dentro de 60 s | `202`; sem novo envio |
| CT-16 | `reenviar-link.test.ts` | Dono define nova senha pelo link, com senha antiga cadastrada | A nova vale; a antiga deixa de valer (R-01) |
| CT-22 | `reenviar-link.test.ts` | Conta criada pelo administrador define a senha pelo link de primeiro acesso | `emailConfirmadoEm` gravado; o login seguinte não recebe `AGUARDANDO_CONFIRMACAO_EMAIL` |
| CT-17 | `cadastro-titular.test.ts` | `GET` com token válido | `200` com os dados da §4.5 |
| CT-18 | `cadastro-titular.test.ts` | `GET` e `PUT` com token de máquina revogada | `401 LICENCA_HWID_REVOGADO` |
| CT-19 | `cadastro-titular.test.ts` | `PUT` com dados válidos | `200`, cadastro atualizado |
| CT-20 | `cadastro-titular.test.ts` | `PUT` com `documento` no corpo | `403 DOCUMENTO_TRAVADO`, nada alterado |
| CT-21 | `cadastro-titular.test.ts` | `PUT` de titular PF | Nome gravado em `pf.nomeCompleto` |

## 9. Testes existentes que a mudança afeta

- `apps/server/test/licenca/licenca-troca-servidor.test.ts`: o login muda só nos erros. Deve passar.
- `apps/server/test/cripto/segredo-fiscal.test.ts`: não muda.

## 10. Perguntas antes da aprovação

- Nenhuma.
- **Como o app recebe a chave (F2).** Resolvida em 2026-11-18: opção B (D-23), pelo login com e-mail e senha.
- **Trial só depois da confirmação (F13).** Resolvida em 2026-11-18: opção A (D-24).
- **Resposta do cadastro e reenvio.** Resolvida na revisão de conflitos (conflito 14, D-31).

## 11. Observações

- **Impacto no `start-big`:** `registrar_licenca` (em `cadastro.py`) passa a receber `202` em vez de uma licença. O tratamento entra na SPEC-03 §6.5. Enquanto esta spec não for entregue, o cadastro do app continua como hoje.
- **Migração Prisma:** a regra de migração do `start-big` não se aplica ao Prisma, mas o princípio vale: os clientes atuais (com licença) recebem `emailConfirmadoEm`, para não serem barrados (CA-10).
