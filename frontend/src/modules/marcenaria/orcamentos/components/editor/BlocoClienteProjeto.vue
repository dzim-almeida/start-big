<script setup lang="ts">
/**
 * @component BlocoClienteProjeto
 * @description Seção "Cliente e projeto" (Spec 06B D21, D22; redesign 10/2026):
 * uma ficha só com cliente, vendedor, quem indicou (BlocoArquiteto) e o projeto.
 *
 * - Cliente: a mesma busca da OS (com cadastro de cliente novo e CNPJ, Spec 02).
 * - Projeto: depois do cliente, uma lista com os projetos que ele já tem,
 *   ou "Novo projeto" (nome + endereço da obra). TROCAR O CLIENTE LIMPA o
 *   projeto escolhido (o nome digitado fica): um projeto de outro cliente nunca
 *   fica preso ao orçamento.
 * - Vendedor: funcionários ativos; vem preenchido com o do usuário logado.
 *
 * Tudo aqui é do cabeçalho: muda o `form` e o salvamento automático grava.
 */
import { computed, ref, watch } from 'vue';
import { MapPin } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import OSClienteSearchModal from '@/modules/order-service/ordens/components/OSClienteSearchModal.vue';
import { useOsEmployeesGet } from '@/modules/order-service/ordens/composables/request/relationship/useOSRelationshipGet.queries';
import type { CustomerUnionReadSchemaDataType } from '@/modules/order-service/ordens/schemas/relationship/customer/customer.schema';
import type { ObjetoBuscaItemDataType } from '@/modules/order-service/ordens/schemas/relationship/objetoBusca.schema';
import { formatCNPJ, formatCPF, formatTelefone } from '@/shared/utils/document.utils';

import { useEditor } from '../../composables/useEditorContexto';
import { useProjetosDoClienteQuery } from '../../composables/useOrcamentoQuery';
import BlocoArquiteto from './BlocoArquiteto.vue';

const { form, detalhe, editavel } = useEditor();

// --- Cliente ----------------------------------------------------------------
const buscaAberta = ref(false);
/** Nome escolhido agora (antes de o servidor responder com o detalhe). */
const nomeEscolhido = ref<string | null>(null);
const nomeCliente = computed(() => {
  // O detalhe só vale se ainda for o MESMO cliente do formulário.
  if (detalhe.value?.cliente && detalhe.value.cliente.id === form.cliente_id) return detalhe.value.cliente.nome;
  return nomeEscolhido.value;
});

/** Iniciais para o avatar ("Studio Arquitetura" → "SA"). */
const iniciais = computed(() =>
  (nomeCliente.value ?? '').split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]).join('').toUpperCase(),
);

/** "00.360.305/0001-04 · (88) 99908-3353" — só do cliente que o detalhe já trouxe. */
const contatoCliente = computed(() => {
  const c = detalhe.value?.cliente;
  if (!c || c.id !== form.cliente_id) return '';
  const digitos = (c.documento ?? '').replace(/\D/g, '');
  const documento = digitos.length === 14 ? formatCNPJ(digitos) : digitos.length === 11 ? formatCPF(digitos) : c.documento;
  return [documento, c.telefone ? formatTelefone(c.telefone) : null].filter(Boolean).join(' · ');
});

/** Nome de exibição do cliente PF (nome) ou PJ (fantasia, senão razão social). */
function nomeDoCliente(cliente: CustomerUnionReadSchemaDataType): string {
  const c = cliente as { tipo?: string; nome?: string; nome_fantasia?: string; razao_social?: string };
  return (c.tipo === 'PF' ? c.nome : c.nome_fantasia || c.razao_social) || c.nome || '';
}

/** Trocar o cliente limpa o projeto escolhido (D21); o nome digitado fica. */
function escolherCliente(cliente: CustomerUnionReadSchemaDataType) {
  if (cliente.id !== form.cliente_id) form.objeto_id = null;
  form.cliente_id = cliente.id;
  nomeEscolhido.value = nomeDoCliente(cliente);
}

/** Na busca, clicar num projeto já entrega o cliente E o projeto. */
function escolherObjeto(objeto: ObjetoBuscaItemDataType) {
  form.cliente_id = objeto.cliente_id;
  form.objeto_id = objeto.objeto_id;
  form.projeto_nome = objeto.modelo ?? form.projeto_nome;
  nomeEscolhido.value = objeto.cliente_nome ?? null;
}

// --- Projeto ----------------------------------------------------------------
const clienteId = computed(() => form.cliente_id);
const { data: projetos } = useProjetosDoClienteQuery(clienteId);

/** Os projetos do cliente na lista, e "Novo projeto" por último. */
const opcoesProjeto = computed(() => [
  ...(projetos.value ?? []).map((p) => ({
    value: String(p.objeto_id),
    label: p.nome,
  })),
  { value: 'novo', label: '+ Novo projeto' },
]);

/** "novo" ou o id do projeto escolhido (a lista "Projeto"). */
const escolhaProjeto = computed({
  get: () => (form.objeto_id != null ? String(form.objeto_id) : 'novo'),
  set: (escolhido: string | number | undefined) => {
    const valor = String(escolhido ?? 'novo');
    if (valor === 'novo') {
      form.objeto_id = null;                               // o nome e o endereço ficam para editar
      return;
    }
    const projeto = projetos.value?.find((p) => p.objeto_id === Number(valor));
    if (!projeto) return;
    form.objeto_id = projeto.objeto_id;
    form.projeto_nome = projeto.nome;                      // o projeto já tem nome e endereço
    form.endereco_obra = projeto.endereco_obra;
  },
});

/** BaseInput devolve '' quando vazio; o backend guarda "sem valor" como null. */
const projetoNome = computed({
  get: () => form.projeto_nome ?? '',
  set: (valor: string) => { form.projeto_nome = valor.trim() ? valor : null; },
});
const enderecoObra = computed({
  get: () => form.endereco_obra ?? '',
  set: (valor: string) => { form.endereco_obra = valor.trim() ? valor : null; },
});

// --- Vendedor ---------------------------------------------------------------
// Sem a permissão de funcionários (403), a lista falha: fica só o vendedor atual.
const { data: funcionarios, isError: erroFuncionarios } = useOsEmployeesGet();
const opcoesVendedor = computed(() => {
  const lista = ((funcionarios.value as unknown as { id: number; nome: string }[] | undefined) ?? [])
    .map((f) => ({ value: f.id, label: f.nome }));
  const atual = detalhe.value?.vendedor;
  // Garante o vendedor gravado na lista (ex.: funcionário que saiu da empresa).
  if (atual && !lista.some((o) => o.value === atual.id)) lista.unshift({ value: atual.id, label: atual.nome });
  return lista;
});
const vendedor = computed({
  get: () => form.funcionario_id ?? undefined,
  set: (valor: string | number | undefined) => { form.funcionario_id = valor == null || valor === '' ? null : Number(valor); },
});

// Foco no "Cliente" ao abrir um orçamento novo (§7.12).
const botaoCliente = ref<InstanceType<typeof BaseButton> | null>(null);
watch(botaoCliente, (botao) => {
  if (botao && !form.cliente_id && editavel.value) (botao.$el as HTMLElement | undefined)?.focus?.();
}, { flush: 'post' });
</script>

<template>
  <section id="secao-cliente" class="scroll-mt-40 rounded-2xl border border-zinc-200 bg-white" aria-labelledby="titulo-cliente">
    <header class="px-6 pb-4 pt-5">
      <h2 id="titulo-cliente" class="text-base font-semibold text-zinc-900">Cliente e projeto</h2>
      <p class="text-xs text-zinc-500">Quem compra, quem vende e onde será instalado.</p>
    </header>

    <div class="grid grid-cols-1 gap-x-5 gap-y-5 px-6 pb-6 lg:grid-cols-3">
      <!-- Cliente -->
      <div>
        <span class="mb-1 block text-xs font-medium text-gray-700">Cliente</span>
        <div class="flex min-h-14 items-center gap-3 rounded-lg border border-zinc-200 px-3 py-2">
          <span
            v-if="nomeCliente"
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-primary text-xs font-bold text-white"
            aria-hidden="true"
          >
            {{ iniciais }}
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm font-semibold" :class="nomeCliente ? 'text-zinc-900' : 'font-normal text-zinc-500'" data-testid="nome-cliente">
              {{ nomeCliente || 'Nenhum cliente escolhido' }}
            </span>
            <span v-if="contatoCliente" class="block truncate text-xs tabular-nums text-zinc-500">{{ contatoCliente }}</span>
          </span>
          <BaseButton
            v-if="editavel"
            ref="botaoCliente"
            :variant="form.cliente_id ? 'secondary' : 'primary'"
            size="sm"
            data-testid="escolher-cliente"
            @click="buscaAberta = true"
          >
            {{ form.cliente_id ? 'Trocar' : 'Escolher' }}
          </BaseButton>
        </div>
      </div>

      <!-- Vendedor (D22) -->
      <BaseSelect
        v-model="vendedor"
        label="Vendedor"
        :options="opcoesVendedor"
        :disabled="!editavel || erroFuncionarios"
        placeholder="Escolha o vendedor"
      />

      <!-- Quem indicou (Spec 09B D1) -->
      <BlocoArquiteto />

      <!-- Projeto (D21): os do cliente, ou um novo -->
      <div v-if="projetos?.length">
        <BaseSelect v-model="escolhaProjeto" label="Projeto" :options="opcoesProjeto" :disabled="!editavel" />
        <p class="mt-1.5 text-xs text-zinc-500">
          {{ projetos.length }} {{ projetos.length === 1 ? 'projeto' : 'projetos' }} deste cliente · ou um novo
        </p>
      </div>
      <BaseInput
        v-model="projetoNome"
        label="Nome do projeto"
        placeholder="Ex.: Residencial Alpha Ville - Apto 802"
        :disabled="!editavel || form.objeto_id != null"
      />
      <div :class="projetos?.length ? '' : 'lg:col-span-2'">
        <BaseInput
          v-model="enderecoObra"
          label="Endereço da obra"
          placeholder="Rua, número, bairro"
          :disabled="!editavel || form.objeto_id != null"
        />
        <p v-if="form.objeto_id != null && editavel" class="mt-1.5 flex items-center gap-1 text-xs text-zinc-500">
          <MapPin :size="12" /> Do projeto escolhido. Para mudar, escolha "Novo projeto".
        </p>
      </div>
    </div>

    <OSClienteSearchModal
      :is-open="buscaAberta"
      @close="buscaAberta = false"
      @select-cliente="escolherCliente"
      @select-objeto="escolherObjeto"
    />
  </section>
</template>
