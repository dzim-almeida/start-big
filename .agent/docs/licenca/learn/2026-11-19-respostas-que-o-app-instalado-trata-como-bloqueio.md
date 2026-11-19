# Respostas da API que o app já instalado trata como bloqueio ou erro

- **Data:** 2026-11-19
- **Módulo:** licenca
- **Spec relacionada:** LIC-06, LIC-09 (revisão de conflitos, rodada 2: conflitos 22, 23 e 27); ADR-004
- **Tipo:** armadilha

## Contexto

Na conferência das specs da API contra o código da plataforma, duas mudanças de contrato pareciam inofensivas (um `202` no cadastro, um `400` novo no heartbeat) e teriam quebrado as lojas que ainda não atualizaram o app. As versões instaladas não se atualizam sozinhas, e a versão do app é `0.1.0` em todas as builds.

## Aprendizado

Como as versões **já instaladas** do start-big reagem a respostas da API:

| Rota da API | Resposta | Reação do app instalado | Onde |
|-------------|----------|-------------------------|------|
| `/licenca/heartbeat` | `400` | Remove o caixa da tabela; se **todos** os caixas recebem `400`, **marca a licença como bloqueada** | `backend-fastapi/app/services/licenca/sincronizacao.py:57-67` |
| `/erp/auto-cadastro` | qualquer `2xx` | Lê `licencaId`, `token` e `chaveAtivacao`; formato diferente vira **erro interno** | `cadastro.py`, `_chamar_api_auto_cadastro` |
| `/erp/auto-cadastro` | `4xx` | Mostra a `message` ("Erro no auto-cadastro de licença: ...") | Idem |
| `/erp/backup/status` | `planoPermiteBackup: false` | **Para o envio em silêncio**, sem tentar | `backend-fastapi/app/services/cloud/flow.py:26-27` |
| `/licenca/conectar` | `402` | Trata como vencimento | `recusa.py:172` |

## Como aplicar

Antes de mudar uma resposta da API (status ou formato), confira esta tabela e a ADR-004: escolha um status que a versão instalada trate de um jeito aceitável, e nunca use `400` como recusa nova no heartbeat. Se descobrir outra reação fatal, acrescente uma linha aqui.
