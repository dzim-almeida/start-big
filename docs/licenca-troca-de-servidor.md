# Troca de servidor — licença (ERP + plataforma)

19/10/2026 · branch `fix/reativar-licenca-maquina-nova`

## O incidente

O servidor de um cliente saiu de um desktop para um notebook. O `start_big.db` foi
copiado para o AppData do notebook, o sistema abriu e, **no login**, apareceu
"o banco pode ter sido copiado de outra máquina" — sem botão nenhum. A correção de
17/10 (`b0d838ff`) só tinha saída na tela de erro de licença, que esse caminho não
alcança: a checagem de licença do boot passa direto quando o serviço ainda está
subindo, e o erro só aparece no login.

## Como o mercado faz

| Prática | Quem faz | Aqui |
|---|---|---|
| Licença é da conta; o computador só tem a **ativação** | JetBrains, Adobe, LicenseSpring, Keygen | já era assim (ativação cifrada com o HWID) |
| **Desativar no antigo, ativar no novo** (self-service) | LicenseSpring, Trados, Keygen | novo: Configurações › Licença › Desativar |
| Computador antigo morto: o login da conta no novo libera a vaga, com **e-mail de aviso** | LicenseSpring (portal), Microsoft | já existia na nuvem; agora o ERP chega até ele por qualquer porta |
| **Limite de transferências** por período, contra abuso | LicenseSpring, Cryptlex | falta — plataforma (item 3) |
| Checklist de troca: backup em mídia externa → servidor novo → apontar estações → **desligar o servidor antigo** | Alterdata | passo a passo na tela de Licença |

Fontes: [LicenseSpring — ativações e transferências](https://docs.licensespring.com/license-entitlements/activations-and-device-transfers),
[Keygen — ativação de máquinas](https://keygen.sh/docs/activating-machines/),
[Alterdata — checklist de troca de servidor](https://ajuda.alterdata.com.br/shopbase/checklist-de-troca-de-servidor-rede-de-lojas-326763488.html),
[RWS Trados — transferir licença](https://community.rws.com/product-groups/trados-portfolio/trados-studio/w/customer-experience/1331/how-to-transfer-my-existing-licence-to-a-new-computer/revision/11).

## O que mudou no ERP

**Backend**
- Um código só para "a licença deste banco é de outro computador":
  `LICENCA_DE_OUTRA_MAQUINA` (era `CLONAGEM_DETECTADA`), levantado igual no boot
  (`/licenca/status`) e no login (`conectar_terminal`) — `services/licenca/recusa.py`.
- `services/licenca/transferencia.py` (novo) concentra o login da conta:
  - `POST /licenca/transferir` (público) — transfere a licença do banco copiado para
    este computador. Só grava depois que a nuvem aprova; limpa as sessões copiadas do
    servidor antigo.
  - `POST /licenca/desativar` (master, só no próprio servidor) — libera as vagas na
    nuvem (`/licenca/desconectar` do servidor e dos caixas) e apaga a ativação local.
    Sem internet, nada muda.
  - `GET /licenca/esta-maquina` (master) — situação para a tela.
  - O `/auth/reconnect` (assistente de primeiro acesso) usa o mesmo núcleo e também
    resolve o banco copiado.
- Erros da nuvem viram códigos distintos: `CREDENCIAIS_INVALIDAS`, `CONTA_RECUSADA`
  (com a frase da nuvem, ex.: "Licença vencida."), `SEM_CONEXAO`,
  `NUVEM_INDISPONIVEL`, `RESPOSTA_INVALIDA`. Antes, "licença vencida" chegava como
  "Credenciais inválidas: Licença vencida.".

**Frontend**
- Tela própria `/licenca/transferir`. As três portas levam a ela: guard do router,
  login e tela de erro de licença. O frontend aceita também o código antigo
  (`CLONAGEM_DETECTADA`), para caixa novo com servidor antigo.
- Configurações › **Licença** (só no servidor, só master): dados da licença,
  passo a passo da troca e o botão **Desativar licença neste computador**.

**Testes**: `test/api/v1/test_licenca_transferencia.py` (22 casos).

## O que falta na plataforma (Plataforma_admin)

Em ordem de importância. Nenhum item quebra o ERP de hoje; o ERP novo funciona sem
eles, mas o item 1 fecha um buraco real.

### 1. Heartbeat não pode ressuscitar sessão encerrada  ⚠️ importante

`apps/server/src/features/dispositivos/dispositivo.service.ts`, `heartbeat()` (~linha 745):
faz `upsertLicencaSessao(licencaId, hwid)` para **qualquer** HWID, sem olhar o limite.

Cenário: o notebook novo transfere a licença (a nuvem apaga as sessões antigas). O
desktop antigo continua ligado — o heartbeat dele roda a cada poucos minutos e
**recria** a sessão do HWID antigo. Os caixas da loja nova passam a bater em
"Limite de N dispositivo(s) atingido", e os dois servidores usam a mesma licença.

⚠️ **Não** basta "heartbeat sem sessão → recusar": o cron
`deletarSessoesInativas(35)` (`features/cron/cron.service.ts:98`) apaga sessões sem
heartbeat há 35 min. Uma loja que ficou 40 min sem internet perderia as sessões e,
na volta, seria bloqueada. A regra precisa distinguir **"caiu a internet"** de
**"perdeu a vaga numa transferência"**:

1. Guardar na licença o **HWID do servidor**: `licenca.hwidServidor` (coluna nova).
   É o HWID que o ERP manda no `autoCadastro` e no `/erp/auth/login` — os dois só
   são chamados pelo backend do servidor, com o HWID dele.
2. No `/erp/auth/login`, se o HWID é diferente do `hwidServidor` gravado: é uma
   troca de servidor. Mover o antigo para uma lista de revogados
   (ex.: `LicencaHwidRevogado { licencaId, hwid, revogadoEm }`), gravar o novo em
   `hwidServidor` e registrar o evento `TROCA_SERVIDOR`. **Só o servidor antigo** é
   revogado — os caixas são os mesmos computadores e continuam na loja nova.
3. No `conectar` (sem `autenticado`), no `validar` e no `heartbeat`: HWID revogado →
   **400** "Licença transferida para outro computador.". O servidor antigo cai na
   próxima checagem de licença (o ERP mostra a tela de licença recusada) e o
   heartbeat dele, que já trata 400 como bloqueio, para de ocupar vaga.
4. No `heartbeat` de HWID **não** revogado e sem sessão: recriar só se
   `countSessoesAtivas < limite` (hoje recria sempre, sem olhar o limite).
5. Um login autenticado vindo de um HWID revogado o tira da lista (o dono decidiu
   voltar para aquele computador).
6. Na troca, derrubar só as sessões que excedem o limite (hoje
   `deletarTodasSessoesDaLicenca` derruba os caixas também; eles voltam no próximo
   login, mas o caixa aberto no momento leva um susto).

Para licenças antigas, `hwidServidor` nasce vazio: preencher no primeiro
`/erp/auth/login` ou `autoCadastro` e, enquanto vazio, não revogar ninguém.

### 2. Erros com `codigo` estruturado no `/erp/auth/login`

`erp-auth.service.ts` (`login`) lança texto puro. O ERP hoje lê o status HTTP
(401 = senha) e repassa a frase nos demais. Mandar também um código deixa a tela
precisa sem depender do texto:

| Caso | HTTP | `codigo` sugerido |
|---|---|---|
| e-mail/senha errados | 401 | `CREDENCIAIS_INVALIDAS` |
| senha nunca criada | 400 | `SENHA_NAO_CONFIGURADA` |
| sem licença ativa | 400 | `SEM_LICENCA_ATIVA` |
| licença vencida | 402 | `LICENCA_VENCIDA` |
| limite de transferências | 429 | `LIMITE_TRANSFERENCIAS` |

### 3. Licença vencida (ou em carência) não consegue transferir

`login()` busca só dispositivos com `status: 'ATIVA'`. Uma licença `VENCIDA` em
carência (cartão sendo re-tentado) responde "Nenhuma licença ativa encontrada" e o
dono não consegue trocar de computador. Sugestão: aceitar `VENCIDA` com carência
vigente (a mesma regra de `carenciaVigente()` usada no `conectar`) e, para vencida
sem carência, responder 402 `LICENCA_VENCIDA` — a tela mostra "renove primeiro".

### 4. Limite de transferências (antiabuso)

Hoje o login autenticado derruba as sessões sem limite. Padrão de mercado: N trocas
por janela (ex.: 3 em 30 dias), contadas pelos eventos `TROCA_DISPOSITIVO` que o
`conectar` já registra. Acima disso, 429 `LIMITE_TRANSFERENCIAS` e liberação manual
pelo suporte (`trocarDispositivo`, já existe no admin).

### 5. (Opcional) Nome do computador

O ERP pode mandar `nomeComputador` (hostname) junto do HWID no login e no conectar.
Com isso o e-mail de aviso e o painel admin mostram "NOTEBOOK-LOJA" em vez de um
GUID, e o suporte identifica a máquina na hora.

## Homologação (antes de qualquer loja)

1. Regerar o sidecar (`npm run build:sidecar`) e o instalador.
2. Máquina A com licença → copiar o `start_big.db` para a máquina B → abrir B:
   deve ir direto para "Transferir a licença para este computador" (pelo boot ou
   pelo login).
3. Senha errada → mensagem de senha; desligar a internet → mensagem de conexão;
   nos dois casos, A continua funcionando.
4. Transferir em B → entrar → caixas buscam o servidor novo em Rede e Conexão.
5. Em A (outro banco de teste): Configurações › Licença › Desativar → A volta ao
   assistente; ativar de novo com a conta deve funcionar.
6. Canário com backup do `start_big.db`, como sempre.
