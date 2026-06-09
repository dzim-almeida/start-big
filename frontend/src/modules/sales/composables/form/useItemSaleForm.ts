import { type Ref, type MaybeRef, watch, computed, unref, ref } from 'vue';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';

import { useAddItemSaleMutation, useUpdateItemSaleMutation } from '../mutates/useItemSaleMutation';
import { useAddItemOrcamentoMutation, useUpdateItemOrcamentoMutation } from '../mutates/useItemOrcamentoMutation';
import { useToast } from '@/shared/composables/useToast';

import {
  ItemSaleFormSchema,
  ItemSaleForm,
  ProductSaleRead,
  ProductSaleCreate,
  ProductSaleUpdate,
} from '../../schemas/productSale.schema';

export function useItemSaleForm(
  saleId: MaybeRef<number | null>,
  selectedItem: Ref<ProductSaleRead | null>,
  onSuccess?: () => void,
  isOrcamento = false,
) {
  const addItemSaleMutation = useAddItemSaleMutation();
  const updateItemSaleMutation = useUpdateItemSaleMutation();
  const addItemOrcamentoMutation = useAddItemOrcamentoMutation();
  const updateItemOrcamentoMutation = useUpdateItemOrcamentoMutation();
  const toast = useToast();

  const { handleSubmit, defineField, values, errors, setFieldValue, resetForm, isSubmitting } =
    useForm<ItemSaleForm>({
      validationSchema: toTypedSchema(ItemSaleFormSchema),
      initialValues: {
        descricao: '',
        valor_unitario: 0,
        quantidade: 1,
        desconto: 0,
      },
    });

  const [descricao] = defineField('descricao');
  const [valorUnitario] = defineField('valor_unitario');
  const [quantidade] = defineField('quantidade');
  const [desconto] = defineField('desconto');

  watch(
    selectedItem,
    (item) => {
      if (!item) {
        resetForm({
          values: {
            descricao: '',
            valor_unitario: 0,
            quantidade: 1,
            desconto: 0,
          },
        });

        return;
      }

      resetForm({
        values: {
          descricao: item.nome ?? '',
          valor_unitario: item.valor_unitario ? item.valor_unitario / 100 : 0,
          quantidade: item.quantidade ?? 1,
          desconto: item.desconto ? item.desconto / 100 : 0,
        },
      });
    },
    { immediate: true },
  );

  const subtotal = computed(() => {
    const formValues = values;

    return formValues.valor_unitario * formValues.quantidade;
  });

  const total = computed(() => {
    const formValues = values;

    return subtotal.value - formValues.desconto;
  });

  watch([subtotal, desconto], ([currentSubtotal, currentDesconto]) => {
    if (currentDesconto > currentSubtotal) {
      toast.warning('Desconto ajustado para o valor máximo do item');
      desconto.value = currentSubtotal;
      return;
    }

    if (currentDesconto < 0) {
      desconto.value = 0;
    }
  });

  function increaseQuantity() {
    const currentQuantity = values.quantidade;

    setFieldValue('quantidade', currentQuantity + 1);
  }

  function decreaseQuantity() {
    const currentQuantity = values.quantidade;

    setFieldValue('quantidade', Math.max(currentQuantity - 1, 1));
  }

  const avisoEstoqueOpen = ref(false);
  const pendingSubmitValues = ref<ItemSaleForm | null>(null);

  function executarSalvar(saleIdValue: number, formValues: ItemSaleForm) {
    if (selectedItem.value) {
      const payload: ProductSaleUpdate = {
        quantidade: formValues.quantidade,
        desconto: formValues.desconto * 100,
      };

      if (selectedItem.value.tipo_produto === 'AVULSO') {
        payload.descricao_avulsa = formValues.descricao;
        payload.valor_unitario = formValues.valor_unitario * 100;
      }

      if (isOrcamento) {
        updateItemOrcamentoMutation.mutate(
          { orcamentoId: saleIdValue, productId: selectedItem.value.id, payload },
          { onSuccess },
        );
      } else {
        updateItemSaleMutation.mutate(
          { saleId: saleIdValue, productId: selectedItem.value.id, payload },
          { onSuccess },
        );
      }

      return;
    }

    const payload: ProductSaleCreate = {
      tipo_produto: 'AVULSO' as const,
      descricao_avulsa: formValues.descricao,
      valor_unitario: formValues.valor_unitario * 100,
      quantidade: formValues.quantidade,
      desconto: formValues.desconto * 100,
    };

    if (isOrcamento) {
      addItemOrcamentoMutation.mutate(
        { orcamentoId: saleIdValue, payload },
        { onSuccess },
      );
    } else {
      addItemSaleMutation.mutate(
        { saleId: saleIdValue, payload },
        { onSuccess },
      );
    }
  }

  const submit = handleSubmit((formValues) => {
    const saleIdValue = unref(saleId);

    if (!saleIdValue) return;

    if (selectedItem.value && selectedItem.value.tipo_produto !== 'AVULSO') {
      const estoque = selectedItem.value.estoque_disponivel;
      if (estoque !== null && estoque !== undefined && formValues.quantidade > estoque) {
        pendingSubmitValues.value = formValues;
        avisoEstoqueOpen.value = true;
        return;
      }
    }

    executarSalvar(saleIdValue, formValues);
  });

  function confirmarSalvarComEstoqueNegativo() {
    const saleIdValue = unref(saleId);
    if (!saleIdValue || !pendingSubmitValues.value) return;
    executarSalvar(saleIdValue, pendingSubmitValues.value);
    avisoEstoqueOpen.value = false;
    pendingSubmitValues.value = null;
  }

  return {
    errors,
    descricao,
    valorUnitario,
    quantidade,
    desconto,
    subtotal,
    total,
    submit,
    increaseQuantity,
    decreaseQuantity,
    resetForm,
    isSubmitting,
    avisoEstoqueOpen,
    confirmarSalvarComEstoqueNegativo,
  };
}
