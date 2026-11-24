# Licença 06 — API: conta e cadastro

| Campo        | Valor |
|--------------|-------|
| Status       | Concluída (2026-11-20) |
| Camada       | Backend da API (NestJS, Prisma) e uma página do painel web (Next.js) |
| Repositório  | Trabalho no fork `dzim-almeida/plataformaADM`; entrega por PR ao `aalan-big/plataformaADM` (D-01) |
| Dependências | SPEC-05 (as rotas do titular usam a recusa de máquina revogada do guard) |
| Bloqueia     | — (a SPEC-03 usa esta spec, mas funciona sem ela pela rede de segurança do `404`) |
| Referência   | [acordo](../../../docs/licenca/ACORDO.md) decisões D-01, D-09, D-22, D-23, D-24, D-28, D-31, D-32, D-34, D-35; [ADR-004](../../../docs/licenca/adr/ADR-004-compatibilidade-api-app-instalado.md); risco R-01; quadro F2, F3, F4, F12, F13, F23 |

> **Revisão 1 (2026-11-18):** dividida da antiga SPEC-06 (vagas foram para a LIC-09); F5 saiu (R-02); entraram o `GET` do titular, o cadastro com resposta única e o `reenviar-link`.

> **Revisão 2 (2026-11-19):** conferência linha a linha no código da plataforma (fork no commit `981fa71`).
> - **Conflito 19 (D-01 revista):** trabalho no fork, entrega por PR.
> - **Conflito 20 (D-32):** a plataforma aplica o schema com `prisma db push`, sem migrações. Os campos novos são opcionais e não há preenchimento de dados: `AGUARDANDO_CONFIRMACAO_EMAIL` só vale para conta **sem licença** com confirmação pendente. Saiu a regra extra do link de primeiro acesso.
> - **Conflito 23 (D-34, ADR-004):** o app novo manda `fluxoConfirmacao: true` e recebe `202`. Sem o campo (versões instaladas), a API faz o mesmo e responde `409 CONFIRMACAO_NECESSARIA` com a instrução, que o app antigo mostra.
> - **Conflito 24 (D-31 revista):** CPF/CNPJ já cadastrado tem o mesmo tratamento do e-mail já cadastrado: resposta igual, aviso ao solicitante e alerta ao titular.
> - **Conflito 25 (D-35):** um campo de token por finalidade, em hash. O link de senha usa `tokenSenha`; o `tokenEmail` fica só para a troca de e-mail.
> - **Conflito 29 (D-28 revista):** as rotas do titular são `GET` e `PUT /erp/usuario/titular`, no controller que já existe.
> - **Conflito 30 (D-31 revista):** caminhos corrigidos. A mudança do cadastro é no serviço, que atende `/erp/auto-cadastro` (usado pelo app) e `/licenca/auto-cadastro`. Os e-mails do painel do administrador ficam fora do escopo.
> - **Revisão 3 (2026-11-19):** mockups aprovados. A página `confirmar-cadastro` segue o quadro 6 de [https://claude.ai/artifact/E5SohwYLXt3pY84pCFwj6z](https://claude.ai/artifact/E5SohwYLXt3pY84pCFwj6z): estado "Conta confirmada" e estado "Este link expirou", no estilo atual das páginas da plataforma (como `primeiro-acesso`).
> - **Documentação (D13, D16 a D20):** erro de validação do Zod sai como `400` com `detalhes`; como as rotas passam pelo guard global; `Cliente.email` não é único; padrão de arquivos do repositório.

> **Revisão 4 (2026-11-20, implementação):** fork `dzim-almeida/plataformaADM`, branch `fix/licenca-seguranca`, commit `9b7ba47`.
> - **Contratação paga do site (decisão do usuário):** `POST /erp/cobranca/contratar` (`erp-contratacao.service.ts`, fora da lista) chamava o mesmo `autoCadastro` e precisa do `licencaId` na hora para o checkout do Stripe. O cadastro de antes virou `criarContaComTrial`, usado **só** pelo site, que continua igual (sem confirmação de e-mail e com o e-mail da chave). As rotas do app seguem esta spec. Registrado no ACORDO §7.
> - **Schema do cadastro:** o `autoCadastroSchema` fica em `dispositivo.service.ts` (não em `packages/schemas`); ganhou `fluxoConfirmacao` opcional.
> - **Cadastro repetido:** e-mail já cadastrado manda o link pelo **estado da conta** (`enviarLinkPeloEstado`, a mesma regra do `reenviar-link`): conta com confirmação pendente recebe um link de confirmação novo; as outras, o aviso "já tem cadastro" com o link de nova senha. Os dois respeitam o limite de um envio por minuto.
> - **Primeiro acesso:** definir a senha pelo link também zera o bloqueio de login (quem tem o link provou ter o e-mail).
> - **Titular PF:** a PF não tem nome fantasia nem telefone no cadastro da nuvem; esses campos do `PUT` são ignorados para PF. Documento formatado (`000.000.000-00`, `00.000.000/0000-00`) no `GET`. Corpo com campo desconhecido (inclusive `tipoPessoa`) → `400`.
> - **Fora da lista:** `apps/server/src/core/seguranca/token-de-link.ts` (hash e geração dos tokens dos links, usado por e-mail, cadastro e login); `apps/web/src/proxy.ts` (a página `/confirmar-cadastro` na lista de rotas públicas, senão o painel mandaria para o login); `erp-contratacao.service.ts` (decisão acima); `licenca-troca-servidor.test.ts` (o caso "senha nunca criada" passa a esperar `401 CREDENCIAIS_INVALIDAS`, como esta spec define).
> - **Testes nas pastas certas:** os casos do login e do reenvio estão em `test/erp/`, e os do cadastro em `test/licenca/`, como a §3.
> - **Verificação:** CT-01 a CT-27 com `node --test`; `npm test` completo (287 passando); `tsc --noEmit` sem erro no servidor e no painel web. **Não verificado:** CA-12 (diff do `db push`), que é conferido no deploy; a página web não foi aberta num navegador.

## 1. Objetivo

Fechar a porta de entrada da licença na API: quem cadastra precisa provar que é dono do e-mail, a chave só vai para quem confirmou e entrou com a senha, e nenhuma resposta revela se um e-mail ou documento é cliente.

## 2. Escopo

**Dentro do escopo**
- Cadastro com resposta única para qualquer caso: e-mail novo, e-mail já cadastrado ou documento já cadastrado (F3, D-31).
- Duas formas de resposta, conforme a versão do app (D-34, ADR-004).
- Confirmação de e-mail antes de criar o trial (F13, D-24). Nenhum e-mail do cadastro pelo app leva a chave de ativação (F2, D-23).
- Login devolve a chave a quem tem licença; conta sem licença com confirmação pendente recebe `AGUARDANDO_CONFIRMACAO_EMAIL` (D-23, D-32).
- Limite progressivo de tentativas de login por e-mail (D-09, F4) e resposta genérica (F12).
- Rota `reenviar-link`, que manda o link certo pelo estado da conta, com limite de frequência (F23, D-31). Ela permite ao dono definir uma nova senha (mitigação do R-01).
- Um campo de token por finalidade, em hash (D-35).
- Leitura e atualização dos dados do titular (`GET` e `PUT /erp/usuario/titular`, D-22, D-28).

**Fora do escopo**
- Sessões, vagas e heartbeat (LIC-09).
- Guard e backups (SPEC-05).
- `tokenSessao` no desconectar (F5): risco aceito R-02.
- E-mails do **painel do administrador** que mandam a chave (criar licença, renovar, cadastrar cliente): ficam como estão (ACORDO §7).
- O bug do `GET /erp/usuario/confirmar-email` (ACORDO §7).

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `apps/server/src/features/dispositivos/dispositivo.service.ts` | alterar | `autoCadastro` (linha ~962): três casos (§6.1), sem criar licença e sem mandar a chave (o envio da linha ~1139 sai). Novo `confirmarCadastro(token)`, que cria a licença de teste. O serviço atende `/erp/auto-cadastro` (`erp-licenca.controller.ts`, usado pelo app) e `/licenca/auto-cadastro` (`dispositivo.controller.ts`). |
| `apps/server/src/features/erp/erp-licenca.controller.ts` | alterar | Nova rota `GET /erp/auto-cadastro/confirmar`. A classe já tem `@Public()`. Responde `202` ou `409` pelo `HttpCode`/exceção da §4.1. |
| `apps/server/src/features/dispositivos/dispositivo.controller.ts` | alterar | A rota gêmea `/licenca/auto-cadastro` passa a responder igual (mesmo serviço). |
| `packages/schemas/src/licenca/` (schema do autocadastro) | alterar | Campo opcional `fluxoConfirmacao: boolean`. |
| `apps/server/src/features/erp/erp-auth.service.ts` | alterar | `login` (linha 48): bloqueio progressivo, `SENHA_NAO_CONFIGURADA` vira `CREDENCIAIS_INVALIDAS`, `AGUARDANDO_CONFIRMACAO_EMAIL`. Novo `reenviarLink(email)`. `primeiroAcesso` (linha ~120) passa a procurar pelo hash em `tokenSenha`. |
| `apps/server/src/features/erp/erp-auth.controller.ts` | alterar | Nova rota `POST /erp/auth/reenviar-link`. A classe já tem `@Public()`. |
| `apps/server/src/features/erp/erp-usuario.controller.ts` | alterar | Novas rotas `GET` e `PUT /erp/usuario/titular`. Herdam o `@Public()` e o `ErpLicencaGuard` da classe. |
| `apps/server/src/features/erp/erp-usuario.service.ts` | alterar | `lerTitular(licencaId)` e `atualizarTitular(licencaId, body)`. |
| `apps/server/src/core/email/email.service.ts` | alterar | Novos: `enviarConfirmacaoCadastro`, `enviarAvisoJaCadastrado`, `enviarAvisoDocumentoJaCadastrado` e `enviarAlertaDocumentoUsado`. `enviarPrimeiroAcesso` (linha 116) passa a gravar o hash em `tokenSenha`, e não mais o token em `tokenEmail`. |
| `apps/web/src/app/confirmar-cadastro/page.tsx` | criar | Página que o link do e-mail abre e que chama a rota de confirmação (mesmo padrão de `apps/web/src/app/primeiro-acesso/page.tsx`). |
| `prisma/schema.prisma` | alterar | Campos novos e opcionais em `Cliente` (§5). Aplicados pelo `db push`. |
| `apps/server/test/licenca/cadastro-confirmacao.test.ts` | criar | Casos CT-01 a CT-08. |
| `apps/server/test/erp/login-bloqueio.test.ts` | criar | Casos CT-09 a CT-14. |
| `apps/server/test/erp/reenviar-link.test.ts` | criar | Casos CT-15 a CT-21. |
| `apps/server/test/erp/usuario-titular.test.ts` | criar | Casos CT-22 a CT-27. |

A pasta `apps/server/test/erp/` é nova. Os testes rodam com `npm test` em `apps/server`. Arquivos novos seguem o padrão do repositório: comentários em PT-BR e o cabeçalho `NOME DO ARQUIVO / MÓDULO / O QUE ESTE ARQUIVO FAZ`.

Testes existentes que precisam continuar passando: `apps/server/test/licenca/licenca-troca-servidor.test.ts` e `apps/server/test/cripto/segredo-fiscal.test.ts`.

## 4. Contrato da API

O `HttpExceptionFilter` responde `{ statusCode, path, message, codigo?, detalhes? }`. Erro de validação do Zod sai como **`400`** com `detalhes` (não `422`).

### 4.1. `POST /erp/auto-cadastro` (muda)

Antes, a resposta trazia `chaveAtivacao` e `token`. Agora nenhum caso cria licença nem devolve a chave. A forma da resposta depende do campo `fluxoConfirmacao` (D-34, ADR-004):

| Pedido | Resposta, em **qualquer** caso da tabela seguinte |
|--------|---------------------------------------------------|
| Com `fluxoConfirmacao: true` (app novo, SPEC-03) | `202` `{ "message": "Enviamos as instruções para o seu e-mail. Se este e-mail já tiver conta, enviamos as instruções para entrar." }` |
| Sem o campo (versões instaladas) | `409` `{ "codigo": "CONFIRMACAO_NECESSARIA", "message": "Enviamos as instruções para o seu e-mail. Depois de confirmar, use a opção 'Já tenho conta' com o seu e-mail e senha." }` |

O `409` existe porque as versões instaladas tratam todo `2xx` como "licença criada" e falham ao ler a resposta. Com um `4xx`, elas mostram a `message` (`backend-fastapi/app/services/licenca/cadastro.py`, `_chamar_api_auto_cadastro`). Os dois caminhos exigem a confirmação: ninguém foge dela omitindo o campo.

| Situação | O que a API faz por trás |
|----------|--------------------------|
| E-mail novo e documento novo | Cria a conta **sem licença** e manda o link de confirmação |
| E-mail já cadastrado | Não cria nada; manda ao e-mail: "Este e-mail já tem cadastro. Entre com a sua senha ou crie uma nova pelo link abaixo" |
| E-mail novo e CPF/CNPJ já cadastrado | Não cria nada; manda ao e-mail informado: "Este CPF/CNPJ já está cadastrado na StartBig. Se a conta é sua, entre com o e-mail dela. Se não lembra qual é, fale com o suporte." E manda ao e-mail da conta dona do documento: "Alguém tentou um cadastro novo com o seu CPF/CNPJ. Se foi você, ignore. Se não foi, fale com o suporte." |

As validações que não revelam conta continuam como hoje, com `400`: CPF/CNPJ inválido e domínio de e-mail inexistente.

### 4.2. `GET /erp/auto-cadastro/confirmar?token=...` (nova)

Confirma o e-mail e cria a licença de teste de 14 dias, contados **a partir da confirmação** (D-24). Não devolve nem envia a chave (D-23). O link do e-mail abre a página `apps/web/.../confirmar-cadastro`, que chama esta rota.

| Status | Corpo | Quando |
|--------|-------|--------|
| 200 | `{ "message": "Conta confirmada. Volte ao StartBig e entre com o seu e-mail e senha." }` | Token válido |
| 400 | `{ "codigo": "TOKEN_CONFIRMACAO_INVALIDO", "message": "Este link não é válido." }` | Token inexistente ou já usado |
| 410 | `{ "codigo": "TOKEN_CONFIRMACAO_EXPIRADO", "message": "Este link expirou. Peça um novo link no StartBig." }` | Token vencido (24 h) |

### 4.3. `POST /erp/auth/login` (muda os erros)

| Situação | Status | `codigo` |
|----------|--------|----------|
| E-mail não existe, senha errada ou conta sem senha | 401 | `CREDENCIAIS_INVALIDAS` (mesma resposta nos três casos, F12). Hoje a conta sem senha responde `400 SENHA_NAO_CONFIGURADA` |
| Muitas tentativas | 429 | `MUITAS_TENTATIVAS` |
| Senha certa, conta **sem nenhuma licença** e com confirmação pendente | 403 | `AGUARDANDO_CONFIRMACAO_EMAIL` |
| Senha certa, licença vencida | 402 | `LICENCA_VENCIDA` (já existe hoje) |
| Senha certa, sem licença e sem confirmação pendente | 400 | `SEM_LICENCA_ATIVA` (já existe hoje) |
| Senha certa, licença utilizável | 200 | Igual a hoje, com `chaveAtivacao` (D-23) |

### 4.4. `POST /erp/auth/reenviar-link` (nova, F23, D-31, D-35)

Corpo `{ "email": "..." }`. Responde **sempre** `202`, com a mesma mensagem, exista ou não o e-mail. Só envia de novo se passaram 60 segundos desde o último envio (`ultimoEnvioLinkEm`).

| Estado da conta | Link enviado |
|-----------------|--------------|
| Não existe | Nenhum (mesma resposta `202`) |
| Com confirmação pendente | Um link de confirmação novo (o anterior deixa de valer) |
| Qualquer outro | Link para definir uma nova senha (`tokenSenha`), mesmo que já exista uma senha (mitigação do R-01) |

O link de senha abre a página que já existe (`apps/web/.../primeiro-acesso`) e usa a rota `POST /erp/auth/primeiro-acesso`, que passa a procurar pelo hash em `tokenSenha`. A mensagem de link expirado muda de "Entre em contato com o suporte" para "Peça um novo link no StartBig". Os links de primeiro acesso já enviados (gravados em `tokenEmail`) deixam de valer; quem tiver um pede outro pelo `reenviar-link`.

### 4.5. `GET /erp/usuario/titular` (nova, D-28)

Devolve os dados da empresa do titular, para pré-preencher o setup do app (SPEC-03 §6.6). Mesma proteção do `GET /erp/usuario/dados` (token da licença).

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

O `GET /erp/usuario/dados` (`{ nome, email, temSenha }`) não muda.

### 4.6. `PUT /erp/usuario/titular` (nova, D-22)

Atualiza os dados da empresa do titular, antes de o setup criar a empresa local. Mesma proteção.

**Corpo:** os campos do `GET`, **sem** `tipoPessoa` e **sem** `documento`.

| Status | `codigo` | Quando |
|--------|----------|--------|
| 200 | — | Dados atualizados; corpo igual ao do `GET` |
| 400 | — | Campo inválido (Zod, com `detalhes`) |
| 401 | `LICENCA_HWID_REVOGADO` | Token de máquina revogada (SPEC-05) |
| 403 | `DOCUMENTO_TRAVADO` | O corpo trouxe `documento` |

## 5. Schemas

```prisma
// prisma/schema.prisma — campos novos em Cliente. Todos opcionais ou com valor padrão,
// para o `db push` aplicar sem aviso e sem preencher dados (D-32).
model Cliente {
  emailConfirmadoEm          DateTime?               // quando o dono confirmou o e-mail (registro)
  falhasLogin                Int        @default(0)  // tentativas erradas seguidas
  bloqueadoAte               DateTime?               // até quando o login fica bloqueado
  tokenConfirmacaoEmail      String?                 // HASH do token do link de confirmação
  tokenConfirmacaoExpiraEm   DateTime?               // validade (24 h)
  tokenSenha                 String?                 // HASH do token do link de primeiro acesso / nova senha
  tokenSenhaExpiraEm         DateTime?               // validade (7 dias, como hoje)
  ultimoEnvioLinkEm          DateTime?               // limite de 60 s do reenvio
}
```

- O `tokenEmail` e o `tokenEmailExpiraEm` **continuam** só para a troca de e-mail (`erp-usuario.service.ts`, `solicitarNovoEmail`), sem mudança.
- **Deploy:** antes do `db push`, conferir o diff como no `docs/deploy-pix-asaas.md` (`npx prisma migrate diff --from-config-datasource --to-schema prisma/schema.prisma --script`). O esperado é **só** `ALTER TABLE "clientes" ADD COLUMN ...` e `ALTER TABLE "clientes_pf" ADD COLUMN ...` (telefone e celular da PF, acrescentados na homologação de 11/2026). Não há script de dados.
- **Risco conhecido:** `Cliente.email` não é único no banco (só tem índice). Dois cadastros simultâneos com o mesmo e-mail podem criar duas contas. Fica registrado, sem mudança nesta série.

## 6. Especificação técnica

### 6.1. Cadastro com resposta única (F3, F13, D-31, D-34)

```typescript
// dispositivo.service.ts — o cadastro nunca diz se o e-mail ou o documento já existem (D-31)
private respostaDoCadastro(fluxoConfirmacao?: boolean) {
  if (fluxoConfirmacao) return { statusCode: 202, message: MSG_CADASTRO_202 }            // app novo
  // Versões instaladas tratam 2xx como "licença criada": recebem um 4xx que elas sabem mostrar (ADR-004).
  throw new ConflictException({ codigo: 'CONFIRMACAO_NECESSARIA', message: MSG_CADASTRO_409 })
}

async autoCadastro(body: unknown) {
  const dados = this.parseBody(autoCadastroSchema, body)
  // ... validações de hoje que não revelam conta: CPF/CNPJ válido, domínio de e-mail ...

  const porEmail = await prisma.cliente.findFirst({ where: { email: dados.email } })
  if (porEmail) {
    await this.emailService.enviarAvisoJaCadastrado(dados.email)                       // só a caixa do dono sabe
    return this.respostaDoCadastro(dados.fluxoConfirmacao)
  }
  const donoDoDocumento = await this.clienteComDocumento(dados.documento)              // CPF em pf, CNPJ em pj
  if (donoDoDocumento) {
    await this.emailService.enviarAvisoDocumentoJaCadastrado(dados.email)               // para quem pediu
    await this.emailService.enviarAlertaDocumentoUsado(donoDoDocumento.email)           // para o titular
    return this.respostaDoCadastro(dados.fluxoConfirmacao)
  }

  // Conta nova: sem licença até a confirmação (D-24).
  const tokenBruto = randomBytes(32).toString('hex')                                    // token do link
  await this.criarClienteSemLicenca(dados, {
    tokenConfirmacaoEmail:    sha256(tokenBruto),                                       // guarda o hash, nunca o token
    tokenConfirmacaoExpiraEm: addHours(new Date(), 24),
    ultimoEnvioLinkEm:        new Date(),
  })
  await this.emailService.enviarConfirmacaoCadastro(dados.email, tokenBruto)
  return this.respostaDoCadastro(dados.fluxoConfirmacao)
}
```

`confirmarCadastro(token)` procura pelo hash, confere a validade, grava `emailConfirmadoEm`, apaga o token e cria a licença de teste com a mesma lógica de plano de hoje (`PLANO_AUTOCADASTRO_ID` ou o plano ativo mais barato). O servidor da licença é registrado no primeiro login com a conta, como já acontece (`assumirServidor`).

### 6.2. Login (D-09, D-23, D-32, F4, F12)

```typescript
// erp-auth.service.ts — bloqueio progressivo, resposta genérica e confirmação pendente
const ESPERAS_MIN = [1, 5, 15]                  // minutos de espera, por nível de falha (D-09)
if (cliente.bloqueadoAte && cliente.bloqueadoAte > new Date())
  throw this.erro(429, 'MUITAS_TENTATIVAS', 'Muitas tentativas. Tente de novo em alguns minutos.')

// Conta sem senha cai no mesmo erro de senha errada (F12).
const senhaOk = !!cliente.senhaHash && await bcrypt.compare(dados.senha, cliente.senhaHash)
if (!senhaOk) {
  const falhas = cliente.falhasLogin + 1
  const nivel = Math.min(falhas - 5, ESPERAS_MIN.length - 1)   // 5ª falha = 1 min, 6ª = 5 min, 7ª em diante = 15 min
  await prisma.cliente.update({ where: { id: cliente.id }, data: {
    falhasLogin: falhas,
    bloqueadoAte: falhas >= 5 ? addMinutes(new Date(), ESPERAS_MIN[nivel]) : null } })
  throw this.erro(401, 'CREDENCIAIS_INVALIDAS', 'E-mail ou senha incorretos.')
}
await prisma.cliente.update({ where: { id: cliente.id }, data: { falhasLogin: 0, bloqueadoAte: null } })

// Conta sem NENHUMA licença e com confirmação pendente (D-32). Conta com licença nunca
// cai aqui, mesmo sem `emailConfirmadoEm`: os clientes de hoje não precisam de nada.
const temAlgumaLicenca = await prisma.licenca.count({ where: { clienteId: cliente.id } }) > 0
if (!temAlgumaLicenca && cliente.tokenConfirmacaoEmail)
  throw this.erro(403, 'AGUARDANDO_CONFIRMACAO_EMAIL', 'Confirme o link enviado ao seu e-mail antes de entrar.')

// ... daqui para baixo, igual a hoje (licença utilizável, LICENCA_VENCIDA, SEM_LICENCA_ATIVA) ...
```

E-mail inexistente responde `CREDENCIAIS_INVALIDAS` sem gravar nada.

### 6.3. Reenviar link e primeiro acesso (F23, D-31, D-35, R-01)

```typescript
// erp-auth.service.ts — um botão só no app; a API escolhe o link pelo estado da conta
async reenviarLink(body: unknown) {
  const { email } = this.parseBody(reenviarLinkSchema, body)
  const resposta = { statusCode: 202, message: 'Se este e-mail tiver conta, enviamos um link.' }
  const cliente = await prisma.cliente.findFirst({ where: { email } })
  if (!cliente) return resposta                                              // não revela que não existe
  if (cliente.ultimoEnvioLinkEm && Date.now() - cliente.ultimoEnvioLinkEm.getTime() < 60_000)
    return resposta                                                          // limite de 60 s
  if (cliente.tokenConfirmacaoEmail)
    await this.enviarNovoLinkDeConfirmacao(cliente)                          // o anterior deixa de valer
  else
    await this.emailService.enviarPrimeiroAcesso({ clienteId: cliente.id, email, nomeCliente: '...' })  // grava tokenSenha
  await prisma.cliente.update({ where: { id: cliente.id }, data: { ultimoEnvioLinkEm: new Date() } })
  return resposta
}
```

`primeiroAcesso` procura **só** por `tokenSenha` (comparando o hash), nunca por `tokenEmail`. Assim um token de troca de e-mail não define senha, e pedir um link de senha não apaga uma troca de e-mail pendente.

### 6.4. Leitura e atualização do titular (D-22, D-28)

```typescript
// erp-usuario.service.ts — o documento é só leitura: nunca muda por este caminho (D-22)
async atualizarTitular(licencaId: string, body: unknown) {
  if (body && typeof body === 'object' && 'documento' in body)
    throw this.erro(403, 'DOCUMENTO_TRAVADO',
                    'O documento do titular não pode ser alterado pelo app. Fale com o suporte.')
  const dados = this.parseBody(atualizarTitularSchema, body)               // Zod: 400 com detalhes
  const cliente = await this.clienteDaLicenca(licencaId)                   // o titular da licença
  // PJ: razão social e nome fantasia em `pj`. PF: o nome vai para `pf.nomeCompleto`.
  // O tipo de pessoa (PF ou PJ) não muda aqui. Sem endereço na nuvem, cria um.
  await this.gravarDadosDoTitular(cliente, dados)
  return this.lerTitular(licencaId)
}
```

## 7. Critérios de aceite

- **CA-01:** o cadastro não cria licença nem devolve a chave, em nenhum caso.
- **CA-02:** o app novo recebe `202`; uma versão instalada recebe `409 CONFIRMACAO_NECESSARIA` com a instrução; nos dois casos a confirmação é exigida.
- **CA-03:** nenhuma resposta de cadastro, reenvio ou login com senha errada revela se o e-mail ou o documento existe.
- **CA-04:** clicar no link de confirmação cria a licença de teste, e nenhum e-mail do cadastro leva a chave.
- **CA-05:** cinco senhas erradas seguidas bloqueiam o login por 1 minuto.
- **CA-06:** login de conta sem licença com confirmação pendente recebe `403 AGUARDANDO_CONFIRMACAO_EMAIL`, sem chave.
- **CA-07:** o reenvio manda o link de confirmação para conta pendente e o link de nova senha para as outras.
- **CA-08:** o dono define uma nova senha pelo link, mesmo com uma senha já cadastrada, e a antiga deixa de valer (R-01).
- **CA-09:** um token de troca de e-mail não define senha, e pedir um link de senha não cancela uma troca de e-mail pendente.
- **CA-10:** clientes que já tinham licença continuam entrando normalmente, sem nenhum preenchimento de dados.
- **CA-11:** `GET /erp/usuario/titular` devolve os dados; `PUT` atualiza; `PUT` com `documento` recebe `403 DOCUMENTO_TRAVADO`.
- **CA-12:** o diff do `db push` mostra só `ADD COLUMN` em `clientes`.

Verificável com `npm test` em `apps/server` (banco falso de `test/apoio/prisma-falso.ts`, e-mails simulados). O CA-12 é conferido no deploy.

## 8. Casos de teste

| ID | Arquivo | Caso | Esperado |
|----|---------|------|----------|
| CT-01 | `cadastro-confirmacao.test.ts` | Cadastro novo com `fluxoConfirmacao: true` | `202`; conta sem licença; e-mail de confirmação, sem chave |
| CT-02 | `cadastro-confirmacao.test.ts` | Cadastro novo sem `fluxoConfirmacao` | `409 CONFIRMACAO_NECESSARIA`; conta sem licença; e-mail enviado |
| CT-03 | `cadastro-confirmacao.test.ts` | E-mail já cadastrado | Mesma resposta; nada criado; e-mail "já tem cadastro" |
| CT-04 | `cadastro-confirmacao.test.ts` | E-mail novo com CPF já cadastrado | Mesma resposta; nada criado; aviso ao solicitante e alerta ao titular |
| CT-05 | `cadastro-confirmacao.test.ts` | E-mail novo com CNPJ já cadastrado | Igual ao CT-04 |
| CT-06 | `cadastro-confirmacao.test.ts` | Confirmação com token válido | Licença de teste de 14 dias a partir de agora; `emailConfirmadoEm` gravado; nenhum e-mail com chave |
| CT-07 | `cadastro-confirmacao.test.ts` | Confirmação com token já usado | `400 TOKEN_CONFIRMACAO_INVALIDO` |
| CT-08 | `cadastro-confirmacao.test.ts` | Confirmação com token vencido | `410 TOKEN_CONFIRMACAO_EXPIRADO` |
| CT-09 | `login-bloqueio.test.ts` | Cinco falhas seguidas | `bloqueadoAte` gravado, 1 minuto |
| CT-10 | `login-bloqueio.test.ts` | Login durante o bloqueio | `429 MUITAS_TENTATIVAS` |
| CT-11 | `login-bloqueio.test.ts` | E-mail inexistente, senha errada e conta sem senha | `401 CREDENCIAIS_INVALIDAS`, mesma resposta nos três |
| CT-12 | `login-bloqueio.test.ts` | Login de conta sem licença com confirmação pendente | `403 AGUARDANDO_CONFIRMACAO_EMAIL`, sem chave |
| CT-13 | `login-bloqueio.test.ts` | Login depois da confirmação | `200` com a chave (D-23) |
| CT-14 | `login-bloqueio.test.ts` | Cliente antigo, com licença e sem `emailConfirmadoEm` | `200` com a chave |
| CT-15 | `reenviar-link.test.ts` | Conta com confirmação pendente | `202`; link de confirmação novo; o anterior deixa de valer |
| CT-16 | `reenviar-link.test.ts` | Conta confirmada | `202`; link de nova senha gravado em `tokenSenha` (hash) |
| CT-17 | `reenviar-link.test.ts` | E-mail inexistente | `202` com a mesma mensagem; nada enviado |
| CT-18 | `reenviar-link.test.ts` | Segundo pedido dentro de 60 s | `202`; sem novo envio |
| CT-19 | `reenviar-link.test.ts` | Dono define nova senha pelo link, com senha antiga | A nova vale; a antiga deixa de valer (R-01) |
| CT-20 | `reenviar-link.test.ts` | Token de troca de e-mail (`tokenEmail`) na rota `primeiro-acesso` | Recusado |
| CT-21 | `reenviar-link.test.ts` | Pedir link de senha com uma troca de e-mail pendente | `tokenEmail` e `emailPendente` continuam como estavam |
| CT-22 | `usuario-titular.test.ts` | `GET /erp/usuario/titular` com token válido | `200` com os dados da §4.5 |
| CT-23 | `usuario-titular.test.ts` | `GET` e `PUT` com token de máquina revogada | `401 LICENCA_HWID_REVOGADO` |
| CT-24 | `usuario-titular.test.ts` | `PUT` com dados válidos | `200`, cadastro atualizado |
| CT-25 | `usuario-titular.test.ts` | `PUT` com `documento` no corpo | `403 DOCUMENTO_TRAVADO`, nada alterado |
| CT-26 | `usuario-titular.test.ts` | `PUT` de titular PF | Nome gravado em `pf.nomeCompleto` |
| CT-27 | `usuario-titular.test.ts` | `PUT` com campo inválido | `400` com `detalhes` |

## 9. Testes existentes que a mudança afeta

- `apps/server/test/licenca/licenca-troca-servidor.test.ts`: o login muda só nos erros. Deve passar.
- `apps/server/test/cripto/segredo-fiscal.test.ts`: não muda.

## 10. Perguntas antes da aprovação

- Nenhuma.
- **Como o app recebe a chave (F2).** Resolvida: D-23, pelo login.
- **Trial só depois da confirmação (F13).** Resolvida: D-24.
- **Resposta do cadastro e reenvio.** Resolvida: D-31 (conflitos 14, 24 e 30) e D-34 (conflito 23).

## 11. Observações

- **Entrega:** branch no fork `dzim-almeida/plataformaADM`, PR para o `aalan-big/plataformaADM`, deploy com a conferência do diff da §5.
- **Impacto no `start-big`:** o app novo manda `fluxoConfirmacao: true` e trata o `202` (SPEC-03 §6.5). As versões instaladas recebem o `409` com a instrução e usam o "Já tenho conta", que elas já têm. Por isso esta spec pode ir para produção a qualquer momento (ADR-004).
- **E-mails do painel:** `criarLicenca` (`dispositivo.service.ts:~444`), `renovar` (`~656`) e o cadastro de cliente pelo painel (`cliente.service.ts:187`) continuam mandando a chave. O app não usa a chave digitada. Ficam registrados no ACORDO §7 para um PR próprio da plataforma.
