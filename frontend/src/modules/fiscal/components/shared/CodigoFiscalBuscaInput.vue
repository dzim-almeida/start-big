<script setup lang="ts">
/**
 * @component CodigoFiscalBuscaInput
 * @description Campo de código da NFS-e (código de tributação nacional, NBS):
 * digita "suporte informática", escolhe 01.07.01.
 *
 * É o NcmBuscaInput generalizado — mesmas razões, que valem aqui também:
 * - não é um BaseSelect porque quem filtra é o servidor (acentos, palavras
 *   soltas); o refiltro local jogaria fora o que o motor achou;
 * - continua aceitando digitação direta: quem sabe o código digita e segue,
 *   e sem o módulo ou sem a tabela o campo é só um campo.
 *
 * A DIFERENÇA: `sugeridos`. O NBS tem uma correlação oficial com o código
 * nacional (Anexo VIII da Receita); com o código escolhido, focar o campo já
 * mostra os NBS que cabem nele, sem o lojista precisar saber o que procurar.
 */

import { ref, computed, watch, onBeforeUnmount } from 'vue';
import { Search, Check, Sparkles } from 'lucide-vue-next';

import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import type { CodigoFiscalItem } from '../../types/fiscal.types';

const props = withDefaults(
  defineProps<{
    /** Só os dígitos — é o que vai para o banco. */
    modelValue: string;
    label: string;
    /** Quantos dígitos tem o código completo (6 no nacional, 9 no NBS). */
    digitos: number;
    /** Como o código aparece na tela ("01.07.01"). */
    formatar: (codigo: string) => string;
    buscar: (termo: string) => Promise<CodigoFiscalItem[]>;
    sugeridos?: CodigoFiscalItem[];
    placeholder?: string;
    disabled?: boolean;
    error?: string;
    ajuda?: string;
  }>(),
  { sugeridos: () => [] },
);

const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>();

const termo = ref('');
const resultados = ref<CodigoFiscalItem[]>([]);
const mostrandoSugeridos = ref(false);
const aberto = ref(false);
const buscando = ref(false);
const descricaoEscolhida = ref('');

let timer: ReturnType<typeof setTimeout> | undefined;
onBeforeUnmount(() => timer && clearTimeout(timer));

const apenasDigitos = (valor: string) => valor.replace(/\D/g, '');

/** 300 ms de espera, como no NCM: sem ela, cada tecla seria uma consulta. */
function agendarBusca(valor: string) {
  if (timer) clearTimeout(timer);
  if (valor.trim().length < 2) {
    resultados.value = [];
    aberto.value = false;
    return;
  }
  timer = setTimeout(() => buscarAgora(valor), 300);
}

async function buscarAgora(valor: string) {
  buscando.value = true;
  try {
    const achados = await props.buscar(valor.trim());
    resultados.value = achados;
    mostrandoSugeridos.value = false;
    aberto.value = achados.length > 0;
  } catch {
    // Sem módulo ou sem tabela: o campo vira digitação livre, sem erro na tela.
    resultados.value = [];
    aberto.value = false;
  } finally {
    buscando.value = false;
  }
}

function aoDigitar(valor: string) {
  termo.value = valor;
  descricaoEscolhida.value = '';
  const digitos = apenasDigitos(valor);
  const soCodigo = digitos === valor.replace(/[.\s]/g, '');

  // Código completo digitado: grava e não oferece lista.
  if (soCodigo && digitos.length === props.digitos) {
    emit('update:modelValue', digitos);
    aberto.value = false;
    return;
  }

  emit('update:modelValue', '');
  agendarBusca(valor);
}

function aoFocar() {
  if (props.sugeridos.length && (!termo.value || props.modelValue)) {
    resultados.value = props.sugeridos;
    mostrandoSugeridos.value = true;
    aberto.value = true;
  } else if (resultados.value.length) {
    aberto.value = true;
  }
}

function escolher(item: CodigoFiscalItem) {
  emit('update:modelValue', item.codigo);
  descricaoEscolhida.value = item.descricao;
  termo.value = props.formatar(item.codigo);
  aberto.value = false;
}

// Código que chega de fora (edição do serviço) aparece formatado.
watch(
  () => props.modelValue,
  (codigo) => {
    if (codigo && codigo !== apenasDigitos(termo.value)) {
      termo.value = props.formatar(codigo);
    }
  },
  { immediate: true },
);

/** A descrição do código atual: a escolhida agora ou, na edição, a dos sugeridos. */
const descricaoAtual = computed(
  () =>
    descricaoEscolhida.value ||
    props.sugeridos.find((s) => s.codigo === props.modelValue)?.descricao ||
    '',
);
</script>

<template>
  <div class="relative">
    <BaseInput
      :model-value="termo"
      :label="label"
      :placeholder="placeholder"
      :disabled="disabled"
      :error="error"
      :ajuda="ajuda"
      @update:model-value="aoDigitar"
      @focusin="aoFocar"
      @blur="aberto = false"
    />
    <!-- focusin, e não focus: o BaseInput não repassa o focus do <input>, e o
         focus não sobe até a div onde o listener cairia. O focusin sobe. -->

    <p v-if="descricaoAtual && !aberto" class="mt-1 text-xs text-emerald-600 flex items-center gap-1">
      <Check :size="12" class="shrink-0" />
      {{ descricaoAtual }}
    </p>

    <p v-else-if="buscando" class="mt-1 text-xs text-zinc-400 flex items-center gap-1">
      <Search :size="12" class="shrink-0" /> procurando…
    </p>

    <!-- Resultados. Sem refiltro local: quem filtrou foi o servidor. -->
    <ul
      v-if="aberto"
      class="absolute z-50 mt-1 w-full max-h-64 overflow-auto rounded-xl border border-zinc-200 bg-white shadow-lg"
    >
      <li
        v-if="mostrandoSugeridos"
        class="px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-brand-primary flex items-center gap-1 border-b border-zinc-100"
      >
        <Sparkles :size="12" class="shrink-0" /> Sugeridos para este serviço
      </li>
      <li
        v-for="item in resultados"
        :key="item.codigo"
        class="cursor-pointer px-3 py-2 hover:bg-brand-primary-light transition-colors"
        @mousedown.prevent="escolher(item)"
      >
        <p class="text-sm font-medium text-zinc-800">
          {{ formatar(item.codigo) }} · {{ item.descricao }}
        </p>
        <p
          v-if="item.descricao_completa && item.descricao_completa !== item.descricao"
          class="text-[11px] text-zinc-400 truncate"
        >
          {{ item.descricao_completa }}
        </p>
      </li>
    </ul>
  </div>
</template>
