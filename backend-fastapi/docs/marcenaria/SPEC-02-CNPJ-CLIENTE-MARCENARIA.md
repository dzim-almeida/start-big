# Spec 02 — Consulta de CNPJ no Cadastro de Cliente

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                       |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado                 |
| Dependências | Spec 00                                                               |
| Bloqueia     | Spec 06B (o orçamento usa o modal de cliente)                         |
| Referência   | SPEC-00: O6, PR1, PR6 · consulta existente em `modules/enterprise/composables/useConsultaCNPJ.ts` |

> Melhoria **geral** do cadastro de cliente, pedida para entrar no início da marcenaria (O6). Vale para **todos os segmentos**: é a mudança visível pretendida, não uma regressão. O que não pode mudar é o resto do formulário de cliente e o cadastro de empresa.

---

## 1. Objetivo

Quando o usuário digita um CNPJ completo e válido no cadastro de cliente **Pessoa Jurídica**, o sistema:

1. confere se **já existe cliente** com esse CNPJ (e avisa, em vez de deixar o erro aparecer só ao salvar);
2. consulta a Receita (BrasilAPI) e **preenche os campos vazios**: razão social, nome fantasia, e-mail, telefone e endereço.

Sem internet, o cadastro continua funcionando à mão, com um aviso claro.

## 2. Escopo

**Dentro do escopo**
- Levar a função de consulta (`buscarDadosCNPJ`) do módulo de empresa para `shared`, com erro tipado e tempo limite.
- Composable `useConsultaCnpjCliente` (gatilho, verificação de duplicidade, preenchimento, estado).
- Botão "Consultar" e mensagem de estado ao lado do campo CNPJ, em `CompanyDataSection.vue`.
- Testes (vitest) e roteiro manual.

**Fora do escopo**
- Backend: nenhuma mudança (a consulta é feita no frontend, como no cadastro de empresa; a duplicidade usa `GET /clientes/?buscar=` que já existe).
- Cadastro de **empresa**: continua exatamente igual (mesma função, mesma mensagem).
- Cliente Pessoa Física (CPF não tem consulta pública).
- **CNPJ alfanumérico** no cadastro de cliente (ver §9).
- Inscrição estadual e regime tributário (a BrasilAPI não devolve IE; o regime fica para outra spec, se pedirem).
- Mudar o `BaseInput` (componente compartilhado por todo o sistema).

---

## 3. Arquivos afetados

```
frontend/src/
├── shared/services/
│   ├── consultaCnpj.service.ts                  # CRIAR — função movida + erro tipado + tempo limite
│   └── __tests__/consultaCnpj.service.spec.ts   # CRIAR
├── modules/enterprise/composables/
│   └── useConsultaCNPJ.ts                       # ALTERAR — vira só re-exportação (empresa não muda)
└── modules/customers/
    ├── composables/modal/
    │   ├── form/useConsultaCnpjCliente.ts       # CRIAR — regra da consulta no cliente
    │   ├── form/__tests__/useConsultaCnpjCliente.spec.ts  # CRIAR
    │   ├── context/useCustomerForm.context.ts   # ALTERAR — instancia e expõe a consulta
    │   └── types/context.type.ts                # ALTERAR — tipos expostos no contexto
    ├── components/modal/form/
    │   └── CompanyDataSection.vue               # ALTERAR — botão e mensagem ao lado do CNPJ
    └── services/customerGet.service.ts          # CONFERIR — getAllCustomers({ search })
```

**Responsabilidade de cada camada:**

| Arquivo | Faz | Não faz |
|---------|-----|---------|
| `consultaCnpj.service.ts` | Chama a BrasilAPI, traduz a resposta, classifica o erro | Saber de formulário |
| `useConsultaCnpjCliente.ts` | Decide quando consultar, verifica duplicidade, preenche só o vazio, guarda o estado | Renderizar |
| `useCustomerForm.context.ts` | Liga a consulta aos campos do formulário PJ | Regra da consulta |
| `CompanyDataSection.vue` | Mostra botão, carregamento e mensagem | Chamar API |

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | `buscarDadosCNPJ` vai para `shared/services/consultaCnpj.service.ts`. O arquivo antigo da empresa vira **re-exportação** | O cliente passa a usar a mesma função sem o módulo de clientes importar do módulo de empresa. A empresa não muda nenhuma linha de comportamento |
| D2 | Erro **tipado**: `NAO_ENCONTRADO` (404) × `INDISPONIVEL` (sem internet, tempo esgotado, 429, 5xx) | Hoje qualquer falha diz "CNPJ não encontrado na Receita Federal", inclusive sem internet. Isso faz o usuário achar que digitou errado |
| D3 | Tempo limite de **8 s** (`AbortController`) | Sem rede, o `fetch` pode ficar pendurado e o campo fica "consultando" para sempre |
| D4 | Consulta **automática** quando o CNPJ chega a 14 dígitos **e** o dígito verificador é válido. Botão **"Consultar"** para repetir à mão | CNPJ inválido não gasta chamada; o botão resolve "a internet voltou" e "quero consultar de novo" |
| D5 | Em **edição**, a consulta automática só roda se o CNPJ for **diferente do salvo** | Abrir um cliente existente não pode disparar consulta nem toast (mesma regra do cadastro de empresa, `cnpjSalvo`) |
| D6 | Preenche **só campos vazios**. Nunca sobrescreve o que o usuário digitou ou o que já estava salvo | Diferente da empresa (que sobrescreve razão social): no cliente, o atendente costuma corrigir o nome ("Studio Renascer" em vez da razão social longa). Sobrescrever apagaria a correção sem aviso |
| D7 | Endereço: preenche o **primeiro endereço só se ele estiver todo vazio**. Se já tiver qualquer campo, não mexe em endereço | Misturar a rua da Receita com o número digitado pelo usuário geraria um endereço errado |
| D8 | Antes da Receita, verifica **duplicidade** com `GET /clientes/?buscar=<dígitos>`, comparando o CNPJ exato e ignorando o próprio cliente em edição. Se existir, mostra o aviso e **não** consulta a Receita | Hoje o usuário preenche tudo e só descobre o `409` ao salvar |
| D9 | Duplicidade e falha da consulta **não bloqueiam** o salvar. São avisos, não erros de validação | Sem internet, o cadastro manual tem que continuar possível. A duplicidade real continua barrada pelo backend (`409`) |
| D10 | Resposta atrasada é **descartada** se o CNPJ do campo mudou enquanto a consulta estava em andamento | Evita preencher o cliente B com os dados do CNPJ A |
| D11 | Sucesso em **toast** (padrão do sistema); avisos e falhas em **texto fixo abaixo do campo** | Toast some em 3 s; o aviso "já existe cliente" precisa ficar visível enquanto o usuário decide |
| D12 | Nenhuma mudança no `BaseInput`. Botão e mensagem ficam ao lado/abaixo do campo, dentro da seção | `BaseInput` é usado no sistema inteiro (PR1) |

---

## 5. Contratos consumidos

### 5.1. BrasilAPI — `GET https://brasilapi.com.br/api/cnpj/v1/{cnpj}`

Mesma chamada do cadastro de empresa. A CSP do Tauri já permite (`connect-src *`).

| Resposta | Classificação |
|----------|---------------|
| `200` | Sucesso |
| `404` | `NAO_ENCONTRADO` |
| `429`, `5xx`, erro de rede, tempo esgotado | `INDISPONIVEL` |

### 5.2. Duplicidade — `GET /api/v1/clientes/?buscar=<14 dígitos>`

Endpoint existente (busca por nome, CPF, razão social, **CNPJ** ou nome fantasia). Como a busca é por termo, o resultado pode trazer outros clientes; a comparação é feita pelo **CNPJ exato**, só com dígitos.

---

## 6. Especificação técnica

### 6.1. Serviço — `shared/services/consultaCnpj.service.ts`

Copiar `CNPJApiData`, `formatCNAECode`, `mapNaturezaJuridica` e o mapeamento da resposta **sem mudança**. Acrescentar:

```ts
/** Por que a consulta falhou (Spec 02, D2). */
export type MotivoFalhaCnpj = 'NAO_ENCONTRADO' | 'INDISPONIVEL';

export class ConsultaCnpjErro extends Error {
  motivo: MotivoFalhaCnpj;                      // declarado no corpo (o tsconfig não aceita parameter properties)
  constructor(motivo: MotivoFalhaCnpj) {
    // A mensagem antiga continua igual: o cadastro de empresa exibe só o toast dele.
    super('CNPJ não encontrado na Receita Federal');
    this.name = 'ConsultaCnpjErro';
    this.motivo = motivo;
  }
}

const TEMPO_LIMITE_MS = 8_000;                  // D3

export async function buscarDadosCNPJ(cnpj: string): Promise<CNPJApiData> {
  const digits = cnpj.replace(/\D/g, '');       // a API só aceita os 14 dígitos
  const controle = new AbortController();       // permite cancelar o fetch
  const timer = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS);

  let resp: Response;
  try {
    resp = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${digits}`, { signal: controle.signal });
  } catch {
    // Sem internet ou tempo esgotado: o fetch rejeita antes de existir resposta.
    throw new ConsultaCnpjErro('INDISPONIVEL');
  } finally {
    clearTimeout(timer);                        // não deixa o timer vivo depois da resposta
  }

  if (resp.status === 404) throw new ConsultaCnpjErro('NAO_ENCONTRADO');
  if (!resp.ok) throw new ConsultaCnpjErro('INDISPONIVEL');   // 429, 5xx...

  const d = await resp.json();
  // ... mapeamento idêntico ao de hoje ...
}
```

### 6.2. Re-exportação — `modules/enterprise/composables/useConsultaCNPJ.ts`

```ts
// A consulta mora em shared desde a Spec 02. Este arquivo existe para que o
// cadastro de empresa continue importando do mesmo lugar, sem mudança.
export { buscarDadosCNPJ, type CNPJApiData } from '@/shared/services/consultaCnpj.service';
```

O `catch` do cadastro de empresa pega qualquer erro e mostra "CNPJ não encontrado na Receita Federal." como hoje. **Não alterar** `useEmpresaFormProvider.ts`.

### 6.3. Composable — `customers/composables/modal/form/useConsultaCnpjCliente.ts`

```ts
import { computed, ref, watch, type Ref } from 'vue';
import { cnpj as validadorCnpj } from 'cpf-cnpj-validator';

import { buscarDadosCNPJ, ConsultaCnpjErro } from '@/shared/services/consultaCnpj.service';
import { useToast } from '@/shared/composables/useToast';
import { getAllCustomers } from '../../../services/customerGet.service';

/** O que aparece abaixo do campo CNPJ. */
export type EstadoConsultaCnpj =
  | { tipo: 'ocioso' }
  | { tipo: 'consultando' }
  | { tipo: 'duplicado'; nomeCliente: string }
  | { tipo: 'nao_encontrado' }
  | { tipo: 'indisponivel' };

interface CamposPJ {
  cnpj: Ref<string | undefined>;
  razao_social: Ref<string | undefined>;
  nome_fantasia: Ref<string | undefined>;
  email: Ref<string | undefined>;
  telefone: Ref<string | undefined>;
  /** Lê e grava o primeiro endereço (o formulário usa useFieldArray). */
  primeiroEndereco: () => Record<string, string> | undefined;
  gravarPrimeiroEndereco: (endereco: Record<string, string>) => void;
}

export function useConsultaCnpjCliente(
  campos: CamposPJ,
  opcoes: {
    clienteId: Ref<number | null>;        // null = cadastro novo
    cnpjSalvo: Ref<string | null>;        // dígitos do CNPJ já gravado (edição)
    desabilitado: Ref<boolean>;           // modo visualização
  },
) {
  const toast = useToast();
  const estado = ref<EstadoConsultaCnpj>({ tipo: 'ocioso' });
  const digitos = computed(() => (campos.cnpj.value ?? '').replace(/\D/g, ''));

  /** Preenche um campo só se estiver vazio (D6). Devolve true se preencheu. */
  function preencherSeVazio(campo: Ref<string | undefined>, valor: string): boolean {
    if ((campo.value ?? '').trim() || !valor) return false;
    campo.value = valor;
    return true;
  }

  async function consultar(): Promise<void> {
    const alvo = digitos.value;                          // CNPJ desta consulta (D10)
    if (alvo.length !== 14 || !validadorCnpj.isValid(alvo)) return;   // D4
    estado.value = { tipo: 'consultando' };

    // 1) Duplicidade (D8): só o CNPJ exato conta, e nunca o próprio cliente.
    const pagina = await getAllCustomers({ search: alvo, limit: 5 }).catch(() => null);
    const outro = pagina?.items.find(
      (c) => 'cnpj' in c && c.cnpj === alvo && c.id !== opcoes.clienteId.value,
    );
    if (digitos.value !== alvo) return;                  // o usuário mudou o CNPJ: descarta (D10)
    if (outro) {
      estado.value = { tipo: 'duplicado', nomeCliente: outro.razao_social ?? '' };
      return;                                            // não consulta a Receita
    }

    // 2) Receita.
    try {
      const dados = await buscarDadosCNPJ(alvo);
      if (digitos.value !== alvo) return;                // resposta atrasada (D10)
      let preenchidos = 0;
      if (preencherSeVazio(campos.razao_social, dados.razao_social)) preenchidos++;
      if (preencherSeVazio(campos.nome_fantasia, dados.nome_fantasia)) preenchidos++;
      if (preencherSeVazio(campos.email, dados.email)) preenchidos++;
      if (preencherSeVazio(campos.telefone, formatarTelefone(dados.telefone))) preenchidos++;
      // Endereço só se o primeiro estiver TODO vazio (D7).
      const end = campos.primeiroEndereco();
      if (end && Object.values(end).every((v) => !String(v ?? '').trim())) {
        campos.gravarPrimeiroEndereco({
          cep: formatarCep(dados.cep), logradouro: dados.logradouro, numero: dados.numero,
          complemento: dados.complemento, bairro: dados.bairro, cidade: dados.cidade, estado: dados.estado,
        });
        preenchidos++;
      }
      estado.value = { tipo: 'ocioso' };
      if (preenchidos > 0) toast.success('Dados da Receita Federal preenchidos nos campos vazios.');
      else toast.info('Os campos já estavam preenchidos; nada foi alterado.');
    } catch (erro) {
      if (digitos.value !== alvo) return;
      const motivo = erro instanceof ConsultaCnpjErro ? erro.motivo : 'INDISPONIVEL';
      estado.value = { tipo: motivo === 'NAO_ENCONTRADO' ? 'nao_encontrado' : 'indisponivel' };
    }
  }

  // Gatilho automático (D4, D5): CNPJ completo, diferente do salvo, fora do modo visualização.
  watch(digitos, (atual) => {
    estado.value = { tipo: 'ocioso' };                   // apagou/mudou o CNPJ: some o aviso antigo
    if (opcoes.desabilitado.value || atual.length !== 14) return;
    if (atual === opcoes.cnpjSalvo.value) return;
    void consultar();
  });

  return { estado, consultar };
}
```

`formatarTelefone` e `formatarCep` = `formatTelefone` e `formatCEP` de `@/shared/utils/document.utils` (os mesmos que o cadastro de empresa usa). Nada a mover.

**Conferido:** `getAllCustomers` devolve `{ items: CustomerUnion[] }`; `toast.info` existe em `useToast`. **Conferir na implementação:** se o `cnpj` que volta na lista vem só com dígitos (o backend grava 14 dígitos; o schema de leitura pode formatar). Ajustar a comparação sem mudar as regras D4–D10.

### 6.4. Contexto do formulário — `useCustomerForm.context.ts`

- Instanciar `useConsultaCnpjCliente` com os campos do formulário **PJ**.
- `clienteId` e `cnpjSalvo` vêm de `selectedCustomer` (null em `isCreateMode`).
- `desabilitado` segue a mesma regra que hoje desabilita a `CompanyDataSection`.
- Expor `consultaCnpj: { estado, consultar }` no contexto e no tipo (`context.type.ts`).
- Ao fechar o modal (o `watch(isOpen)` que já reseta os formulários), o estado volta a `ocioso`.

### 6.5. Tela — `CompanyDataSection.vue`

Ao lado do campo CNPJ, um botão de ícone **"Consultar"** (lupa), com `aria-label="Consultar CNPJ na Receita"`, desabilitado quando o CNPJ não está completo e válido ou quando já está consultando. Abaixo do campo, uma linha de texto (fora do `error` do `BaseInput`, para não parecer erro de validação):

| Estado | Texto abaixo do campo | Aparência |
|--------|-----------------------|-----------|
| `ocioso` | — | — |
| `consultando` | "Consultando a Receita Federal…" | Cinza, com spinner no botão |
| `duplicado` | "Já existe um cliente com este CNPJ: **{nome}**. Salvar vai dar erro de duplicidade." | Âmbar |
| `nao_encontrado` | "CNPJ não encontrado na Receita. Confira os números ou preencha manualmente." | Âmbar |
| `indisponivel` | "Não foi possível consultar a Receita agora. Preencha manualmente ou tente de novo." + botão "Tentar de novo" | Cinza |

- O texto fica numa região `aria-live="polite"` para ser anunciado por leitores de tela.
- Os campos **não** ficam bloqueados durante a consulta: o usuário pode continuar digitando. Quem já foi digitado não é sobrescrito (D6).
- Erro de validação do CNPJ (dígito verificador errado) continua aparecendo como hoje, pelo schema, no `error` do campo.

---

## 7. Prova de não regressão (⚠️ PR1)

1. **Cadastro de empresa idêntico:** digitar um CNPJ válido no cadastro de empresa antes e depois. Mesmos campos preenchidos (inclusive a razão social sobrescrita) e mesma mensagem de erro.
2. **Cliente PF idêntico:** nenhuma mudança visual nem de comportamento.
3. **Cliente PJ sem digitar CNPJ:** formulário igual ao de hoje (o botão aparece desabilitado; nenhuma mensagem).
4. `npm run test` e `npx vue-tsc --noEmit` sem erros.

## 8. Mudança visível pretendida (todos os segmentos)

Esta spec **muda de propósito** o cadastro de cliente PJ em informática, oficina, serigrafia e marcenaria: botão "Consultar", preenchimento automático e avisos. É a melhoria aprovada em O6. Vale avisar as lojas na atualização.

## 9. Limitações conhecidas

- **CNPJ alfanumérico:** desde julho de 2026 a Receita emite CNPJ com letras. O cadastro de cliente hoje **não aceita** esse formato em nenhuma camada: a máscara é só de números, o validador (`cpf-cnpj-validator`) é numérico, e a coluna `cliente.cnpj` tem 14 dígitos. Esta spec mantém a consulta só para CNPJ numérico. Aceitar o alfanumérico é uma mudança maior (frontend, backend e fiscal), registrada como **PEND-001** em `docs/pendencias-sistema.md`.
- **Dependência externa:** a BrasilAPI é gratuita e tem limite de uso (`429`). Em uso normal de uma loja não deve aparecer; se aparecer, cai em `INDISPONIVEL` e o cadastro segue à mão.
- **Telefone:** a BrasilAPI devolve um telefone sem dizer se é fixo ou celular. Vai sempre para o campo **Telefone**, nunca para **Celular**.

---

## 10. Critérios de aceite

- [ ] Cliente PJ novo: digitar um CNPJ válido preenche razão social, nome fantasia, e-mail, telefone e endereço (os vazios).
- [ ] Campo já preenchido pelo usuário nunca é sobrescrito.
- [ ] Endereço só é preenchido se o primeiro endereço estiver todo vazio.
- [ ] CNPJ com dígito verificador inválido não dispara consulta.
- [ ] Abrir um cliente existente não dispara consulta nem toast; trocar o CNPJ dele dispara.
- [ ] CNPJ de outro cliente cadastrado mostra o aviso de duplicidade com o nome, e a Receita não é consultada.
- [ ] O próprio cliente em edição não aparece como duplicado.
- [ ] Sem internet, aparece "Não foi possível consultar a Receita agora…" em até 8 s, e o cadastro pode ser salvo à mão.
- [ ] CNPJ inexistente mostra "CNPJ não encontrado na Receita…" (e não a mensagem de sem internet).
- [ ] Trocar o CNPJ durante uma consulta não preenche o formulário com dados do CNPJ anterior.
- [ ] O cadastro de empresa e o cliente PF se comportam exatamente como antes.
- [ ] `BaseInput` não foi alterado.
- [ ] Código novo comentado (PR6).

## 11. Casos de teste

### Serviço — `shared/services/__tests__/consultaCnpj.service.spec.ts` (`fetch` substituído por mock)

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Resposta `200` da BrasilAPI | Mesmo objeto que a função antiga devolvia (comparar com a resposta de exemplo) |
| 02 | `404` | `ConsultaCnpjErro` com `motivo = 'NAO_ENCONTRADO'` |
| 03 | `429` e `503` | `motivo = 'INDISPONIVEL'` |
| 04 | `fetch` rejeita (sem rede) | `motivo = 'INDISPONIVEL'` |
| 05 | `fetch` não responde em 8 s (timers falsos) | `motivo = 'INDISPONIVEL'`, `fetch` abortado |
| 06 | Qualquer erro | `message` igual à antiga ("CNPJ não encontrado na Receita Federal") |
| 07 | Import pelo caminho antigo (`enterprise/composables/useConsultaCNPJ`) | Mesma função |

### Composable — `useConsultaCnpjCliente.spec.ts` (serviço e `getAllCustomers` substituídos por mocks)

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 08 | Cadastro novo, CNPJ válido digitado | Consulta chamada uma vez; campos vazios preenchidos; toast de sucesso |
| 09 | `razao_social` já digitada | Mantida; os outros vazios preenchidos |
| 10 | Todos os campos já preenchidos | Nada muda; toast "nada foi alterado" |
| 11 | Primeiro endereço com só o número preenchido | Endereço intacto |
| 12 | CNPJ com dígito verificador errado | Nenhuma chamada |
| 13 | 13 dígitos | Nenhuma chamada |
| 14 | Edição, CNPJ igual ao salvo | Nenhuma chamada |
| 15 | Edição, CNPJ trocado | Consulta chamada |
| 16 | Busca devolve outro cliente com o mesmo CNPJ | `estado = duplicado` com o nome; Receita **não** consultada |
| 17 | Busca devolve o próprio cliente (mesmo id) | Não é duplicado; Receita consultada |
| 18 | Busca devolve cliente com CNPJ parecido (só contém o termo) | Não é duplicado |
| 19 | Receita `NAO_ENCONTRADO` | `estado = nao_encontrado`; nenhum campo alterado |
| 20 | Receita `INDISPONIVEL` | `estado = indisponivel`; `consultar()` manual tenta de novo |
| 21 | CNPJ trocado enquanto a consulta do anterior está pendente | Resposta antiga descartada; nada preenchido |
| 22 | Modo visualização (`desabilitado = true`) | Nenhuma chamada |
| 23 | Busca de duplicidade falha (rede) | Segue para a Receita (a duplicidade real é barrada no salvar) |

### Roteiro manual (dev, `npm run tauri dev`)

1. Novo cliente PJ: digitar o CNPJ de uma empresa real. Campos preenchidos, toast de sucesso.
2. Repetir digitando antes a razão social: ela é mantida.
3. Digitar o CNPJ de um cliente já cadastrado: aviso de duplicidade com o nome.
4. Desligar a internet e digitar um CNPJ: aviso de indisponível em até 8 s; salvar à mão funciona. Religar e clicar "Tentar de novo".
5. Abrir um cliente PJ existente: nada é consultado. Trocar o CNPJ: consulta.
6. Cadastro de **empresa** (Configurações): consulta de CNPJ igual à de antes.
