# Roteiro de implementação — `licenca`

Ordem das specs e das tarefas auxiliares. A série cruza dois repositórios, então o roteiro é o que diz quando cada parte pode começar.

Branch de trabalho: `fix/licenca-seguranca`, no `start-big`. Um commit por spec concluída, e um único PR no fim, só quando você pedir (AGENT.md §7). As specs da API (LIC-05, 06 e 09) vão em branch própria no `aalan-big/plataformaADM`.

> **Revisão 1 (2026-11-18):** revisão de conflitos com o usuário. Entraram a LIC-08 (avisos) e a LIC-09 (vagas, separada da antiga SPEC-06). A LIC-03 deixou de esperar a LIC-06, graças à rede de segurança do `404` (conflito 8). O "Pronto quando" passou a exigir **todos** os CT e CA de cada spec, sem números fixos (conflito 15): a versão anterior dava a LIC-06 como pronta sem o CT-20, que é a mitigação do R-01.

## 1. Passos

| Passo | Spec | Repositório | Camada | Depende de | Pode começar quando |
|-------|------|-------------|--------|------------|---------------------|
| 1 | LIC-01 · Cofre e backup cifrado | start-big | Backend | — | Aprovação da LIC-01 |
| 2 | Tarefa: comentário do heartbeat | start-big | Backend | — | Qualquer momento (uma linha) |
| 3 | LIC-02 · Token offline | start-big | Backend | 1 | Passo 1 concluído |
| 4 | LIC-04 · Rede e front | start-big | Front, Backend, NSIS e Tauri | — | Aprovação da LIC-04 (pode correr em paralelo aos passos 1 a 3) |
| 5 | LIC-03 · Re-login | start-big | Backend e Front | 1, 3 | Passos 1 e 3 concluídos |
| 6 | LIC-08 · Avisos | start-big | Backend e Front | 1, 3 | Passos 1 e 3 concluídos |
| 7 | LIC-05 · API revogação e backup | plataformaADM | API | Acesso de escrita | Acesso liberado |
| 8 | LIC-06 · API conta e cadastro | plataformaADM | API | 7 | Passo 7 concluído |
| 9 | LIC-09 · API vagas | plataformaADM | API | 2 e acesso de escrita | Passo 2 concluído e acesso liberado |
| 10 | Verificação de integração | ambos | — | Todos | Passos 1 a 9 concluídos |

**Pronto quando (vale para todo passo de spec):** **todos** os CT da spec passam e **todos** os CA foram verificados. Os que exigem Windows ou o app instalado são verificados na skill `verify`, ou marcados como "não verificado" com o motivo.

## 2. Por passo

### Passo 1 · LIC-01 (cofre e backup cifrado)

- **Pontos de atenção:** a migração de dados do token e da chave é idempotente, mas não há backup automático antes dela. Testar em banco de teste, nunca em `start_big.db`. O cofre é de escopo de máquina, porque o backend roda como SYSTEM e como o usuário (conflito 1).
- **Sidecar:** avisar o usuário para `npm run build:sidecar` depois da entrega.

### Passo 2 · Comentário do heartbeat

- **Onde:** `backend-fastapi/app/core/tarefas.py:34`. O comentário diz "5 minutos" e o valor é `100` segundos.
- **Pronto quando:** o comentário diz o valor real.
- **Motivo:** a LIC-09 reduz a vida da sessão para 10 minutos, e a folga depende deste intervalo.

### Passo 3 · LIC-02 (token offline)

- **Pontos de atenção:** os testes `test_licenca_validacao_offline.py`, `test_licenca_recusa_vencimento.py` e `test_licenca_transferencia.py` mudam de fixture. A expectativa de vencimento não muda.
- **Migração:** coluna `ultimo_horario_visto`, adicionada só se não existir.

### Passo 4 · LIC-04 (rede e front)

- **Pontos de atenção:** a origem da janela Tauri no Windows precisa ser confirmada antes do fechamento do CORS. Mudança nas permissões do Tauri e no instalador exige recompilar o app. Testar a instalação **por cima** de uma versão antiga, para conferir que as regras de firewall antigas foram apagadas (CA-11).

### Passo 5 · LIC-03 (re-login)

- **Pontos de atenção:** a restauração é aplicada no próximo boot, e a tela não pode deixar sair no meio.
- **Integração:** sem a LIC-06, o setup funciona como hoje (rede de segurança do `404`), e o cadastro continua devolvendo a licença. Com a LIC-06 no ar, o app passa a usar os dados da nuvem e o cadastro `202` sozinho, sem nova versão.

### Passo 6 · LIC-08 (avisos)

- **Pontos de atenção:** a pausa do envio fica em memória. Depois de reiniciar o backend, o primeiro envio tenta de novo, e isso é esperado.

### Passo 7 · LIC-05 (API revogação e backup)

- **Repositório:** `aalan-big/plataformaADM`, em branch própria, seguindo o padrão do repositório.
- **Pontos de atenção:** o guard vira `async`, e os testes que o usam precisam de `await`.

### Passo 8 · LIC-06 (API conta e cadastro)

- **Pontos de atenção:** a migração Prisma marca como confirmados os clientes que já têm licença, senão eles seriam barrados no login (CA-10). O CT-16 é a mitigação obrigatória do R-01.

### Passo 9 · LIC-09 (API vagas)

- **Pontos de atenção:** a expiração real hoje está no `cron.service.ts` (35 min), não na constante `HEARTBEAT_TIMEOUT_MS`. A contagem passa a olhar o `ultimoHeartbeat`.

### Passo 10 · Verificação de integração

Feita pela skill `verify`, com o app rodando no Windows, na ordem:

1. Cadastro novo, confirmação de e-mail e primeiro acesso, com o setup preenchido pela nuvem.
2. Login diário, com internet e depois sem internet (dias "estimados").
3. Re-login no caso 1 (outro computador): aviso, troca, o computador antigo parando e o backup dele pausado.
4. Re-login no caso 2 (banco perdido): escolha, restauração da cópia cifrada, reinício e dados de volta.
5. Troca de servidor com caixas conectados: as vagas da loja antiga liberadas.
6. Banco copiado para outro computador: token e chave não abrem, e a tela orienta o re-login.

**Pronto quando:** os seis fluxos foram verificados ou marcados como "não verificado", com o motivo.

## 3. Perguntas abertas

Nenhuma. A revisão de conflitos (2026-11-18) fechou as perguntas das specs e confirmou as duas sub-decisões que estavam "para revisão" (documento do titular travado; redes privadas fixas). As specs estão prontas para aprovação, uma por vez.

## 4. Riscos conhecidos

- **Dependência de API:** o caso 1 do re-login pede a revogação (LIC-05). Sem ela, o computador antigo continua conseguindo enviar backup.
- **R-01 (aceito):** a senha é definida no cadastro, antes da confirmação do e-mail. Mitigação: o dono define uma nova senha pelo `reenviar-link` (LIC-06, CT-16).
- **R-02 (aceito):** quem tiver a chave de ativação consegue derrubar sessões (F5). Mitigação: a LIC-01 tira a chave do alcance de quem copia o banco.
- **Módulos entre validações:** se a chave pública for estragada no banco depois de uma validação, as rotas leem "não sei" até a próxima validação, em até 5 minutos (LIC-02 §6.3).
- **Rede em texto claro:** a D-21 corta o acesso de fora da loja, mas quem já está na rede ainda lê o tráfego. Até a LIC-07 (TLS), o token do login e os dados de venda continuam sem cifra dentro da loja. A janela de uso do token (ADR-003) limita o dano.
- **Backups antigos na nuvem:** os enviados antes da LIC-01 continuam em claro até expirarem.
