---
name: code-review
description: Revisão de código do StartBig baseada na arquitetura do projeto, isolamento por empresa, segurança, regras fiscais/financeiras, SOLID, YAGNI, DRY, KISS e convenções de Python/FastAPI e Vue/TypeScript. Produz achados classificados por severidade com arquivo e linha. Use antes de concluir uma spec, na versão curta ao fim da trilha leve e quando o usuário pedir revisão.
---

# Skill `code-review`

> Caminhos com `@/` são relativos a `.agent/`.

## 0. Escopo e postura

- **O que revisar:** o diff da tarefa (`git diff` + `git diff --staged` + arquivos novos em `git status`). Se o usuário indicar um alvo (branch, arquivo, PR), revise esse alvo.
- **Contra o quê:** a spec ativa, `@/rules/*` e esta checklist.
- **Postura:** revisor sênior, direto e específico, **e didático**: o usuário é iniciante. Cada achado aponta `arquivo:linha`, explica o **problema concreto** (o que quebra, para quem, em que cenário), **por que** isso é um problema e sugere a correção com um exemplo comentado. Nada de "considere talvez...", nem elogio genérico.
- **Não invente achado.** Se não souber se algo é um problema, verifique (leia o código chamado, rode o teste). Se ainda assim for incerto, classifique como `pergunta`.
- Revisão de código próprio exige o mesmo rigor: releia o diff como se fosse de outra pessoa.
- **Revisão curta** (trilha leve, `@/AGENT.md` §3.2): só §2.1, §2.2 (se o diff tiver consulta em tabela de negócio) e §2.3, sobre o diff. Saída no formato da §3, só com as seções que têm achados. Se a revisão achar algo da trilha completa (endpoint, model, contrato, código de outro módulo), diga isso e pare.

## 1. Severidades

| Severidade | Significado | Bloqueia conclusão da spec? |
|------------|-------------|-----------------------------|
| 🔴 **bloqueante** | Bug, falha de segurança, vazamento entre empresas, perda de dados, cálculo de dinheiro/imposto errado, violação de regra obrigatória, critério de aceite não atendido | Sim |
| 🟠 **importante** | Problema de design ou manutenção que vai custar caro logo (acoplamento errado, duplicação real, teste faltando para caso da spec) | Sim, salvo acordo explícito com o usuário |
| 🟡 **sugestão** | Melhoria de legibilidade, nome, simplificação | Não |
| ❔ **pergunta** | Dúvida que precisa do usuário ou da spec para decidir | Depende da resposta |

## 2. Ordem da revisão (do mais caro ao mais barato)

### 2.1. Correção e aderência à spec

- [ ] Faz o que a spec pede, e **só** isso? Algo fora do escopo foi implementado?
- [ ] Critérios de aceite e casos de teste da spec cobertos?
- [ ] Casos de borda: vazio, nulo, zero, negativo, limites, duplicidade, duas abas ou dois caixas ao mesmo tempo, falha de rede ou de banco, app fechado no meio de uma operação.
- [ ] Erros tratados no lugar certo, sem engolir exceção (`except: pass`, `catch {}` vazio).
- [ ] **Dinheiro, quantidade e imposto:** usa `Decimal`/`Numeric` (nunca `float`), arredonda em **um** lugar e conferido com valor exato. Soma de parcelas bate com o total.

### 2.2. Isolamento por empresa — sempre que houver consulta em tabela de negócio

- [ ] Toda consulta/gravação filtra por `empresa_id` vindo do **token**.
- [ ] Nenhum schema de entrada aceita `empresa_id` do cliente.
- [ ] Busca por `id` sem filtrar empresa (`db.get(Model, id)`, `query.get`) em tabela de negócio é **bloqueante**.
- [ ] Registro de outra empresa devolve `404` (não `403`, não o dado).
- [ ] Existe teste de isolamento (empresa A × empresa B) para o recurso novo.

### 2.3. Segurança

- [ ] Rota autenticada declara `check_permission(...)` com a permissão certa; rota de segmento/módulo opcional também checa o módulo habilitado.
- [ ] Sem segredo em código, log ou docs (senha, token, chave, certificado, `.env`). Sem `print` de dado sensível.
- [ ] Sem SQL montado por concatenação de texto (`text(f"... {entrada}")`); use parâmetros.
- [ ] Upload e caminho de arquivo: nome sanitizado, sem `..`, tamanho e tipo limitados.
- [ ] Resposta não expõe hash de senha, token, dado de outra empresa, nem stack trace.
- [ ] Frontend: nada sensível em `localStorage` além do que o projeto já guarda (token); sem `v-html` com dado do usuário.
- [ ] Tauri: comando nativo novo exposto ao front tem permissão mínima (capabilities) e valida os argumentos.

### 2.4. Arquitetura (`@/rules/`)

- [ ] Arquivo no lugar certo e import na direção certa (`frontend-architecture` §3, `backend-architecture` §3).
- [ ] Endpoint sem regra de negócio; service sem `commit`; crud sem regra de negócio.
- [ ] Um módulo do frontend não importa de outro; compartilhado foi para `shared/`.
- [ ] Contrato da API respeita `api-contract` (status, erro, paginação).
- [ ] Mexeu em `models/`? Há migração revisada (skill `migration`) e import no `alembic/env.py`.

### 2.5. Design e princípios

- [ ] **YAGNI:** nada "para o futuro" (parâmetro sem uso, camada extra, flag sem consumidor).
- [ ] **DRY (de verdade):** duplicação de **regra** é problema; duas linhas parecidas, não. Prefira duplicar a abstrair cedo demais.
- [ ] **KISS:** a solução mais simples que resolve. Função longa demais (> ~40 linhas) ou aninhamento profundo → separar.
- [ ] **Responsabilidade única:** cada função/arquivo faz uma coisa descritível em uma frase.
- [ ] Nomes revelam intenção (`calcular_total_com_desconto`, não `calc2`).
- [ ] Sem número ou texto "mágico" repetido: constante com nome.

### 2.6. Convenções profissionais

**Python / FastAPI**
- [ ] Tipos nas assinaturas; `Optional`/`| None` explícito; `Decimal` para dinheiro.
- [ ] `logging` em vez de `print`; log sem dado sensível.
- [ ] Docstring curta em PT-BR nas funções públicas; comentário explica o **porquê**.
- [ ] Sem `except Exception: pass`; erro de negócio com `HTTPException` e mensagem útil.
- [ ] Sem import dinâmico/`eval` (quebra o PyArmor/PyInstaller).

**Vue / TypeScript**
- [ ] `<script setup lang="ts">`, props e emits tipados; sem `any` sem justificativa.
- [ ] Sem lógica de negócio em `.vue`; sem chamada HTTP fora de `services/`.
- [ ] `v-for` com `:key` estável; `watch` com limpeza quando preciso; sem efeito colateral no `computed`.
- [ ] Estilo por tokens/`Base*`; sem cor ou medida solta.
- [ ] Estados de **carregando, vazio e erro** tratados.
- [ ] Tipos derivados dos schemas Zod (`z.infer`), sem duplicar interface à mão.

**Geral**
- [ ] **Comentários para iniciante** (`AGENT.md` §7): código novo explica o que faz e por quê, em PT-BR simples.
- [ ] Sem código morto, `console.log`/`print` de depuração, `TODO` sem dono, arquivo temporário esquecido (`tmp_*.db`, `nota.txt`).

### 2.7. Testes

- [ ] Cada caso da spec tem teste; o teste falharia sem o código novo.
- [ ] Teste de permissão e de isolamento por empresa nos recursos novos.
- [ ] Sem `skip`/`xfail` para "passar"; sem teste dependendo de ordem, relógio real ou rede.
- [ ] Valores monetários conferidos com valor exato.

## 3. Formato da saída

```markdown
## Revisão — <escopo> (<spec>)

**Veredito:** ✅ aprovado | ⚠️ aprovado com ressalvas | ❌ mudanças necessárias

### 🔴 Bloqueantes
1. `backend-fastapi/app/db/crud/cliente/cadastro.py:42` — `buscar_cliente` busca só por `id`.
   **Problema:** um usuário da empresa A lê um cliente da empresa B informando o `id` na URL (vazamento entre empresas).
   **Correção:** filtrar também por `empresa_id`:
   ```python
   # só devolve o cliente se ele pertencer à empresa do usuário logado
   db.query(Cliente).filter(Cliente.id == id, Cliente.empresa_id == empresa_id).first()
   ```

### 🟠 Importantes
...
### 🟡 Sugestões
...
### ❔ Perguntas
...

**Verificações executadas:** `python -m pytest test/` (48 passed), `npx vue-tsc --noEmit` (ok)
```

Seções vazias são omitidas. Se não houver achados, diga isso e liste o que foi verificado.

## 4. Depois da revisão

- Corrija os bloqueantes e importantes (ou peça ao usuário para decidir sobre os que exigem escolha).
- Revise de novo **só o diff das correções**, não o diff inteiro, rodando os testes dos arquivos corrigidos. A suíte completa roda uma vez, ao fim das correções.
- Achado recorrente entre sessões → candidato a aprendizado (`@/rules/session-learnings.md`) ou a regra nova (proponha ao usuário).
