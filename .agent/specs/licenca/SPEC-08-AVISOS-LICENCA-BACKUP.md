# Licença 08 — Avisos de licença e de backup

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend (FastAPI) e Frontend (Vue 3 + TypeScript) |
| Dependências | SPEC-02 (gera `aviso` e `estimativa`), SPEC-01 (gera `PASTA_DADOS_ABERTA`). Integração com a SPEC-05, com rede de segurança: sem os códigos novos, a tela mostra os de hoje |
| Bloqueia     | — |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-05, D-06, D-19; quadro F7, F15, F26 |

> **Origem (2026-11-18):** nasceu na revisão de conflitos (conflito 13), reunindo avisos que outras specs geram e que nenhuma tela mostrava. O número 07 está reservado para o TLS na rede da loja.

> **Revisão 2 (2026-11-19, conflito 22):** a versão anterior supunha que o envio para a nuvem "recebe recusa de hora em hora" e criava uma pausa em memória (`estado_envio.py`). Na verdade, o start-big consulta o `GET /erp/backup/status` antes de enviar e **para em silêncio** quando ele diz que o plano não permite (`backend-fastapi/app/services/cloud/flow.py:26-27`). A pausa saiu: o aviso passa a ser o **código do último ciclo de envio** (o `codigoBloqueio` do `/status` ou o código do erro). Entrou o código `TRIAL_BACKUP_USADO` (SPEC-05).

> **Revisão 3 (2026-11-19):** mockups aprovados pelo usuário. A referência de design desta spec são os quadros 4 e 9 (faixa do relógio e dias estimados) e 5 (avisos na tela de backup) da página [https://claude.ai/artifact/E5SohwYLXt3pY84pCFwj6z](https://claude.ai/artifact/E5SohwYLXt3pY84pCFwj6z) (skill `design`). Propostas aprovadas junto: a faixa do relógio **não tem botão de fechar** (some sozinha quando o aviso deixa de vir); o aviso `TRIAL_BACKUP_USADO` tem o botão "Assinar", que leva à tela de renovação que já existe (`/renovar-assinatura`).

## 1. Objetivo

O dono precisa **saber** quando algo que o protege não está funcionando. Hoje o sistema detecta (ou vai detectar) estas situações e só registra no log:

- o relógio do computador voltou no tempo (D-05: "o app avisa o dono");
- sem internet, os dias restantes da licença são um cálculo local;
- o backup na nuvem está parado: a loja em teste já usou o seu backup (D-06), a licença não está ativa, ou o computador deixou de ser o servidor;
- a pasta de dados está aberta para outros usuários do Windows.

## 2. Escopo

**Dentro do escopo**
- Faixa de aviso quando `GET /licenca/status` trouxer `aviso: "relogio_recuou"`.
- Rótulo "estimado" nos dias restantes quando a resposta trouxer `estimativa: true`.
- Guardar o resultado do último ciclo de envio para a nuvem (código e horário).
- A tela de backup mostra o motivo quando o backup na nuvem está parado.
- A tela de backup mostra o aviso `PASTA_DADOS_ABERTA`.

**Fora do escopo**
- Gerar os avisos (SPEC-01 e SPEC-02) e os códigos (SPEC-05).
- Mudar o comportamento do envio para a nuvem: ele continua parando pelo `/status`, como hoje.

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `backend-fastapi/app/services/cloud/ultimo_ciclo.py` | criar | `registrar(codigo)` e `ler()`: o código e o horário do último ciclo de envio (§6.2). |
| `backend-fastapi/app/core/tarefas.py` | alterar | `_loop_cloud_sync` (linha ~190) registra o código de cada ciclo: o `code` do `SyncResponse` quando o ciclo para por bloqueio, ou o `code` do `CloudSyncError`. |
| `backend-fastapi/app/core/permissoes.py` | alterar | Guarda o resultado de `verificar_pasta_de_dados` (SPEC-01) para a tela consultar. |
| `backend-fastapi/app/api/v1/endpoints/backup.py` | alterar | Nova rota `GET /backup/avisos` (§4.1). |
| `frontend/src/modules/configuracoes/services/backup.service.ts` | alterar | `getAvisosBackup()`. |
| `frontend/src/modules/configuracoes/components/sections/backup-dados/components/BackupDados.vue` | alterar | Mostra os avisos (§6.3). |
| `frontend/src/shared/services/licenca.service.ts` | alterar | `LicencaStatusResponse` ganha `aviso?` e `estimativa?`. |
| `frontend/src/modules/mainLayout/components/ui/LicencaStatusBadge.vue` | alterar | Rótulo "estimado" nos dias e faixa do relógio (§6.1). |
| `backend-fastapi/test/services/cloud/test_ultimo_ciclo.py` | criar | Casos CT-01 a CT-05. |
| `frontend/src/modules/configuracoes/__tests__/avisos-backup.spec.ts` | criar | Casos CT-06 a CT-09. |
| `frontend/src/modules/mainLayout/__tests__/licenca-avisos.spec.ts` | criar | Casos CT-10 e CT-11. |

## 4. Contrato da API

### 4.1. `GET /api/v1/backup/avisos` (nova)

Protegida como as outras rotas de backup. Lista vazia significa "nada a avisar".

```json
{
  "avisos": [
    { "codigo": "TRIAL_BACKUP_USADO", "desde": "2026-11-18T10:00:00" },
    { "codigo": "PASTA_DADOS_ABERTA", "desde": "2026-11-18T08:02:00" }
  ]
}
```

A tela traduz cada `codigo` pela tabela da §6.3. O backend não manda texto, para a mensagem ficar num lugar só.

### 4.2. Códigos que o ciclo de envio pode registrar

| Origem | Códigos |
|--------|---------|
| `codigoBloqueio` do `/erp/backup/status` (ciclo parado em silêncio) | `TRIAL_BACKUP_USADO` (SPEC-05), `TRIAL` (API antiga), `LICENCA_VENCIDA`, `LICENCA_SUSPENSA`, `LICENCA_BLOQUEADA`, `LICENCA_REVOGADA` |
| Erro do `/erp/backup/*` (`CloudSyncError`) | `BACKUP_MAQUINA_REVOGADA`, `BACKUP_HWID_AUSENTE`, `LICENCA_HWID_REVOGADO` (SPEC-05) |

Um ciclo que envia com sucesso, ou que não tem nada novo, limpa o aviso.

## 5. Schemas

```python
# Resposta de GET /backup/avisos
from datetime import datetime
from pydantic import BaseModel


class AvisoBackup(BaseModel):
    codigo: str          # um dos códigos da §4.2 ou PASTA_DADOS_ABERTA
    desde: datetime      # quando o aviso começou


class AvisosBackupResposta(BaseModel):
    avisos: list[AvisoBackup]
```

## 6. Especificação técnica

### 6.1. Relógio e dias estimados (D-05, F26)

A SPEC-02 inclui `aviso: "relogio_recuou"` e `estimativa: true` na resposta de `GET /licenca/status`. O front mostra:

| Situação | Onde | Texto |
|----------|------|-------|
| `aviso = "relogio_recuou"` | Faixa no topo, enquanto o aviso vier | O relógio deste computador está atrasado. Ajuste a data e a hora do Windows para a licença continuar funcionando sem internet. |
| `estimativa = true` | Ao lado dos dias, no `LicencaStatusBadge` | (estimado, sem internet) |

A faixa não bloqueia nada (D-05) e não tem botão de fechar: ela some sozinha quando o `/licenca/status` deixa de trazer o aviso.

### 6.2. Resultado do último ciclo (`ultimo_ciclo.py`)

```python
# ultimo_ciclo.py — lembra o código do último ciclo de envio para a nuvem (LIC-08).
# Não muda o comportamento do envio: só guarda o que aconteceu, para a tela mostrar.
from datetime import datetime

_ultimo: dict | None = None            # None = último ciclo sem nada a avisar


def registrar(codigo: str | None) -> None:
    """Chamado ao fim de cada ciclo. `None` = enviou, ou não havia nada novo: limpa o aviso."""
    global _ultimo
    if codigo is None:
        _ultimo = None
    elif _ultimo is None or _ultimo["codigo"] != codigo:
        _ultimo = {"codigo": codigo, "desde": datetime.now()}   # mantém o "desde" se o código se repete


def ler() -> dict | None:
    return _ultimo
```

O valor fica **em memória**, sem tabela nova. O ciclo roda a cada hora (`tarefas.py`), e o primeiro ciclo depois do boot já preenche o valor. Antes dele, a tela não mostra aviso de backup, e isso é esperado.

### 6.3. Avisos na tela de backup

`BackupDados.vue` consulta `GET /backup/avisos` ao abrir e mostra um quadro para cada aviso:

| Código | Texto |
|--------|-------|
| `TRIAL_BACKUP_USADO` | Período de teste: 1 backup na nuvem, feito em {data}. Assine para ter backups contínuos. Com o botão "Assinar", que abre `/renovar-assinatura`. |
| `TRIAL` | O backup na nuvem não está disponível no período de teste. |
| `LICENCA_VENCIDA` | Licença vencida: o backup na nuvem volta quando a assinatura for renovada. |
| `LICENCA_SUSPENSA`, `LICENCA_BLOQUEADA`, `LICENCA_REVOGADA` | A licença não está ativa: o backup na nuvem está parado. Fale com o suporte. |
| `BACKUP_MAQUINA_REVOGADA`, `LICENCA_HWID_REVOGADO` | Este computador não é mais o servidor da licença. O backup na nuvem está parado. |
| `BACKUP_HWID_AUSENTE` | O backup na nuvem está parado por um problema na licença. Entre de novo com a conta StartBig. |
| `PASTA_DADOS_ABERTA` | A pasta de dados do sistema está aberta para outros usuários deste computador. Peça ao técnico para restringir o acesso. |
| Outro código | O backup na nuvem não foi concluído. Tente de novo mais tarde. |

O "feito em {data}" do trial vem do `historicoEventos` do `/status` (o full confirmado mais recente).

## 7. Critérios de aceite

- **CA-01:** com o relógio recuado, a faixa aparece e o sistema continua funcionando.
- **CA-02:** sem internet, os dias restantes aparecem com "(estimado, sem internet)".
- **CA-03:** loja em teste, depois do único backup, vê o aviso do trial na tela de backup.
- **CA-04:** o computador que deixou de ser servidor mostra o motivo na tela de backup.
- **CA-05:** depois de um ciclo que envia com sucesso, o aviso de backup some.
- **CA-06:** com a pasta de dados aberta, a tela de backup mostra o aviso.
- **CA-07:** com a API sem a SPEC-05, a tela mostra os códigos de hoje (`TRIAL`, `LICENCA_*`).

CA-01, CA-04 e CA-06 também são verificados no app pela skill `verify`, no fim da série.

## 8. Casos de teste

| ID | Arquivo | Caso | Esperado |
|----|---------|------|----------|
| CT-01 | `test_ultimo_ciclo.py` | Ciclo parado com `codigoBloqueio = TRIAL_BACKUP_USADO` | Registrado com o horário |
| CT-02 | `test_ultimo_ciclo.py` | `CloudSyncError` com `BACKUP_MAQUINA_REVOGADA` | Registrado |
| CT-03 | `test_ultimo_ciclo.py` | O mesmo código em dois ciclos seguidos | O `desde` não muda |
| CT-04 | `test_ultimo_ciclo.py` | Ciclo com envio confirmado depois de um aviso | Aviso limpo |
| CT-05 | `test_ultimo_ciclo.py` | `GET /backup/avisos` com aviso de ciclo e pasta aberta | Os dois avisos, com `desde` |
| CT-06 | `avisos-backup.spec.ts` | Aviso `TRIAL_BACKUP_USADO` | Texto do trial com a data |
| CT-07 | `avisos-backup.spec.ts` | Aviso `PASTA_DADOS_ABERTA` | Texto da pasta aberta |
| CT-08 | `avisos-backup.spec.ts` | Código desconhecido | Texto genérico |
| CT-09 | `avisos-backup.spec.ts` | Lista vazia | Nenhum quadro de aviso |
| CT-10 | `licenca-avisos.spec.ts` | `aviso: "relogio_recuou"` | Faixa visível, sem bloquear a navegação |
| CT-11 | `licenca-avisos.spec.ts` | `estimativa: true` | Rótulo "(estimado, sem internet)" |

## 9. Testes existentes que a mudança afeta

- Testes do envio para a nuvem (`services/cloud`): o comportamento do envio não muda; só o registro do código é acrescentado.

## 10. Perguntas antes da aprovação

- Nenhuma. O conteúdo foi decidido na revisão de conflitos (conflitos 2, 13 e 22).

## 11. Observações

- Mudou o backend e o front: avisar o usuário para rodar `npm run build:sidecar` depois da entrega.
