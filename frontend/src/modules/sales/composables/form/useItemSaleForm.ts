import { type Ref, type MaybeRef, watch, computed, unref } from 'vue';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';

import { useAddItemSaleMutation, useUpdateItemSaleMutation } from '../mutates/useItemSaleMutation';

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
) {
  const addItemSaleMutation = useAddItemSaleMutation();
  const updateItemSaleMutation = useUpdateItemSaleMutation();

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

  const submit = handleSubmit((values) => {
    const saleIdValue = unref(saleId);

    if (!saleIdValue) return;

    if (selectedItem.value) {
      
      const payload: ProductSaleUpdate = {
        quantidade: values.quantidade,
        desconto: values.desconto * 100,
      }

      if (selectedItem.value.tipo_produto === 'AVULSO') {
        payload.descricao_avulsa = values.descricao;
        payload.valor_unitario = values.valor_unitario * 100;
      }
      
      updateItemSaleMutation.mutate(
        {
          saleId: saleIdValue,
          productId: selectedItem.value.id,
          payload: payload,
        },
        {
          onSuccess: onSuccess,
        },
      );

      return;
    }

    const payload: ProductSaleCreate = {
      tipo_produto: 'AVULSO' as const,
      descricao_avulsa: values.descricao,
      valor_unitario: values.valor_unitario * 100,
      quantidade: values.quantidade,
      desconto: values.desconto * 100,
    };

    addItemSaleMutation.mutate(
      {
        saleId: saleIdValue,
        payload: payload,
      },
      {
        onSuccess: onSuccess,
      },
    );
  });

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
  };
}
