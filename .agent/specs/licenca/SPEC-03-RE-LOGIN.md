# Licença 03 — Re-login, restauração e avisos de troca

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend (FastAPI) e Frontend (Vue 3 + TypeScript) |
| Dependências | SPEC-01 (backup cifrado, restauração que entende o formato 2), SPEC-02 (aviso de relógio e códigos de recusa) |
| Bloqueia     | — |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-07, D-08, D-11, D-16; quadro F10, F11, F16, F18, F19, F22 |

## 1. Objetivo

Fazer o caso 2 do re-login funcionar: o dono perdeu o banco, entra com a conta da loja e recupera os dados, em vez de cair num setup vazio. Também fazer o caso 1 avisar antes de qualquer troca de computador, e mostrar mensagens claras no lugar de textos técnicos.

## 2. Escopo

**Dentro do escopo**
- Nova rota `POST /api/v1/licenca/restaurar-backup`, para o titular que prova a senha (D-07).
- Tela de primeiro acesso oferece "Restaurar backup da nuvem" antes do setup, quando houver backup.
- Aviso antes de confirmar uma troca de computador (D-08, F18 e F22).
- Mensagens de erro vindas de código, com texto fixo em português (D-16, F10).
- Comparação do CPF ou CNPJ do setup com o documento do titular (D-11, F16). Depende de uma decisão pendente (seção 10).

**Fora do escopo**
- Trial com backup (D-06). É da API, na SPEC-05.
- Reenvio do link de primeiro acesso (F23). É da API, na SPEC-05.
- Contagem de troca na reinstalação. Já é feita pelo servidor. Esta spec só avisa.

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `backend-fastapi/app/api/v1/endpoints/licenca.py` | alterar | Rota `POST /restaurar-backup`. Público, como `/transferir`, porque roda antes do login. |
| `backend-fastapi/app/services/licenca/restauracao_titular.py` | criar | Confere a conta na nuvem, confere se a licença é a desta máquina e prepara a restauração. |
| `backend-fastapi/app/services/backup/restore.py` | alterar | Expõe `preparar_restauracao_do_titular(ciclo)`, sem exigir Master. |
| `backend-fastapi/app/services/sistema/setup.py` | alterar | Confere o documento informado com o do titular antes de criar a empresa. |
| `backend-fastapi/app/schemas/licenca/restauracao.py` | criar | Schemas `RestaurarBackupPayload` e `RestaurarBackupResposta`. |
| `frontend/src/modules/sign-in/services/sign-in.service.ts` | alterar | Função `restaurarBackupDaNuvem(email, senha, ciclo?)`. |
| `frontend/src/modules/sign-in/components/steps/ReconnectStep.vue` | alterar | Depois do re-login, mostra a escolha entre restaurar e começar do zero. |
| `frontend/src/modules/sign-in/composables/useSignIn.ts` | alterar | Novo passo `escolha-restauracao` no fluxo de re-login. |
| `frontend/src/modules/license/views/TransferirLicencaView.vue` | alterar | Aviso antes de confirmar a troca (texto da seção 6.4). |
| `frontend/src/shared/services/licenca.service.ts` | alterar | Tabela `MENSAGENS_DE_CODIGO` e função `mensagemDoCodigo(codigo)`. |
| `backend-fastapi/test/api/v1/test_restaurar_backup_titular.py` | criar | Casos CT-01 a CT-07. |
| `backend-fastapi/test/api/v1/test_setup_documento_titular.py` | criar | Casos CT-08 a CT-10. |
| `frontend/src/modules/sign-in/__tests__/reconnect.spec.ts` | criar | Casos CT-11 a CT-14. |

Testes existentes que precisam continuar passando: `test/api/v1/test_licenca_transferencia.py` (fluxo de transferência), `test/api/v1/test_backup_preserva_licenca.py` (restauração preserva a licença local).

## 4. Contrato da API

### 4.1. `POST /api/v1/licenca/restaurar-backup` (nova)

Público, como `/licenca/transferir`, porque roda antes de existir um login local. A proteção é a conta da loja e a licença já ativada nesta máquina.

**Corpo**

```json
{
  "email": "dono@exemplo.com.br",
  "senha": "senha-da-conta",
  "ciclo": null
}
```

`ciclo` é opcional. Quando `null`, a restauração usa o ciclo mais recente disponível.

**Regras de negócio**

1. A conta e a senha são conferidas na nuvem (`/erp/auth/login`), pelo mesmo caminho de `transferencia.py::_entrar_na_conta`.
2. O `licencaId` devolvido pela nuvem tem que ser igual ao `licenca_id` da licença local. Se for outro, recusa com `LICENCA_DE_OUTRA_CONTA`. Sem essa regra, qualquer conta poderia substituir o banco.
3. Só pode haver uma restauração pendente por vez.
4. A restauração é aplicada no próximo boot, pelo marcador que já existe em `restore.py`.

**Respostas**

| Status | Corpo | Quando |
|--------|-------|--------|
| 200 | `{ "status": "pendente_reinicio", "ciclo": "2026-11-17", "mensagem": "..." }` | Restauração preparada |
| 401 | `{ "codigo": "CREDENCIAIS_INVALIDAS", "mensagem": "E-mail ou senha da conta StartBig incorretos." }` | Senha errada |
| 403 | `{ "codigo": "LICENCA_DE_OUTRA_CONTA", "mensagem": "Esta conta não é dona da licença deste computador." }` | `licencaId` diferente |
| 404 | `{ "codigo": "BACKUP_INEXISTENTE", "mensagem": "Não há backup na nuvem para esta licença." }` | Sem backup |
| 409 | `{ "codigo": "RESTAURACAO_JA_PENDENTE", "mensagem": "Uma restauração já está pendente. Reinicie o sistema para aplicá-la." }` | Já existe marcador |
| 503 | `{ "codigo": "NUVEM_INDISPONIVEL", "mensagem": "O servidor da StartBig não respondeu. Tente de novo em alguns minutos." }` | Falha de rede ou 5xx |

Os códigos são os mesmos já usados em `transferencia.py`, para o front tratar tudo do mesmo jeito.

### 4.2. Mudança em `POST /api/v1/auth/reconnect` (existente)

Nenhuma mudança de contrato. O front passa a mostrar a escolha da seção 6.3 quando `inicializado` for `false`.

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

## 6. Especificação técnica

### 6.1. Restauração pelo titular (`restauracao_titular.py`)

```python
# restauracao_titular.py — o dono que provou a senha pode restaurar o banco dele (D-07)
from app.services.licenca.transferencia import _entrar_na_conta
from app.db.crud.configuracao import licenca as licenca_crud

def conferir_titular_da_licenca(db, email: str, senha: str) -> None:
    # 1. Confere a senha na nuvem. Erros saem com o mesmo código de transferencia.py.
    resposta = _entrar_na_conta(email, senha, obter_hwid())
    # 2. A conta tem que ser dona da licença que está gravada aqui.
    local = licenca_crud.get_licenca(db)
    if local is None or local.licenca_id != resposta.licencaId:
        raise _erro(403, "LICENCA_DE_OUTRA_CONTA",
                    "Esta conta não é dona da licença deste computador.")
```

Depois disso, a função chama `download_chain` (`services/cloud/download.py`) e `prepare_restore` (`services/backup/restore.py`), sem passar pela rota de Master.

### 6.2. Escolha depois do re-login (front)

Quando `inicializado` volta `false`, o fluxo em `useSignIn.ts` leva a uma tela com duas opções. O texto é fixo:

| Elemento | Texto |
|----------|-------|
| Título | Sua licença foi encontrada |
| Corpo | Se você já usava o sistema neste computador ou em outro, é possível recuperar os dados do último backup da nuvem. |
| Botão principal | Restaurar backup da nuvem |
| Botão secundário | Começar do zero |
| Aviso, quando não houver backup | Não há backup na nuvem para esta licença. Você pode começar do zero. |

"Começar do zero" segue o setup atual, sem mudança.

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

### 6.4. Mensagens por código (D-16, F10)

`licenca.service.ts` guarda uma tabela fixa. Quando o código não está na tabela, a tela mostra a mensagem genérica "Não foi possível concluir agora. Tente de novo em instantes." e nunca o texto da exceção.

```typescript
// licenca.service.ts — texto fixo para cada código de erro da licença (D-16)
export const MENSAGENS_DE_CODIGO: Record<string, string> = {
  CREDENCIAIS_INVALIDAS: 'E-mail ou senha da conta StartBig incorretos.',
  LICENCA_TRANSFERIDA: 'Esta licença foi transferida para outro computador.',
  LICENCA_DE_OUTRA_CONTA: 'Esta conta não é dona da licença deste computador.',
  BACKUP_INEXISTENTE: 'Não há backup na nuvem para esta licença.',
  RESTAURACAO_JA_PENDENTE: 'Uma restauração já está pendente. Reinicie o sistema para aplicá-la.',
  NUVEM_INDISPONIVEL: 'O servidor da StartBig não respondeu. Tente de novo em alguns minutos.',
};

// Devolve a mensagem do código, ou a mensagem genérica se o código não existir.
export function mensagemDoCodigo(codigo: string | undefined): string {
  return MENSAGENS_DE_CODIGO[codigo ?? ''] ?? 'Não foi possível concluir agora. Tente de novo em instantes.';
}
```

### 6.5. Documento do titular no setup (D-11, F16)

Hoje `setup.py` não compara o CPF ou CNPJ informado com o do titular. A comparação exige que a nuvem devolva o documento do titular. Essa resposta ainda não existe na API. A seção 10 traz a recomendação.

## 7. Critérios de aceite

- **CA-01:** no caso 2, depois do re-login com backup disponível, a tela oferece restaurar antes do setup, com os textos da seção 6.2.
- **CA-02:** a restauração com a senha certa e a licença desta máquina prepara o backup e pede reinicialização.
- **CA-03:** conta de outra licença recebe 403 e o banco não muda.
- **CA-04:** trocar o servidor mostra o aviso da seção 6.3 antes de qualquer chamada à API.
- **CA-05:** nenhum erro mostra texto técnico do servidor (sem "Expecting value", sem nome de classe).
- **CA-06:** com o documento do titular disponível, um CPF diferente pede confirmação.

CA-01 e CA-02 precisam do sistema rodando (`verify`). Ficam marcados como verificados por teste automatizado, e a verificação no app é feita na skill `verify` no fim da série.

## 8. Casos de teste

| ID | Caso | Esperado |
|----|------|----------|
| CT-01 | Senha certa, licença desta máquina | 200, `pendente_reinicio` |
| CT-02 | Senha errada | 401, `CREDENCIAIS_INVALIDAS`, nada preparado |
| CT-03 | Conta de outra licença | 403, `LICENCA_DE_OUTRA_CONTA`, nada preparado |
| CT-04 | Sem backup na nuvem | 404, `BACKUP_INEXISTENTE` |
| CT-05 | Já existe restauração pendente | 409, `RESTAURACAO_JA_PENDENTE` |
| CT-06 | Nuvem fora do ar | 503, `NUVEM_INDISPONIVEL` |
| CT-07 | Restauração com ciclo informado | Usa o ciclo pedido |
| CT-08 | CPF do setup igual ao do titular | Segue o setup |
| CT-09 | CPF diferente do titular | Pede confirmação (erro `DOCUMENTO_DIFERENTE` até a confirmação) |
| CT-10 | Titular sem documento na resposta da nuvem | Segue o setup e registra aviso no log |
| CT-11 | Código conhecido no front | Mostra o texto da tabela |
| CT-12 | Código desconhecido no front | Mostra a mensagem genérica |
| CT-13 | Tela de escolha depois do re-login sem backup | Mostra o aviso e só "Começar do zero" |
| CT-14 | Aviso de troca aparece antes da chamada à API | Sim |

## 9. Testes existentes que a mudança afeta

- `test/api/v1/test_licenca_transferencia.py`: nenhuma mudança de contrato. Deve passar sem alteração.
- `test/api/v1/test_backup_preserva_licenca.py`: a restauração continua preservando a licença local. Deve passar sem alteração.

## 10. Perguntas antes da aprovação

- **Como comparar o documento do titular (D-11).** A nuvem precisa devolver o documento, e não dá para comparar com um CPF inteiro sem expor dados.
  - **A.** A API devolve os últimos 4 dígitos do documento do titular na resposta de login. O app compara só esses 4 dígitos. Recomendo esta opção: não expõe o documento completo e cobre o erro de digitação.
  - **B.** A API devolve o documento completo, criptografado com a chave de ativação. Mais seguro, mas mais complexo.
  - **C.** O app não compara; só mostra o documento do titular para o dono conferir visualmente.

## 11. Observações

- Mudou o backend e o front: avisar o usuário para rodar `npm run build:sidecar` depois da entrega.
- A restauração é aplicada no próximo boot. A tela precisa avisar isso e não pode deixar o usuário clicar em sair no meio.
