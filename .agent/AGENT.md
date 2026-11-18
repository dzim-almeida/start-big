# AGENT.md — StartBig

Ponto de entrada do agente. Leia este arquivo inteiro antes de qualquer tarefa. Ele indexa o resto do Harness: abra os outros arquivos **só quando a tarefa pedir**.

> Caminhos com `@/` são relativos a `.agent/`. Caminhos sem prefixo são relativos à raiz do repositório.
>
> ⚠️ **Cuidado com dois significados de `@/`:** nos documentos do Harness, `@/rules/...` é a pasta `.agent/rules/`. Já dentro de **código do frontend** (`import api from '@/api/axios'`), `@/` é o **alias do Vite** para `frontend/src/`. Quando o texto estiver num bloco de código de import, é o alias do Vite.
>
> O `CLAUDE.md` da raiz continua sendo a fonte dos **comandos de desenvolvimento, portas, sidecar, banco e papel da máquina**. Este Harness diz **como trabalhar** (processo, camadas, specs, revisão); o `CLAUDE.md` diz **como o projeto roda**. Os dois não se repetem.

---

## 1. O projeto em 30 segundos

**StartBig** é um ERP / PDV (ponto de venda) que roda como **aplicativo desktop**: casca **Tauri** (Rust), interface **Vue 3** e backend **FastAPI** (Python) com banco **SQLite**. Cada instalação atende uma empresa (`empresa_id` está nas tabelas de negócio e vem do token do usuário), com permissões por usuário e cargo. **Dado de uma empresa nunca pode aparecer para outra.**

| Camada | Tecnologia |
|--------|------------|
| Desktop | Tauri 2 (Rust): sidecar do backend, rede e papel da máquina, Stronghold e keyring |
| Frontend | Vue 3 + TypeScript + Vite · Pinia · TanStack Query (vue-query) · VeeValidate + Zod · Tailwind 4 · Vitest · Storybook |
| Backend | Python + FastAPI · SQLAlchemy (sessão **síncrona**) · Pydantic · Alembic · pytest |
| Banco | SQLite (arquivo local da instalação; em memória nos testes) |
| Empacotamento | PyArmor + PyInstaller (sidecar) → instalador NSIS pelo Tauri |

### Módulos

Os módulos do frontend ficam em `frontend/src/modules/` e os do backend se espalham por `schemas/`, `services/`, `db/crud/` e `db/models/` (um nome de domínio por pasta). O Harness acompanha cada módulo em `@/docs/{módulo}/` e `@/specs/{módulo}/`, **criados na primeira tarefa que tocar o módulo** (modelos em `@/docs/_modelo/` e `@/specs/_modelo/`).

| Domínio | Frontend (`modules/`) | Backend (pasta de domínio) |
|---------|-----------------------|----------------------------|
| Acesso e sessão | `auth`, `sign-in`, `minha-conta` | `acesso`, `funcionario` |
| Cadastros | `customers`, `employees`, `enterprise`, `products` | `cliente`, `empresa`, `produto`, `endereco`, `fornecedor` |
| Vendas e caixa | `sales`, `home` | `vendas`, `sessao_caixa`, `forma_pagamento` |
| Ordens de serviço e orçamentos | `order-service` | `ordem_servico`, `orcamentos` |
| Compras e estoque | `compras` | `compras` |
| Financeiro e fiscal | `financeiro`, `fiscal` | `financeiro`, `fiscal` |
| Segmentos | `marcenaria`, `lava-rapido` | `marcenaria`, `lava_rapido`, `fabrica` |
| Configuração e infraestrutura | `configuracoes`, `license`, `network-config`, `mainLayout`, `reports` | `configuracao`, `licenca`, `backup`, `relatorio`, `core/` |

> A tabela é um **mapa de navegação**, não um registro de status. O estado real de cada módulo fica no `SUMMARY.md` dele (`@/docs/{módulo}/`), quando existir.

---

## 2. Índice de `.agent/`

| Pasta / arquivo | Responsabilidade | Quando abrir |
|-----------------|------------------|--------------|
| `@/AGENT.md` | Este índice: regras globais, comandos e arquitetura resumida | Sempre (já carregado) |
| `@/rules/` | Regras **obrigatórias** de arquitetura e de processo | Antes de criar ou mover arquivos; ao fim de toda sessão |
| `@/skills/` | Procedimentos passo a passo (TDD, review, migração, docs, design, specs, verificação ponta a ponta, handbook do módulo) | Quando a tarefa bate com a coluna "Quando usar" da seção 4 |
| `@/docs/{módulo}/` | Conhecimento consolidado do módulo: visão geral, resumo, histórico e aprendizados | **Primeiro passo** de toda tarefa |
| `@/specs/{módulo}/` | O que implementar: specs numeradas, índice e ordem de dependência | Depois dos docs, para achar a spec certa |
| `@/specs/active/` | A spec em andamento (no máximo uma) | Ao começar e ao retomar trabalho |
| `@/evals/` | Cenários para avaliar se o agente segue este Harness | Só quando pedido ou ao alterar o Harness |

Cada pasta tem um `README.md` com o contrato dela.

---

## 3. Fluxo obrigatório de trabalho

Toda tarefa segue uma de duas trilhas. Escolha no início e diga ao usuário qual é e por quê, em uma linha. Na dúvida entre as duas, pergunte.

| Trilha | Quando | Fluxo |
|--------|--------|-------|
| **Completa** | Implementar uma spec; criar endpoint, tela, model, migração ou dependência; mudar contrato da API, autenticação, permissões, isolamento por empresa, regra fiscal ou financeiro | §3.1 (skill `doc`) |
| **Leve** | Correção pontual, ajuste visual ou de texto, refatoração pequena dentro de um módulo, pergunta ou investigação, ajuste de docs ou do Harness | §3.2 |

O custo do processo acompanha o tamanho da tarefa. Em qualquer trilha, rode só o que a mudança pede e uma rodada completa de verificação no fim (§7, "Verificação").

### 3.1. Trilha completa

Segue a skill **`doc`** (`@/skills/doc/SKILL.md`). Resumo:

1. **Identificar o módulo** da intenção (`customers`, `sales`, `fiscal`...). Na dúvida, perguntar.
2. **Ler `@/docs/{módulo}/`**: `SUMMARY.md`, `CHANGELOG.md` (entradas recentes), o índice `learn/README.md` (e o de `@/docs/_shared/learn/`) e **todo** aprendizado que a tarefa toca. Do `README.md` do módulo, só as seções que a tarefa toca.
3. **Ir para `@/specs/{módulo}/README.md`** e escolher a spec pela ordem de dependência. Se houver algo em `@/specs/active/`, retomar essa spec. Sem spec para a tarefa: planejar e escrever com a skill `spec`.
4. **Ativar a spec** (mover para `@/specs/active/`), implementar com as skills necessárias e cumprir os critérios de aceite.
5. **Concluir**: rodar a verificação completa uma vez, revisar (skill `code-review`), verificar no app quando um critério de aceite pedir e ao fim da série (skill `verify`), mover a spec para `@/specs/{módulo}/completed/`, atualizar `CHANGELOG.md` (e `SUMMARY.md` na spec avulsa ou no fim da série) e registrar aprendizados (regra `session-learnings`).

### 3.2. Trilha leve

1. **Contexto mínimo:** `SUMMARY.md` do módulo (se existir), os índices de `learn/` (módulo e `_shared`) e só os aprendizados que a tarefa toca. Spec e `README.md` do módulo só na seção que a tarefa pede. Não leia skills que a tarefa não usa.
2. **Sem ativar spec.** Se a mudança altera um comportamento descrito numa spec concluída, acrescente nela uma nota de revisão (`> **Revisão N (AAAA-MM-DD):** ...`).
3. **Testes:** mudança de comportamento segue a skill `tdd`, rodando só os testes dos arquivos tocados. A verificação completa do lado afetado roda uma vez, quando o usuário encerrar a rodada ou ao fim da tarefa.
4. **Sem `verify`**, salvo pedido do usuário.
5. **Revisão curta** (skill `code-review` §0) sobre o diff.
6. **Docs:** uma entrada no `CHANGELOG.md` do módulo, se o comportamento mudou. `SUMMARY.md` só se mudou o que está pronto ou as pendências. Aprendizados pela regra `session-learnings`.
7. **Subir de trilha:** se a tarefa passar a pedir algo da trilha completa (endpoint, model, migração, dependência, código de produção de outro módulo), pare, diga isso ao usuário e siga a §3.1.

**Hierarquia de fontes** (em caso de conflito, a de cima vence e o agente **para e pergunta** antes de seguir):

1. Instrução explícita do usuário na conversa
2. Spec ativa
3. `@/rules/`
4. `CLAUDE.md` e `@/docs/{módulo}/`
5. `@/skills/`
6. Código existente (código antigo e marcadores provisórios não são referência de padrão)

Nunca "corrija" uma spec em silêncio. Divergência encontrada → registrar e perguntar.

---

## 4. Skills

| Skill | Arquivo | Quando usar |
|-------|---------|-------------|
| `doc` | `@/skills/doc/SKILL.md` | **Início e fim de toda tarefa da trilha completa** (§3.1) |
| `tdd` | `@/skills/tdd/SKILL.md` | Qualquer código novo ou alteração de comportamento (backend ou frontend) |
| `migration` | `@/skills/migration/SKILL.md` | Criar ou alterar models SQLAlchemy, gerar ou aplicar migrações Alembic |
| `design` | `@/skills/design/SKILL.md` | Implementar ou ajustar telas e componentes visuais a partir de um protótipo, imagem ou tela de referência, respeitando os tokens e os componentes `Base*` |
| `verify` | `@/skills/verify/SKILL.md` | Verificação ponta a ponta local (backend na porta certa, frontend, login, fluxos no navegador ou na janela Tauri) quando um critério de aceite pedir, ao fim de uma série de specs e quando o usuário pedir |
| `code-quality` | `@/skills/code-quality/SKILL.md` | Checklist de DRY, YAGNI e Clean Code. Use junto com `code-review` ao revisar qualidade |
| `code-review` | `@/skills/code-review/SKILL.md` | Antes de concluir uma spec, na versão curta ao fim da trilha leve (§3.2) e quando o usuário pedir revisão |
| `spec` | `@/skills/spec/SKILL.md` | Planejar um módulo ou série (acordo, ADR, roteiro) e escrever ou revisar specs no modelo padrão, com o checklist de validação |
| `handbook` | `@/skills/handbook/SKILL.md` | Documentar um módulo implementado para pessoas em três artefatos (Visão Geral, Especificação de Negócio, Documentação Técnica). Sob demanda, ou quando a skill `doc` §7.4 sugerir |

---

## 5. Arquitetura (resumo)

Detalhes e regras estritas: `@/rules/frontend-architecture.md` e `@/rules/backend-architecture.md`. Formato da API (rotas, status, erros, paginação): `@/rules/api-contract.md`.

### Frontend — arquitetura por módulos (`frontend/src/`)

```
main.ts · App.vue · router/index.ts     composição da aplicação
api/                                    cliente Axios e descoberta da URL do backend
core/                                   configuração central do app
shared/                                 código transversal; NUNCA importa de modules/
  components/ composables/ stores/ services/ schemas/ types/ utils/ constants/ theme/ assets/
modules/{módulo}/                       uma pasta por domínio (customers, sales...)
  views/ components/ composables/ services/ schemas/ types/ constants/ routes.ts
```

Dependência em uma direção só: `views → components/composables → services → schemas/types → api`. As rotas de `modules/**/routes.ts` são descobertas sozinhas pelo `router/index.ts`.

### Backend — camadas (`backend-fastapi/app/`)

```
main.py                    composição: routers, handlers, middlewares, startup
api/v1/api.py              agregação dos routers
api/v1/endpoints/          rotas (controllers) — só HTTP
services/{domínio}/        regras de negócio
db/crud/{domínio}/         acesso ao banco (consultas e gravações)
db/models/                 models SQLAlchemy
schemas/{domínio}/         contratos Pydantic de entrada e saída
core/                      infraestrutura transversal (config, segurança, dependências)
```

Dependência em uma direção só: `endpoint → service → crud → model`. Toda consulta a dado de negócio é filtrada por `empresa_id` vindo do **token** (`check_permission`), nunca do corpo da requisição.

---

## 6. Comandos

Os comandos de desenvolvimento (subir backend e frontend, portas, sidecar, venv) estão no `CLAUDE.md`. Esta seção só classifica **o que o agente pode executar sozinho**. O ambiente padrão do usuário é **Windows** (PowerShell/Git Bash): confira o shell antes de montar o comando.

### 6.1. Permitidos sem pedir confirmação

| Área | Comandos |
|------|----------|
| Git (leitura) | `git status`, `git diff`, `git log`, `git show`, `git branch --show-current` |
| Backend (em `backend-fastapi/`, com a venv ativa) | `python -m pytest <arquivo ou pasta>`, `alembic current / history / heads / check`, `alembic revision --autogenerate -m "..."`, `alembic upgrade head` (**só banco local de teste**, nunca o `start_big.db` da loja) |
| Frontend (em `frontend/`) | `npm run dev`, `npm run test`, `npx vitest run <arquivo>`, `npx vitest related <arquivo> --run`, `npx vue-tsc --noEmit`, `npm run lint:check`, `npm run check:tokens` (e os outros `check:*`), `npm run storybook` |
| Diagnóstico | Listar portas em uso (`netstat -ano`, `Get-NetTCPConnection`) e testar `http://localhost:8000/docs` |
| Arquivos | Ler, buscar e editar arquivos do repositório; `git mv` dentro de `.agent/specs/` |

### 6.2. Permitidos só com confirmação explícita do usuário

- `git add`, `git commit`, `git push` (sem force), criar branch. **Só commitar quando o usuário pedir.** Mensagens em português, no padrão Conventional Commits do histórico (`feat(modulo): ...`, `fix(modulo): ...`).
- Instalar ou remover dependências (`pip install`, `npm install <pacote>`), exceto as já previstas na spec ativa. Dependência de backend entra no `requirements.txt` (`pip freeze > requirements.txt`).
- `npm run build`, `npm run build:sidecar` e `npm run tauri build` (demorados e geram artefatos).
- `alembic downgrade -1` (só banco de teste, para validar a migração).
- Apagar arquivos que o agente não criou nesta sessão.
- Qualquer comando contra o banco de uma instalação real.

### 6.3. Proibidos (não executar nem com pedido indireto; orientar o usuário a fazer)

| Comando | Motivo |
|---------|--------|
| `git push --force` / `-f`, `git push` direto para a branch principal | Reescreve ou publica histórico compartilhado |
| `git reset --hard`, `git clean -f*`, `git checkout -- .`, `git restore .`, `git stash clear`, `git branch -D` | Descarta trabalho não commitado sem volta |
| `git commit --amend` em commit já enviado, `git rebase` em branch compartilhada, `git filter-branch` | Reescreve histórico |
| `--no-verify` em qualquer comando git | Pula verificações de qualidade |
| `rm -rf`, `Remove-Item -Recurse -Force`, `rmdir /s`, `del /s` | Remoção em massa irreversível |
| Apagar, renomear ou sobrescrever `start_big.db` (ou qualquer `*.db` de dados reais); chamar o endpoint `reset_bd` | O `create_all()` do startup cria um banco **vazio** ao lado do verdadeiro: o sintoma é "o sistema não reconhece meu usuário" |
| `DROP DATABASE/TABLE`, `TRUNCATE`, `DELETE` sem `WHERE`, `alembic downgrade base` | Destrói schema ou dados |
| Editar ou apagar uma migração já aplicada ou já publicada | Quebra o histórico do Alembic nas máquinas dos clientes |
| Mover a pasta do projeto sem recriar a `.venv` | Os atalhos da venv guardam o caminho absoluto e passam a sair com exit 1 sem mensagem |
| Ler ou imprimir `.env`, certificados (`*.pfx`), `system-config.json` de produção ou o conteúdo do `rede.log`; colocar segredos em código, logs ou docs | Vazamento de credenciais e dados de cliente |
| Publicar pacote ou release (`npm publish`, upload de instalador) | Publicação externa |

---

## 7. Convenções globais

- **Idioma:** documentação, specs, **código e comentários em PT-BR**, como no `CLAUDE.md` (variáveis, funções, campos de banco, mensagens de API e texto de tela). Palavras técnicas sem tradução natural (`token`, `hook`, `store`, `composable`) ficam como são. Siga o idioma do módulo em que você está: pastas antigas em inglês (`customers`, `employees`) não são renomeadas fora de uma spec.
- **Comentários explicativos:** o usuário é **programador iniciante**. Todo código novo ou alterado leva comentários que expliquem **o que a linha ou bloco faz e por quê**, em PT-BR simples, sem presumir que o leitor conhece o framework. Explique também o conceito quando for a primeira vez que ele aparece (ex.: o que é um `composable`, o que o `Depends` faz). Esta regra vale para código em specs, exemplos de skills e respostas ao usuário.
- **Branches:** nunca trabalhar direto na branch principal (`master`). Padrão: `feat/<módulo>`, `fix/<escopo>`, `chore/<escopo>`. **Série de specs:** uma branch para a série inteira, um commit por spec concluída e um único PR no fim. Spec avulsa: uma branch por spec. Não abrir PR sem o usuário pedir.
- **Escopo:** implementar só o que a spec ativa pede (YAGNI). Melhorias fora do escopo → anotar e sugerir, não implementar. Precisar alterar **código de produção** fora de "Arquivos afetados" da spec (outro módulo, `core/` ou `shared/`, contrato da API, model, migração, dependência, segurança) é **divergência**: pare e pergunte **antes** de editar. Arquivos de apoio (testes, fixtures, índices e re-exports, tipos e docs do próprio módulo) seguem sem parar e ficam registrados na spec (skill `doc` §5).
- **Mexeu no backend → o sidecar fica velho.** O instalador leva o backend empacotado, e `npm run build` falha se ele estiver mais antigo que o código. Ao concluir uma tarefa que altera `backend-fastapi/app/`, avise o usuário para rodar `npm run build:sidecar` antes de gerar instalador. Não rode sozinho (§6.2).
- **Migração nova** decide pelo **schema antigo**, não pela ausência do novo: o `create_all()` do startup roda antes do `upgrade("head")` (modelo: `965c71a2da9a`; skill `migration`). Não há backup automático antes de migrar.
- **Testes:** nenhuma spec é concluída com teste falhando ou sem os casos de teste listados nela.
- **Verificação:** durante o trabalho, rode só os testes do que mudou. Suíte completa do lado afetado, `vue-tsc` e lint rodam **uma vez**, depois da última mudança de código (skill `tdd` §6), e a revisão reaproveita essa saída. Lembrete: o `npm run build` **não** roda o `vue-tsc`; type error só aparece se você rodar `npx vue-tsc --noEmit`.
- **Limite de tentativas:** o mesmo comando ou ferramenta falhou duas vezes com o mesmo sintoma → pare de tentar.
  - **Falha de ambiente** (porta ocupada, venv quebrada, backend em outra porta, rede, janela Tauri sem resposta): registre como "não verificado", com o motivo, e siga com o resto. Se ela bloqueia um critério de aceite, pergunte ao usuário. Antes de culpar o banco, **cheque a porta** (dev usa 8000; app instalado usa 8080–8083).
  - **Falha do código:** antes da terceira tentativa, investigue a causa uma vez (log, código, teste isolado). Não varie flags nem repita o comando às cegas.
  - Nunca espere em laço (`sleep`, polling) por algo fora do seu controle.
- **Arquivos provisórios e legado:** arquivos de teste solto (`tmp_test.txt`, `nota.txt`), scripts de uma vez só e código antigo fora do padrão **não** são exemplo de padrão. Use o módulo mais recente e a regra.

---

## 8. Ao terminar qualquer sessão

- [ ] Trilha completa: spec ativa movida ou com status atualizado (skill `doc`)
- [ ] Aprendizados importantes registrados em `@/docs/{módulo}/learn/` (regra `@/rules/session-learnings.md`)
- [ ] `CHANGELOG.md` do módulo atualizado por spec concluída (ou por mudança de comportamento na trilha leve); `SUMMARY.md` na spec avulsa ou no fim da série
- [ ] Backend alterado → usuário avisado sobre `npm run build:sidecar`
- [ ] Resumo final para o usuário, em linguagem simples: trilha usada, o que foi feito, o que foi verificado (e como), o que ficou "não verificado" (e por quê) e o que ficou pendente
