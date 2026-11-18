# Licença 02 — Confiança no token offline e nos dias restantes

| Campo        | Valor |
|--------------|-------|
| Status       | Backlog |
| Camada       | Backend (FastAPI) |
| Dependências | SPEC-01 (o token passa a ser lido pelo `ler_token`) |
| Bloqueia     | SPEC-03 (a tela de re-login mostra os dias vindos desta spec) |
| Referência   | [acordo](../../docs/licenca/ACORDO.md) decisões D-05, D-13, D-14, D-15, D-16; quadro F7, F8, F24, F25, F26, F27 |

## 1. Objetivo

Fazer o app confiar só no que a API assinou. Hoje ele confia em colunas do banco que qualquer pessoa edita, e recalcula datas com o relógio do computador. Depois desta spec:

- a carência e os prazos offline vêm do token assinado;
- o token só vale para a licença e para a máquina a que pertence;
- os módulos ficam bloqueados quando a chave pública não pode ser lida;
- o número de dias restantes é o que a API informou;
- o relógio do computador que voltou no tempo gera aviso, e não bloqueia o PDV (D-05).

## 2. Escopo

**Dentro do escopo**
- Ler `emCarencia` e `dataLimiteCarencia` do token assinado (D-13).
- Validar `licencaId` e `hwid` do token contra a licença local e `obter_hwid()` (D-15).
- Bloquear módulos quando a chave pública não puder ser lida (D-14).
- Usar `diasRestantes` e `diasRestantesCarencia` da API (F26).
- Ramificar a recusa de `/licenca/conectar` pelo `codigo` da API, quando ele existir (D-16).
- Guardar o maior horário visto e avisar quando o relógio voltar (D-05).

**Fora do escopo**
- Reduzir a validade do token para 24 h (ACORDO D-04, alternativa B). Fica para depois.
- Mudanças na API. Os códigos novos de vencimento são da SPEC-06, na API.
- Tela do front. O front só mostra o aviso de relógio, e isso entra na SPEC-03.

## 3. Arquivos afetados

| Arquivo | Ação | O quê |
|---------|------|-------|
| `backend-fastapi/app/services/licenca/validacao.py` | alterar | `_validar_offline` lê carência e prazos do token. `_tentar_conexao_remota` usa `diasRestantes` da API. `ler_modulos_liberados` e `modulos_da_licenca` recusam quando a chave falha. |
| `backend-fastapi/app/services/licenca/recusa.py` | alterar | `_recusa_por_vencimento` usa `codigo` antes de texto. `_carencia_vigente` passa a aceitar o valor vindo do token. |
| `backend-fastapi/app/services/licenca/relogio.py` | criar | `verificar_relogio(licenca, agora)` e `registrar_horario(licenca, agora)`. Um único ponto de decisão sobre o relógio. |
| `backend-fastapi/app/db/models/configuracao_licenca.py` | alterar | Coluna nova `ultimo_horario_visto` (DateTime, nullable). |
| `backend-fastapi/alembic/versions/` | criar | Migração que adiciona `ultimo_horario_visto`. Decide pelo schema antigo: só adiciona se a coluna não existir. |
| `backend-fastapi/app/services/licenca/sincronizacao.py` | alterar | Grava as colunas de carência também na renovação em segundo plano (F25, caminho que falha hoje). |
| `backend-fastapi/test/api/v1/test_licenca_validacao_offline.py` | alterar | Fixtures passam a montar o token com as claims novas. |
| `backend-fastapi/test/api/v1/test_licenca_recusa_vencimento.py` | alterar | Casos com `codigo` e casos sem `codigo`. |
| `backend-fastapi/test/api/v1/test_licenca_transferencia.py` | alterar | Ajustar só o que depende da leitura de claims. |
| `backend-fastapi/test/services/licenca/test_token_offline.py` | criar | Casos CT-01 a CT-12. |
| `backend-fastapi/test/services/licenca/test_relogio.py` | criar | Casos CT-13 a CT-16. |

## 4. Contrato consumido

Rota: `POST /api/v1/licenca/conectar` (API StartBig, `dispositivo.service.ts`).

Campos da resposta de sucesso que este módulo passa a usar:

| Campo | Uso |
|-------|-----|
| `token` | Guardado pela SPEC-01 e validado localmente |
| `diasRestantes` | Mostrado no lugar do cálculo local (F26) |
| `diasRestantesCarencia` | Mostrado durante a carência |
| `emCarencia`, `dataLimiteCarencia` | Gravados nas colunas e lidos do token (D-13) |

Campos de recusa: `codigo` (quando existir), `message` e `statusCode`. Códigos que o app passa a tratar:

| `codigo` | Status HTTP | Tratamento no app |
|----------|-------------|-------------------|
| `LICENCA_TRANSFERIDA` | 400 | Erro `LICENCA_TRANSFERIDA`, para o front levar à tela de transferência |
| `LICENCA_VENCIDA` | 402 ou 400 | Erro `LICENCA_EXPIRADA` |
| (sem `codigo`) | qualquer | Cai na leitura do texto, como hoje, até a SPEC-06 ser entregue |

O tratamento sem `codigo` é a rede de segurança: a SPEC-02 não depende da SPEC-06 para funcionar.

## 5. Schemas

Nenhum schema da API muda. Mudança interna: a coluna `ultimo_horario_visto` em `configuracao_licenca`. Ela é `NULL` para licenças antigas, e `NULL` significa "ainda não registrado".

## 6. Especificação técnica

### 6.1. Carência e prazos vêm do token (D-13)

Hoje `_validar_offline` lê `licenca.data_vencimento`, `licenca.em_carencia` e `licenca.data_limite_carencia`. A mudança é ler as claims do token assinado. A verificação da assinatura continua obrigatória.

```python
# validacao.py — lê a carência do token assinado, não de uma coluna editável (D-13)
from jose import jwt  # biblioteca que confere a assinatura do token

def _claims_do_token(token: str, chave_publica: str) -> dict:
    # Confere a assinatura RS256. Se a assinatura não bater, lança erro.
    # verify_exp fica ligado: token vencido também é recusado.
    return jwt.decode(
        token,
        chave_publica,
        algorithms=["RS256"],             # aceita só o algoritmo que a API usa
        options={"verify_aud": False},    # a API não envia 'aud'
    )

def _carencia_do_token(claims: dict, agora) -> bool:
    # A carência só vale se a flag e a data limite estiverem presentes e a data não passou.
    if not claims.get("emCarencia"):
        return False
    limite = claims.get("dataLimiteCarencia")
    if not limite:
        return False                      # flag sem data não basta (regra de recusa.py)
    return agora < datetime.fromisoformat(limite)
```

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

O `hwid` é checado só quando o token tem o campo. Token sem `hwid` vem de login sem máquina, e nesse caso a checagem de licença já basta.

### 6.3. Módulos bloqueados sem chave (D-14)

`ler_modulos_liberados` hoje devolve `None` quando a chave pública não pode ser lida, e `None` libera tudo. A mudança é devolver um valor que bloqueia:

```python
# validacao.py — sem chave ou com assinatura inválida, nenhum módulo é liberado (D-14)
def ler_modulos_liberados(token, chave_publica) -> list[str] | None:
    if not token or not chave_publica:
        return []                          # sem chave: lista vazia = nenhum módulo liberado
    try:
        claims = _claims_do_token(token, chave_publica)
    except JWTError:
        return []                          # assinatura inválida também bloqueia
    if "modulos" not in claims:
        return None                        # token antigo, sem a claim: a API manda liberar
    return [str(m) for m in claims["modulos"]]
```

Atenção à diferença, que o comentário do código precisa deixar clara:
- **Chave ausente ou assinatura inválida:** bloqueia (`[]`). É o caso que a D-14 corrige.
- **Claim `modulos` ausente, com chave válida:** libera (`None`). É o contrato da API para tokens emitidos antes da claim existir (`validacao.py`, comentário de `ler_modulos_liberados`).

O `None` continua existindo só para esse segundo caso. O comentário de `ler_modulos_liberados` precisa ser reescrito para dizer isso, sem a frase antiga que mandava liberar em qualquer falha.

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
from datetime import datetime, timedelta, timezone

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

Quando `verificar_relogio` devolve o aviso, `_validar_offline` inclui `"aviso": "relogio_recuou"` na resposta. O front mostra a mensagem (SPEC-03).

### 6.6. Recusa por código (D-16)

`_recusa_por_vencimento` passa a olhar `codigo` antes do texto, e a checagem de texto fica como último recurso. Esta é a mudança que mantém o comportamento atual para quem recebe uma API antiga.

### 6.7. Migração da coluna (regra `migration`)

A coluna nova exige migração Alembic. A migração decide pelo schema antigo: só adiciona `ultimo_horario_visto` se ela não existir, para não quebrar o `create_all()` que roda antes do `upgrade("head")` (regra da seção 6 de `CLAUDE.md`, "Atualização de cliente").

## 7. Critérios de aceite

- **CA-01:** token com `licencaId` de outra licença é recusado no modo offline (sonda T1 vira teste que passa).
- **CA-02:** token com carência vigente é aceito mesmo com as colunas de carência vazias (sonda T2 vira teste que passa).
- **CA-03:** sem chave pública legível, nenhum módulo é liberado.
- **CA-04:** o número de dias mostrado vem de `diasRestantes` da resposta, mesmo com o relógio do computador errado.
- **CA-05:** relógio recuado mais de 5 minutos gera o aviso e usa o último horário visto.
- **CA-06:** a migração adiciona a coluna uma vez, e rodar de novo não faz nada.
- **CA-07:** recusa com `LICENCA_TRANSFERIDA` chega ao front com esse código.

Todos são verificáveis no Windows com backend na porta 8000 e banco de teste.

## 8. Casos de teste

| ID | Caso | Esperado |
|----|------|----------|
| CT-01 | Token com `licencaId` diferente | `TOKEN_DE_OUTRA_LICENCA` |
| CT-02 | Token com `hwid` diferente | `TOKEN_DE_OUTRA_LICENCA` |
| CT-03 | Token sem `hwid` | Aceito, desde que a licença confira |
| CT-04 | Token com `emCarencia: true` e data futura | Carência vigente, mesmo com colunas vazias |
| CT-05 | `emCarencia: true` sem `dataLimiteCarencia` | Carência não vale |
| CT-06 | Assinatura inválida | Nenhum módulo liberado |
| CT-07 | Chave pública ausente | Lista vazia de módulos |
| CT-08 | Token vencido (`exp` no passado) | Recusa offline |
| CT-09 | Prazo `grace_period` estourado | `REQUISITA_CONEXAO_INTERNET` |
| CT-10 | `diasRestantes` = 3 com relógio local em outra data | Mostra 3 |
| CT-11 | Resposta de conexão sem `codigo` | Cai no texto, como antes |
| CT-12 | `codigo = LICENCA_TRANSFERIDA` | Erro `LICENCA_TRANSFERIDA` |
| CT-13 | Primeiro uso, `ultimo_horario_visto` nulo | Usa o agora, sem aviso |
| CT-14 | Relógio recuado 10 min | Aviso e uso de `ultimo_horario_visto` |
| CT-15 | Relógio recuado 2 min | Sem aviso (dentro da tolerância) |
| CT-16 | Horário novo maior que o visto | `ultimo_horario_visto` avança |
| CT-17 | Token válido sem a claim `modulos` (emitido antes da claim existir) | `None`: libera, como manda a API |

## 9. Testes existentes que a mudança quebra

- `test_licenca_validacao_offline.py`: as fixtures montam carência nas colunas. Passam a montar o token com as claims. Os casos de expiração continuam iguais.
- `test_licenca_recusa_vencimento.py`: os casos que dependem só de texto continuam valendo. Acrescentar casos com `codigo`.
- `test_licenca_transferencia.py`: confere se a transferência aceita o token novo. Revisar o que depende de `em_carencia` nas colunas.

## 10. Perguntas antes da aprovação

- Nenhuma. As decisões D-05, D-13, D-14, D-15 e D-16 já estão fechadas no ACORDO.

## 11. Observações

- A SPEC-02 não depende da API para funcionar, graças ao tratamento sem `codigo` (seção 4).
- Mudou o backend: avisar o usuário para rodar `npm run build:sidecar` depois da entrega.
- A migração da coluna roda no startup, por `tarefas.py`. Não há backup automático antes dela.
