<script setup lang="ts">
/**
 * @fileoverview Modelos de etiqueta da LOJA: listar, criar, editar e excluir.
 * Ficam no banco e aparecem em todos os terminais (plano, critério E9).
 */
import { computed, ref, watch } from 'vue';
import { Plus, Pencil, Trash2, ArrowLeft } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import type { ModeloEtiqueta } from '@/shared/etiquetas/modelo';
import { useExcluirModeloEtiqueta, useSalvarModeloEtiqueta } from '../../composables/useModelosEtiqueta';
import ModeloEtiquetaForm from './ModeloEtiquetaForm.vue';

const props = defineProps<{
  isOpen: boolean;
  modelos: ModeloEtiqueta[];
  /**
   * Atalho "Editar layout" da fila: abre este modelo já no editor visual.
   * Modelo da loja é editado; preset vira uma CÓPIA (preset não se altera).
   */
  abrirNoEditor?: ModeloEtiqueta | null;
}>();

const emit = defineEmits<{
  close: [];
  /** Modelo recém-salvo, para a fila já passar a usá-lo. */
  salvo: [chave: string];
}>();

const emEdicao = ref<ModeloEtiqueta | null>(null);
const criando = ref(false);
/** Ponto de partida de um modelo NOVO (cópia de preset); nulo = formulário em branco. */
const rascunho = ref<{ nome: string; definicao: ModeloEtiqueta['definicao'] } | null>(null);
const iniciarNoEditor = ref(false);
const paraExcluir = ref<ModeloEtiqueta | null>(null);
const formRef = ref<InstanceType<typeof ModeloEtiquetaForm> | null>(null);

const salvar = useSalvarModeloEtiqueta();
const excluir = useExcluirModeloEtiqueta();

const noFormulario = computed(() => criando.value || emEdicao.value !== null);

watch(
  () => props.isOpen,
  (aberto) => {
    if (!aberto) return;
    const alvo = props.abrirNoEditor;
    iniciarNoEditor.value = !!alvo;
    if (alvo?.id) {
      emEdicao.value = alvo;
      criando.value = false;
      rascunho.value = null;
      return;
    }
    emEdicao.value = null;
    rascunho.value = alvo ? { nome: `${alvo.nome} (cópia)`, definicao: alvo.definicao } : null;
    // Sem modelo da loja ainda, a lista vazia é um passo inútil: vai direto ao formulário.
    criando.value = !!alvo || props.modelos.length === 0;
  },
);

function voltar() {
  emEdicao.value = null;
  criando.value = false;
  rascunho.value = null;
  iniciarNoEditor.value = false;
}

function confirmar() {
  const payload = formRef.value?.payload();
  if (!payload) return;
  salvar.mutate(
    { id: emEdicao.value?.id ?? null, payload },
    {
      onSuccess: (modelo) => {
        emit('salvo', `loja:${modelo.id}`);
        voltar();
      },
    },
  );
}

function confirmarExclusao() {
  const alvo = paraExcluir.value;
  if (!alvo?.id) return;
  excluir.mutate(alvo.id, { onSettled: () => (paraExcluir.value = null) });
}

function resumo(m: ModeloEtiqueta): string {
  const p = m.definicao.pagina;
  const medida = `${p.largura_mm.toLocaleString('pt-BR')} × ${p.altura_mm.toLocaleString('pt-BR')} mm`;
  return p.tipo === 'folha' ? `Folha · ${medida} · ${p.colunas * (p.folha?.linhas ?? 1)} por folha` : `Rolo · ${medida} · ${p.colunas} col.`;
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    :title="noFormulario ? (emEdicao ? 'Editar modelo' : 'Novo modelo de etiqueta') : 'Modelos da loja'"
    :subtitle="noFormulario ? 'Depois de salvo, aparece em todos os terminais da loja' : 'Compartilhados com todos os terminais da loja'"
    :size="noFormulario ? '3xl' : 'lg'"
    @close="emit('close')"
  >
    <ModeloEtiquetaForm
      v-if="noFormulario"
      :key="emEdicao?.chave ?? rascunho?.nome ?? 'novo'"
      ref="formRef"
      :inicial="emEdicao ? { nome: emEdicao.nome, definicao: emEdicao.definicao } : rascunho"
      :iniciar-no-editor="iniciarNoEditor"
    />

    <div v-else class="space-y-3">
      <div v-if="modelos.length" class="divide-y divide-zinc-100 border border-zinc-100 rounded-xl">
        <div v-for="m in modelos" :key="m.chave" class="flex items-center gap-3 px-4 py-3">
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-zinc-800 truncate">{{ m.nome }}</p>
            <p class="text-xs text-zinc-400">{{ resumo(m) }}</p>
          </div>
          <button
            class="p-2 rounded-lg text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 cursor-pointer"
            title="Editar"
            @click="emEdicao = m"
          >
            <Pencil :size="16" />
          </button>
          <button
            class="p-2 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 cursor-pointer"
            title="Excluir"
            @click="paraExcluir = m"
          >
            <Trash2 :size="16" />
          </button>
        </div>
      </div>
      <p v-else class="text-sm text-zinc-400 text-center py-6">A loja ainda não tem modelos próprios.</p>
    </div>

    <template #footer>
      <div class="flex justify-between gap-2">
        <BaseButton v-if="noFormulario && modelos.length" variant="secondary" class="flex items-center gap-1" @click="voltar">
          <ArrowLeft :size="16" />
          Voltar
        </BaseButton>
        <span v-else />
        <BaseButton
          v-if="noFormulario"
          :is-loading="salvar.isPending.value"
          @click="confirmar"
        >
          Salvar modelo
        </BaseButton>
        <BaseButton v-else class="flex items-center gap-1" @click="criando = true">
          <Plus :size="16" />
          Novo modelo
        </BaseButton>
      </div>
    </template>
  </BaseModal>

  <BaseConfirmModal
    :is-open="paraExcluir !== null"
    title="Excluir modelo?"
    :description="`O modelo ${paraExcluir?.nome} some de todos os terminais da loja.`"
    confirm-label="Excluir"
    variant="danger"
    @close="paraExcluir = null"
    @confirm="confirmarExclusao"
  />
</template>
