# Roteiro de implementação — `licenca`

Ordem das seis specs e das tarefas auxiliares. A série cruza dois repositórios, então o roteiro é o que diz quando cada parte pode começar.

Branch de trabalho: `fix/licenca-seguranca`, no `start-big`. Um commit por spec concluída, e um único PR no fim, só quando você pedir (AGENT.md §7).

## 1. Passos

| Passo | Spec | Repositório | Camada | Depende de | Pode começar quando |
|-------|------|-------------|--------|------------|---------------------|
| 1 | LIC-01 · Cofre e backup cifrado | start-big | Backend | — | Aprovação da SPEC-01 |
| 2 | Tarefa: comentário do heartbeat | start-big | Backend | — | Qualquer momento (uma linha) |
| 3 | LIC-02 · Token offline | start-big | Backend | 1 | Passo 1 concluído |
| 4 | LIC-04 · Rede e front | start-big | Front, Backend e Tauri | 1 | Passo 1 concluído; decisões da SPEC-04 §10 |
| 5 | LIC-03 · Re-login | start-big | Backend e Front | 2, 4 | Passos 3 e 4 concluídos; decisão D-11 da SPEC-03 §10 |
| 6 | LIC-05 · API revogação e backup | plataformaADM | API | Acesso de escrita | Acesso liberado |
| 7 | LIC-06 · API cadastro e sessões | plataformaADM | API | Passo 6 e acesso | Decisões da SPEC-06 §10 |
| 8 | Verificação de integração | ambos | — | Todos | Passos 1 a 7 concluídos |

## 2. Por passo

### Passo 1 · LIC-01 (cofre e backup cifrado)

- **Pontos de atenção:** a migração de dados do token é idempotente, mas não há backup automático antes dela. Testar em banco de teste, nunca em `start_big.db`.
- **Pronto quando:** CT-01 a CT-12 passam, e CA-01 a CA-05 foram verificados. CA-06 e CA-07 exigem Windows real.
- **Sidecar:** avisar o usuário para `npm run build:sidecar` depois da entrega.

### Passo 2 · Comentário do heartbeat

- **Onde:** `backend-fastapi/app/core/tarefas.py:34`. O comentário diz "5 minutos" e o valor é `100` segundos.
- **Pronto quando:** o comentário diz o valor real, ou o valor é ajustado com decisão registrada.
- **Motivo:** a SPEC-06 reduz o timeout de sessão para 10 minutos, e a folga depende deste intervalo.

### Passo 3 · LIC-02 (token offline)

- **Pontos de atenção:** os testes `test_licenca_validacao_offline.py`, `test_licenca_recusa_vencimento.py` e `test_licenca_transferencia.py` mudam de fixture. A expectativa de vencimento não muda.
- **Migração:** coluna `ultimo_horario_visto`. Decide pela presença da coluna.
- **Pronto quando:** CT-01 a CT-17 passam, e CA-01 a CA-07 foram verificados.

### Passo 4 · LIC-04 (rede e front)

- **Pontos de atenção:** a origem da janela Tauri no Windows precisa ser confirmada antes do fechamento do CORS. Mudança nas permissões do Tauri exige recompilar o app.
- **Decisões pendentes:** SPEC-04 §10, pergunta 1 (token nos terminais) e pergunta 2 (rede da loja). Sem resposta, a spec não sai do backlog.
- **Pronto quando:** CT-01 a CT-12 passam e CA-01 a CA-08 foram verificados (os de Windows na skill `verify`).

### Passo 5 · LIC-03 (re-login)

- **Pontos de atenção:** a restauração é aplicada no próximo boot. A tela não pode deixar sair no meio.
- **Decisões pendentes:** SPEC-03 §10 (como comparar o documento do titular, D-11). Sem resposta, a comparação fica de fora, e o resto da spec segue.
- **Dependência de integração:** o cadastro da API (LIC-06) muda o retorno para `202`. O tratamento disso no `registrar_licenca` entra aqui, junto com o re-login depois da confirmação.
- **Pronto quando:** CT-01 a CT-14 passam e CA-01 a CA-06 foram verificados.

### Passo 6 · LIC-05 (API revogação e backup)

- **Repositório:** `plataformaADM`, em branch própria, seguindo o padrão do repositório.
- **Pontos de atenção:** o guard vira `async`, e os testes que o usam precisam de `await`.
- **Pronto quando:** CT-01 a CT-10 passam e CA-01 a CA-06 foram verificados com `npm test`.

### Passo 7 · LIC-06 (API cadastro e sessões)

- **Decisões pendentes:** SPEC-06 §10. Pergunta 1 (como o app recebe a chave depois da confirmação) e pergunta 2 (trial só depois da confirmação). A recomendação é B e A.
- **Pontos de atenção:** a migração Prisma tem campos novos em `Cliente` e `LicencaSessao`. Mudança de heartbeat depende do passo 2.
- **Pronto quando:** CT-01 a CT-14 passam e CA-01 a CA-07 foram verificados.

### Passo 8 · Verificação de integração

Feita pela skill `verify`, com o app rodando no Windows, na ordem:

1. Cadastro novo, confirmação de e-mail e primeiro acesso.
2. Login diário, com internet e depois sem internet.
3. Re-login no caso 1 (outro computador): aviso, troca, e o computador antigo parando.
4. Re-login no caso 2 (banco perdido): escolha, restauração, reinício e dados de volta.
5. Troca de servidor com caixas conectados.

**Pronto quando:** os cinco fluxos foram verificados ou marcados como "não verificado", com o motivo.

## 3. Perguntas abertas

| Spec | Pergunta | Recomendação |
|------|----------|--------------|
| LIC-03 | Como comparar o documento do titular (D-11) | A: API devolve os últimos 4 dígitos |
| LIC-04 | Onde guardar o token nos terminais | A: cofre do Tauri, com dependência aprovada |
| LIC-04 | Proteção da rede da loja (F34) | A agora, com C no plano de infraestrutura |
| LIC-06 | Como o app recebe a chave depois da confirmação | B: login com e-mail e senha (re-login) |
| LIC-06 | Trial só depois da confirmação | A: sim |

Cada pergunta é respondida separadamente, como combinado. Até a resposta, a spec correspondente fica no backlog.

## 4. Riscos conhecidos

- **Terminais sem cofre:** a DPAPI só protege o servidor. A pergunta sobre o token dos terminais é necessária antes de dizer que o token está protegido na loja inteira.
- **Dependência de API:** o caso 1 do re-login pede a revogação (LIC-05). Sem ela, o computador antigo continua gerando backup, mesmo com o novo funcionando.
- **Cadastro:** a confirmação de e-mail sem a SPEC-03 deixa o novo cadastro sem caminho no app.
