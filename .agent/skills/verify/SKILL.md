---
name: verify
description: Verificação ponta a ponta local do StartBig. Sobe o backend de desenvolvimento (porta 8000) e o frontend (porta 1420), confere as portas, prepara uma conta de teste em banco descartável, percorre os fluxos no navegador ou na janela Tauri e registra a evidência no formato do relatório. Use quando um critério de aceite pedir verificação no navegador, ao fim de uma série de specs ou quando o usuário pedir.
---

# Skill `verify` — verificação ponta a ponta

> Caminhos com `@/` são relativos a `.agent/`. Comandos rodam na raiz do repositório, salvo indicação.

## 0. Quando usar

| Situação | Verificação |
|----------|-------------|
| Critério de aceite da spec pede o navegador (login, guardas de rota, permissões por cargo, formulários reais, impressão) | Ao concluir a spec |
| Série de specs | **Uma vez**, ao concluir a última spec, com o roteiro da verificação final da série. Spec do meio só roda antes se tiver critério de navegador; os outros fluxos dela entram nesse roteiro |
| Pedido do usuário | Quando ele pedir |
| Spec com tela, sem critério de navegador, fora de série | Não rode; os testes cobrem. Ofereça a verificação no resumo final |
| Trilha leve (`@/AGENT.md` §3.2) | Não rode, salvo pedido |

- O comportamento que só aparece com frontend e backend **juntos** é o motivo desta skill.
- **Não substitui** os testes da skill `tdd`. Se a verificação achar um bug, ele ganha um teste que o reproduz.
- Mudança só de backend, sem tela: verifique pela API (`curl` ou o Swagger em `http://localhost:8000/docs`), sem navegador.
- Telas novas: a comparação visual com o design é da skill `design` §3. Esta skill confere **comportamento**.

## 1. Preparar o ambiente

### 1.1. Conferir as portas antes de subir

Dev e app instalado usam faixas **separadas** (`CLAUDE.md`): **8000** para dev e **8080–8083** para a loja. Se o login "parece quebrado", **cheque a porta antes do banco**.

```powershell
# Windows (PowerShell): quem está escutando nas portas do projeto?
Get-NetTCPConnection -LocalPort 8000,1420,8080 -State Listen -ErrorAction SilentlyContinue
```
```bash
# Linux / Mac
lsof -i :8000 -i :1420 -i :8080 | grep LISTEN
```

- Porta ocupada por **algo seu** de uma sessão anterior: reaproveite se for o mesmo serviço.
- Porta ocupada por **outro programa** (ou pela loja na 8080): não derrube; avise o usuário e use outra porta só se o `CLAUDE.md` permitir.

### 1.2. Subir a stack

**Backend de dev** (na pasta `backend-fastapi/`, venv ativa) — sempre contra um **banco descartável**, nunca o da loja:

```bash
export DATABASE_URL="sqlite:///./tmp_verify.db"      # PowerShell: $env:DATABASE_URL = "sqlite:///./tmp_verify.db"
fastapi dev app/main.py                              # sobe na porta 8000, recarrega ao editar
```

Confira: `http://localhost:8000/docs` abre o Swagger.

**Frontend** (na pasta `frontend/`):

```bash
npm run dev          # só o Vite, porta 1420. NÃO sobe o backend.
```

- **Navegador:** abra `http://localhost:1420`. O front procura o backend na **8000** (`api/backendUrl.ts`).
- **Janela Tauri:** `npm run tauri dev` também usa a **8000** (chumbada em modo debug). Só use se o critério pedir recurso nativo (impressão, rede, keyring).
- Backend mexido? Em dev ele recarrega sozinho; o **sidecar** (`npm run build:sidecar`) só importa para o instalador.

### 1.3. Contas de teste

- O banco descartável nasce vazio: crie empresa, usuário e dados **pelo próprio app** (onboarding) ou por script de seed do projeto, **com dados fictícios** (nomes, CPF/CNPJ de teste, e-mail `@example.com`).
- Para testar permissões, crie **um usuário por cargo** relevante ao fluxo (ex.: administrador e vendedor).
- **Nunca** registre senha no relatório nem em docs. **Nunca** use conta ou dado de cliente real.

## 2. Percorrer os fluxos

1. **Monte o roteiro antes de começar**, como tabela `# · Fluxo · Resultado esperado`, a partir dos critérios de aceite da spec e, numa série, da verificação final do roteiro (`@/specs/{módulo}/ROTEIRO-IMPLEMENTACAO.md`).
2. **Ferramentas do navegador do app:** prefira ler texto e estado da página a tirar screenshot; use clique e digitação para agir; tire screenshot só como evidência final de cada fluxo visual.
3. **A cada fluxo**, confira o console do navegador (erros) e as requisições de rede (4xx/5xx inesperados, chamadas repetidas, payload com dado que não deveria estar lá).
4. **Sessões e permissões:**
   - Login errado, login certo, sair e entrar de novo.
   - Rota proibida: abra pelo endereço como um cargo sem permissão e confira o bloqueio.
   - Token expirado (`401`): o app deve voltar ao login com aviso "Sessão Expirada".
5. **Backend fora do ar:** pare o backend e confira que o app mostra o estado de "sem conexão" em vez de tela em branco.
6. **Campos com máscara** (CPF, telefone, dinheiro): ao digitar num campo já preenchido, o texto pode **anexar**; limpe o campo antes de digitar.

### 2.1. Limite de tentativas (`@/AGENT.md` §7)

- Screenshot em branco ou painel que não desenha: leia o estado pelo texto da página e siga. Não repita o screenshot.
- Uma ação (clique, navegação, subir um serviço) falhou duas vezes com o mesmo sintoma: pare. Se for ambiente (painel, porta, venv, janela Tauri), marque o fluxo como "Não verificado" no relatório, com o motivo, e passe para o próximo.
- Não espere em laço por um serviço que não sobe: leia o log uma vez e reporte.

## 3. Achou um problema

- **Bug no escopo da spec ativa:** escreva primeiro o teste que o reproduz (skill `tdd`). Se o teste de componente não reproduz, simule o uso real. Depois corrija e verifique de novo no navegador.
- **Bug em outra spec ou módulo:** é divergência (skill `doc` §5). Pare, descreva o fluxo, o esperado e o observado, e pergunte. Aprovada a correção, ela entra como nota de revisão na spec dona do código.
- **Não "conserte" o roteiro** para o fluxo passar. Se o esperado estava errado, isso é decisão do usuário.

## 4. Encerrar

- Pare só o que **você** subiu (backend de dev e Vite).
- Apague o banco descartável que você criou (`tmp_verify.db`) e limpe a variável `DATABASE_URL`.
- Nunca mexa no `start_big.db` da loja nem em `%LOCALAPPDATA%\StartBigERP\` (`AGENT.md` §6.3).

## 5. Relatório

```markdown
### Verificação ponta a ponta — <spec ou série>
- Ambiente: navegador (1420 → 8000) | janela Tauri (dev), commit `<hash>`
- Contas: <cargos usados> (dados fictícios; senhas não registradas; banco descartável apagado)

| # | Fluxo | Esperado | Resultado | Evidência |
|---|-------|----------|-----------|-----------|
| 1 | Administrador abre Clientes e cria um cliente PF | Cliente aparece na lista, toast de sucesso | ✅ | texto lido da página |

- Console e rede: sem erros | <lista>
- Achados: <bug, onde, teste que o reproduz, status>
- Não verificado: <fluxo> — <motivo> (ex.: janela Tauri não abriu)
```

Fluxo **não verificado** que é critério de aceite mantém a spec em `active/` (skill `doc` §6). Diga o motivo e o que falta.
