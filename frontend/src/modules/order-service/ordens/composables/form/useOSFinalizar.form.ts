import { computed } from 'vue';
import { useForm, useFieldArray } from 'vee-validate';
import type { Ref } from 'vue';

import { orderServiceReadyValidationSchema } from '../../schemas/orderServiceMutate.schema';
import type { OsPaymentCreateSchemaDataType } from '../../schemas/relationship/osPayment.schema';

import type { OSFinalizarFormContext } from '../../types/context.type';

import { useReadyOrderServiceMutation } from '../request/useOrderServiceUpdate.mutate';

import { DEFAULT_OS_PAGAMENTO_VALUES } from '../../constants/core.constant';


export function useOSFinalizarForm(opts: {
  osNumber: Ref<string | null>;
  onSuccess?: () => void;
}): OSFinalizarFormContext {
  const finalizarMutation = useReadyOrderServiceMutation();

  const { handleSubmit, errors, defineField, resetForm: veeReset } = useForm({
    validationSchema: orderServiceReadyValidationSchema,
    initialValues: {
      solucao: '',
      observacoes: '',
      desconto: 0,
      taxa_entrega: 0,
      acrescimo: 0,
      valor_entrada: 0,
      pagamentos: [],
    },
  });

  const [solucao] = defineField('solucao');
  const [observacoes] = defineField('observacoes');
  const [desconto] = defineField('desconto');
  const [taxa_entrega] = defineField('taxa_entrega');
  const [acrescimo] = defineField('acrescimo');
  const [valor_entrada] = defineField('valor_entrada');

  // FieldArray com generic explícito para inferência correta de tipos
  const {
    fields: pagamentos,
    push: pushPagamento,
    remove: removePagamento,
  } = useFieldArray<OsPaymentCreateSchemaDataType>('pagamentos');

  const handleAddPagamento = (pagamento?: Partial<OsPaymentCreateSchemaDataType>) => {
    pushPagamento({ ...DEFAULT_OS_PAGAMENTO_VALUES, ...pagamento });
  };

  const handleRemovePagamento = (index: number) => {
    removePagamento(index);
  };

  const resetForm = () => {
    veeReset({
      values: {
        solucao: '',
        observacoes: '',
        desconto: 0,
        taxa_entrega: 0,
        acrescimo: 0,
        valor_entrada: 0,
        pagamentos: [],
      },
    });
  };

  const onSubmit = handleSubmit((formData) => {
    if (!opts.osNumber.value) return;
    finalizarMutation.mutate(
      { osNumber: opts.osNumber.value, readyOs: formData },
      {
        onSuccess: () => {
          resetForm();
          opts.onSuccess?.();
        },
      },
    );
  });

  const isPending = computed(() => finalizarMutation.isPending.value);

  return {
    solucao,
    observacoes,
    desconto,
    taxa_entrega,
    acrescimo,
    valor_entrada,
    pagamentos,
    handleAddPagamento,
    handleRemovePagamento,
    errors,
    isPending,
    onSubmit,
    resetForm,
  };
}
