import { reactive, watch, computed, unref, type MaybeRef } from 'vue';
import { useDebounceFn } from '@vueuse/core';

import { useUpdateSaleMutation } from '../mutates/useUpdateSaleMutation';
import { useToast } from '@/shared/composables/useToast';
import type { SaleRead, SaleUpdate } from '../../schemas/sale.schema';

export function useSaleDetailsForm(sale: MaybeRef<SaleRead | undefined>) {
  const updateSaleMutation = useUpdateSaleMutation();
  const toast = useToast();

  const form: SaleUpdate = reactive({
    desconto: 0,
    entrega: 0,
    observacao: '',
    observacao_interna: '',
  });

  const saleId = computed(() => unref(sale)?.id);

  let isHydrating = false;

  function hydrateForm(currentSale: SaleRead) {
    isHydrating = true;

    form.desconto = currentSale.descontos ? currentSale.descontos / 100 : 0;
    form.entrega = currentSale.entrega ? currentSale.entrega / 100 : 0;
    form.observacao = currentSale.observacao ?? '';
    form.observacao_interna = currentSale.observacao_interna ?? '';

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

    const currentSale = unref(sale);
    const subtotal = currentSale?.subtotal ?? 0;

    const descontoAtual = form.desconto ?? 0;
    if (Math.round(descontoAtual * 100) > subtotal) {
      form.desconto = subtotal / 100;
      toast.warning('Desconto ajustado para o valor máximo permitido');
    }

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
    () => [form.observacao, form.observacao_interna],
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
