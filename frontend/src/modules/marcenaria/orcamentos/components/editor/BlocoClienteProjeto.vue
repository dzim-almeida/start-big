<script setup lang="ts">
/**
 * @component BlocoClienteProjeto
 * @description Cliente, vendedor e projeto do orçamento (Spec 06B D21, D22).
 *
 * - Cliente: a mesma busca da OS (com cadastro de cliente novo e CNPJ, Spec 02).
 * - Projeto: depois do cliente, mostra os projetos que ele já tem para escolher,
 *   ou "Novo projeto" (nome + endereço da obra). TROCAR O CLIENTE LIMPA o
 *   projeto escolhido (o nome digitado fica): um projeto de outro cliente nunca
 *   fica preso ao orçamento.
 * - Vendedor: funcionários ativos; vem preenchido com o do usuário logado.
 *
 * Tudo aqui é do cabeçalho: muda o `form` e o salvamento automático grava.
 */
import { computed, ref, watch } from 'vue';
import { UserCircle2 } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import OSClienteSearchModal from '@/modules/order-service/ordens/components/OSClienteSearchModal.vue';
import { useOsEmployeesGet } from '@/modules/order-service/ordens/composables/request/relationship/useOSRelationshipGet.queries';
import type { CustomerUnionReadSchemaDataType } from '@/modules/order-service/ordens/schemas/relationship/customer/customer.schema';
import type { ObjetoBuscaItemDataType } from '@/modules/order-service/ordens/schemas/relationship/objetoBusca.schema';
import { formatDataPura } from '@/shared/utils/date.utils';

import { useEditor } from '../../composables/useEditorContexto';
import { useProjetosDoClienteQuery } from '../../composables/useOrcamentoQuery';

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

/** "novo" ou o id do projeto escolhido (os botões de rádio). */
const escolhaProjeto = computed({
  get: () => (form.objeto_id != null ? String(form.objeto_id) : 'novo'),
  set: (valor: string) => {
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
  <section class="rounded-2xl border border-zinc-200 bg-white p-5" aria-labelledby="titulo-cliente">
    <h2 id="titulo-cliente" class="mb-4 text-sm font-bold text-zinc-800">Cliente e projeto</h2>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <!-- Cliente -->
      <div>
        <p class="mb-1 text-xs font-medium text-zinc-600">Cliente</p>
        <div class="flex items-center gap-2">
          <div class="flex min-w-0 flex-1 items-center gap-2 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2">
            <UserCircle2 :size="16" class="shrink-0 text-zinc-400" />
            <span class="truncate text-sm" :class="nomeCliente ? 'text-zinc-800' : 'text-zinc-400'" data-testid="nome-cliente">
              {{ nomeCliente || 'Nenhum cliente escolhido' }}
            </span>
          </div>
          <BaseButton
            v-if="editavel"
            ref="botaoCliente"
            variant="secondary"
            size="sm"
            data-testid="escolher-cliente"
            @click="buscaAberta = true"
          >
            {{ form.cliente_id ? 'Trocar' : 'Escolher' }}
          </BaseButton>
        </div>
      </div>

      <!-- Vendedor (D22) -->
      <div>
        <BaseSelect
          v-model="vendedor"
          label="Vendedor"
          :options="opcoesVendedor"
          :disabled="!editavel || erroFuncionarios"
          placeholder="Escolha o vendedor"
        />
      </div>
    </div>

    <!-- Projeto (D21): os do cliente, ou um novo -->
    <fieldset class="mt-4">
      <legend class="mb-2 text-xs font-medium text-zinc-600">Projeto</legend>
      <div v-if="projetos?.length" class="mb-3 flex flex-col gap-1.5">
        <label
          v-for="projeto in projetos"
          :key="projeto.objeto_id"
          class="flex cursor-pointer items-start gap-2 text-sm"
        >
          <input
            v-model="escolhaProjeto"
            type="radio"
            :value="String(projeto.objeto_id)"
            :disabled="!editavel"
            class="mt-1 accent-brand-primary"
          />
          <span>
            <span class="font-medium text-zinc-800">{{ projeto.nome }}</span>
            <span v-if="projeto.endereco_obra" class="text-zinc-500"> · {{ projeto.endereco_obra }}</span>
            <span class="block text-[11px] text-zinc-400">Último orçamento em {{ formatDataPura(projeto.ultimo_uso) }}</span>
          </span>
        </label>
        <label class="flex cursor-pointer items-center gap-2 text-sm">
          <input v-model="escolhaProjeto" type="radio" value="novo" :disabled="!editavel" class="accent-brand-primary" />
          <span class="font-medium text-zinc-800">Novo projeto</span>
        </label>
      </div>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <BaseInput
          v-model="projetoNome"
          label="Nome do projeto"
          placeholder="Ex.: Residencial Alpha Ville - Apto 802"
          :disabled="!editavel || form.objeto_id != null"
        />
        <BaseInput
          v-model="enderecoObra"
          label="Endereço da obra"
          placeholder="Rua, número, bairro"
          :disabled="!editavel || form.objeto_id != null"
        />
      </div>
    </fieldset>

    <OSClienteSearchModal
      :is-open="buscaAberta"
      @close="buscaAberta = false"
      @select-cliente="escolherCliente"
      @select-objeto="escolherObjeto"
    />
  </section>
</template>
