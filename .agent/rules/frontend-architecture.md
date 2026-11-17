# Regra — Arquitetura do Frontend (por módulos)

**Status:** obrigatória · **Escopo:** `frontend/src/` · **Origem:** estrutura atual de `frontend/src/modules/` e `shared/`, e a seção "Architecture" do `CLAUDE.md`.

Se esta regra e uma spec divergirem, a spec ativa vence. Nesse caso, pare e pergunte se a regra deve ser atualizada.

---

## 1. Estrutura

```
frontend/src/
├── main.ts              # Composição: Pinia, vue-query, router
├── App.vue              # Casca da aplicação: RouterView e estados globais (carregando, sem conexão)
├── router/index.ts      # Cria o router e descobre sozinho todos os modules/**/routes.ts
├── api/                 # axios.ts (cliente + interceptors) e backendUrl.ts (onde está o backend)
├── core/                # Configuração central do app
├── shared/              # Transversal, sem regra de negócio de nenhum módulo
│   ├── components/      # ui/ (primitivos Base*), form/, layout/, commons/, print/, icons/...
│   ├── composables/     # Composables usados por mais de um módulo
│   ├── stores/          # Stores Pinia globais (auth, configurações, licença...)
│   ├── services/        # Chamadas HTTP usadas por mais de um módulo
│   ├── schemas/         # Schemas Zod compartilhados (ex.: cliente, usado em vendas e OS)
│   ├── types/ utils/ constants/ config/ theme/ assets/
└── modules/
    └── {módulo}/        # customers, sales, fiscal...
        ├── views/       # Páginas ligadas a rotas (*View.vue)
        ├── components/  # Componentes do módulo (modais em components/modal/)
        ├── composables/ # Orquestração; chamadas do vue-query em composables/request/
        ├── services/    # Chamadas HTTP do módulo (*.service.ts)
        ├── schemas/     # Zod: formulário e resposta da API (*.schema.ts)
        ├── types/       # Tipos do módulo (*.types.ts)
        ├── constants/   # Valores fixos (*.constants.ts)
        └── routes.ts    # Rotas do módulo (export default RouteRecordRaw[])
```

**Módulo grande** (ex.: `compras`, `financeiro`) pode ter **submódulos**, cada um com a mesma estrutura, e uma pasta `shared/` interna para o que só os submódulos daquele módulo dividem. A regra de dependência da §3 vale em cada nível.

**Pasta só nasce quando precisa.** Não crie `constants/` ou `types/` vazios "para ficar completo": crie ao ter o primeiro arquivo.

---

## 2. Responsabilidade estrita de cada camada

| Camada | Faz | **Não faz** |
|--------|-----|-------------|
| `views/*View.vue` | Monta a página: layout + componentes do módulo. Lê parâmetros de rota e repassa por props. | Lógica de formulário, chamada à API, regra de negócio, estilo "na mão" de inputs e botões |
| `components/*.vue` | Renderiza UI do módulo. Recebe props e emite eventos. Pode ter validação de formulário (VeeValidate + schema Zod) e estado visual local. | Chamar `service` direto, escrever em store, navegar (`router.push`), montar requisições |
| `composables/use*.ts` | Orquestra um caso de uso: chama service, usa vue-query (`useQuery`/`useMutation`), navega, traduz erro da API em aviso para o usuário. | Renderizar, mexer no DOM, conhecer detalhes do Axios |
| `composables/request/*` | Um arquivo por consulta (`*.queries.ts`) ou gravação (`*.mutate.ts`): envolve o service com vue-query e invalida cache. | Formatar dado para a tela (isso é do composable do caso de uso) |
| `shared/stores/*.store.ts` (Pinia) | Estado **de cliente** que várias telas compartilham (sessão, configuração, licença). | Guardar cache de dado do servidor (isso é do vue-query) |
| `services/*.service.ts` | Uma função por endpoint. Chama `@/api/axios`, **valida a resposta com Zod** e devolve dado tipado. | Guardar estado, navegar, mostrar toast, tratar erro de UI |
| `schemas/*.schema.ts` | Schemas Zod de formulário e de resposta da API, e os tipos derivados (`z.infer`). | Chamada HTTP, efeito colateral |
| `types/`, `constants/` | Tipos e valores fixos. | Código executável com efeito colateral |
| `routes.ts` | Rotas do módulo (`meta`, permissão exigida). | Lógica de tela |
| `api/axios.ts` | Instância Axios, token no cabeçalho, tratamento global de erro (rede, 401). | Importar regra de módulo |
| `shared/components/ui/` | Primitivos visuais `Base*` genéricos, sem conhecimento de domínio, usando os tokens do tema. | Texto de negócio fixo, chamada à API, store |
| `main.ts` | Único ponto que liga as peças globais. | Regra de negócio |

---

## 3. Regras de dependência (imports)

```
views → components / composables → services → schemas / types / constants → @/api
```

1. Cada camada só importa da **mesma linha ou de baixo**. `service` nunca importa `composable`; `schema` nunca importa `service`.
2. `shared/` **nunca** importa de `modules/`. Se o `shared` precisa de algo de um módulo, aquilo deveria estar no `shared`.
3. **Módulo não importa de outro módulo.** Se dois módulos usam o mesmo schema, componente ou função, promova para `shared/` (como `shared/schemas/customer/`). Exceção aceita: tipo puro (`import type`) quando promover não compensa, registrado na spec.
4. Use o alias `@/` para imports entre pastas. Dentro do mesmo módulo, caminho relativo curto (`../constants/...`) é aceito.
5. Componente do `shared/components/ui` não conhece `auth.store`, `router` nem `axios`.

---

## 4. Convenções

- **Nomes de arquivo:** componente em `PascalCase.vue`; composable `useAlgo.ts`; service `entidadeAcao.service.ts` (ex.: `customerGet.service.ts`); schema `entidade.schema.ts`; store `nome.store.ts`; arquivos de teste `*.spec.ts` ao lado do código ou em `__tests__/`.
- **Componente `Base*`:** antes de escrever um `<input>`, `<select>` ou `<button>` na mão, procure em `shared/components/ui/` (`BaseInput`, `BaseSelect`, `BaseButton`, `BaseMoneyInput`...). Faltou variação? Proponha ajustar o `Base*` em vez de estilizar por fora.
- **Vue:** `<script setup lang="ts">`. Props tipadas com `defineProps<{...}>()`, eventos com `defineEmits`.
- **Estilo:** Tailwind 4 com **tokens do tema** (`shared/theme/`, `shared/assets/styles/`). Cor ou espaçamento "solto" (hex, `px` mágico) é achado de revisão. Os scripts `check:tokens`, `check:paleta` e `check:print-bw` barram o build quando um token é usado sem existir: rode-os depois de mexer em estilo.
- **Formulário:** VeeValidate + schema Zod. A mensagem de validação vem do schema, em PT-BR.
- **Dinheiro e data:** nunca calcule em `number` solto o que é dinheiro sem usar o util do projeto (`shared/utils`). Quantia vem do backend como número ou texto decimal; formate só na hora de exibir.
- **Tauri:** chamada a recurso nativo (arquivo, diálogo, keyring, rede) fica atrás de uma função em `shared/` ou no `service` do módulo, nunca espalhada nos componentes. O código tem de continuar abrindo no **navegador** (porta 1420) sem quebrar: proteja com a checagem de ambiente que o projeto já usa.
- **Teste:** Vitest para composables, services, schemas e utils; componente com `@vue/test-utils` quando tiver lógica. Componente novo do `shared/components/ui/` ganha uma story (`*.stories.ts`).

---

## 5. Checklist rápido antes de criar um arquivo

1. É da **tela** (view), de um **pedaço da tela** (component), de **orquestração** (composable), de **chamada HTTP** (service), de **forma do dado** (schema/type) ou de **valor fixo** (constants)? A tabela da §2 dá o lugar.
2. Outro módulo vai usar? Então é `shared/`.
3. Já existe um `Base*` ou util que resolve? Reaproveite.
4. O import que estou escrevendo respeita a §3?
5. Tem teste para o comportamento novo (skill `tdd`)?
