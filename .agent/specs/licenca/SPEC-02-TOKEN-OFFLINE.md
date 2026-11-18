# Licença 02 — Confiança no token offline e nos dias restantes

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend (FastAPI) |
| Dependências | SPEC-01 (o token e a chave passam a ser lidos por `segredos_licenca.py`) |
| Bloqueia     | SPEC-03, LIC-08 (os avisos desta spec são mostrados pela LIC-08) |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-05, D-13, D-14, D-15; quadro F7, F8, F24, F25, F26, F27 |

> **Revisão 1 (2026-11-18):** revisão de conflitos com o usuário, antes da aprovação.
> - **Conflito 9:** as claims foram conferidas no `aalan-big/plataformaADM` (`apps/server/src/features/dispositivos/dispositivo.service.ts:275-307`). O token já traz `licencaId`, `hwid`, `dataVencimento`, `gracePeriodDias`, `proximaValidacaoEm`, `emCarencia`, `dataLimiteCarencia` e `modulos`. A spec não depende de mudança na API.
> - **Conflito 18 (D-14 revista):** "bloquear com lista vazia" não bloqueia nada, porque no app lista vazia significa "não sei, libera" (`app/core/modulos.py:77-93`, `modulos.store.ts:43-74`). A §6.3 foi reescrita: com internet, a chave pública ilegível é buscada de novo, como o caminho sem internet já faz.
> - **Conflito 13:** o aviso de relógio e o rótulo de estimativa são mostrados pela **LIC-08**, não pela SPEC-03.
> - **Documentação:** a recusa por código cita o F27 (antes, o D-16, que no ACORDO é "mensagem de tela por código"). Os códigos de vencimento são da SPEC-05, não da SPEC-06. O CT-17 ganhou arquivo de teste.

## 1. Objetivo

Fazer o app confiar só no que a API assinou. Hoje ele confia em colunas do banco que qualquer pessoa edita, e recalcula datas com o relógio do computador. Depois desta spec:

- a carência, o vencimento e os prazos offline vêm do token assinado;
- o token só vale para a licença e para a máquina a que pertence;
- os módulos nunca são lidos com uma chave pública ilegível;
- o número de dias restantes é o que a API informou;
- o relógio do computador que voltou no tempo gera aviso, e não bloqueia o PDV (D-05).

## 2. Escopo

**Dentro do escopo**
- Ler `dataVencimento`, `emCarencia` e `dataLimiteCarencia` do token assinado (D-13).
- Validar `licencaId` e `hwid` do token contra a licença local e `obter_hwid()` (D-15).
- Com internet, buscar de novo a chave pública quando a local não abrir, antes de ler os módulos (D-14 revista).
- Usar `diasRestantes` e `diasRestantesCarencia` da API (F26).
- Ramificar a recusa de `/licenca/conectar` pelo `codigo` da API, quando ele existir (F27, lado do app).
- Guardar o maior horário visto e gerar o aviso quando o relógio voltar (D-05).

**Fora do escopo**
- Reduzir a validade do token para 24 h (ACORDO D-04, alternativa B).
- Mudanças na API. O código `LICENCA_VENCIDA` no `/licenca/conectar` é da SPEC-05.
- Tela do front. O aviso de relógio e o rótulo "estimado" são mostrados pela LIC-08.

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `backend-fastapi/app/services/licenca/validacao.py` | alterar | `_validar_offline` lê vencimento, carência e prazos do token. `_tentar_conexao_remota` usa `diasRestantes` da API. No caminho online, chave pública ilegível → `resgatar_chave_publica_online` antes de ler os módulos. |
| `backend-fastapi/app/services/licenca/recusa.py` | alterar | `_recusa_por_vencimento` já olha o `codigo` antes do texto; acrescentar `LICENCA_VENCIDA` e `LICENCA_TRANSFERIDA` aos códigos reconhecidos. `_carencia_vigente` passa a receber o valor vindo do token. |
| `backend-fastapi/app/services/licenca/relogio.py` | criar | `verificar_relogio(licenca, agora)` e `registrar_horario(licenca, agora)`. Um único ponto de decisão sobre o relógio. |
| `backend-fastapi/app/db/models/configuracao_licenca.py` | alterar | Coluna nova `ultimo_horario_visto` (DateTime, nullable). |
| `backend-fastapi/alembic/versions/` | criar | Migração que adiciona `ultimo_horario_visto` só se a coluna não existir. |
| `backend-fastapi/app/services/licenca/sincronizacao.py` | alterar | Grava as colunas de carência também na renovação em segundo plano (F25). As colunas viram só informação de tela; a decisão vem do token. |
| `backend-fastapi/test/api/v1/test_licenca_validacao_offline.py` | alterar | Fixtures passam a montar o token com as claims. |
| `backend-fastapi/test/api/v1/test_licenca_recusa_vencimento.py` | alterar | Casos com `codigo` e casos sem `codigo`. |
| `backend-fastapi/test/api/v1/test_licenca_transferencia.py` | alterar | Ajustar só o que depende da leitura de claims. |
| `backend-fastapi/test/services/licenca/test_token_offline.py` | criar | Casos CT-01 a CT-12, CT-17 e CT-18. |
| `backend-fastapi/test/services/licenca/test_relogio.py` | criar | Casos CT-13 a CT-16. |

## 4. Contrato consumido

Rota: `POST /licenca/conectar` da API StartBig (`apps/server/src/features/dispositivos/dispositivo.service.ts`, método `conectar`).

Claims do token que este módulo passa a usar (conferidas no `plataformaADM`):

| Claim | Uso |
|-------|-----|
| `licencaId`, `hwid` | Conferir a identidade do token (D-15) |
| `dataVencimento` | Vencimento do plano no modo offline (D-13) |
| `emCarencia`, `dataLimiteCarencia` | Carência no modo offline (D-13) |
| `modulos` | Módulos liberados (já usado hoje) |

Campos da resposta (fora do token) que passam a ser usados:

| Campo | Uso |
|-------|-----|
| `diasRestantes` | Mostrado no lugar do cálculo local (F26). A API deixa fora do token de propósito, para não congelar o número por 7 dias |
| `diasRestantesCarencia` | Mostrado durante a carência |

Códigos de recusa que o app trata:

| `codigo` | Status HTTP | Tratamento no app |
|----------|-------------|-------------------|
| `LICENCA_TRANSFERIDA` | 400 | Erro `LICENCA_TRANSFERIDA`, para o front levar à tela de transferência. A API já manda este código hoje |
| `LICENCA_VENCIDA` | 402 (depois da SPEC-05) ou 400 | Erro `LICENCA_EXPIRADA` |
| (sem `codigo`) | qualquer | Cai na leitura do texto, como hoje. Hoje o `conectar` manda `400 "Licença vencida."` sem código |

O tratamento sem `codigo` é a rede de segurança: a SPEC-02 não depende da SPEC-05 para funcionar.

## 5. Schemas

Nenhum schema da API muda. A resposta de `GET /licenca/status` ganha dois campos opcionais, que a LIC-08 mostra:

| Campo | Quando aparece |
|-------|----------------|
| `aviso: "relogio_recuou"` | `verificar_relogio` detectou o recuo |
| `estimativa: true` | O número de dias foi calculado offline |

Mudança interna: a coluna `ultimo_horario_visto` em `configuracao_licenca`. `NULL` significa "ainda não registrado".

## 6. Especificação técnica

### 6.1. Carência e vencimento vêm do token (D-13)

Hoje `_validar_offline` lê `licenca.data_vencimento`, `licenca.em_carencia` e `licenca.data_limite_carencia`. A mudança é ler as claims do token assinado. A verificação da assinatura continua obrigatória.

```python
# validacao.py — lê vencimento e carência do token assinado, não de uma coluna editável (D-13)
from datetime import datetime
from jose import jwt  # biblioteca que confere a assinatura do token


def _claims_do_token(token: str, chave_publica: str) -> dict:
    # Confere a assinatura RS256. Se a assinatura não bater, lança erro.
    # A validade ('exp') continua sendo conferida: token vencido também é recusado.
    return jwt.decode(
        token,
        chave_publica,
        algorithms=["RS256"],             # aceita só o algoritmo que a API usa
        options={"verify_aud": False},    # a API não envia 'aud'
    )


def _data_da_claim(valor: str | None) -> datetime | None:
    # A API manda datas em ISO com "Z" no fim (UTC). Trocar o "Z" por "+00:00"
    # deixa o fromisoformat entender em qualquer versão do Python.
    if not valor:
        return None
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def _carencia_do_token(claims: dict, agora: datetime) -> bool:
    # A carência só vale se a flag e a data limite estiverem presentes e a data não passou.
    if not claims.get("emCarencia"):
        return False
    limite = _data_da_claim(claims.get("dataLimiteCarencia"))
    if limite is None:
        return False                      # flag sem data não basta (regra de recusa.py)
    return agora < limite
```

O vencimento do plano vem de `_data_da_claim(claims.get("dataVencimento"))`. Token sem `dataVencimento` é licença sem vencimento, como a API define.

### 6.2. Conferir o token com a licença e a máquina (D-15)

Antes de qualquer decisão offline, o app confere as duas identidades do token:

```python
# validacao.py — o token precisa ser desta licença e desta máquina (D-15)
claims = _claims_do_token(token, chave_publica)
if claims.get("licencaId") != licenca.licenca_id:
    raise _erro_licenca("TOKEN_DE_OUTRA_LICENCA", "O token não confere com esta instalação.")
if claims.get("hwid") and claims.get("hwid") != obter_hwid():
    raise _erro_licenca("TOKEN_DE_OUTRA_LICENCA", "O token não confere com esta máquina.")
```

O `hwid` é checado só quando o token tem o campo. A API emite `hwid: null` quando o conectar é feito sem máquina, e nesse caso a checagem da licença basta.

### 6.3. Módulos nunca são lidos com chave ilegível (D-14 revista)

No app, `None` e lista vazia significam "não sei", e "não sei" **libera** (exceto os módulos fiscais e de compras, que negam). A plataforma manda `modulos: []` quando ainda não configurou a loja, e esse é o caso comum hoje. Por isso, devolver `[]` não bloqueia nada, e o significado de "não sei" não muda nesta spec.

O buraco está no caminho **com internet** (`validacao.py:372-380`): a validação dá certo, os módulos são lidos com a chave pública local e, se ela não abrir, viram "não sei". O caminho **sem internet** já está certo: busca a chave de novo e, se não conseguir, dá `CHAVE_CORROMPIDA` (`validacao.py:386-401`). A mudança é dar ao caminho com internet a mesma regra:

```python
# validacao.py — com internet: chave pública ilegível é buscada de novo antes de ler os módulos (D-14)
resultado = _tentar_conexao_remota(db, licenca, chave_ativacao, hwid)
chave_publica = _decifrar_public_key(licenca, hwid)        # None se a coluna não abrir
if not chave_publica:
    try:
        # Mesma função do caminho offline: busca a chave na API e grava a boa no banco.
        chave_publica = resgatar_chave_publica_online(db, hwid, licenca.licenca_id)
    except Exception:
        raise _erro_licenca(
            "CHAVE_CORROMPIDA",
            "Chave de segurança corrompida. Necessária ligação à internet para recuperação.",
        )
resultado["modulos"] = ler_modulos_liberados(licenca.token, chave_publica)
return resultado
```

O comentário de `ler_modulos_liberados` continua dizendo que `None` é "não sei". A diferença é que ele deixa de ser chamado com uma chave ilegível.

Limite conhecido: se a coluna for estragada **depois** da validação, as rotas protegidas (`modulos_da_licenca`) leem "não sei" até a próxima validação, que o front faz a cada 5 minutos. A próxima validação busca a chave de novo e fecha o intervalo sozinha.

### 6.4. Dias restantes da API (F26)

`_tentar_conexao_remota` hoje calcula `(vencimento - agora).days`. A mudança é usar o campo da API:

```python
# validacao.py — mostra o número que a API calculou, sem usar o relógio local (F26)
dias_restantes = resposta.get("diasRestantes")
dias_carencia = resposta.get("diasRestantesCarencia")
```

O cálculo local continua existindo só no modo offline, e a resposta offline marca o número como estimativa (`"estimativa": true`).

### 6.5. Relógio que voltou no tempo (D-05, F7)

Decisão: avisar e continuar. O bloqueio foi recusado porque pararia o PDV no meio do expediente.

```python
# relogio.py — guarda o maior horário visto e avisa quando o relógio recua
from datetime import datetime, timedelta

TOLERANCIA = timedelta(minutes=5)    # pequenos ajustes de relógio não geram aviso


def verificar_relogio(licenca, agora: datetime) -> tuple[datetime, bool]:
    """Devolve (horário a usar nas contas offline, se houve recuo)."""
    visto = licenca.ultimo_horario_visto
    if visto is None:
        return agora, False                      # primeira vez: nada a comparar
    if agora + TOLERANCIA < visto:
        return visto, True                       # relógio recuou: usa o último horário visto
    return agora, False


def registrar_horario(licenca, agora: datetime) -> None:
    """Guarda sempre o maior horário já visto."""
    visto = licenca.ultimo_horario_visto
    if visto is None or agora > visto:
        licenca.ultimo_horario_visto = agora
```

Quando `verificar_relogio` devolve o aviso, `_validar_offline` inclui `"aviso": "relogio_recuou"` na resposta. A LIC-08 mostra a mensagem.

### 6.6. Recusa por código (F27, lado do app)

`_recusa_por_vencimento` já olha o `codigo` antes do texto (`recusa.py:168-179`). A mudança é acrescentar `LICENCA_VENCIDA` aos códigos de vencimento reconhecidos. A checagem de texto continua como último recurso, para quem recebe a API atual.

### 6.7. Migração da coluna (regra `migration`)

A coluna nova exige migração Alembic. Ela só adiciona `ultimo_horario_visto` se a coluna não existir. O `create_all()` do startup não acrescenta colunas a tabelas existentes, então a ausência da coluna é o sinal do schema antigo (regra do `CLAUDE.md`, "Atualização de cliente").

## 7. Critérios de aceite

- **CA-01:** token com `licencaId` de outra licença é recusado no modo offline.
- **CA-02:** token com carência vigente é aceito mesmo com as colunas de carência vazias.
- **CA-03:** com internet e a chave pública local ilegível, o sistema busca a chave de novo e lê os módulos com ela; se não conseguir, responde `CHAVE_CORROMPIDA`.
- **CA-04:** o número de dias mostrado vem de `diasRestantes` da resposta, mesmo com o relógio do computador errado.
- **CA-05:** relógio recuado mais de 5 minutos gera o aviso e usa o último horário visto.
- **CA-06:** a migração adiciona a coluna uma vez, e rodar de novo não faz nada.
- **CA-07:** recusa com `LICENCA_TRANSFERIDA` chega ao front com esse código.
- **CA-08:** o vencimento offline vem da claim `dataVencimento`, mesmo com a coluna editada.

Todos são cobertos por teste automatizado, com backend na porta 8000 e banco de teste.

## 8. Casos de teste

| ID | Arquivo | Caso | Esperado |
|----|---------|------|----------|
| CT-01 | `test_token_offline.py` | Token com `licencaId` diferente | `TOKEN_DE_OUTRA_LICENCA` |
| CT-02 | `test_token_offline.py` | Token com `hwid` diferente | `TOKEN_DE_OUTRA_LICENCA` |
| CT-03 | `test_token_offline.py` | Token com `hwid: null` | Aceito, desde que a licença confira |
| CT-04 | `test_token_offline.py` | Token com `emCarencia: true` e data futura | Carência vigente, mesmo com colunas vazias |
| CT-05 | `test_token_offline.py` | `emCarencia: true` sem `dataLimiteCarencia` | Carência não vale |
| CT-06 | `test_token_offline.py` | Com internet, chave pública local ilegível, resgate funciona | Módulos lidos com a chave resgatada; chave boa gravada |
| CT-07 | `test_token_offline.py` | Com internet, chave pública local ilegível, resgate falha | `CHAVE_CORROMPIDA` |
| CT-08 | `test_token_offline.py` | Token vencido (`exp` no passado) | Recusa offline |
| CT-09 | `test_token_offline.py` | Prazo `gracePeriodDias` estourado | `REQUISITA_CONEXAO_INTERNET` |
| CT-10 | `test_token_offline.py` | `diasRestantes` = 3 com relógio local em outra data | Mostra 3 |
| CT-11 | `test_token_offline.py` | Resposta de conexão sem `codigo` | Cai no texto, como antes |
| CT-12 | `test_token_offline.py` | `codigo = LICENCA_TRANSFERIDA` | Erro `LICENCA_TRANSFERIDA` |
| CT-13 | `test_relogio.py` | Primeiro uso, `ultimo_horario_visto` nulo | Usa o agora, sem aviso |
| CT-14 | `test_relogio.py` | Relógio recuado 10 min | Aviso e uso de `ultimo_horario_visto` |
| CT-15 | `test_relogio.py` | Relógio recuado 2 min | Sem aviso (dentro da tolerância) |
| CT-16 | `test_relogio.py` | Horário novo maior que o visto | `ultimo_horario_visto` avança |
| CT-17 | `test_token_offline.py` | Token válido sem a claim `modulos` | `None`: "não sei", como manda a API |
| CT-18 | `test_token_offline.py` | Coluna `data_vencimento` editada para o futuro, claim `dataVencimento` no passado | Recusa por vencimento (a claim vence) |

## 9. Testes existentes que a mudança quebra

- `test_licenca_validacao_offline.py`: as fixtures montam carência nas colunas. Passam a montar o token com as claims. Os casos de expiração continuam iguais.
- `test_licenca_recusa_vencimento.py`: os casos que dependem só de texto continuam valendo. Acrescentar casos com `codigo`.
- `test_licenca_transferencia.py`: confere se a transferência aceita o token novo. Revisar o que depende de `em_carencia` nas colunas.

## 10. Perguntas antes da aprovação

- Nenhuma. D-05, D-13, D-14 (revista no conflito 18) e D-15 estão fechadas no ACORDO.

## 11. Observações

- A SPEC-02 não depende da API para funcionar, graças ao tratamento sem `codigo` (seção 4) e às claims que o token já traz.
- Mudou o backend: avisar o usuário para rodar `npm run build:sidecar` depois da entrega.
- A migração da coluna roda no startup, por `tarefas.py`. Não há backup automático antes dela.
