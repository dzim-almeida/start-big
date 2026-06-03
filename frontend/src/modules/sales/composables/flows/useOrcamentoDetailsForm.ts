import { reactive, watch, computed, unref, type MaybeRef } from 'vue';
import { useDebounceFn } from '@vueuse/core';

import { useUpdateOrcamentoMutation } from '../mutates/useUpdateOrcamentoMutation';
import { useToast } from '@/shared/composables/useToast';
import type { OrcamentoRead, OrcamentoUpdate } from '../../schemas/orcamento.schema';

export function useOrcamentoDetailsForm(orcamento: MaybeRef<OrcamentoRead | undefined>) {
  const updateMutation = useUpdateOrcamentoMutation();
  const toast = useToast();

  const form: OrcamentoUpdate = reactive({
    desconto: 0,
    entrega: 0,
    observacao: '',
  });

  const orcamentoId = computed(() => unref(orcamento)?.id);

  let isHydrating = false;

  function hydrateForm(current: OrcamentoRead) {
    isHydrating = true;

    form.desconto = current.descontos ? current.descontos / 100 : 0;
    form.entrega = current.entrega ? current.entrega / 100 : 0;
    form.observacao = current.observacao ?? '';

    queueMicrotask(() => {
      isHydrating = false;
    });
  }

  watch(
    () => unref(orcamento),
    (current) => {
      if (!current) return;
      hydrateForm(current);
    },
    { immediate: true },
  );

  function saveNow() {
    if (!orcamentoId.value) return;

    const current = unref(orcamento);
    const subtotal = current?.subtotal ?? 0;

    if (Math.round(form.desconto * 100) > subtotal) {
      form.desconto = subtotal / 100;
      toast.warning('Desconto ajustado para o valor máximo permitido');
    }

    updateMutation.mutate({
      payload: form,
      orcamentoId: orcamentoId.value,
    });
  }

  const debouncedSave = useDebounceFn(() => {
    if (isHydrating) return;
    saveNow();
  }, 700);

  watch(
    () => form.observacao,
    () => {
      if (isHydrating) return;
      debouncedSave();
    },
  );

  return {
    form,
    isSaving: updateMutation.isPending,
    saveNow,
  };
}
