# Spec 02 — Consulta de CNPJ no Cadastro de Cliente (o que falta)

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Implementada em 09/10/2026 (roteiro manual da §11 pendente)           |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado                 |
| Dependências | Spec 00                                                               |
| Bloqueia     | Spec 06B (o orçamento usa o modal de cliente)                         |
| Referência   | SPEC-00: O6, R15-CNPJ, PR1, PR6 · código existente: `shared/services/cnpj.service.ts`, `customers/composables/modal/context/useCustomerForm.context.ts` (`consultarReceita`) |

> **Revisão 1 (08/10/2026) — R15-CNPJ, spec reescrita.** A versão de 06/10 desta spec planejava levar a consulta de CNPJ para `shared` e ligá-la ao cliente PJ. Isso **já foi feito** no commit `011dff7` (06/10, linha fiscal): a consulta mora em `shared/services/cnpj.service.ts`, o arquivo da empresa só reexporta, e o cadastro de cliente PJ consulta sozinho quando o CNPJ fica completo (cadastro novo) ou pelo botão (edição). O **preenchimento** de hoje prevalece (FB2/R15-CNPJ): ele sobrescreve razão social e endereço com a Receita e preenche o regime MEI/Simples, que resolveu uma rejeição real da SEFAZ. As regras D6/D7 da versão anterior ("só campos vazios") **saem**. Esta spec fica só com o que ainda falta.

---

## 1. Objetivo

Completar a consulta de CNPJ do cliente PJ com quatro coisas que o código de hoje não faz:

1. **Dizer por que falhou:** hoje toda falha (inclusive sem internet) mostra "CNPJ não encontrado na Receita Federal", e o usuário acha que digitou errado.
2. **Não ficar pendurada:** sem rede, o `fetch` pode não responder nunca; a consulta passa a ter tempo limite.
3. **Não consultar CNPJ inválido:** a consulta automática passa a exigir o dígito verificador correto.
4. **Avisar cliente duplicado antes de preencher tudo:** hoje o usuário só descobre o `409` ao salvar.

## 2. Escopo

**Dentro do escopo**
- `buscarDadosCNPJ`: erro tipado e tempo limite (a mensagem do erro não muda, para o cadastro de empresa).
- `consultarReceita` do cliente: verificação de duplicidade, mensagem por motivo, descarte de resposta atrasada, estado exposto para a tela.
- `CompanyDataSection.vue`: dígito verificador antes da consulta automática; aviso fixo abaixo do campo.
- Testes e roteiro manual.

**Fora do escopo**
- O preenchimento (quais campos, sobrescrever ou não): **não muda** (R15-CNPJ).
- Cadastro de **empresa**: continua exatamente igual (mesma função, mesma mensagem).
- Backend: nenhuma mudança (a duplicidade usa `GET /clientes/?buscar=`, que já existe).
- **CNPJ alfanumérico** (PEND-001).
- Mudar o `BaseInput`.

---

## 3. Arquivos afetados

```
frontend/src/
├── shared/services/
│   ├── cnpj.service.ts                               # ALTERAR — ConsultaCnpjErro + tempo limite
│   └── __tests__/cnpj.service.spec.ts                # ALTERAR — casos novos (os de hoje continuam)
└── modules/customers/
    ├── composables/modal/
    │   ├── context/useCustomerForm.context.ts        # ALTERAR — duplicidade, motivo, resposta atrasada, estado
    │   ├── types/context.type.ts                     # ALTERAR — `consultaCnpj` no contexto
    │   └── context/__tests__/consultaReceita.spec.ts # CRIAR
    ├── components/modal/form/CompanyDataSection.vue  # ALTERAR — dígito verificador + aviso abaixo do campo
    └── services/customerGet.service.ts               # CONFERIR — getAllCustomers({ search, limit })
```

| Arquivo | Faz | Não faz |
|---------|-----|---------|
| `cnpj.service.ts` | Chama a BrasilAPI, classifica a falha, corta a espera | Saber de formulário |
| `useCustomerForm.context.ts` | Decide se é duplicado, preenche (como hoje), guarda o estado | Renderizar |

> **Nota da implementação (09/10/2026):** para os casos 08–15 poderem ser testados sem montar o modal inteiro, a lógica de `consultarReceita` foi **movida** para `customers/composables/modal/context/consultaReceita.ts` (`criarConsultaReceita`), e o provider passou a usá-la. O preenchimento foi movido sem mudança de linha (D9).
| `CompanyDataSection.vue` | Dispara a consulta automática e mostra o estado | Chamar API |

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | `buscarDadosCNPJ` lança `ConsultaCnpjErro` com `motivo`: `NAO_ENCONTRADO` (404) ou `INDISPONIVEL` (sem rede, tempo esgotado, 429, 5xx). A **mensagem** do erro continua "CNPJ não encontrado na Receita Federal" | O cadastro de empresa mostra a mensagem do erro num toast genérico e não pode mudar (PR1); o cliente lê o `motivo` |
| D2 | Tempo limite de **8 s** (`AbortController`) | Sem rede, o campo ficaria "consultando" para sempre |
| D3 | A consulta automática (cadastro novo, CNPJ com 14 dígitos) só roda se o **dígito verificador** for válido (`cpf-cnpj-validator`) | CNPJ errado não gasta chamada e não mostra "não encontrado" por cima do erro do schema. O botão "Consultar" segue a mesma regra |
| D4 | Antes da Receita, **duplicidade**: `getAllCustomers({ search: dígitos, limit: 5 })`, comparando o CNPJ **exato** (só dígitos) e ignorando o próprio cliente em edição. Duplicado: aviso fixo abaixo do campo, **sem** consultar a Receita e **sem** preencher | Hoje o usuário preenche tudo e só descobre o `409` ao salvar |
| D5 | Falha da busca de duplicidade (rede) **não** impede a consulta à Receita | A duplicidade real continua barrada pelo backend (`409`) |
| D6 | Mensagens: sucesso e "não encontrado" continuam em **toast** (como hoje); "indisponível" vira toast com o texto novo; **duplicado** fica como texto fixo âmbar abaixo do campo até o CNPJ mudar | O aviso de duplicidade precisa ficar visível enquanto o usuário decide; os outros já são toast hoje |
| D7 | Resposta **atrasada** é descartada se o CNPJ do campo mudou durante a consulta | Evita preencher o cliente B com os dados do CNPJ A |
| D8 | Duplicidade e falha **não bloqueiam** o salvar | Sem internet, o cadastro manual continua possível |
| D9 | O preenchimento de hoje **não muda** (razão social, fantasia, regime, endereço do primeiro item, contato vazio) | R15-CNPJ |

---

## 5. Contratos consumidos

- BrasilAPI `GET https://brasilapi.com.br/api/cnpj/v1/{cnpj}` (o mesmo de hoje): `200` sucesso; `404` → `NAO_ENCONTRADO`; `429`, `5xx`, erro de rede, tempo esgotado → `INDISPONIVEL`.
- `GET /api/v1/clientes/?buscar=<14 dígitos>&limit=5` (existente): busca por nome, CPF, razão social, **CNPJ** ou fantasia. O backend grava o CNPJ só com dígitos (`schemas/cliente.py`, `^\d{14}$`); comparar só dígitos dos dois lados.

---

## 6. Especificação técnica

### 6.1. Serviço — `shared/services/cnpj.service.ts`

O mapeamento da resposta (`converterRespostaBrasilApi`, `mapRegimeTributario`, `mapNaturezaJuridica`) **não muda**. Muda só a chamada:

```ts
/** Por que a consulta falhou (Spec 02, D1). */
export type MotivoFalhaCnpj = 'NAO_ENCONTRADO' | 'INDISPONIVEL';

export class ConsultaCnpjErro extends Error {
  motivo: MotivoFalhaCnpj;                      // declarado no corpo (o tsconfig não aceita parameter properties)
  constructor(motivo: MotivoFalhaCnpj) {
    // Mensagem antiga, de propósito: o cadastro de empresa mostra só ela (D1).
    super('CNPJ não encontrado na Receita Federal');
    this.name = 'ConsultaCnpjErro';             // facilita reconhecer o erro no console
    this.motivo = motivo;                       // o cliente decide o texto por aqui
  }
}

const TEMPO_LIMITE_MS = 8_000;                  // D2: 8 segundos

export async function buscarDadosCNPJ(cnpj: string): Promise<DadosCnpj> {
  const digits = cnpj.replace(/\D/g, '');                        // a API só aceita os 14 dígitos
  const controle = new AbortController();                        // permite cancelar o fetch
  const timer = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS); // corta a espera em 8 s

  let resp: Response;
  try {
    resp = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${digits}`, { signal: controle.signal });
  } catch {
    throw new ConsultaCnpjErro('INDISPONIVEL');                  // sem rede ou tempo esgotado
  } finally {
    clearTimeout(timer);                                         // não deixa o timer vivo
  }

  if (resp.status === 404) throw new ConsultaCnpjErro('NAO_ENCONTRADO');
  if (!resp.ok) throw new ConsultaCnpjErro('INDISPONIVEL');      // 429, 5xx...
  return converterRespostaBrasilApi(await resp.json());          // mapeamento de hoje, sem mudança
}
```

### 6.2. Contexto do cliente — `consultarReceita` (`useCustomerForm.context.ts`)

```ts
/** O que a tela mostra abaixo do CNPJ (só o aviso que precisa ficar visível, D6). */
export type AvisoCnpj = { tipo: 'duplicado'; nomeCliente: string } | null;

const avisoCnpj = ref<AvisoCnpj>(null);         // aviso fixo de duplicidade
let consultaAtual = '';                          // CNPJ da consulta em andamento (D7)

async function consultarReceita(cnpjDigitos: string) {
  if (isConsultingCNPJ.value) return;                            // regra de hoje: uma por vez
  isConsultingCNPJ.value = true;
  consultaAtual = cnpjDigitos;                                   // marca qual CNPJ está sendo consultado
  avisoCnpj.value = null;                                        // começa limpo
  try {
    // 1) Duplicidade (D4). Falha da busca não impede seguir (D5).
    const pagina = await getAllCustomers({ search: cnpjDigitos, limit: 5 }).catch(() => null);
    if (cnpjAtual() !== consultaAtual) return;                   // o usuário mudou o CNPJ: descarta (D7)
    const outro = pagina?.items.find(
      (c) => 'cnpj' in c && (c.cnpj ?? '').replace(/\D/g, '') === cnpjDigitos   // CNPJ exato
        && c.id !== selectedCustomer.value?.id,                  // nunca o próprio cliente
    );
    if (outro) {
      avisoCnpj.value = { tipo: 'duplicado', nomeCliente: outro.razao_social ?? '' };
      return;                                                    // não consulta nem preenche
    }

    // 2) Receita.
    const dados = await buscarDadosCNPJ(cnpjDigitos);
    if (cnpjAtual() !== consultaAtual) return;                   // resposta atrasada (D7)
    // ... preenchimento IDÊNTICO ao de hoje (pjForm.setValues com razão social,
    //     fantasia, regime, contato vazio e o primeiro endereço) — D9
    toast.success('Dados da Receita Federal preenchidos. Confira e informe a Inscrição Estadual, se o cliente tiver.');
  } catch (erro) {
    if (cnpjAtual() !== consultaAtual) return;                   // erro de uma consulta velha: ignora
    const motivo = erro instanceof ConsultaCnpjErro ? erro.motivo : 'INDISPONIVEL';
    if (motivo === 'NAO_ENCONTRADO') toast.error('CNPJ não encontrado na Receita Federal.');  // texto de hoje
    else toast.error('Não foi possível consultar a Receita agora.', 'Preencha manualmente ou tente de novo.');
  } finally {
    isConsultingCNPJ.value = false;
  }
}
```

- `cnpjAtual()` lê os dígitos do campo `pjForm` naquele instante.
- Expor `avisoCnpj` no contexto (`context.type.ts`) junto com `isConsultingCNPJ` e `consultarReceita`.
- No `watch` que já reseta o formulário ao fechar o modal, voltar `avisoCnpj` a `null`.
- Ao mudar o CNPJ (qualquer dígito), `avisoCnpj` volta a `null` (o aviso era do CNPJ anterior).

### 6.3. Tela — `CompanyDataSection.vue`

```ts
import { cnpj as validadorCnpj } from 'cpf-cnpj-validator';

/** CNPJ completo e com dígito verificador certo (D3). */
const cnpjValido = computed(() => cnpjDigitos.value.length === 14 && validadorCnpj.isValid(cnpjDigitos.value));

watch(cnpjDigitos, (digitos, anterior) => {
  if (digitos !== anterior) limparAvisoCnpj();                   // o aviso era do CNPJ anterior
  // Regra de hoje (só no cadastro novo) + dígito verificador (D3).
  if (!isCreateMode.value || !cnpjValido.value || digitos === anterior) return;
  consultarReceita(digitos);
});
```

- O botão "Consultar" que já existe passa a ficar desabilitado sem `cnpjValido`.
- Abaixo do campo, fora do `error` do `BaseInput`, numa região `aria-live="polite"`: com `avisoCnpj.tipo === 'duplicado'`, o texto âmbar "Já existe um cliente com este CNPJ: **{nome}**. Salvar vai dar erro de duplicidade."

---

## 7. Prova de não regressão (⚠️ PR1)

1. **Cadastro de empresa idêntico:** CNPJ válido e CNPJ inexistente, antes e depois: mesmos campos preenchidos e mesma mensagem.
2. **Cliente PJ, CNPJ válido de cliente novo:** mesmos campos preenchidos de hoje (comparar com um snapshot do `pjForm.values`).
3. **Cliente PF:** nenhuma mudança.
4. `npm run test` e `npx vue-tsc --noEmit` sem erros (baseline de 08/10: 188 testes, 0 erros de tipo).

## 8. Mudança visível pretendida (todos os segmentos)

No cliente PJ, em todos os segmentos: CNPJ com dígito errado não consulta; sem internet aparece "Não foi possível consultar a Receita agora" em até 8 s; CNPJ de outro cliente mostra o aviso de duplicidade. Avisar as lojas na atualização.

## 9. Limitações conhecidas

- **CNPJ alfanumérico:** fora (PEND-001).
- **Dependência externa:** a BrasilAPI tem limite de uso (`429` → `INDISPONIVEL`).
- **Edição:** a consulta continua só pelo botão (regra de hoje), e sobrescreve com a Receita (D9). Quem corrigiu a razão social à mão não deve clicar "Consultar" de novo.

---

## 10. Critérios de aceite

- [ ] Sem internet (ou sem resposta em 8 s), o cliente mostra "Não foi possível consultar a Receita agora…", e não "CNPJ não encontrado".
- [ ] CNPJ inexistente continua mostrando "CNPJ não encontrado na Receita Federal."
- [ ] CNPJ com dígito verificador errado não dispara a consulta automática e deixa o botão desabilitado.
- [ ] CNPJ de outro cliente mostra o aviso de duplicidade com o nome, sem consultar a Receita e sem preencher.
- [ ] O próprio cliente em edição nunca aparece como duplicado.
- [ ] Trocar o CNPJ durante uma consulta não preenche o formulário com os dados do anterior.
- [ ] Preenchimento, cadastro de empresa e cliente PF iguais aos de antes.
- [ ] Código novo comentado (PR6).

## 11. Casos de teste

### Serviço — `shared/services/__tests__/cnpj.service.spec.ts` (`fetch` substituído por mock; os casos de hoje continuam)

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `200` | Mesmo objeto de `converterRespostaBrasilApi` |
| 02 | `404` | `ConsultaCnpjErro`, `motivo = 'NAO_ENCONTRADO'` |
| 03 | `429` e `503` | `motivo = 'INDISPONIVEL'` |
| 04 | `fetch` rejeita (sem rede) | `motivo = 'INDISPONIVEL'` |
| 05 | `fetch` não responde em 8 s (timers falsos) | `motivo = 'INDISPONIVEL'`; `fetch` abortado |
| 06 | Qualquer erro | `message` = "CNPJ não encontrado na Receita Federal" |
| 07 | Import pelo caminho da empresa (`enterprise/composables/useConsultaCNPJ`) | Mesma função |

### Contexto — `consultaReceita.spec.ts` (serviço e `getAllCustomers` substituídos por mocks)

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 08 | Busca devolve outro cliente com o mesmo CNPJ | `avisoCnpj = duplicado` com o nome; Receita **não** chamada; formulário igual |
| 09 | Busca devolve o próprio cliente (edição) | Não é duplicado; Receita chamada |
| 10 | Busca devolve cliente com CNPJ que só contém o termo | Não é duplicado |
| 11 | Busca de duplicidade falha | Receita chamada (D5) |
| 12 | Receita `NAO_ENCONTRADO` | Toast "CNPJ não encontrado na Receita Federal."; formulário igual |
| 13 | Receita `INDISPONIVEL` | Toast "Não foi possível consultar a Receita agora."; formulário igual |
| 14 | CNPJ trocado durante a consulta | Resposta descartada; nada preenchido; nenhum toast |
| 15 | Sucesso | `pjForm.values` igual ao do código de hoje para a mesma resposta (snapshot) |

### Tela — `CompanyDataSection`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 16 | Cadastro novo, 14 dígitos com DV errado | Nenhuma chamada; botão desabilitado |
| 17 | Cadastro novo, CNPJ válido | Uma chamada |
| 18 | Edição, CNPJ salvo | Nenhuma chamada automática (regra de hoje) |
| 19 | Aviso de duplicidade e depois troca de um dígito | Aviso some |

### Roteiro manual (dev, `npm run tauri dev`)

1. Novo cliente PJ: CNPJ de uma empresa real → preenche como hoje.
2. CNPJ com o último dígito trocado → nada é consultado.
3. CNPJ de um cliente já cadastrado → aviso de duplicidade com o nome.
4. Desligar a internet → "Não foi possível consultar a Receita agora" em até 8 s; salvar à mão funciona.
5. Cadastro de **empresa** (Configurações): igual ao de antes.
