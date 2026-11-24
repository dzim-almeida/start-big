# Roteiro de implementação — `licenca`

Ordem das specs e das tarefas auxiliares. A série cruza dois repositórios, então o roteiro é o que diz quando cada parte pode começar e como cada uma chega à produção.

- **start-big:** branch `fix/licenca-seguranca`. Um commit por spec concluída, e um único PR no fim, só quando você pedir (AGENT.md §7).
- **Plataforma:** fork `dzim-almeida/plataformaADM`, uma branch por spec (por exemplo, `fix/licenca-revogacao`), seguindo o padrão do repositório. Cada spec concluída vira um PR para o `aalan-big/plataformaADM`. A produção da plataforma faz deploy com `git pull` da branch principal do `aalan-big`, então **nada entra lá sem PR** (D-01).

> **Revisão 1 (2026-11-18):** entraram a LIC-08 e a LIC-09. A LIC-03 deixou de esperar a LIC-06 (rede de segurança do `404`). O "Pronto quando" passou a exigir **todos** os CT e CA de cada spec.

> **Revisão 3 (2026-11-19):** as specs só definiam os textos das telas, sem referência visual. Entrou o **passo 0**: mockups das telas da série, aprovados pelo usuário antes de qualquer spec com tela (skill `design`, §0).

> **Revisão 2 (2026-11-19):** as specs da API deixaram de estar bloqueadas (fork + PR, conflito 19). Entrou o passo de PR e deploy da plataforma, com a conferência do diff do `db push` para a LIC-06. Pela ADR-004, cada spec da API pode ir para produção sem esperar as lojas atualizarem o app.

## 1. Passos

| Passo | Spec | Repositório | Camada | Depende de | Pode começar quando |
|-------|------|-------------|--------|------------|---------------------|
| 0 | Mockups das telas da série | — | Design | — | **Concluído: aprovado em 2026-11-19, com as propostas** |
| 1 | LIC-01 · Cofre e backup cifrado | start-big | Backend | — | Aprovação da LIC-01 |
| 2 | Tarefa: comentário do heartbeat | start-big | Backend | — | Qualquer momento (uma linha) |
| 3 | LIC-02 · Token offline e heartbeat com token | start-big | Backend | 1 | Passo 1 concluído |
| 4 | LIC-04 · Rede e front | start-big | Front, Backend, NSIS e Tauri | — | Aprovação da LIC-04 (pode correr em paralelo aos passos 1 a 3) |
| 5 | LIC-03 · Re-login | start-big | Backend e Front | 0, 1, 3 | Passos 0, 1 e 3 concluídos |
| 6 | LIC-08 · Avisos | start-big | Backend e Front | 0, 1, 3 | Passos 0, 1 e 3 concluídos |
| 7 | LIC-05 · API revogação e backup | plataforma (fork) | API | — | Aprovação da LIC-05 (pode correr em paralelo aos passos do start-big) |
| 8 | LIC-06 · API conta e cadastro | plataforma (fork) | API e painel web | 0, 7 | Passos 0 e 7 concluídos |
| 9 | LIC-09 · API vagas e heartbeat | plataforma (fork) | API | 2, 7 | Passos 2 e 7 concluídos |
| 10 | PR e deploy da plataforma | plataforma | — | 7, 8, 9 (um PR por spec) | Cada spec da API concluída |
| 11 | Verificação de integração | ambos | — | Todos | Passos 1 a 10 concluídos |

**Pronto quando (vale para todo passo de spec):** **todos** os CT da spec passam e **todos** os CA foram verificados. Os que exigem Windows, o app instalado ou um PostgreSQL real são verificados na skill `verify` (ou pelo script indicado na spec), ou marcados como "não verificado", com o motivo.

## 2. Por passo

### Passo 0 · Mockups das telas (design)

- **Onde:** página de mockups [https://claude.ai/artifact/E5SohwYLXt3pY84pCFwj6z](https://claude.ai/artifact/E5SohwYLXt3pY84pCFwj6z) (privada: só abre para quem tiver acesso compartilhado).
- **Situação:** publicada e **aprovada pelo usuário em 2026-11-19**, com as propostas. Ajustes futuros são pedidos por comentário na própria página ou na conversa, e entram nas specs como nota de revisão.
- **O que cobre:**

| Tela | Spec | Quadro |
|------|------|--------|
| Licença encontrada, com backup e sem backup | LIC-03 §6.2 | 1a, 1b |
| Restauração preparada | LIC-03 §6.2 | 2 |
| Cadastro enviado e login antes da confirmação | LIC-03 §6.5 | 3a, 3b |
| Página do link de confirmação (painel web) | LIC-06 §4.2 | 6 |
| Faixa do relógio e dias estimados | LIC-08 §6.1 | 4 e 9 |
| Avisos na tela de backup | LIC-08 §6.3 | 5 |
| Setup com documento travado | LIC-03 §6.6 | 7 |
| Confirmação antes da troca de servidor | LIC-03 §6.3 | 8 |

- **Pronto quando:** o usuário aprovou os quadros (com ou sem ajustes). A versão aprovada passa a ser a **referência de design** da skill `design` para a LIC-03, a LIC-06 (página web) e a LIC-08.
- **Propostas além das specs** (anotadas ao lado de cada linha da página): senha pedida de novo na tela 1a (D-07), semana do backup na 1a, "Reenviar link" também na 3a, botão "Assinar" no aviso do trial, faixa do relógio sem botão de fechar. **Aprovadas** junto com os mockups e registradas como "Revisão 3" na SPEC-03, na LIC-06 e na LIC-08.
- **Arquivo do design:** a pasta `docs/licenca/design/` é do time (o agente não edita, `docs/README.md`). Depois da aprovação, o link entra no `docs/licenca/design/LINKS.md` por quem mantém a pasta, ou pelo agente com autorização.
- **Sem tela nova:** LIC-01, LIC-02, LIC-05 e LIC-09. A LIC-04 só mexe no `BaseConfirmModal` (o negrito vem por slot, sem mudança visual).

### Passo 1 · LIC-01 (cofre e backup cifrado)

- **Pontos de atenção:** a migração de dados do token e da chave é idempotente, mas não há backup automático antes dela. Testar em banco de teste, nunca em `start_big.db`. O cofre é de escopo de máquina, porque o backend roda como SYSTEM e como o usuário (conflito 1).
- **Sidecar:** avisar o usuário para `npm run build:sidecar` depois da entrega.

### Passo 2 · Comentário do heartbeat

- **Onde:** `backend-fastapi/app/core/tarefas.py:34`. O comentário diz "5 minutos" e o valor é `100` segundos.
- **Pronto quando:** o comentário diz o valor real.
- **Motivo:** a LIC-09 reduz a vida da sessão para 10 minutos, e a folga depende deste intervalo.

### Passo 3 · LIC-02 (token offline e heartbeat com token)

- **Pontos de atenção:** os testes `test_licenca_validacao_offline.py`, `test_licenca_recusa_vencimento.py` e `test_licenca_transferencia.py` mudam de fixture. O heartbeat com `404` nunca pode bloquear a licença (CT-21).
- **Migração:** coluna `ultimo_horario_visto`, adicionada só se não existir.

### Passo 4 · LIC-04 (rede e front)

- **Pontos de atenção:** a origem da janela Tauri no Windows precisa ser confirmada antes do fechamento do CORS. Mudança nas permissões do Tauri e no instalador exige recompilar o app. Testar a instalação **por cima** de uma versão antiga (CA-11).

### Passo 5 · LIC-03 (re-login)

- **Pontos de atenção:** a restauração é aplicada no próximo boot, e a tela não pode deixar sair no meio.
- **Integração:** sem a LIC-06, o setup funciona como hoje (rede de segurança do `404`), e o cadastro continua devolvendo a licença. Com a LIC-06 no ar, o app novo passa a usar os dados da nuvem e o cadastro `202` sozinho.

### Passo 6 · LIC-08 (avisos)

- **Pontos de atenção:** o resultado do último ciclo fica em memória; antes do primeiro ciclo depois do boot, a tela não mostra aviso de backup, e isso é esperado.

### Passo 7 · LIC-05 (API revogação e backup)

- **Pontos de atenção:** o guard vira `async`. As licenças antigas com `hwidServidor` vazio ganham servidor na primeira chamada de backup (CT-07 e CT-08). O trial é decidido no `/status`, e o start-big atual já reage certo (CA-07).
- **Banco:** nenhuma mudança (sem `db push`).

### Passo 8 · LIC-06 (API conta e cadastro)

- **Pontos de atenção:** o caminho das versões instaladas (`409 CONFIRMACAO_NECESSARIA`, ADR-004) e o CT-19 (mitigação do R-01) são obrigatórios. Os links de primeiro acesso já enviados deixam de valer: avisar o suporte de que o dono pede outro pelo "Reenviar link".
- **Banco:** campos novos opcionais em `clientes`, pelo `db push`, sem script de dados (D-32).

### Passo 9 · LIC-09 (API vagas e heartbeat)

- **Pontos de atenção:** nenhuma recusa nova do heartbeat pode ser `400` (CT-12). A corrida real é conferida com `scripts/testar-corrida-vagas.ts` contra um PostgreSQL de desenvolvimento.
- **Banco:** nenhuma mudança (sem `db push`).

### Passo 10 · PR e deploy da plataforma

Para cada spec da API concluída no fork:

1. Abrir o PR do fork para o `aalan-big/plataformaADM`, com a spec e os testes no texto do PR.
2. Depois do merge, o deploy segue o roteiro da própria plataforma (`docs/deploy-pix-asaas.md`), e **não** o `npm run deploy` direto, quando houver mudança de banco:
   - conferir o diff: `npx prisma migrate diff --from-config-datasource --to-schema prisma/schema.prisma --script`;
   - para a LIC-06, o esperado é **só** `ALTER TABLE "clientes" ADD COLUMN ...` e `ALTER TABLE "clientes_pf" ADD COLUMN ...` (telefone e celular da PF). Qualquer `DROP`, `RENAME`, `ALTER COLUMN` ou `SET NOT NULL` → **parar**;
   - aplicar o `db push`, fazer o build e reiniciar a API.
3. A LIC-05 e a LIC-09 não mudam o banco: o deploy normal serve.

A ordem de deploy entre plataforma e app é livre: pela ADR-004, cada lado funciona com a versão atual do outro.

### Passo 11 · Verificação de integração

Feita pela skill `verify`, com o app rodando no Windows, na ordem:

1. Cadastro novo com o app novo, confirmação de e-mail e primeiro acesso, com o setup preenchido pela nuvem.
2. Cadastro com um instalador **antigo**: a instrução do `409` aparece e o "Já tenho conta" funciona depois da confirmação.
3. Login diário, com internet e depois sem internet (dias "estimados").
4. Re-login no caso 1 (outro computador): aviso, troca, o computador antigo parando e o backup dele parado com o motivo na tela.
5. Re-login no caso 2 (banco perdido), numa segunda-feira antes do full da semana: escolha, restauração do ciclo anterior, reinício e dados de volta.
6. Troca de servidor com caixas conectados: as vagas da loja antiga liberadas.
7. Banco copiado para outro computador: token e chave não abrem, e a tela orienta o re-login.
8. Loja em teste: um backup na nuvem, o aviso do trial depois dele, e o download funcionando.

**Pronto quando:** os oito fluxos foram verificados ou marcados como "não verificado", com o motivo.

## 3. Perguntas abertas

Nenhuma. As rodadas de revisão de conflitos (2026-11-18 e 2026-11-19) fecharam as perguntas das specs. As specs estão prontas para aprovação, uma por vez.

## 4. Riscos conhecidos

- **R-01 (aceito):** a senha é definida no cadastro, antes da confirmação do e-mail. Mitigação: o dono define uma nova senha pelo `reenviar-link` (LIC-06, CT-19).
- **R-02 (aceito, revisto):** quem tiver a chave de ativação consegue derrubar sessões (F5). A LIC-01 tira a chave do alcance de quem copia o banco, e a LIC-09 fecha a segunda porta (o heartbeat sem credencial).
- **Heartbeat sem token na transição:** até a recusa do pedido sem token (ADR-004), quem souber o `licencaId` e o HWID de um caixa consegue manter viva a sessão dele. Não consegue criar sessão nova.
- **Módulos entre validações:** se a chave pública for estragada no banco depois de uma validação, as rotas leem "não sei" até a próxima validação, em até 5 minutos (LIC-02 §6.3).
- **Rede em texto claro:** até a LIC-07 (TLS), o token do login e os dados de venda continuam sem cifra dentro da loja.
- **Backups antigos na nuvem:** os enviados antes da LIC-01 continuam em claro até expirarem.
- **`Cliente.email` não é único** na plataforma: dois cadastros simultâneos com o mesmo e-mail podem criar duas contas (LIC-06 §5).
