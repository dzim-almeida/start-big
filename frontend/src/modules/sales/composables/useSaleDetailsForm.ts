import { reactive, watch, computed, unref, type MaybeRef } from 'vue';
import { useDebounceFn } from '@vueuse/core';

import { useUpdateSaleMutation } from './mutates/useUpdateSaleMutation';
import type { SaleRead, SaleUpdate } from '../schemas/sale.schema';

export function useSaleDetailsForm(sale: MaybeRef<SaleRead | undefined>) {
  const updateSaleMutation = useUpdateSaleMutation();

  const form: SaleUpdate = reactive({
    desconto: 0,
    entrega: 0,
    observacao: '',
  });

  const saleId = computed(() => unref(sale)?.id);

  let isHydrating = false;

  function hydrateForm(currentSale: SaleRead) {
    isHydrating = true;

    form.desconto = currentSale.descontos ? currentSale.descontos / 100 : 0;
    form.entrega = currentSale.entrega ? currentSale.entrega / 100 : 0;
    form.observacao = currentSale.observacao ?? '';

    queueMicrotask(() => {
      isHydrating = false;
    });
  }

  watch(
    () => unref(sale),
    (currentSale) => {
      if (!currentSale) return;
      hydrateForm(currentSale);
    },
    { immediate: true },
  );

  function saveNow() {
    if (!saleId.value) return;

    updateSaleMutation.mutate({
        payload: form,
        saleId: saleId.value
    })
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
    }
  )

  return {
    form,
    isSaving: updateSaleMutation.isPending,
    saveNow,
  }
}
