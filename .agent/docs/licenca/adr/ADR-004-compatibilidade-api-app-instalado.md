# ADR-004 — Compatibilidade de contrato entre a API e as versões instaladas do app

- **Status:** Aceita em 2026-11-19 (revisão de conflitos, rodada 2: conflitos 23 e 27; ACORDO D-34 e D-37)
- **Módulos afetados:** `licenca` (start-big) e a API StartBig (`plataformaADM`): cadastro, heartbeat e toda mudança futura de contrato

## 1. Contexto

A API StartBig é uma só, e o app roda em versões diferentes em cada loja. As versões instaladas **não se atualizam sozinhas**: não há atualizador automático, e a versão no `package.json` e no `tauri.conf.json` é `0.1.0` em todas as builds, então a API também não consegue saber qual versão está do outro lado.

Duas mudanças desta série esbarraram nisso:

- **Cadastro (LIC-06, conflito 23).** O cadastro passou a exigir a confirmação de e-mail e a responder `202`, sem licença. As versões instaladas tratam todo `2xx` como "licença criada" (`backend-fastapi/app/services/licenca/cadastro.py`, `_chamar_api_auto_cadastro`) e quebrariam com um erro interno, sem explicação.
- **Heartbeat (LIC-09, conflito 27).** O heartbeat passou a exigir o token da licença. As versões instaladas não mandam o token. E, se recebem `400` em todos os caixas, **bloqueiam a licença da loja** (`sincronizacao.py:57-67`).

Em ambos, a solução "simples" tinha dois defeitos possíveis: ou quebrava a loja que não atualizou, ou deixava um caminho antigo aberto, por onde qualquer pessoa fugiria da proteção nova.

## 2. Decisão

Toda mudança de contrato da API segue estas regras:

1. **Nenhuma versão instalada fica sem saída.** Ela recebe uma resposta que **já sabe tratar**, com uma instrução que leva a um caminho que **já existe** nela.
2. **A proteção nova vale para todos.** O caminho das versões antigas não pode ser uma porta para fugir dela. Se o app antigo não consegue cumprir a regra nova, ele recebe menos (por exemplo, não cria sessão), nunca mais.
3. **O app novo avisa o que entende.** O pedido traz um sinal explícito, como `fluxoConfirmacao: true` no cadastro, ou o próprio cabeçalho `Authorization` no heartbeat. A API não tenta adivinhar a versão.
4. **Conhecer as respostas que o app antigo trata como fatais.** Antes de escolher o status de uma recusa nova, conferir como as versões instaladas reagem. Hoje: `400` no heartbeat bloqueia a licença; qualquer `2xx` com formato novo vira erro interno; `4xx` no cadastro mostra a `message`.
5. **O caminho de transição tem data para acabar.** Quando as lojas tiverem atualizado, a API pode recusar o pedido antigo. Isso é uma decisão nova, registrada no ACORDO, e não acontece sozinho.

Aplicações desta série:

| Mudança | App novo | Versão instalada |
|---------|----------|------------------|
| Cadastro com confirmação (LIC-06) | `fluxoConfirmacao: true` → `202` | Sem o campo → `409 CONFIRMACAO_NECESSARIA` com a instrução "use 'Já tenho conta'". A confirmação é exigida nos dois casos |
| Heartbeat autenticado (LIC-09) | Manda o token → cria e renova sessão | Sem token → só renova sessão existente; sessão inexistente → `404 SESSAO_INEXISTENTE` (nunca `400`) |
| Vencimento no `conectar` (SPEC-05) | `402 LICENCA_VENCIDA` | O app instalado já trata `402` como vencimento |

## 3. Alternativas consideradas

| Alternativa | Por que foi descartada |
|-------------|------------------------|
| Manter o caminho antigo intacto para quem não manda o sinal novo | Anula a proteção: quem quisesse fugir dela era só não mandar o sinal. |
| Só fazer o deploy da API quando todas as lojas tiverem atualizado | Não há como saber quando isso acontece, nem quantos instaladores antigos estão guardados. |
| Versionar a API pela URL (`/v2/...`) | Mesma fuga do primeiro item, com o dobro de rotas para manter. |
| Mandar a versão do app no pedido | A versão é `0.1.0` em todas as builds hoje, e o sinal por funcionalidade diz exatamente o que importa. |

## 4. Consequências

- **Aceitas:**
  - A API carrega, por um tempo, dois comportamentos para o mesmo pedido.
  - Na versão instalada, a mensagem do cadastro aparece com o prefixo "Erro no auto-cadastro de licença:", estranho mas compreensível.
  - Cada caminho de transição gera uma pendência no ACORDO (§7), para ser desligado depois.
- **Efeitos em outros módulos, regras e skills:**
  - Specs que mudam o contrato da API citam esta ADR e dizem como fica a versão instalada.
  - O aprendizado `docs/licenca/learn/2026-11-19-respostas-que-o-app-instalado-trata-como-bloqueio.md` lista as respostas fatais conhecidas.

## 5. Como reverter

- Desligar um caminho de transição é a evolução prevista (regra 5), não uma reversão.
- Abandonar esta ADR seria aceitar quebrar as lojas que não atualizaram, o que exige uma ADR nova com o motivo.
