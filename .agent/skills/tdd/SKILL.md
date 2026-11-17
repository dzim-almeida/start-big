---
name: tdd
description: Desenvolvimento guiado por testes (red-green-refactor) no StartBig, com pytest + SQLite em memória no backend e Vitest + @vue/test-utils no frontend. Transforma a tabela "Casos de teste" da spec em testes que falham antes do código. Use para qualquer código novo ou mudança de comportamento.
---

# Skill `tdd` — Red → Green → Refactor

> Caminhos com `@/` são relativos a `.agent/`.

## Princípio

Nenhuma linha de código de produção sem um teste falhando que a exija. As specs já trazem uma tabela **"Casos de teste"**: ela é o backlog de testes. Cada linha vira pelo menos um teste.

**Red → Green → Refactor** em português claro: (1) escreva um teste e veja ele **falhar**; (2) escreva o mínimo de código para ele **passar**; (3) **arrume** o código sem quebrar o teste.

---

## 1. Ciclo

1. **Listar** os casos da spec ativa (tabela "Casos de teste" + "Critérios de aceite" que sejam testáveis). Escolha o próximo caso: o mais simples que ainda não passa. Sem spec (trilha leve): o caso é o comportamento que o usuário pediu.
2. **Red** — escreva **um** teste para esse caso. Rode e **confirme que falha pelo motivo certo** (asserção, não erro de import ou de sintaxe). Teste que passa de primeira é suspeito: revise.
   - **Erro de coleta ou de import não conta como Red.** Se o teste não chega a rodar porque o símbolo ainda não existe, crie antes o **esqueleto mínimo**: assinaturas e classes vazias, sem comportamento. Aí rode de novo e veja a falha por asserção.
   - Não escreva a tabela inteira de casos de uma vez. Um teste por ciclo; no máximo, agrupe casos que exercitam **a mesma** linha de código (ex.: vários valores inválidos do mesmo campo, via `parametrize`).
3. **Green** — escreva o **mínimo** de código para o teste passar. Sem antecipar casos futuros.
4. **Refactor** — com tudo verde, melhore nomes, remova duplicação e ajuste às regras de arquitetura. Rode o arquivo de teste de novo.
5. Repita até esgotar a lista. Nos ciclos, rode só o teste do caso (ou o arquivo dele). No final, a verificação completa (§6), uma vez.

---

## 2. Backend (pytest)

- **Onde:** `backend-fastapi/test/`, espelhando o código: `test/api/` (chama a rota), `test/services/` (regra de negócio), `test/core/`, `test/db/`. Nome do arquivo `test_<assunto>.py`.
- **Banco:** SQLite **em memória** criado pelo `test/conftest.py` (cada teste começa limpo). **Nunca** aponte teste para o `start_big.db` da loja.
- **Como rodar** (na pasta `backend-fastapi/`, venv ativa):
  ```bash
  python -m pytest test/services/test_cliente.py            # um arquivo
  python -m pytest test/services/test_cliente.py -k "duplicado"  # um caso, por parte do nome
  python -m pytest test/                                    # tudo (só na §6)
  ```
  Use `python -m pytest` em vez de só `pytest`: o atalho da venv quebra quando a pasta do projeto é movida (`CLAUDE.md`).
- **Teste de rota:** use o `TestClient` do `conftest.py` e o usuário de teste que ele cria. Verifique **status**, **corpo** e o **efeito no banco**.
- **Teste de service:** chame a função direto com a sessão de teste (`db`) e um `empresa_id`. Sem HTTP.
- **Obrigatórios em todo domínio novo:** (a) um caso de **permissão** (sem a permissão → `403`); (b) um caso de **isolamento por empresa** (registro da empresa A → `404` para a empresa B).
- **Dados de teste:** funções/fixtures pequenas que criam só o necessário. Dados fictícios (nomes, CPF/CNPJ de teste); nunca copie dado de cliente real.

```python
# Exemplo comentado de teste de service
def test_criar_cliente_duplicado_levanta_erro(db, empresa_a):
    # Arrange (preparar): cria um cliente com um CPF
    criar_cliente(db, empresa_id=empresa_a.id, cpf="111.444.777-35")
    # Act + Assert (agir e conferir): criar outro com o mesmo CPF deve falhar
    with pytest.raises(ValueError, match="CPF já cadastrado"):  # espera o erro e confere a mensagem
        criar_cliente(db, empresa_id=empresa_a.id, cpf="111.444.777-35")
```

---

## 3. Frontend (Vitest)

- **Onde:** ao lado do código (`useAlgo.spec.ts`) ou em `__tests__/`. Extensão `*.spec.ts`.
- **Como rodar** (na pasta `frontend/`):
  ```bash
  npx vitest run src/modules/customers/composables/useCustomers.spec.ts   # um arquivo
  npx vitest related src/modules/customers/services/customerGet.service.ts --run  # testes ligados a um arquivo
  npm run test                                                               # tudo (só na §6)
  ```
- **O que testar:** `schemas` (entradas válidas e inválidas), `utils`, `services` (com o Axios simulado), composables (regra de tela) e componentes **com lógica**. Não teste CSS nem a biblioteca.
- **Simulando a API:** simule o módulo `@/api/axios` (`vi.mock`) ou use um adaptador de mock. Erro da API simulado precisa ter o formato real (`{ response: { status, data: { error, detail } } }`).
- **Fixture de lista ≠ fixture de detalhe:** monte a fixture de uma rota de lista a partir do schema de **lista**, não copiando o detalhe (o teste passa e a tela quebra).
- **Componente novo em `shared/components/ui/`:** acrescente uma story (`*.stories.ts`) e confira no `npm run storybook`.

---

## 4. O que é um bom teste aqui

- Testa **comportamento** (entrada → saída/efeito), não detalhe interno.
- Um motivo para falhar. Nome diz o caso: `test_<o_que>_<condicao>_<resultado>` (backend) ou `it('<faz o quê> quando <condição>')` (frontend).
- Independente: não depende de ordem nem de outro teste.
- Sem `sleep` nem relógio real: injete a data/hora ou simule o tempo.
- Dinheiro e quantidade: confira **o valor exato** (`Decimal("10.50")`), não "aproximadamente".

---

## 5. Armadilhas conhecidas

Esta lista cresce a partir de `@/docs/*/learn/` quando um aprendizado vira padrão (`@/rules/session-learnings.md` §4). Comece por estas:

### 5.1. Backend

- **Pasta do projeto movida:** `pytest`, `alembic`, `fastapi`... saem com exit 1 e **sem mensagem**. Use `python -m pytest`; se `python -m` funciona e o atalho não, recrie a venv (`CLAUDE.md`).
- **Teste que passa sozinho e falha em conjunto:** quase sempre dado vazando entre testes (variável global, cache em módulo). Cada teste cria o que precisa.
- **`commit` no service:** quem dá `commit` é o `_handle_db_transaction`. Teste de service chama a função e, se precisa ver o dado, usa `db.flush()`/`db.refresh()`.
- **SQLite não impõe tudo que outros bancos impõem:** chave estrangeira só vale com `PRAGMA foreign_keys=ON`. Se o teste depende disso, confira o `conftest.py`.
- **Arquivo `.db` de teste sobrando:** teste novo usa memória; se aparecer `*.db` na árvore, apague o que **você** criou e investigue.

### 5.2. Frontend

- **`vue-tsc` não faz parte do build.** Erro de tipo não quebra `npm run build`. Rode `npx vue-tsc --noEmit` (na `frontend/`) uma vez no fim.
- **Teste de componente não vê `blur`:** para disparar a validação de um campo, simule o uso real (`setValue` e depois `trigger('blur')`).
- **Router e `window.location`:** simule em vez de navegar de verdade.
- **vue-query:** crie um `QueryClient` novo por teste, com `retry: false` e `gcTime: 0`, senão o cache vaza entre testes.
- **Argumento opcional acrescentado a um service:** `toHaveBeenCalledWith` passa a falhar se o novo argumento vier `undefined`. Atualize a asserção.
- **Tauri:** `@tauri-apps/*` não existe em teste. Simule o módulo (`vi.mock('@tauri-apps/api/core')`).

---

## 6. Checklist de saída (verificação completa)

Rode **uma vez**, depois da **última** mudança de código. A revisão (`code-review`) reaproveita esta saída; só rode de novo se o código mudou depois.

**Backend** (em `backend-fastapi/`):
- [ ] `python -m pytest test/` — tudo passando
- [ ] Se mexeu em `models/`: `alembic check` sem pendência (skill `migration` §1.7)

**Frontend** (em `frontend/`):
- [ ] `npm run test` — tudo passando
- [ ] `npx vue-tsc --noEmit` — sem erro de tipo
- [ ] `npm run lint:check` — sem erro (use `npm run lint` só quando quiser o auto-fix, e confira o diff)
- [ ] Se mexeu em estilo: `npm run check:tokens`, `npm run check:paleta` e `npm run check:print-bw`

**Geral:**
- [ ] Todos os casos da tabela "Casos de teste" da spec têm teste correspondente
- [ ] Nenhum teste foi pulado (`skip`) ou removido para "ficar verde"
- [ ] Alterou o backend? Avisar o usuário sobre `npm run build:sidecar`
