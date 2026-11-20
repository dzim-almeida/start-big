# Licença 03 — Re-login, restauração e avisos de troca

| Campo        | Valor |
|--------------|-------|
| Status       | Concluída (2026-11-20) |
| Camada       | Backend (FastAPI) e Frontend (Vue 3 + TypeScript) |
| Dependências | SPEC-01 (download que entende a cópia cifrada), SPEC-02 (códigos de recusa). Integração com a LIC-06, com rede de segurança: funciona sem ela |
| Bloqueia     | — |
| Referência   | [acordo](../../../docs/licenca/ACORDO.md) decisões D-07, D-08, D-16, D-22, D-23, D-28, D-29, D-31, D-34, D-36; [ADR-004](../../../docs/licenca/adr/ADR-004-compatibilidade-api-app-instalado.md); quadro F10, F11, F16, F18, F19, F22 |

> **Revisão 1 (2026-11-18):** revisão de conflitos com o usuário, antes da aprovação.
> - **Conflito 8 (D-28):** os dados da nuvem vêm do `GET /erp/cadastro/titular` (LIC-06; na revisão 2 o caminho passou a ser `/erp/usuario/titular`). Se a rota responder `404` (API antiga), o setup funciona como hoje, só local. Com isso esta spec pode ir para produção antes da LIC-06.
> - **Conflito 10:** a conferência da senha continua por `_entrar_na_conta`. Foi verificado no `plataformaADM` que um segundo login seguido do mesmo computador não conta como troca e não derruba caixa. Entram `SEM_CONEXAO` e a lista completa de mensagens por código.
> - **Conflito 11 (D-29):** o corpo de erro é `{"error": ..., "detail": {"codigo", "mensagem"}}`, como o backend já faz. O front ganha `lerErroDaLicenca`.
> - **Conflito 14 (D-31):** o cadastro sempre responde `202`. A tela trata só esse caso.
> - **Conflito 16:** o documento nunca vai para a nuvem e nunca vem da tela: o corpo do `PUT` tem uma lista fechada de campos, e a empresa local recebe o documento da nuvem. Cada erro tem o seu tratamento.
> - **Conflito 13:** o aviso de relógio fica na LIC-08.
> - **Documentação:** o reenvio de link (F23) é da LIC-06, não da SPEC-05.

> **Revisão 2 (2026-11-19):** conferência no código da plataforma.
> - **Conflito 23 (D-34, ADR-004):** o app novo manda `fluxoConfirmacao: true` no cadastro e recebe `202`. As versões instaladas recebem `409 CONFIRMACAO_NECESSARIA` com a instrução.
> - **Conflito 26 (D-36):** sem ciclo informado, a API usa a semana atual, e o registro local de ciclos some junto com o banco. A restauração descobre o ciclo mais recente com full pelo `historicoEventos` do `/erp/backup/status`.
> - **Conflito 29 (D-28 revista):** as rotas do titular são `GET` e `PUT /erp/usuario/titular`.
> - **Documentação (D13):** erro de validação da API sai como `400`, não `422`.

> **Revisão 3 (2026-11-19):** mockups aprovados pelo usuário. A referência de design desta spec são os quadros 1a, 1b, 2, 3a, 3b, 7 e 8 da página [https://claude.ai/artifact/E5SohwYLXt3pY84pCFwj6z](https://claude.ai/artifact/E5SohwYLXt3pY84pCFwj6z) (skill `design`). Propostas aprovadas junto: a tela 1a pede a senha da conta de novo (D-07), com o e-mail preenchido e travado, e mostra a semana do backup encontrado; a tela 3a também oferece "Reenviar link". As tabelas da §6.2 e da §6.5 já trazem isso.

> **Revisão 4 (2026-11-20, implementação):** lacunas de contrato achadas ao implementar, decididas com o usuário, e ajustes registrados.
> - **Dados do re-login no `/auth/reconnect` (decisão 1).** A spec não dizia como a tela sabe se há backup (§6.2) nem como recebe os dados do titular (§6.6). A resposta do `/auth/reconnect` ganhou `backup` (`{ciclo, ultimo_envio}` ou `null`) e `titular` (`TitularNuvem` ou `null`), só com `inicializado=false`. Só quem acabou de provar a senha recebe o documento. Falha na nuvem deixa o campo `null` e nunca derruba o re-login (`dados_depois_do_relogin`). O CT-08 testa essa resposta.
> - **Setup com `409 CONFIRMACAO_NECESSARIA` (decisão 2).** O cadastro roda dentro do `/auth/setup`. Quando a nuvem responde `202` (ou o `409` das versões antigas), o setup responde `409 CONFIRMACAO_NECESSARIA`, a transação é desfeita e nada é gravado; o front abre o quadro 3a.
> - **Rota local `POST /api/v1/licenca/reenviar-link` (decisão 3).** Pública, repassa à nuvem e responde sempre `202` (também quando a nuvem ainda não tem a rota). Só sem rede (`SEM_CONEXAO`) ou com a nuvem fora (`NUVEM_INDISPONIVEL`) responde erro.
> - **Códigos do login repassados (decisão 4).** `_entrar_na_conta` (`transferencia.py`) passa `AGUARDANDO_CONFIRMACAO_EMAIL`, `MUITAS_TENTATIVAS` (429), `LICENCA_VENCIDA` e `SEM_LICENCA_ATIVA` com o próprio código; o resto continua `CONTA_RECUSADA`.
> - **Telas como componentes (decisão 5).** `EscolhaRestauracaoStep`, `RestauracaoPreparadaStep` e `ConfirmarEmailStep` em `sign-in/components/steps`, mostrados pelo `SignInView`. O `ResponsavelStep` trava CPF/CNPJ e o tipo de pessoa quando os dados vêm da nuvem. O quadro 3b ficou dentro do `ReconnectStep`.
> - **Quadro 2 sem "Reiniciar o sistema".** O marcador só é aplicado quando o serviço do backend liga de novo, e o app não tem comando que pare e religue o serviço (o `reiniciar_backend_local` só liga um que está parado). A tela orienta reiniciar o computador e não tem "Voltar" nem "Sair". Um botão de reinício de verdade exige mexer no Tauri (fica como sugestão).
> - **Campos travados com `disabled`.** O `BaseInput` não tem `readonly`; o e-mail da tela 1a e o documento do setup usam `disabled`, que já tem o visual cinza.
> - **Setup sem backup também usa o tipo de pessoa da nuvem.** Junto com o documento, para um CNPJ nunca virar CPF. O documento é gravado só com os números (como hoje).
> - **`historicoEventos`:** o formato exato não estava no repositório; `tipo` e `status` são comparados sem diferenciar maiúsculas (`FULL`/`full`, `CONFIRMADO`/`confirmado`) e a data do último envio é lida de `confirmadoEm`, `criadoEm`, `dataHora` ou `data`. **Não conferido contra a API** nesta sessão: conferir na verificação de integração (roteiro, passo 11, fluxo 5).
> - **`restore.py`:** `preparar_restauracao_do_titular` faz `prepare_restore` + `confirm_restore` (o banco está vazio, não há o que comparar); `restauracao_pendente()` olha o marcador.
> - **Fora da lista:** `api/v1/endpoints/auth.py` (decisão 1); `services/licenca/transferencia.py` (decisão 4); `services/licenca/constantes.py` (URLs do titular e do reenvio); `schemas/licenca/cadastro.py` (`fluxoConfirmacao`); `sign-in/views/SignInView.vue`, `components/steps/ResponsavelStep.vue` e os três componentes novos (decisão 5); `sign-in/types/sign-in.types.ts`.
> - **Verificação:** CT-01 a CT-23 com pytest e Vitest, mais casos das decisões (códigos do login, reenvio, resposta que não é JSON). Suítes completas, `vue-tsc` e lint no fim da série (pedido do usuário). **Não verificados no app** (sessão em Linux, sem a janela Tauri nem a API real): CA-01, CA-02 e CA-06 na tela; ficam para a verificação de integração.

## 1. Objetivo

Fazer o caso 2 do re-login funcionar: o dono perdeu o banco, entra com a conta da loja e recupera os dados, em vez de cair num setup vazio. Também fazer o caso 1 avisar antes de qualquer troca de computador, e mostrar mensagens claras no lugar de textos técnicos.

## 2. Escopo

**Dentro do escopo**
- Nova rota `POST /api/v1/licenca/restaurar-backup`, para o titular que prova a senha (D-07).
- Depois do re-login, a tela oferece "Restaurar backup da nuvem" quando houver backup, e só isso.
- Aviso antes de confirmar uma troca de computador (D-08, F18 e F22).
- Mensagens de erro por código, com texto fixo em português, e um leitor único do código do erro (D-16, D-29, F10).
- Cadastro novo que responde `202`: nada é gravado, e a tela leva ao re-login (D-23, D-31).
- Re-login sem backup: o setup abre com os dados da nuvem, o documento vem travado, e a empresa local só é criada depois que a nuvem confirma (D-22, D-28, F16).

**Fora do escopo**
- Trial com um backup completo (D-06). É da API, na SPEC-05.
- Reenvio do link de confirmação e de nova senha (F23). É da API, na LIC-06.
- Aviso de relógio e rótulo de estimativa. Ficam na LIC-08.
- Contagem de troca na reinstalação. Já é feita pela API. Esta spec só avisa.

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `backend-fastapi/app/api/v1/endpoints/licenca.py` | alterar | Rota `POST /restaurar-backup`. Pública, como `/transferir`, porque roda antes do login local. |
| `backend-fastapi/app/services/licenca/restauracao_titular.py` | criar | Confere a conta na nuvem, confere se a licença é a desta máquina, descobre o ciclo pelo `/status` (§6.1) e prepara a restauração. |
| `backend-fastapi/app/services/backup/restore.py` | alterar | Expõe `preparar_restauracao_do_titular(ciclo)`, sem exigir Master. |
| `backend-fastapi/app/services/licenca/titular_nuvem.py` | criar | `buscar_titular()` (`GET /erp/usuario/titular`) e `atualizar_titular(campos)` (`PUT`), com a rede de segurança do `404`. |
| `backend-fastapi/app/services/licenca/cadastro.py` | alterar | Manda `fluxoConfirmacao: true` e trata a resposta `202` do cadastro sem gravar licença (§6.5). |
| `backend-fastapi/app/services/sistema/setup.py` | alterar | Sem backup: busca o titular, monta o corpo com a lista fechada, atualiza a nuvem e só então cria a empresa local, com o documento vindo da nuvem (§6.6). |
| `backend-fastapi/app/schemas/licenca/restauracao.py` | criar | `RestaurarBackupPayload` e `RestaurarBackupResposta`. |
| `backend-fastapi/app/schemas/licenca/titular.py` | criar | `TitularNuvem` (o que o `GET` devolve) e `AtualizarTitularCorpo` (os campos permitidos no `PUT`). |
| `frontend/src/modules/sign-in/composables/useSetup.ts` | alterar | Pré-preenche o setup com os dados da nuvem e trava o documento. |
| `frontend/src/modules/sign-in/services/sign-in.service.ts` | alterar | Função `restaurarBackupDaNuvem(email, senha, ciclo?)`. |
| `frontend/src/modules/sign-in/components/steps/ReconnectStep.vue` | alterar | Depois do re-login, mostra a escolha da §6.2. |
| `frontend/src/modules/sign-in/composables/useSignIn.ts` | alterar | Novo passo `escolha-restauracao` e o caminho do `202` do cadastro. |
| `frontend/src/modules/license/views/TransferirLicencaView.vue` | alterar | Aviso antes de confirmar a troca (§6.3). |
| `frontend/src/shared/services/licenca.service.ts` | alterar | `MENSAGENS_DE_CODIGO`, `mensagemDoCodigo` e `lerErroDaLicenca` (§6.4). |
| `backend-fastapi/test/api/v1/test_restaurar_backup_titular.py` | criar | Casos CT-01 a CT-07 e CT-21 a CT-23. |
| `backend-fastapi/test/api/v1/test_setup_dados_nuvem.py` | criar | Casos CT-08 a CT-13. |
| `frontend/src/modules/sign-in/__tests__/reconnect.spec.ts` | criar | Casos CT-14 a CT-20. |

Testes existentes que precisam continuar passando: `test/api/v1/test_licenca_transferencia.py` e `test/api/v1/test_backup_preserva_licenca.py`.

## 4. Contrato da API

Todo erro desta spec segue o formato do projeto (D-29), já usado pelos erros de licença:

```json
{
  "error": "Licença de outra conta",
  "detail": {
    "codigo": "LICENCA_DE_OUTRA_CONTA",
    "mensagem": "Esta conta não é dona da licença deste computador."
  }
}
```

As tabelas abaixo mostram só o `codigo` e a `mensagem` de cada caso.

### 4.1. `POST /api/v1/licenca/restaurar-backup` (nova)

Pública, como `/licenca/transferir`, porque roda antes de existir um login local. A proteção é a conta da loja e a licença já ativada nesta máquina.

**Corpo**

```json
{
  "email": "dono@exemplo.com.br",
  "senha": "senha-da-conta",
  "ciclo": null
}
```

`ciclo` é opcional. Quando `null`, a restauração descobre o ciclo mais recente com full confirmado pelo `/erp/backup/status` (§6.1). A API, sem ciclo, usaria a semana atual, que pode estar vazia.

**Regras de negócio**

1. A conta e a senha são conferidas na nuvem (`/erp/auth/login`), pelo mesmo caminho de `transferencia.py::_entrar_na_conta`. Verificado no `plataformaADM` (`dispositivo.service.ts:380-382` e `802-835`): o login do mesmo computador que já é o servidor não conta como troca e é tratado como reconexão, sem derrubar caixa nem mandar e-mail.
2. O `licencaId` devolvido pela nuvem tem que ser igual ao `licenca_id` da licença local. Se for outro, recusa com `LICENCA_DE_OUTRA_CONTA`. Sem essa regra, qualquer conta poderia substituir o banco.
3. Só pode haver uma restauração pendente por vez.
4. A restauração é aplicada no próximo boot, pelo marcador que já existe em `restore.py`.

**Respostas**

| Status | `codigo` | `mensagem` | Quando |
|--------|----------|------------|--------|
| 200 | — | Corpo `{ "status": "pendente_reinicio", "ciclo": "2026-11-17", "mensagem": "..." }` | Restauração preparada |
| 401 | `CREDENCIAIS_INVALIDAS` | E-mail ou senha da conta StartBig incorretos. | Senha errada |
| 403 | `LICENCA_DE_OUTRA_CONTA` | Esta conta não é dona da licença deste computador. | `licencaId` diferente |
| 404 | `BACKUP_INEXISTENTE` | Não há backup na nuvem para esta licença. | Sem backup |
| 409 | `RESTAURACAO_JA_PENDENTE` | Uma restauração já está pendente. Reinicie o sistema para aplicá-la. | Já existe marcador |
| 422 | `BACKUP_CHAVE_INVALIDA` | O backup da nuvem não abre com a chave desta licença. | SPEC-01 |
| 503 | `SEM_CONEXAO` | Sem conexão com a StartBig. Verifique a internet. | Falha de rede |
| 503 | `NUVEM_INDISPONIVEL` | O servidor da StartBig não respondeu. Tente de novo em alguns minutos. | A nuvem respondeu 5xx |

### 4.2. `POST /api/v1/auth/reconnect` (existente)

Nenhuma mudança de contrato. O front passa a mostrar a escolha da §6.2 quando `inicializado` for `false`.

### 4.3. Rotas da API StartBig consumidas (LIC-06)

| Rota | Uso | Sem a LIC-06 (resposta `404`) |
|------|-----|-------------------------------|
| `GET /erp/usuario/titular` | Dados para pré-preencher o setup | Setup abre vazio, como hoje |
| `PUT /erp/usuario/titular` | Atualizar a nuvem antes da empresa local | Empresa criada só localmente, como hoje |

## 5. Schemas

```python
# schemas/licenca/restauracao.py — corpo e resposta de POST /licenca/restaurar-backup
from pydantic import BaseModel, EmailStr   # EmailStr confere o formato do e-mail


class RestaurarBackupPayload(BaseModel):
    email: EmailStr                        # e-mail da conta StartBig
    senha: str                             # senha da conta, usada só para conferir
    ciclo: str | None = None               # ciclo do backup; None = o mais recente


class RestaurarBackupResposta(BaseModel):
    status: str                            # sempre "pendente_reinicio" nesta versão
    ciclo: str                             # ciclo que será restaurado
    mensagem: str                          # texto para mostrar ao dono
```

```python
# schemas/licenca/titular.py — o que a nuvem devolve e o que pode ser enviado a ela (D-22, conflito 16)
from pydantic import BaseModel


class EnderecoTitular(BaseModel):
    cep: str
    logradouro: str
    numero: str
    bairro: str
    cidade: str
    estado: str


class TitularNuvem(BaseModel):
    tipoPessoa: str                        # "PF" ou "PJ"
    nomeOuRazao: str
    documento: str                         # CPF ou CNPJ: só LEITURA, nunca enviado de volta
    nomeFantasia: str | None = None
    telefone: str | None = None
    celular: str | None = None
    endereco: EnderecoTitular | None = None


class AtualizarTitularCorpo(BaseModel):
    """Lista FECHADA de campos que podem ir à nuvem. O documento não existe aqui de propósito."""
    nomeOuRazao: str
    nomeFantasia: str | None = None
    telefone: str | None = None
    celular: str | None = None
    endereco: EnderecoTitular | None = None
```

## 6. Especificação técnica

### 6.1. Restauração pelo titular (`restauracao_titular.py`)

```python
# restauracao_titular.py — o dono que provou a senha pode restaurar o banco dele (D-07)
from app.core.hwid import obter_hwid
from app.db.crud.configuracao import licenca as licenca_crud
from app.services.licenca.transferencia import _entrar_na_conta, _erro


def conferir_titular_da_licenca(db, email: str, senha: str) -> None:
    # 1. Confere a senha na nuvem. Os erros saem com os mesmos códigos de transferencia.py
    #    (CREDENCIAIS_INVALIDAS, SEM_CONEXAO, NUVEM_INDISPONIVEL...).
    resposta = _entrar_na_conta(email, senha, obter_hwid())
    # 2. A conta tem que ser dona da licença que está gravada aqui.
    local = licenca_crud.get_licenca(db)
    if local is None or local.licenca_id != resposta.licencaId:
        raise _erro(403, "LICENCA_DE_OUTRA_CONTA",
                    "Esta conta não é dona da licença deste computador.")
```

Depois disso, a função descobre o ciclo (abaixo), chama `download_chain(db, ciclo)` (`services/cloud/download.py`, que decifra a cópia da nuvem pela SPEC-01) e `prepare_restore` (`services/backup/restore.py`), sem passar pela rota de Master.

```python
# restauracao_titular.py — qual ciclo restaurar quando o dono não escolheu (D-36).
# Sem ciclo, a API usaria a SEMANA ATUAL, que pode estar vazia (segunda de manhã, trial).
# O registro local de ciclos (journal) some junto com o banco, então a fonte é o /status.
def ciclo_mais_recente_com_full(status: dict) -> str | None:
    ciclos = [
        evento["ciclo"]
        for evento in status.get("historicoEventos", [])          # os 30 envios mais recentes
        if evento.get("tipo") == "FULL" and evento.get("status") == "CONFIRMADO"
    ]
    return max(ciclos) if ciclos else None                        # ciclo é data ISO: o maior é o mais recente
```

Sem nenhum full confirmado, a resposta é `BACKUP_INEXISTENTE`. Limite registrado: o `historicoEventos` traz os 30 envios mais recentes; com o limite diário de envios e o ciclo semanal, o full do ciclo mais recente cabe nessa janela.

Observação da verificação: se a sessão deste computador tiver expirado entre o re-login e a restauração **e** o plano estiver no limite, a nuvem trata o login como computador novo e encerra a sessão mais antiga. Como a restauração vem segundos depois do re-login, o caso é raro, e não há ação nesta spec.

### 6.2. Escolha depois do re-login (front)

Quando `inicializado` volta `false`, o fluxo em `useSignIn.ts` leva a uma tela com o texto fixo:

| Elemento | Texto |
|----------|-------|
| Título | Sua licença foi encontrada |
| Corpo | Se você já usava o sistema neste computador ou em outro, é possível recuperar os dados do último backup da nuvem. |
| Backup encontrado (só quando houver backup) | Backup encontrado na nuvem · Semana de {dd/mm/aaaa} · último envio em {data e hora} (do `/status`) |
| Campos (só quando houver backup) | "E-mail da conta StartBig" (preenchido do re-login, travado) e "Confirme a senha da conta" (D-07: a senha vai na chamada de `restaurar-backup`) |
| Botão (só quando houver backup) | Restaurar backup da nuvem |
| Botão (só quando não houver backup) | Preencher os dados da empresa |
| Aviso, quando não houver backup | Não há backup na nuvem para esta licença. Confira os dados da empresa, que vêm da sua conta na StartBig. |

"Há backup" é a mesma regra da §6.1: existe um ciclo com full confirmado no `/status`.

Regra: **com backup, a tela só oferece restaurar.** Sem backup, só oferece preencher os dados da empresa (D-22).

Ao restaurar, a tela mostra a mensagem da resposta 200 e pede para reiniciar o sistema. Antes de reiniciar, o botão de sair fica desabilitado, para não deixar o banco pela metade.

### 6.3. Aviso antes da troca (D-08, F18, F22)

Antes de confirmar a transferência, a tela `TransferirLicencaView.vue` mostra o texto abaixo. Ele não cita o nome do computador antigo, porque o app não tem esse dado.

> **Trocar o servidor de computador**
>
> O computador que é servidor hoje deixará de funcionar com esta licença. Os caixas precisarão apontar para este computador.
>
> Esta é uma troca de computador. Ela conta no limite de 3 trocas em 30 dias.
>
> [Cancelar] [Trocar para este computador]

### 6.4. Mensagens por código (D-16, D-29, F10)

O front lê o código num lugar só e mostra um texto fixo. Quando o código não está na tabela, mostra a mensagem genérica, e nunca o texto da exceção.

```typescript
// licenca.service.ts — lê o código do erro num lugar só (D-29).
// O backend manda { error, detail: { codigo, mensagem } }. Também aceitamos o código
// no topo, porque um caixa atualizado pode falar com um servidor ainda na versão antiga.
export function lerErroDaLicenca(erro: unknown): { codigo?: string; mensagem?: string } {
  const dados = (erro as { response?: { data?: any } })?.response?.data ?? {};
  const detalhe = typeof dados.detail === 'object' && dados.detail !== null ? dados.detail : dados;
  return { codigo: detalhe.codigo, mensagem: detalhe.mensagem };
}

// Texto fixo para cada código de erro da licença (D-16). Lista completa: todo código
// citado nas specs LIC-01 a LIC-09 que pode chegar à tela tem uma linha aqui (CT-17).
export const MENSAGENS_DE_CODIGO: Record<string, string> = {
  CREDENCIAIS_INVALIDAS: 'E-mail ou senha da conta StartBig incorretos.',
  SENHA_NAO_CONFIGURADA: 'Sua conta ainda não tem senha. Use "Reenviar link" para criar uma.',
  MUITAS_TENTATIVAS: 'Muitas tentativas. Aguarde alguns minutos e tente de novo.',
  AGUARDANDO_CONFIRMACAO_EMAIL: 'Confirme o link enviado ao seu e-mail antes de entrar.',
  CONFIRMACAO_NECESSARIA: 'Enviamos as instruções para o seu e-mail. Depois de confirmar, entre com o seu e-mail e senha.',
  CONTA_RECUSADA: 'A StartBig recusou o acesso desta conta. Fale com o suporte.',
  SEM_LICENCA_ATIVA: 'Nenhuma licença ativa foi encontrada para este e-mail.',
  LICENCA_VENCIDA: 'Sua licença está vencida. Renove a assinatura para continuar.',
  LICENCA_TRANSFERIDA: 'Esta licença foi transferida para outro computador.',
  LICENCA_HWID_REVOGADO: 'Este computador não é mais o servidor desta licença.',
  LICENCA_DE_OUTRA_CONTA: 'Esta conta não é dona da licença deste computador.',
  TOKEN_DE_OUTRA_LICENCA: 'A licença guardada não confere com este computador. Entre de novo com a conta StartBig.',
  TOKEN_ILEGIVEL: 'Não foi possível ler a licença guardada. Conecte-se à internet ou entre de novo com a conta StartBig.',
  CHAVE_ATIVACAO_ILEGIVEL: 'A licença deste banco foi ativada em outro computador. Entre de novo com a conta StartBig.',
  CHAVE_CORROMPIDA: 'A chave de segurança da licença está danificada. Conecte-se à internet para recuperá-la.',
  COFRE_INDISPONIVEL: 'O Windows não permitiu acessar o cofre da licença. Reinicie o computador e tente de novo.',
  BACKUP_INEXISTENTE: 'Não há backup na nuvem para esta licença.',
  BACKUP_CHAVE_INVALIDA: 'O backup da nuvem não abre com a chave desta licença.',
  RESTAURACAO_JA_PENDENTE: 'Uma restauração já está pendente. Reinicie o sistema para aplicá-la.',
  DOCUMENTO_TRAVADO: 'O CPF ou CNPJ do titular não pode ser alterado pelo sistema. Fale com o suporte.',
  RESPOSTA_INVALIDA: 'A StartBig respondeu de um jeito inesperado. Tente de novo em instantes.',
  SEM_CONEXAO: 'Sem conexão com a StartBig. Verifique a internet.',
  NUVEM_INDISPONIVEL: 'O servidor da StartBig não respondeu. Tente de novo em alguns minutos.',
};

// Devolve a mensagem do código, ou a mensagem genérica se o código não existir.
export function mensagemDoCodigo(codigo: string | undefined): string {
  return MENSAGENS_DE_CODIGO[codigo ?? ''] ?? 'Não foi possível concluir agora. Tente de novo em instantes.';
}
```

### 6.5. Cadastro novo com confirmação de e-mail (D-23, D-31)

O app novo manda `fluxoConfirmacao: true` no cadastro, e a API responde `202` (LIC-06 §4.1; D-34, ADR-004). As versões instaladas, que não mandam o campo, recebem `409 CONFIRMACAO_NECESSARIA` com uma instrução que elas já sabem mostrar. O app novo não grava licença nenhuma e mostra:

> Enviamos as instruções para o seu e-mail. Se este e-mail já tiver conta, enviamos as instruções para entrar.
>
> [Já confirmei, quero entrar]
>
> Não recebeu? Reenviar link

- Em `registrar_licenca` (`services/licenca/cadastro.py`), o caminho do `202` não grava nada e devolve o aviso.
- "Já confirmei, quero entrar" leva ao re-login com e-mail e senha. A chave vem da resposta do login (D-23).
- Se o login responder `AGUARDANDO_CONFIRMACAO_EMAIL`, a tela mostra a mensagem do código e o botão "Reenviar link" (LIC-06 §4.4).
- Enquanto a API não tiver a LIC-06, o cadastro devolve a licença como hoje, e o caminho atual continua funcionando.

### 6.6. Setup com os dados da nuvem, sem backup (D-22, D-28, conflito 16)

O setup não roda no re-login com backup. Sem backup, ele abre com os dados que a nuvem já tem.

**Regras:**
- O **documento do titular fica travado** na tela, e não é editado pelo app. Para mudá-lo, só o suporte.
- O **documento nunca vai para a nuvem**: o corpo do `PUT` é montado com `AtualizarTitularCorpo`, uma lista fechada de campos.
- O **documento da empresa local vem da nuvem** (`buscar_titular`), e não do formulário. Um formulário alterado por fora não muda o documento.
- A **ordem é nuvem primeiro, banco depois.** Se a nuvem recusar ou não responder, nada é criado localmente.

```python
# setup.py — a nuvem é atualizada antes da empresa local, e o documento nunca vem da tela (D-22)
from app.schemas.licenca.titular import AtualizarTitularCorpo
from app.services.licenca import titular_nuvem


def setup_sem_backup(db, dados_setup):
    # 1. Busca o titular na nuvem. None = a API ainda não tem a rota (404): setup como hoje.
    titular = titular_nuvem.buscar_titular()
    if titular is None:
        return criar_empresa_local(db, dados_setup)

    # 2. Monta o corpo SÓ com os campos permitidos. O documento não existe nesta classe.
    corpo = AtualizarTitularCorpo(
        nomeOuRazao=dados_setup.nome_responsavel_ou_razao,
        nomeFantasia=dados_setup.nome_loja,
        telefone=dados_setup.telefone,
        celular=dados_setup.celular,
        endereco=dados_setup.endereco_principal,
    )

    # 3. Atualiza a nuvem. Se der erro, para aqui: nada foi criado localmente.
    #    Os erros sobem com o código certo (tabela abaixo).
    titular_nuvem.atualizar_titular(corpo)

    # 4. Só agora cria a empresa local. O documento vem da NUVEM, não do formulário.
    dados_setup.documento = titular.documento
    return criar_empresa_local(db, dados_setup)
```

**Tratamento das respostas da nuvem:**

| Resposta | O que o setup faz |
|----------|-------------------|
| `404` (rota inexistente) | Rede de segurança: setup como hoje, só local (D-28) |
| `401 LICENCA_HWID_REVOGADO`, `403 DOCUMENTO_TRAVADO`, `400` (validação) | Mostra a mensagem do código (`lerErroDaLicenca`). Nada criado |
| Falha de rede | `SEM_CONEXAO`: "tente de novo". Nada criado |
| `5xx` | `NUVEM_INDISPONIVEL`: "tente de novo". Nada criado |

Isso segue o mesmo padrão de `transferencia.py::desativar_esta_maquina`: nuvem primeiro, banco depois.

## 7. Critérios de aceite

- **CA-01:** no caso 2, depois do re-login com backup disponível, a tela oferece restaurar antes do setup, com os textos da §6.2.
- **CA-02:** a restauração com a senha certa e a licença desta máquina prepara o backup e pede reinicialização.
- **CA-03:** conta de outra licença recebe 403 e o banco não muda.
- **CA-04:** trocar o servidor mostra o aviso da §6.3 antes de qualquer chamada à API.
- **CA-05:** nenhum erro mostra texto técnico do servidor (sem "Expecting value", sem nome de classe).
- **CA-06:** sem backup, o setup abre com os dados da nuvem, o documento aparece travado, e a empresa local só existe depois que a nuvem confirmou.
- **CA-07:** com backup, o re-login não mostra o setup em nenhum momento.
- **CA-08:** com a API sem a LIC-06 (`404`), o setup funciona como hoje.
- **CA-09:** cadastro com resposta `202` não grava licença e leva ao re-login.
- **CA-10:** sem ciclo informado, a restauração usa o ciclo mais recente com full, mesmo que a semana atual esteja vazia.

CA-01, CA-02 e CA-06 são cobertos por teste automatizado e verificados no app pela skill `verify`, no fim da série.

## 8. Casos de teste

| ID | Arquivo | Caso | Esperado |
|----|---------|------|----------|
| CT-01 | `test_restaurar_backup_titular.py` | Senha certa, licença desta máquina | 200, `pendente_reinicio` |
| CT-02 | `test_restaurar_backup_titular.py` | Senha errada | 401, `CREDENCIAIS_INVALIDAS`, nada preparado |
| CT-03 | `test_restaurar_backup_titular.py` | Conta de outra licença | 403, `LICENCA_DE_OUTRA_CONTA`, nada preparado |
| CT-04 | `test_restaurar_backup_titular.py` | Sem backup na nuvem | 404, `BACKUP_INEXISTENTE` |
| CT-05 | `test_restaurar_backup_titular.py` | Já existe restauração pendente | 409, `RESTAURACAO_JA_PENDENTE` |
| CT-06 | `test_restaurar_backup_titular.py` | Sem rede / nuvem com 5xx | 503 `SEM_CONEXAO` / 503 `NUVEM_INDISPONIVEL` |
| CT-07 | `test_restaurar_backup_titular.py` | Restauração com ciclo informado | Usa o ciclo pedido |
| CT-08 | `test_setup_dados_nuvem.py` | Setup sem backup, `GET` do titular ok | Dados da nuvem devolvidos para o front, documento incluído só para leitura |
| CT-09 | `test_setup_dados_nuvem.py` | Corpo enviado no `PUT` | Não contém o documento (lista fechada) |
| CT-10 | `test_setup_dados_nuvem.py` | Formulário com documento diferente do da nuvem | Empresa local criada com o documento da nuvem |
| CT-11 | `test_setup_dados_nuvem.py` | `PUT` responde 5xx ou sem rede | Nenhuma empresa local criada; `NUVEM_INDISPONIVEL` ou `SEM_CONEXAO` |
| CT-12 | `test_setup_dados_nuvem.py` | `PUT` responde 401, 403 ou 400 | Nenhuma empresa local; erro com o código recebido |
| CT-13 | `test_setup_dados_nuvem.py` | `GET` responde 404 | Setup como hoje, empresa só local |
| CT-14 | `reconnect.spec.ts` | Campo do documento no setup | Travado, sem edição |
| CT-15 | `reconnect.spec.ts` | Código conhecido no front | Mostra o texto da tabela |
| CT-16 | `reconnect.spec.ts` | Código desconhecido no front | Mostra a mensagem genérica |
| CT-17 | `reconnect.spec.ts` | Lista dos códigos citados nas specs LIC-01 a LIC-09 | Todos têm mensagem em `MENSAGENS_DE_CODIGO` |
| CT-18 | `reconnect.spec.ts` | `lerErroDaLicenca` com código em `detail` e com código no topo | Lê nos dois casos |
| CT-19 | `reconnect.spec.ts` | Tela de escolha depois do re-login | Com backup: só restaurar. Sem backup: só preencher |
| CT-20 | `reconnect.spec.ts` | Aviso de troca e cadastro `202` | Aviso aparece antes da chamada à API; `202` mostra a mensagem e leva ao re-login |
| CT-21 | `test_restaurar_backup_titular.py` | Semana atual sem full, semana anterior com full | Restaura o ciclo da semana anterior |
| CT-22 | `test_restaurar_backup_titular.py` | Trial com um full antigo | Restaura o ciclo do full do trial |
| CT-23 | `test_restaurar_backup_titular.py` | Nenhum full confirmado no `historicoEventos` | `404 BACKUP_INEXISTENTE` |

## 9. Testes existentes que a mudança afeta

- `test/api/v1/test_licenca_transferencia.py`: nenhuma mudança de contrato. Deve passar sem alteração.
- `test/api/v1/test_backup_preserva_licenca.py`: a restauração continua preservando a licença local. Deve passar sem alteração.

## 10. Perguntas antes da aprovação

- Nenhuma. Re-login sem backup (D-22) e o documento travado foram confirmados na revisão de conflitos (conflito 16 e bloco de documentação).

## 11. Observações

- Mudou o backend e o front: avisar o usuário para rodar `npm run build:sidecar` depois da entrega.
- A restauração é aplicada no próximo boot. A tela precisa avisar isso e não pode deixar o usuário clicar em sair no meio.

