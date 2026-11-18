# Licença 08 — Avisos de licença e de backup

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend (FastAPI) e Frontend (Vue 3 + TypeScript) |
| Dependências | SPEC-02 (gera `aviso` e `estimativa`), SPEC-01 (gera `PASTA_DADOS_ABERTA`). Integração com a SPEC-05, com rede de segurança: sem os códigos novos, nada muda |
| Bloqueia     | — |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-05, D-06, D-19; quadro F7, F15, F26 |

> **Origem (2026-11-18):** esta spec nasceu na revisão de conflitos (conflito 13). Ela reúne avisos que outras specs geram e que nenhuma tela mostrava: o relógio que recuou (SPEC-02), os dias estimados offline (SPEC-02), as recusas novas de backup da API (SPEC-05) e a pasta de dados aberta (SPEC-01, conflito 2). O número 07 está reservado para o TLS na rede da loja.

## 1. Objetivo

O dono precisa **saber** quando algo que o protege não está funcionando. Hoje o sistema detecta (ou vai detectar) estas situações e só registra no log:

- o relógio do computador voltou no tempo (D-05: "o app avisa o dono");
- sem internet, os dias restantes da licença são um cálculo local;
- a loja em teste já usou o seu único backup na nuvem (D-06), e o envio de hora em hora recebe recusa sem ninguém saber;
- o computador deixou de ser o servidor da licença, e o envio de backup é recusado;
- a pasta de dados está aberta para outros usuários do Windows.

## 2. Escopo

**Dentro do escopo**
- Faixa de aviso quando `GET /licenca/status` trouxer `aviso: "relogio_recuou"`.
- Rótulo "estimado" nos dias restantes quando a resposta trouxer `estimativa: true`.
- O envio para a nuvem entende `BACKUP_TRIAL_LIMITE`, `BACKUP_MAQUINA_REVOGADA`, `LICENCA_HWID_REVOGADO` e `BACKUP_HWID_AUSENTE`: pausa os envios e guarda o motivo.
- A tela de backup mostra o motivo da pausa.
- A tela de backup mostra o aviso `PASTA_DADOS_ABERTA`.

**Fora do escopo**
- Gerar os avisos (SPEC-01 e SPEC-02) e os códigos (SPEC-05).
- Mudar a regra do trial (D-06) ou da troca de servidor.

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `backend-fastapi/app/services/cloud/sync.py` | alterar | Reconhece os códigos da §4.2 e pausa os envios, guardando o motivo (§6.2). |
| `backend-fastapi/app/services/cloud/estado_envio.py` | criar | `pausar(motivo)`, `motivo_da_pausa()` e `retomar()`. Estado em memória (§6.2). |
| `backend-fastapi/app/core/tarefas.py` | alterar | `_loop_cloud_sync` (linha ~190) pula o ciclo enquanto houver pausa. |
| `backend-fastapi/app/core/permissoes.py` | alterar | Guarda o resultado de `verificar_pasta_de_dados` (SPEC-01) para a tela consultar. |
| `backend-fastapi/app/api/v1/endpoints/backup.py` | alterar | Nova rota `GET /backup/avisos` (§4.1). |
| `frontend/src/modules/configuracoes/services/backup.service.ts` | alterar | `getAvisosBackup()`. |
| `frontend/src/modules/configuracoes/components/sections/backup-dados/components/BackupDados.vue` | alterar | Mostra os avisos de backup e de pasta aberta (§6.3). |
| `frontend/src/shared/services/licenca.service.ts` | alterar | `LicencaStatusResponse` ganha `aviso?` e `estimativa?`. |
| `frontend/src/modules/mainLayout/components/ui/LicencaStatusBadge.vue` | alterar | Rótulo "estimado" nos dias e faixa do relógio (§6.1). |
| `backend-fastapi/test/services/cloud/test_pausa_envio.py` | criar | Casos CT-01 a CT-06. |
| `frontend/src/modules/configuracoes/__tests__/avisos-backup.spec.ts` | criar | Casos CT-07 a CT-09. |
| `frontend/src/modules/mainLayout/__tests__/licenca-avisos.spec.ts` | criar | Casos CT-10 e CT-11. |

## 4. Contrato da API

### 4.1. `GET /api/v1/backup/avisos` (nova)

Protegida como as outras rotas de backup. Devolve só avisos; uma lista vazia significa "nada a avisar".

```json
{
  "avisos": [
    { "codigo": "BACKUP_TRIAL_LIMITE", "desde": "2026-11-18T10:00:00" },
    { "codigo": "PASTA_DADOS_ABERTA", "desde": "2026-11-18T08:02:00" }
  ]
}
```

A tela traduz cada `codigo` pela tabela da §6.3. O backend não manda texto, para a mensagem ficar num lugar só.

### 4.2. Códigos da API StartBig que o envio para a nuvem passa a entender (SPEC-05)

| Código | O que significa | Ação do envio |
|--------|-----------------|---------------|
| `BACKUP_TRIAL_LIMITE` | A loja em teste já fez o seu único backup completo | Pausa até a licença deixar de ser de teste |
| `BACKUP_MAQUINA_REVOGADA` | Este computador não é mais o servidor da licença | Pausa |
| `LICENCA_HWID_REVOGADO` | Idem, recusado pelo guard (depois de renovar o token uma vez, como já faz o `_http.py`) | Pausa |
| `BACKUP_HWID_AUSENTE` | O token não tem o HWID. Não deveria acontecer no servidor | Registra no log e pausa |

Enquanto a API não tiver a SPEC-05, esses códigos nunca chegam, e o envio funciona como hoje.

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

A faixa não bloqueia nada (D-05).

### 6.2. Pausa do envio para a nuvem (`estado_envio.py`)

```python
# estado_envio.py — lembra por que o envio para a nuvem está pausado (LIC-08)
from datetime import datetime

_pausa: dict | None = None            # None = enviando normalmente


def pausar(codigo: str) -> None:
    """Guarda o motivo e a hora. Chamado quando a API recusa o envio com um código da §4.2."""
    global _pausa
    if _pausa is None or _pausa["codigo"] != codigo:
        _pausa = {"codigo": codigo, "desde": datetime.now()}


def motivo_da_pausa() -> dict | None:
    return _pausa


def retomar() -> None:
    """Volta a enviar. Chamado quando a licença muda (renovou, deixou de ser teste, re-login)."""
    global _pausa
    _pausa = None
```

O estado fica **em memória**, sem tabela nova. Quando o backend reinicia, o primeiro envio tenta de novo; se a API recusar outra vez, a pausa volta. Uma tentativa a cada boot é aceitável, e evita uma migração só para isso.

`retomar()` é chamado quando a validação da licença percebe que ela mudou: deixou de ser de teste, foi renovada, ou o computador voltou a ser o servidor por um re-login.

### 6.3. Avisos na tela de backup

`BackupDados.vue` consulta `GET /backup/avisos` ao abrir e mostra um quadro para cada aviso:

| Código | Texto |
|--------|-------|
| `BACKUP_TRIAL_LIMITE` | Período de teste: 1 backup na nuvem, feito em {data}. Assine para ter backups contínuos. |
| `BACKUP_MAQUINA_REVOGADA`, `LICENCA_HWID_REVOGADO` | Este computador não é mais o servidor da licença. O backup na nuvem está pausado. |
| `BACKUP_HWID_AUSENTE` | O backup na nuvem está pausado por um problema na licença. Entre de novo com a conta StartBig. |
| `PASTA_DADOS_ABERTA` | A pasta de dados do sistema está aberta para outros usuários deste computador. Peça ao técnico para restringir o acesso. |

O "feito em {data}" do trial vem do último envio confirmado no journal da nuvem (`cloud_journal.get_ciclos_enviados()`).

## 7. Critérios de aceite

- **CA-01:** com o relógio recuado, a faixa aparece e o sistema continua funcionando.
- **CA-02:** sem internet, os dias restantes aparecem com "(estimado, sem internet)".
- **CA-03:** loja em teste, depois do único backup, não tenta enviar de hora em hora, e a tela de backup mostra o aviso do trial.
- **CA-04:** o computador que deixou de ser servidor para de enviar backup, e a tela mostra o motivo.
- **CA-05:** quando a licença deixa de ser de teste, o envio volta sozinho.
- **CA-06:** com a pasta de dados aberta, a tela de backup mostra o aviso.
- **CA-07:** com a API sem a SPEC-05, o envio funciona como hoje.

CA-01, CA-04 e CA-06 também são verificados no app pela skill `verify`, no fim da série.

## 8. Casos de teste

| ID | Arquivo | Caso | Esperado |
|----|---------|------|----------|
| CT-01 | `test_pausa_envio.py` | API recusa com `BACKUP_TRIAL_LIMITE` | Pausa com o código; o próximo ciclo não chama a API |
| CT-02 | `test_pausa_envio.py` | API recusa com `BACKUP_MAQUINA_REVOGADA` | Pausa com o código |
| CT-03 | `test_pausa_envio.py` | `401 LICENCA_HWID_REVOGADO` depois de renovar o token | Pausa com o código |
| CT-04 | `test_pausa_envio.py` | Licença deixa de ser de teste | `retomar()`; o próximo ciclo envia |
| CT-05 | `test_pausa_envio.py` | Recusa sem código conhecido | Comportamento de hoje (registra e encerra o ciclo, sem pausa) |
| CT-06 | `test_pausa_envio.py` | `GET /backup/avisos` com pausa e pasta aberta | Os dois avisos, com `desde` |
| CT-07 | `avisos-backup.spec.ts` | Aviso `BACKUP_TRIAL_LIMITE` | Texto do trial com a data |
| CT-08 | `avisos-backup.spec.ts` | Aviso `PASTA_DADOS_ABERTA` | Texto da pasta aberta |
| CT-09 | `avisos-backup.spec.ts` | Lista vazia | Nenhum quadro de aviso |
| CT-10 | `licenca-avisos.spec.ts` | `aviso: "relogio_recuou"` | Faixa visível, sem bloquear a navegação |
| CT-11 | `licenca-avisos.spec.ts` | `estimativa: true` | Rótulo "(estimado, sem internet)" |

## 9. Testes existentes que a mudança afeta

- Testes do envio para a nuvem (`services/cloud`): o caminho sem código novo não muda.

## 10. Perguntas antes da aprovação

- Nenhuma. O conteúdo foi decidido na revisão de conflitos (conflitos 2 e 13).

## 11. Observações

- Mudou o backend e o front: avisar o usuário para rodar `npm run build:sidecar` depois da entrega.
