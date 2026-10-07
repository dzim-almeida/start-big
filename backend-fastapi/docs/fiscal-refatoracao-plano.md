# Plano: refatorar o fiscal sem derrubar quem já emite

> Escrito em 06/10/2026, depois da primeira NF-e real do Celso (CNPJ
> 58.348.941/0001-09), que levou **5 rejeições**, cadastro manual no painel da
> Focus e token colado à mão no admin. Tudo aqui foi conferido no código dos dois
> lados (ERP `start-big-master` e plataforma `Plataforma_admin/meu-projeto-fullstack`)
> e, onde dava, no servidor (`curl` em `api.startbig.com.br`).

---

## Resumo em uma página

O **motor** de emissão funciona: a nota do Celso saiu. O que está ruim é o que
fica **em volta** dele:

1. **Ativar uma empresa** exige 4 passos manuais em 3 lugares (painel da Focus,
   admin, ERP) numa ordem que ninguém avisa. Se a ordem sai errada, o
   certificado fica "validado só localmente" e o token tem que ser colado à mão.
2. **A empresa nasce em homologação** (`ambiente @default(2)`), quando o
   normal agora é produção.
3. **O sistema deixa salvar cadastro contraditório** (Natureza MEI + Regime
   Simples), e a SEFAZ é quem descobre, gastando número.
4. **O diagnóstico procura palavras soltas na mensagem** e errou as 3
   rejeições de hoje (481, 539 e 305).
5. **Cada tentativa gasta um número novo**, e quem já emitia por outro sistema
   colide com a numeração antiga (539).
6. **A plataforma não tem nenhum teste automatizado.** Hoje, qualquer
   refatoração lá é feita no escuro.

O plano tem **6 fases**. A **ordem** é o que protege as lojas em produção:
primeiro a rede de segurança (testes e censo), depois as correções pequenas que
teriam evitado o dia de hoje, depois a ativação automática e, **por último**, a
reorganização dos arquivos grandes. Cada fase sobe sozinha e é aditiva: quem já
emite continua emitindo igual.

| Fase | O quê | Custo | Risco p/ quem já emite |
|---|---|---|---|
| **F0** | Rede de segurança: testes na plataforma, censo das fichas, fotografia dos payloads | 2–3 d | nenhum (não muda comportamento) |
| **F1** | Correções rápidas: produção como padrão, diagnóstico por código, trava MEI, aviso de PJ sem IE, mensagem do 501 | 2 d | baixo |
| **F2** | **Ativar emissão** num botão: a plataforma cria/atualiza a empresa na Focus e guarda os tokens sozinha | 4–5 d | médio (mexe no cadastro da Focus) |
| **F3** | Numeração: "já emitia antes?", tratar 539, rever o "número novo a cada tentativa" | 2–3 d | médio (mexe em numeração) |
| **F4** | Painel de saúde fiscal no admin, por cliente | 2 d | nenhum (só leitura) |
| **F5** | Reorganizar os arquivos grandes (ERP e plataforma) **sem mudar comportamento** | 4–6 d | controlado pelos testes da F0 |

---

## 0. O que "pronto" significa

| # | Critério de aceite | Hoje |
|---|---|---|
| R1 | Cliente novo emite a primeira NF-e **sem ninguém abrir o painel da Focus** | precisa cadastrar a empresa lá à mão |
| R2 | Ninguém **copia token** de um painel para outro | token colado à mão quando o certificado não passa |
| R3 | Empresa nova nasce em **produção**. Homologação só por escolha explícita, com rótulo "teste" | nasce em homologação |
| R4 | Cadastro contraditório (MEI × Simples, IE × indicador) é **barrado antes** de reservar número | vai para a SEFAZ e volta 481 |
| R5 | Toda rejeição comum mostra **a causa certa e onde corrigir**, pelo código `cStat` | 481 → "cadastre o certificado"; 539 → "ajuste o CSOSN" |
| R6 | Quem já emitia por outro sistema informa **série e último número** na ativação | começa do 1 e colide (539) |
| R7 | O suporte vê no admin, por cliente, **o que falta** para emitir (empresa na Focus, certificado, habilitação, token, CSC, ambiente) | precisa abrir a Focus e adivinhar |
| R8 | **As lojas que já emitem não percebem nada** em nenhuma fase, a não ser a mensagem melhor | cláusula de não-regressão |

**R8 manda em tudo.** Toda mudança é aditiva, tem comportamento definido quando
o outro lado ainda não subiu, e passa pela loja canário com backup antes de ir
para as outras.

---

## 1. O incidente de hoje, rejeição por rejeição

| Tentativa | cStat | O que a SEFAZ disse | Causa real | O que o sistema disse | Que fase evita |
|---|---|---|---|---|---|
| 1, 2, 3 | 481 | Regime tributário diverge do cadastro | Natureza **MEI** + Regime **1 - Simples** no cadastro. O CRT sai do regime ([helpers.py:130-145](../app/services/fiscal/helpers.py#L130-L145)) e a natureza é ignorada | "Cadastre o certificado e as séries" (casou com a palavra "emitente", [fiscalDiagnostic.ts:72-77](../../frontend/src/modules/fiscal/utils/fiscalDiagnostic.ts#L72-L77)) | F1 (trava + diagnóstico) |
| 4 | 539 | Duplicidade com diferença na chave | Série 2 nº 4 **já emitida em 09/2026 por outro sistema** (a chave devolvida tem AAMM = 2609) | "Ajuste o CSOSN" | F1 (diagnóstico) + F3 (numeração) |
| 5 | 305 | Destinatário bloqueado na UF | CNPJ da Lojinha da Fé bloqueado no estado dela. Ela estava sem IE no cadastro e saiu como não contribuinte ([payload_builder.py:172-174](../app/services/fiscal/payload_builder.py#L172-L174)) | "Revise os dados da venda" | F1 (diagnóstico + aviso de PJ sem IE) |
| — | — | — | O certificado ficou "Validado, não enviado" porque a empresa ainda não existia na Focus quando foi enviado | "A plataforma ainda não recebe certificado" (a rota existe: `POST /erp/fiscal/certificado` responde 401 sem token) | F1 (mensagem) + F2 (ativação) |

A venda #1 esgotou as 5 reemissões e a nota saiu numa venda nova, no CPF da
compradora. Ficaram para trás: números da série 2 e da série 1 cuja situação
(usados por fora ou só rejeitados) só o contador sabe dizer. Isso é a F3.

---

## 2. Como funciona hoje (conferido no código)

```
 ERP (loja)                      Plataforma (VPS)                     Focus NFe → SEFAZ
 ─────────                       ────────────────                     ─────────────────
 Dados da Empresa ──(payload)──► /erp/fiscal/nfe/emitir ──(traduz)──► /v2/nfe?ref=…
   CRT, IE, endereço             token da EMPRESA (focusEmpresaToken)  regime_tributario_emitente
                                 ambiente da FICHA (1|2)
 Centro Fiscal ──(.pfx)───────►  /erp/fiscal/certificado
                                   1. acha empresa na Focus pelo CNPJ   GET  /v2/empresas?cnpj=
                                      (NÃO cria se faltar → 501)
                                   2. grava certificado + habilita      PUT  /v2/empresas/{id}
                                   3. guarda token do ambiente da ficha
 Admin (painel) ─────────────►   ficha EmpresaFiscalConfig
                                   cnpj, razão, IE, ambiente (padrão 2),
                                   focusEmpresaId, token (texto puro)
```

**Pontos que o desenho atual deixa soltos:**

| # | Ponto | Onde |
|---|---|---|
| A1 | A plataforma **não cria** a empresa na Focus. Escolha deliberada, porque a ficha não tem endereço nem regime | `fiscal.service.ts`, comentário em `prepararCadastroNaFocus` |
| A2 | Os dados do emitente vivem em **dois lugares**: o ERP (completo) e a ficha do admin (CNPJ, razão, IE), digitados por pessoas diferentes | `cliente.service.ts:340-423` |
| A3 | O token só é gravado sozinho quando o **certificado** passa. Se ele não passa, só resta colar à mão | `enviarCertificado` |
| A4 | A plataforma guarda **só o token do ambiente atual**. Trocar homologação → produção exige reenviar o certificado ou colar o outro token | idem |
| A5 | O token fica **em texto puro** no banco (o próprio schema avisa) | `schema.prisma:616` |
| A6 | Ambiente padrão = homologação, no banco e na tela do admin | `schema.prisma:609`, `ModalPerfilCliente.tsx:1062,1074` |
| A7 | O ERP trata 404/405/501 como "a plataforma ainda não recebe certificado". Isso foi verdade em setembro; hoje o 501 quer dizer "empresa sem cadastro na Focus" ou "falta token de parceiro no `.env`" | `client_startbig.py:402`, `FiscalConfiguracoesView.vue:200` |
| A8 | O status `VALIDADO_LOCAL` não sai sozinho, nem depois de o certificado ser posto à mão na Focus. A tela continua dizendo "a emissão não vai funcionar" | `empresa.py:517` |
| A9 | O diagnóstico é por **palavra-chave**, não por `cStat` | `fiscalDiagnostic.ts` |
| A10 | O gate não confere Natureza × Regime nem PJ sem IE | `validators.py:36`, `:173` |
| A11 | Cada reemissão **reserva número novo**. O comentário diz que reusar dá 204, e isso precisa ser provado (§F3) | `reemissao.py:14,59` |
| A12 | **Zero teste automatizado** na plataforma. Não há `*.spec.ts`/`*.test.ts` em `apps/` nem script `test` | `package.json` |
| A13 | Arquivos grandes, perto do teto do PyArmor: `emissao.py` 1415 linhas, `endpoints/fiscal.py` 1321, `payload_builder.py` 1120; na plataforma, `fiscal.service.ts` 1213 | — |

---

## 3. Princípios (valem para todas as fases)

1. **O ERP é a fonte da verdade do emitente** (razão, CNPJ, IE, regime,
   endereço). A plataforma guarda **credenciais** (id e tokens da Focus) e
   **política** (ambiente, cota). Ninguém digita o mesmo dado em dois lugares.
2. **Aditivo e tolerante à ordem de deploy.** Loja e plataforma não sobem
   juntas. Toda rota nova tem comportamento definido quando o outro lado é
   antigo (como já é hoje com o 404/501).
3. **Nada muda o payload da nota sem teste de fotografia** (F0.3). O payload é
   o que a SEFAZ autoriza; se ele mudar sem querer, quebra nota em produção.
4. **Plataforma primeiro, ERP depois**, quando a mudança atravessa os dois. A
   plataforma atualiza todo mundo de uma vez; o ERP depende de instalador em
   cada loja.
5. **Canário com backup** a cada fase que toca emissão ou numeração: uma loja,
   uma nota real de valor baixo, cancelamento dentro da janela, só então as
   demais.
6. **Arquivo novo para código novo** no ERP (teto de bytecode do PyArmor).

---

## 4. Fases

### F0 — Rede de segurança (2–3 dias, sem mudança de comportamento)

| # | O quê | Onde | Por quê |
|---|---|---|---|
| F0.1 | Montar o runner de testes na plataforma (vitest ou jest) e cobrir **o que encosta na Focus**: `focus-payload.mapper.ts` (tradução aninhado → plano), `FocusNfeService` com `fetch` falso, `prepararCadastroNaFocus` (acha, não acha, 401), `enviarCertificado` (token do ambiente certo), `emitir` (idempotência, cota) | `apps/server` | Hoje qualquer mudança lá é feita no escuro (A12) |
| F0.2 | **Censo** read-only das fichas em produção: por cliente, ambiente, tem token?, tem `focusEmpresaId`?, `certificadoStatus`, vencimento, `cscConfigurado`, última nota autorizada | script em `scripts/`, roda na VPS | Saber quem está meio configurado **antes** de mudar a regra |
| F0.3 | **Fotografia do payload** no ERP: para 6–8 cenários (venda PF/PJ, interestadual, MEI, Simples, Normal, OS, NFC-e, devolução), gravar o JSON gerado hoje e testar que continua igual | `test/services/fiscal/` | É o que permite a F5 mexer nos arquivos grandes sem medo |
| F0.4 | Ler no log da VPS **por que** o certificado do Celso voltou 501: `nenhuma empresa de CNPJ` (era a ordem dos passos) ou `FOCUS_NFE_PARTNER_TOKEN ausente` (falta variável) | `~/.pm2/logs/api-out.log` / `api-error.log` | Decide se a F2 precisa também mexer no `.env` |

**Pronto quando:** a suíte da plataforma roda com `npm test`, o censo foi lido,
e o ERP tem as fotografias passando.

**Entrega (06/10/2026):**
- **F0.1 — FEITA** (plataforma, branch `feat/fiscal-ativacao`, `0c3225f`): 60
  testes com `node --test` + `tsx`, **sem dependência nova**. O banco falso entra
  por `globalThis.prisma` (o `@startbig/database` o reaproveita), e o setup
  apaga o `DATABASE_URL` para nunca encostar num Postgres real. A Focus é
  simulada pelo `fetch` ou por classe falsa. Prova de que pegam erro: trocar
  `regime_tributario_emitente` no tradutor derruba 2 testes. Rodar:
  `cd apps/server && npm test`.
- **F0.2 — FEITA** (`34c7f6b`): `npm run fiscal:censo` na VPS. Só leitura, não
  fala com a Focus e do token mostra só "sim/não". **Falta o Alan rodar e ler.**
- **F0.3 — FEITA** (ERP): `test/services/fiscal/test_payload_fotografias.py`, 5
  cenários em `docs/payloads/fotografias/` (MEI → PF de outro estado, que é o
  caso do Celso; Simples → PJ contribuinte interestadual; PJ sem IE; NFC-e com e
  sem CPF). Somam-se aos 2 exemplos que já existiam em
  `test_payload_exemplo_auditoria.py`. Devolução e NF-e da OS ficam cobertas
  pelos testes que já existem (`test_emissao_devolucao.py`, `test_nfe_da_os.py`).
- **F0.4 — FEITA** (ver §7.1).

### F1 — Correções rápidas (2 dias)

Cada item é pequeno e teria evitado parte do dia de hoje.

| # | O quê | Lado | Detalhe |
|---|---|---|---|
| F1.1 | **Produção como padrão** | plataforma | `ambiente @default(1)` (migration Prisma), tela do admin abre em 1, opção 2 rotulada **"Homologação (teste — sem valor fiscal)"**. Fichas existentes **não mudam** |
| F1.2 | **Diagnóstico por `cStat`** | ERP (front) | Tabela de códigos antes das palavras-chave. Mínimo: 204, 225, 232, 233, 301, 302, 305, 481, 539, 778 e os de certificado (280–286). A 539 extrai a chave e mostra *"o nº X da série Y já foi emitido em mm/aaaa, provavelmente por outro sistema"*. A palavra-chave fica só como último recurso |
| F1.3 | **Trava MEI** | ERP | No gate (`verificar_emitente`): natureza MEI com regime ≠ 4, ou regime 4 com natureza ≠ MEI → pendência bloqueante *antes* de reservar número. Na tela de Dados Fiscais, o mesmo aviso ao salvar. **Não** corrigir sozinho: em loja já em produção, mudar o CRT calado muda a tributação |
| F1.4 | **Aviso de PJ sem IE** | ERP | Cliente com CNPJ e IE vazia: aviso (não bloqueio) *"vai sair como não contribuinte; se ele tem IE, cadastre"*. Bloquear quebraria quem vende para PJ não contribuinte de verdade |
| F1.5 | **Mensagem do 501** | plataforma + ERP | A plataforma já devolve `codigo` (`EMPRESA_SEM_CADASTRO_NA_EMISSORA`, `PLATAFORMA_SEM_TOKEN_DA_CONTA`, e no 404 `SEM_CONFIGURACAO_FISCAL`, o caso do Celso). O ERP passa a ler o `codigo` e dizer a coisa certa. A plataforma passa a logar o 404 de ficha ausente, que hoje não deixa rastro. Sem código (plataforma antiga) → mensagem de hoje |
| F1.6 | **Reconferir `VALIDADO_LOCAL`** | ERP | O card do certificado ganha "Conferir de novo", que chama `/erp/fiscal/config` e, se a plataforma disser que o certificado está ativo, troca para `CONECTADO_NUVEM`. Resolve o caso do Celso sem reenviar o `.pfx` |

**Pronto quando:** refazer o cadastro do Celso do zero, num CNPJ de teste,
mostra a trava MEI antes de emitir, e cada rejeição de hoje aparece com a causa
certa.

**Entrega (06/10/2026)** — branch `feat/fiscal-ativacao` nos dois repositórios:

| Item | Onde | O que ficou |
|---|---|---|
| F1.1 | plataforma `18bc936` | `ambiente @default(1)`; painel abre a ficha nova em Produção e rotula Homologação "teste — sem valor fiscal". Fichas existentes intactas |
| F1.2 | ERP `bd533fc` | `fiscalDiagnosticCodigos.ts`: tabela por cStat **antes** das palavras-chave (204, 207, 208, 209, 213, 237, 280–286, 301, 302, 305, 481, 539). A 539 lê a chave e diz "nº 4 da série 2, emitido em 09/2026". Achados no caminho: 207/209 eram tratados como erro do cliente (são do emitente) e 778 como IE (é NCM). "Emitente" na mensagem só vira configuração quando **não** há cStat. Ação nova `CENTRO_FISCAL` |
| F1.3 | ERP `bd533fc` | **Virou aviso, não trava** — ver abaixo. `services/fiscal/avisos.py`; aparece em Dados Fiscais (na hora), no painel do Centro Fiscal e no modal de emissão |
| F1.4 | ERP `bd533fc` | PJ sem IE: aviso na prévia da NF-e (`avisos` novo em `EmissaoPreviewResponse`, opcional) |
| F1.5 | plataforma `18bc936` + ERP | Plataforma loga o 404 sem ficha. ERP lê o `codigo` (`SEM_CONFIGURACAO_FISCAL`, `EMPRESA_SEM_CADASTRO_NA_EMISSORA`, `PLATAFORMA_SEM_TOKEN_DA_CONTA`) e diz o motivo certo. **Achado:** o endpoint de upload respondia "enviado e configurado com sucesso" SEMPRE, e o modal ficava verde mesmo com o certificado parado aqui — agora devolve `enviado` e o modal mostra o motivo em amarelo |
| F1.6 | ERP | `POST /fiscal/certificado/reconferir` + botão "Conferir de novo" no aviso de "Validado, não enviado". Só promove a `CONECTADO_NUVEM` quando a plataforma afirma certificado ATIVO **e** token; "não sei" nunca muda nada |

**Por que a trava MEI virou aviso:** a contradição tem um caso legítimo — a
empresa **deixou** de ser MEI e o cadastro ficou com a natureza antiga. Aí o
regime (que é o que vai na nota) está certo e a nota sai; travar pararia uma
loja que emite bem, contra o R8. O aviso aparece em três lugares, inclusive no
modal de emissão, antes de gastar número.

**Para chegar às lojas:** deploy da plataforma (`npm run deploy` na VPS — o
`db:push` só troca o DEFAULT da coluna) e, no ERP, `npm run build:sidecar` +
instalador desta branch. Os dois lados funcionam um sem o outro (ERP antigo
ignora o `codigo`; plataforma antiga não manda `codigo` e o ERP novo cai na
frase genérica).

### F2 — "Ativar emissão" num botão (4–5 dias) ← o coração do plano

**Hoje:** criar na Focus → ficha no admin → certificado no ERP → (às vezes)
colar token.
**Depois:** o admin libera o módulo NF-e na licença; o lojista (ou o suporte)
abre o Centro Fiscal e clica **Ativar emissão**.

```
ERP: Ativar emissão
  envia { emitente completo (razão, CNPJ, IE, IM, regime, endereço, e-mail),
          .pfx + senha,
          numeração anterior (F3) }
        │
        ▼
Plataforma: POST /erp/fiscal/ativacao   (idempotente)
  1. CNPJ do emitente == CNPJ da licença/ficha? senão 422 (nunca grava em empresa alheia)
  2. Focus GET /v2/empresas?cnpj=
       existe  → PUT  /v2/empresas/{id}  (certificado, habilita_nfe/nfce, dados)
       não existe → POST /v2/empresas?dry_run=1  (valida sem criar)
                    → POST /v2/empresas         (cria)
  3. grava focusEmpresaId + token_producao + token_homologacao (cifrados)
  4. responde { status por item: empresa, certificado, habilitação, token, CSC }
        │
        ▼
ERP: mostra o checklist verde/amarelo, item por item
```

| # | O quê | Detalhe |
|---|---|---|
| F2.1 | Rota `POST /erp/fiscal/ativacao` | Junta o que hoje é `certificado` + criação. A rota `certificado` continua viva (ERP antigo) |
| F2.2 | Criar empresa na Focus | Com `dry_run=1` antes. A objeção do comentário atual ("a ficha não tem endereço nem regime") cai, porque agora o ERP manda os dois |
| F2.3 | **Guardar os dois tokens** | Trocar homologação ↔ produção vira só mudar o `ambiente` da ficha. Some o A4 |
| F2.4 | **Cifrar os tokens** em repouso | Chave no `.env`; migration que cifra os existentes. Leitura tolera o texto puro durante a transição |
| F2.5 | Ficha nasce sozinha | Ao liberar NF-e/NFC-e na licença, cria a ficha com o CNPJ da licença e **ambiente 1**. O admin só edita se quiser (homologação, cota) |
| F2.6 | Sincronizar ao mudar o cadastro | Salvar Dados Fiscais no ERP com emissão ativa → `PUT` na Focus (regime, IE, endereço). Assim o cadastro da Focus não envelhece |
| F2.7 | Campos manuais viram "avançado" | `focusEmpresaId` e token continuam no admin, atrás de "suporte avançado", para emergência |

**Antes de codar:** confirmar que a conta da Focus permite **criar** empresa
pela API com o token de parceiro (plano de revenda). O `GET`/`PUT` já
funcionam; o `POST` nunca foi chamado. Fazer **um `dry_run`** na VPS com o CNPJ
de teste.

**Canário:** um CNPJ novo de teste em homologação, depois um cliente novo de
verdade em produção. As fichas que já emitem só passam pela ativação se alguém
clicar. Nada migra sozinho.

**Entrega (06/10/2026)** — `dry_run` feito antes na VPS: **422** (conta pode
criar empresa; a Focus recusou só os dados do teste — "Município inválido").

| Item | Onde | O que ficou |
|---|---|---|
| F2.1 | plataforma `d2b9a46` | `POST /erp/fiscal/ativacao` (`ativarEmissao`). Recebe o MESMO `emitente{}` das notas + contato + certificado |
| F2.2 | plataforma | Acha a empresa pelo id da ficha ou pelo CNPJ; se não existe, **cria** (`criarEmpresa`, `POST /v2/empresas`). **Sem `dry_run`** antes: um POST recusado por validação não cria nada, então o `dry_run` só dobraria a chamada. Antes de criar, `camposFaltandoParaCriar` devolve a lista inteira do que falta (a Focus recusa um campo por vez) |
| F2.3 | plataforma | Guarda `focusTokenProducao` e `focusTokenHomologacao`. Trocar o ambiente na ficha passa a bastar |
| F2.4 | plataforma | Cifra AES-256-GCM com `FISCAL_TOKENS_KEY` (`common/cripto/segredo-fiscal.ts`). **Sem a chave, grava em texto como antes** — não derruba ninguém. Precedência na emissão: o token colado à mão (`focusEmpresaToken`) vence; sem ele, o cifrado do ambiente. Fichas antigas não mudam |
| F2.5 | plataforma | **Mudou:** a ficha só nasce sozinha se a licença trouxer NFE/NFCE **explícito** na claim. Motivo: criar empresa na Focus pode custar, e a claim vazia (licença antiga, `ENTITLEMENTS_ENFORCE` desligado) liberaria qualquer ERP. Sem isso, o admin cria a ficha com o CNPJ — o resto é automático |
| ERP | ERP | O upload do certificado chama `ativar_emissao` com o emitente (`services/fiscal/ativacao.py`). Plataforma antiga (404 sem `codigo`) → cai sozinho na rota antiga de certificado |
| F2.6, F2.7 | — | **Não feitos.** F2.6 (sincronizar ao salvar Dados da Empresa) fica para depois: a nota já leva o emitente inteiro, então o cadastro da Focus envelhecido só importa para o certificado. F2.7 é tela do admin |

Travas testadas (91 testes na plataforma): CNPJ do ERP ≠ ficha → 422; CNPJ de
outro cliente → 409; 401/403 da Focus → 501 (nosso token, nunca "certificado
recusado"); recusa de validação da Focus → 422 com as mensagens dela, sem ecoar
senha; resposta ao ERP sem token nenhum.

**Para subir:** (1) na VPS, gerar a chave e pôr no `.env`:
`node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"` →
`FISCAL_TOKENS_KEY=...` em `apps/server/.env`; (2) `npm run deploy` (o
`db:push` só acrescenta duas colunas nulas); (3) ERP: sidecar + instalador.
Ordem livre: ERP novo com plataforma antiga usa a rota antiga; plataforma nova
com ERP antigo continua recebendo `/certificado`.

### F3 — Numeração (2–3 dias)

| # | O quê | Detalhe |
|---|---|---|
| F3.1 | **"Já emitia nota antes?"** na ativação | Por modelo (NF-e e NFC-e): série usada e último número. Grava `serie_*` e `ultimo_numero_*`. Texto: *"Pergunte ao seu contador. Se errar, a SEFAZ recusa com 'duplicidade'."* |
| F3.2 | **539 vira ação** | Ao receber 539, o ERP lê a chave devolvida, marca o número como **usado fora do StartBig** e oferece *"Pular para o próximo número livre e emitir de novo"*, sempre com confirmação e nunca sozinho |
| F3.3 | **Provar em homologação** se um número **rejeitado** pode ser reusado | O comentário de `reemissao.py` diz que reusar dá 204. A regra geral da SEFAZ é que rejeição não registra o número. Se a homologação confirmar, a reemissão de rejeição **de validação** (não 539, não denegada) reusa o número, e quase toda inutilização some. Se não confirmar, fica como está e o comentário ganha a prova |
| F3.4 | **Inutilização sugerida certa** | Sugerir só os números que o StartBig **rejeitou e nunca foram usados por fora**. Os marcados na F3.2 ficam fora da sugestão |

**Risco:** numeração errada gera nota duplicada ou buraco. Tudo aqui passa por
teste com SEFAZ de homologação antes do canário.

**Entrega (06/10/2026)** — ERP, branch `feat/fiscal-ativacao`:

| Item | O que ficou |
|---|---|
| F3.1 | A trava `numeracao_confirmada` **já existia**, com um texto de orientação que dava para ignorar (campos chegam com Série 1 / Último 0 e salvar libera). Agora, na **primeira** confirmação, a tela pergunta "esta empresa já emitiu nota antes?" e não salva sem resposta; "já emitia" com tudo zerado também não salva. Quem já confirmou não vê a pergunta |
| F3.2 | `services/fiscal/numeracao.py` + `POST /fiscal/numeracao/ajustar-duplicidade`. No detalhe da nota com 539 aparece "qual foi o último número do sistema anterior?" (já preenchido com o número que a SEFAZ acusou) e **"Ajustar numeração e reemitir"**. Nunca pula sozinho (decisão 7.1-3), nunca anda para trás, nunca troca a série |
| F3.3 | **Não feito — precisa de SEFAZ de homologação.** Roteiro abaixo |
| F3.4 | Sugestão de inutilização corrigida. **Achado:** listava todo número de 1 até o contador — para quem veio de outro sistema, os números USADOS lá (a SEFAZ recusa inutilizar). Agora existe o **piso** (`numeracao_piso_nfe`, migration `d7a3e9c2f418`): o último número informado à mão. Abaixo dele só aparece o que uma nota do StartBig usou. Números com 204/539 nunca aparecem e inutilizá-los é recusado (409 `NUMERO_USADO_FORA`). **Piso 0 (padrão, todo banco existente) = regra antiga idêntica** |
| extra | O contador não volta para trás de uma nota do próprio StartBig na mesma série (422) — voltar repetiria o número |

**Roteiro da F3.3 (homologação, ~15 min):** numa ficha em homologação, emitir
uma NF-e com erro de cadastro proposital (ex.: CRT errado → 481); anotar o nº N;
corrigir o cadastro; pôr o contador de volta em N−1 **direto no banco** (a tela
agora recusa, de propósito); emitir de novo. Se autorizar com o nº N, rejeição
de validação **não** consome número e a reemissão pode reusar o número (some
quase toda inutilização). Se voltar 204/539, o comentário de `reemissao.py`
estava certo e fica como está.


### F4 — Painel de saúde fiscal no admin (2 dias, só leitura)

Na ficha do cliente, um quadro com o que o `GET /v2/empresas/{id}` e o nosso
banco dizem:

| Item | Verde quando |
|---|---|
| Empresa na Focus | `focusEmpresaId` existe e o CNPJ confere |
| Certificado | presente, CNPJ confere, vence em > 30 dias |
| Habilitação | `habilita_nfe` (e `habilita_nfce` se tiver o módulo) |
| Token do ambiente | presente para o ambiente da ficha |
| CSC | marcado para o ambiente (só se tiver NFC-e) |
| Ambiente | produção (amarelo se homologação) |
| Última nota | data da última AUTORIZADA; rejeições dos últimos 7 dias por `cStat` |

E um botão **"Rodar conferência"**, que refaz tudo sem emitir nada. É o que o
suporte abre quando o lojista liga. Reaproveita o censo da F0.2.

**Entrega (07/10/2026)** — só plataforma, branch `feat/fiscal-ativacao`; o ERP não muda:

| Item | O que ficou |
|---|---|
| Achado | **A consulta não gravava o desfecho na `EmissaoLog`.** NF-e na Focus é assíncrona: a emissão responde "processando" e a autorização ou rejeição chega pela consulta, que só escrevia no log do processo. Para NF-e, "última autorizada" e "rejeições" do censo saíam vazias. Agora a consulta grava `autorizado`/`erro` uma vez por ref (reconsulta não duplica) |
| cStat | Coluna nova `EmissaoLog.codigoSefaz` (nula, aditiva — sobe pelo `db:push` do deploy). Emissão, consulta, cancelamento, carta e inutilização gravam |
| Painel | `GET /fiscal/clientes/:id/saude` (`fiscal-saude.service.ts`) + quadro "Saúde fiscal" no perfil do cliente, abaixo da Configuração Fiscal, com **Rodar conferência**. Itens: empresa na Focus (id e CNPJ conferem; sem id, acha pelo CNPJ e avisa), certificado (vencido / < 30 dias / outro CNPJ — mesma raiz aceita), habilitação NF-e (e NFC-e só com o módulo), token do ambiente (diz quando é a `FISCAL_TOKENS_KEY` que falta), CSC (só com NFC-e), ambiente, última autorizada, rejeições de 7 dias por cStat. Focus fora do ar ou sem token de parceiro: o quadro abre com os dados locais |
| Só leitura | Na Focus, só `GET /v2/empresas` (busca e consulta). Nada grava. Nenhum token/CSC sai na resposta (teste confere) |
| Censo | Contava "processando" como recusa; agora só `erro`, e agrupa pelo cStat |
| Fora | O botão "Ativar emissão" pelo admin (decisão 7.1-2) **não** entrou: a ativação precisa do certificado e do bloco `emitente{}`, que só o ERP tem. Fica para quando houver upload de certificado no admin |

Testes da plataforma: 91 → 111.

### F5 — Reorganizar sem mudar comportamento (4–6 dias)

Só depois das fases anteriores e **guiada pelas fotografias da F0.3**.

| Lado | O quê |
|---|---|
| ERP | `emissao.py` → um módulo por documento (`emissao_nfe_venda.py`, `emissao_nfe_os.py`, `emissao_nfce.py`), com o núcleo comum (reserva, aplicar resultado) num só. `endpoints/fiscal.py` dividido por assunto (emissão, documentos, configuração, eventos). `payload_builder.py` dividido em emitente/destinatário/itens/totais. **O payload não muda nem um byte**: as fotografias garantem |
| ERP | Diagnóstico: a tabela de `cStat` sai do front e vem do backend, para a mesma explicação aparecer no Centro Fiscal, no drawer e no relatório de diagnóstico |
| Plataforma | `fiscal.service.ts` (1213 linhas) → `fiscal-onboarding.service.ts` (ativação, certificado, CSC), `fiscal-emissao.service.ts` (emitir, consultar, cancelar, inutilizar, CC-e) e `fiscal-cota.service.ts` (consumo, extras) |
| Ambos | Apagar o que ficou morto no caminho (conferir com `git log -S` antes de cada remoção) |

**Pronto quando:** fotografias e suítes iguais antes e depois, sidecar gerado
sem estourar o PyArmor, e uma nota real no canário.

**Entrega (07/10/2026)** — branch `feat/fiscal-ativacao` nos dois repositórios.
Método em todos os arquivos: o código foi **movido por script, nunca
reescrito**, e conferido nó a nó pela árvore sintática (AST) antes e depois.
O arquivo antigo virou porta de entrada que reexporta tudo, então nenhum
`import` de fora mudou.

| Item | O que ficou |
|---|---|
| Plataforma | `20a2da8`: `fiscal.service.ts` → `fiscal-onboarding`, `fiscal-emissao`, `fiscal-cota` + `fiscal-comum.ts`. 20/20 métodos idênticos. Injeção conferida montando o `AppModule` compilado. 111 testes |
| ERP `emissao.py` | `cdd525a`: `emissao_nucleo`, `emissao_nfe_venda`, `emissao_nfce`, `emissao_nfe_os`, `emissao_eventos`, `emissao_teste`. 33/33 idênticos. Nos testes só mudou o **alvo do monkeypatch** (o patch vai onde a função mora) |
| ERP `payload_builder.py` | `303c567`: `payload_comum`, `payload_emitente`, `payload_destinatario`, `payload_itens`, `payload_totais`; o builder fica com os 4 `montar_payload_*`. 36/36 idênticos, fotografias passando |
| ERP `endpoints/fiscal.py` | `e7a4431`: `fiscal_documentos`, `fiscal_emissao`, `fiscal_eventos`, `fiscal_config`, incluídos sem prefixo. Mesmo conjunto de 331 rotas, nenhum par reordenado capaz de casar a mesma URL, as 42 rotas com a trava NFE. 45/45 idênticos |
| Código morto | `3c2f31e`: `uf_do_cliente`, `is_simples_nacional` (DEPRECADO) e um import que sobrou. Plataforma: nada morto achado |
| **Achado** | `reconciliacao.reconciliar_no_startup` **nunca foi ligado ao lifespan** (desde `e2d93f8`), embora o comentário diga que é. Nota presa em PROCESSANDO/INDETERMINADA depois de fechar o app só sai pela tela. Não é morto: falta ligar — e ligar faz rede no boot (até 50 consultas). **Decisão do Alan** |
| cStat no backend | **Não feito.** A tabela do front (`fiscalDiagnosticCodigos.ts`) é texto de tela com rótulo, cor e ação; levar ao backend é funcionalidade nova, não reorganização. Fica para quando o relatório de diagnóstico precisar dela |

Falta, para fechar a fase: **uma nota real no canário** com um instalador desta
branch.

---

## 5. Ordem, custo e deploy

| Ordem | Fase | Custo | Sobe onde | Depende de |
|---|---|---|---|---|
| 1 | F0 | 2–3 d | nada vai para produção | — |
| 2 | F1 (plataforma: F1.1, F1.5) | ½ d | VPS | F0.1 |
| 3 | F1 (ERP: F1.2–F1.6) | 1½ d | instalador | F0.3 |
| 4 | F2 | 4–5 d | VPS, depois instalador | F0.1, F0.4, `dry_run` na Focus |
| 5 | F3 | 2–3 d | instalador (+ VPS se F3.3 mudar reemissão) | F2 (usa a tela de ativação) |
| 6 | F4 | 2 d | VPS | F0.2 |
| 7 | F5 | 4–6 d | instalador + VPS | tudo acima |

**Total: ~3 semanas de código**, mais canário e prova em homologação. A F1
sozinha (≈ 2 dias depois da F0) já teria evitado 4 das 5 rejeições de hoje.

**Rollback:** a plataforma sobe por `git pull` + `pm2 restart api` e volta do
mesmo jeito; toda migration Prisma desta trilha é aditiva (coluna nova, padrão
novo). No ERP, o instalador anterior continua funcionando contra a plataforma
nova (princípio 2).

---

## 6. O que NÃO entra

- **NFS-e**: municipal, sem rota na plataforma, sem decisão comercial.
- **Trocar de emissora** (sair da Focus): a tradução está isolada no
  `focus-payload.mapper.ts` de propósito; isso fica para outro plano.
- **Contingência offline de NFC-e**: o certificado vive na Focus por desenho.
- **Consulta automática da IE do destinatário (CCC/SINTEGRA)** antes de
  emitir: útil (teria evitado a 305), mas depende de serviço pago ou de
  scraping. Fica anotado para depois da F4.
- **Mudar o CRT sozinho** quando houver contradição: o sistema avisa e trava;
  quem decide é o lojista ou o contador.

---

## 7. Decisões do Alan

1. **Branch base no ERP.** A `feat/compras` ainda não foi para as lojas.
   Partir dela atrasa o fiscal até Compras/Fábrica serem liberados; partir da
   branch de onde sai o instalador atual das lojas manda o fiscal sozinho.
   **Recomendação:** branch nova `feat/fiscal-ativacao` a partir da linhagem do
   instalador em produção, e trazer para a `feat/compras` depois.
2. **Quem clica "Ativar emissão"**: o lojista (como no Bling/Omie) ou só o
   suporte? **Recomendação:** o lojista, com o checklist na tela. O suporte
   tem o mesmo botão pelo painel da F4.
3. **539: pular número sozinho ou perguntar?** **Recomendação:** perguntar
   sempre (F3.2).
4. **Guardar os dois tokens da Focus?** **Recomendação:** sim, cifrados
   (F2.3–F2.4).
5. **Fichas que já emitem passam pela ativação nova?** **Recomendação:** não
   automaticamente. A F4 mostra quem está incompleto e o suporte resolve caso a
   caso.

---

### 7.1 Respostas do Alan (06/10/2026)

| # | Decisão | Resposta |
|---|---|---|
| 1 | Branch base | "Tanto faz, só garanta que está saindo o exe completo." → branch **`feat/fiscal-ativacao` a partir da `feat/compras`**, que contém tudo das lojas (etiquetas, embalagens) e mais Compras/Fábrica. O instalador sai dela, completo. Consequência: Compras/Fábrica vão junto para as lojas, então eles precisam estar homologados (atrás das chaves `COMPRAS` e modo fábrica, desligadas por padrão) antes do primeiro exe desta trilha |
| 2 | Quem ativa | **O lojista**, no Centro Fiscal do ERP, com checklist. O suporte tem o mesmo botão no admin (F4) |
| 3 | 539 | **Pergunta antes de pular** (F3.2) |
| 4 | Tokens | **Os dois, cifrados** (F2.3–F2.4) |
| 5 | Quem já emite | **Fica como está.** Nenhuma migração automática; a F4 mostra quem está incompleto |
| — | Log do Celso (F0.4) — **FEITO** | Lido na VPS em 06/10: `Certificado do cliente 39052b49… cadastrado na Focus NFe` às 11:48 (o caminho automático funcionou, então o `FOCUS_NFE_PARTNER_TOKEN` está certo) e nenhuma linha de "nenhuma empresa" ou "PARTNER_TOKEN". O "validado só localmente" de antes veio, quase certamente, de certificado enviado **sem ficha no admin**: a plataforma responde 404 `SEM_CONFIGURACAO_FISCAL`, sem log, e o ERP lê qualquer 404 como "a plataforma não recebe certificado". Entra na F1.5 (ler também esse `codigo`) e some com a F2.5 (ficha nasce sozinha) |

---

## 8. Riscos

| Risco | Defesa |
|---|---|
| Mudar o payload sem querer derruba nota em produção | Fotografias (F0.3) em todo commit da F5; F1–F4 não tocam no payload |
| Criar empresa duplicada na Focus | Sempre `GET` por CNPJ antes do `POST`; `dry_run`; CNPJ conferido contra a licença |
| Gravar certificado na empresa de outro cliente | Conferência do CNPJ que já existe em `buscarEmpresaPorCnpj` vira teste na F0.1 |
| Token cifrado ilegível depois do deploy | Leitura aceita texto puro e cifrado na transição; migration reversível |
| Numeração (F3) gerar duplicidade ou buraco | Prova em homologação antes; 539 nunca pula sozinho |
| Plataforma sem teste hoje | F0.1 é pré-requisito de qualquer mudança lá |
| PyArmor estourar com arquivo maior | Código novo em módulo novo; F5 diminui os arquivos grandes |
| Deploy em duas pontas fora de ordem | Plataforma primeiro; ERP antigo continua funcionando com a plataforma nova |
| Exe desta trilha leva Compras/Fábrica às lojas (decisão 7.1-1) | Os dois nascem desligados (chave `COMPRAS`, modo fábrica); a suíte inteira e o canário conferem que loja sem eles não vê diferença |

---

## Fontes

- ERP: `app/services/fiscal/` (helpers, validators, payload_builder, emissao,
  reemissao, http/client_startbig), `app/services/empresa.py`,
  `frontend/src/modules/fiscal/` (utils/fiscalDiagnostic.ts,
  views/FiscalConfiguracoesView.vue).
- Plataforma: `apps/server/src/common/focus-nfe/` (service, mapper),
  `apps/server/src/features/fiscal/fiscal.service.ts`,
  `apps/server/src/features/cliente/cliente.service.ts`,
  `apps/web/src/app/clientes/_components/ModalPerfilCliente.tsx`,
  `prisma/schema.prisma` (`EmpresaFiscalConfig`).
- Servidor: `curl -X POST https://api.startbig.com.br/erp/fiscal/certificado`
  → 401 (rota existe); rota inexistente → 404. Conferido em 06/10/2026.
- Planos anteriores: `fiscal-onboarding-plano.md` (API de empresas da Focus,
  §2), `fiscal-conclusao-plano.md`, `contrato-api-fiscal-plataforma.md`.
