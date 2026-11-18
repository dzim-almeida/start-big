# Acordo — `licenca` (correções de segurança e re-login)

> Escrito pelo agente na skill `spec` §2.2 e aprovado pelo usuário **antes** de qualquer spec. As decisões `D-NN` são citadas pelas specs e pelos testes.

**Status:** Aprovado em 2026-11-18 (D1 a D12 respondidas pelo usuário; itens técnicos da seção 2.C sem objeção)
**Branch de trabalho:** `fix/licenca-seguranca` (a partir de `origin/develop`). Só o `start-big` nesta fase.

## 1. Contexto

### 1.1. Material lido

- Análise de segurança, dados e experiência da integração start-big ↔ API StartBig (sessão desta data).
- Quadro interativo "Quadro da Licença" (38 erros, 17 etapas, 28 relações) e plano "Plano de Correção" (ordem de prioridade, três métodos por erro, roteiro).
- Harness da branch `develop`: `.agent/AGENT.md`, `rules/api-contract.md`, `skills/spec`, `skills/doc`.

### 1.2. Fatos do sistema que moldaram as decisões

- O token da licença é guardado em texto puro na coluna `token`: `backend-fastapi/app/db/models/configuracao_licenca.py:57`. O banco não é cifrado (`app/db/session.py:70`).
- O backup é um ZIP do snapshot inteiro, sem cifra e sem exclusão de tabela: `app/services/backup/local.py:188`.
- O guard da API só verifica assinatura e validade do token: `plataformaADM/apps/server/src/core/guards/erp-licenca.guard.ts`. A revogação por máquina (`licencaHwidRevogado`) não é consultada no backup.
- O cofre Stronghold e o keyring existem no front, mas o Rust não registra o plugin e nenhum código os usa (`frontend/src/shared/services/system/secureStorage.service.ts`; `frontend/src-tauri/src/lib.rs`).
- O login do ERP usa `Bearer` guardado em `localStorage` (`frontend/src/api/axios.ts:14,26-28`). O CLAUDE.md diz cookie HTTP-only.
- O backend é um sidecar Python. Ele não consegue chamar plugins do Tauri.
- O backend roda em `0.0.0.0` e os terminais chamam `http://IP:porta/api` (`frontend/src/api/backendUrl.ts`).

## 2. Decisões

### A. Arquitetura e modelo de dados

| ID | Decisão | Motivo | Alternativa descartada |
|----|---------|--------|------------------------|
| D-01 | As specs dos itens da API ficam em `.agent/specs/licenca/` com a marca "repositório: plataformaADM". A implementação só começa quando houver acesso de escrita ao repositório da API. | Um único lugar de planejamento; o `start-big` já depende do contrato da API. | Harness copiado para a API (B); lista sem spec (C). |
| D-02 | O segredo local (token, e depois dados sensíveis) é protegido pela **DPAPI do Windows**, chamada direto do Python por `ctypes`. Sem dependência nova. Ver **ADR-001**. | O sidecar Python não chama plugins do Tauri. A DPAPI não exige dependência nova e o backend controla o próprio segredo. | Plugin de keyring no Rust (A); Stronghold (C). |
| D-03 | O ZIP do backup é cifrado com chave derivada da **chave de ativação da licença**. | A chave é igual em todas as máquinas da licença, então a restauração funciona no computador novo (caso 1 do re-login). | Chave só da máquina (quebra a restauração); senha do dono (mais atrito); não cifrar (dados em claro na nuvem). |

### B. Regras de negócio

| ID | Decisão | Motivo | Alternativa descartada |
|----|---------|--------|------------------------|
| D-04 | Validade do token continua em **7 dias**. O guard da API passa a consultar a revogação (`hwidRevogado` e `hwidServidor`) antes de aceitar o token. Redução para 24 h fica para uma etapa futura. | A revogação já é por máquina, e o guard já recebe a licença e o HWID do token. Uma lista de tokens (`jti`) não traria proteção a mais e exigiria tabela nova. | Reduzir para 24 h agora (B): mais dependência de internet; lista de tokens (C): tabela e migração sem ganho imediato. |
| D-05 | Relógio do PC voltou no tempo: o app **avisa o dono** e segue usando até o último horário registrado. | Bloquear o PDV no meio do expediente causa mais prejuízo que o risco de relógio manipulado. | Bloquear até reconectar (A); ignorar (C). |
| D-06 | Trial tem **um backup completo** (sem incrementais). | Protege quem perde o banco nos primeiros dias sem custo alto de armazenamento. | Liberar backup completo no trial (A); só avisar (B). |
| D-07 | A restauração depois do re-login é liberada ao **titular que acabou de provar a senha**, com a senha pedida de novo na chamada. | Resolve o caso 2 sem exigir Master e sem etapa de e-mail. | Só Master com aviso (B); código por e-mail (C). |
| D-08 | Reinstalação do Windows **conta como troca** de computador, com aviso antes de confirmar. | Ver a explicação na seção 3. | Não contar quando o nome ou o ID anterior for reconhecido (B); suporte libera caso a caso (C), como complemento futuro. |
| D-09 | Limite de tentativas de senha: **bloqueio progressivo por e-mail**, com espera de 1, 5 e 15 minutos (teto de 15). | Protege a conta; o teto curto evita trancar o dono por muito tempo. | 5 tentativas por minuto por IP (A); CAPTCHA após 3 falhas (C). |
| D-10 | Sessões sem heartbeat expiram em **10 minutos**, em vez de 35. | Libera vagas sem depender do dono. | Tela para liberar vagas (B), que pode vir depois; manter 35 min (C). |
| D-11 | Setup com CPF ou CNPJ diferente do titular da licença: **pede confirmação explícita** antes de seguir. | Evita erro de digitação sem criar bloqueio por e-mail. | Bloquear até confirmar por e-mail (B); só avisar (C). |

### C. Permissões e contrato da API

| ID | Decisão | Motivo | Alternativa descartada |
|----|---------|--------|------------------------|
| D-12 | O login do ERP continua com **Bearer**. O token fica só em `sessionStorage`: some ao fechar o app e não é guardado em disco. Vale igual para servidor e terminal. Ver **ADR-002** (Bearer) e **ADR-003** (armazenamento). | O backend roda em outra origem e o cookie complicaria a comunicação dentro do Tauri. O token do login fica só na sessão da janela, sem persistir (ADR-003). | Migrar para cookie HTTP-only (B); híbrido com refresh no cofre (C). |

### 2.C. Decisões técnicas padrão (sem objeção do usuário)

| ID | Decisão |
|----|---------|
| D-13 | Carência e prazo offline passam a vir do **token assinado**. O app deixa de usar as colunas para isso (F25, F7). |
| D-14 | Módulos são **bloqueados** quando a chave pública não puder ser lida (F8). |
| D-15 | O app confere `licencaId` e `hwid` do token com a licença local e a máquina (F24). |
| D-16 | Erros de tela saem por código, nunca com o texto da exceção (F10, F27). |
| D-17 | `v-html` dos modais é trocado por texto escapado (F35). |
| D-18 | CORS com lista fechada de origens (F1). |
| D-19 | Permissões de arquivo do banco e da configuração restritas ao usuário (F37). |
| D-20 | Argumentos do sidecar e escopo do `fs` restritos (F38). |
| D-21 | Rede da loja: a API local só aceita conexões das redes privadas (`10/8`, `172.16/12`, `192.168/16`), por regra de firewall no instalador e por verificação no app (F34, opção A). **Aprovada em 2026-11-18.** TLS (opção C) fica para a LIC-07. |

## 3. Consequências

- **D-02 e D-03:** o backend passa a depender da DPAPI, que só existe no Windows. Os testes no Linux precisam de um caminho alternativo que não grave segredo real. A ADR-001 registra isso.
- **D-03:** o backup antigo, cifrado pela regra antiga ou não cifrado, precisa de caminho de leitura para não quebrar a restauração. Isso entra na spec de backup.
- **D-08 (explicação):** o identificador da máquina no Windows (MachineGuid) muda quando o Windows é reinstalado. Para a nuvem, é um computador novo. Sem o aviso, o dono pode gastar as trocas do mês (3 em 30 dias) sem perceber e depois ficar bloqueado até falar com o suporte.
- **D-12:** o CLAUDE.md muda. Pela regra, a alteração de premissa do projeto vai por ADR; a ADR-003 substitui a parte do cofre da ADR-002.

## 4. Endpoints e códigos de erro

Ainda não definidos. Cada spec que alterar rota ou erro registra aqui antes de ser implementada.

## 5. Mapeamento das specs

A ser detalhado depois da aprovação deste acordo. Ordem sugerida, por entrega testável:

| Ordem | Arquivo | Camada | Conteúdo | Depende de |
|-------|---------|--------|----------|------------|
| 1 | `SPEC-01-COFRE-LICENCA.md` | Backend | Cofre DPAPI (D-02), token cifrado (F30), ACL (D-19), backup cifrado (D-03, F31) | — |
| 2 | `SPEC-02-TOKEN-OFFLINE.md` | Backend | D-13, D-14, D-15, D-05 | 1 |
| 3 | `SPEC-03-RE-LOGIN.md` | Backend e front | D-07, D-06 (trial), D-11, D-16, D-17 | 1, 2 |
| 4 | `SPEC-04-REDE-E-FRONT.md` | Front e Tauri | D-12, D-18, D-17, D-20 | 1 |
| 5 | `SPEC-05-API-REVOGACAO.md` | API (`plataformaADM`) | D-04, D-01 | depende de acesso |
| 6 | `SPEC-06-API-CADASTRO-SESSOES.md` | API (`plataformaADM`) | D-09, D-10, cadastro idempotente, confirmação de e-mail | depende de acesso |

## 6. Pontos pendentes

- **Aberto (escrito em 2026-11-18, ao criar as specs):** três perguntas, uma por vez, com recomendação em cada spec:
  - **LIC-03 · D-11:** como comparar o documento do titular. Recomendação: a API devolve os últimos 4 dígitos.
  - **LIC-06:** como o app recebe a chave depois da confirmação de e-mail. Recomendação: login com e-mail e senha.
  - **LIC-06:** trial só depois da confirmação. Recomendação: sim.
- **Fechado em 2026-11-18:** proteção da rede da loja (F34), opção A aprovada (D-21).
- **Fechado em 2026-11-18:** token do terminal (LIC-04): token do login fica só em `sessionStorage` (ADR-003), para servidor e terminal. Não há cofre para o login, então as rotas `/sessao/token-erp` saem da SPEC-04.
- **Fechado em 2026-11-18:** CLAUDE.md corrigido na seção de autenticação e na seção do Tauri (Stronghold e keyring declarados, não registrados). Módulo com `README.md` e `learn/`.
- **Próxima etapa:** SPEC-01 (cofre e backup). Só começa com a aprovação explícita da spec.

## 7. Fora do escopo (registrado)

- Alterações no `plataformaADM` — quando houver acesso de escrita (D-01).
- TLS na rede da loja com certificado próprio (F34, opção C) — **LIC-07**, spec própria depois da LIC-04. Exige IP ou nome estável na loja e instalação da autoridade da loja em cada caixa.
- SQLCipher para o banco inteiro (F30 alternativa B) — pode voltar se o cofre não for suficiente.
- Lista de tokens revogados por `jti` (D-04, alternativa C) — só se for preciso revogar um token específico.
- Tela de liberação manual de vagas (D-10, alternativa B) — depois de medir se o expurgo automático basta.
- Reduzir a validade do token para 24 h (D-04, alternativa B) — depois do guard ser validado.
