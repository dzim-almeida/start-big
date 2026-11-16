<script setup lang="ts">
/**
 * @view OrcamentoEditorView
 * @description Rotas `/orcamentos/novo` e `/orcamentos/:id` (Spec 06B D1, D5).
 *
 * Esta tela só decide QUANDO o editor recomeça do zero:
 * - abrir outro orçamento ou outra versão → editor novo (`:key` muda);
 * - a própria tela criou o orçamento ("novo" → `/orcamentos/:id`) → o MESMO
 *   editor continua (o usuário está no meio da digitação).
 */
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';

import EditorOrcamento from '../components/editor/EditorOrcamento.vue';
import { useExigeCapacidade } from '../composables/useExigeCapacidade';
import { usePermissoesOrcamento } from '../composables/usePermissoesOrcamento';

const props = defineProps<{ id?: number }>();

// Outro segmento digitou o endereço: volta ao início (D3).
useExigeCapacidade('orcamento_tecnico');

const router = useRouter();
const { podeVer, podeGerir } = usePermissoesOrcamento();

/** Chave do editor: muda só quando é OUTRO orçamento. */
const chave = ref(String(props.id ?? 'novo'));
/** id que a própria tela acabou de criar (a troca de rota não recomeça o editor). */
let criadoAqui: number | null = null;

watch(() => props.id, (novo) => {
  if (novo != null && novo === criadoAqui) return;
  chave.value = String(novo ?? 'novo');
});

/** Criou na tela "novo" (D5): troca a rota sem empilhar no "voltar". */
function aoCriar(id: number) {
  criadoAqui = id;
  void router.replace({ name: 'marcenaria-orcamento', params: { id } });
}
</script>

<template>
  <div v-if="!podeVer || (props.id == null && !podeGerir)" class="rounded-2xl border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-500">
    {{ podeVer ? 'Você não tem permissão para criar orçamentos.' : 'Você não tem permissão para ver orçamentos.' }}
  </div>
  <EditorOrcamento v-else :key="chave" :id-inicial="props.id ?? null" @criado="aoCriar" />
</template>
