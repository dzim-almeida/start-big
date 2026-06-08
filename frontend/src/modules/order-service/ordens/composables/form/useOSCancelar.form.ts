import { computed, ref } from 'vue';
import { useForm } from 'vee-validate';
import type { Ref } from 'vue';

import { orderServiceCancelValidationSchema } from '../../schemas/orderServiceMutate.schema';

import type { OSCancelarFormContext } from '../../types/context.type';

import { useCancelOrderServiceMutation } from '../request/useOrderServiceUpdate.mutate';

export function useOSCancelarForm(opts: {
  osNumber: Ref<string | null>;
  zerarAdiantamento?: Ref<boolean>;
  onSuccess?: () => void;
}): OSCancelarFormContext {
  const zerarAdiantamento = opts.zerarAdiantamento ?? ref(false);
  const cancelarMutation = useCancelOrderServiceMutation();

  const { handleSubmit, errors, defineField, resetForm: veeReset } = useForm({
    validationSchema: orderServiceCancelValidationSchema,
    initialValues: { motivo: '', zerar_adiantamento: false },
  });

  const [motivo] = defineField('motivo');

  const resetForm = () => {
    veeReset({ values: { motivo: '', zerar_adiantamento: false } });
  };

  const onSubmit = handleSubmit((formData) => {
    if (!opts.osNumber.value) return;
    cancelarMutation.mutate(
      {
        osNumber: opts.osNumber.value,
        cancelOs: { ...formData, zerar_adiantamento: zerarAdiantamento.value },
      },
      {
        onSuccess: () => {
          resetForm();
          opts.onSuccess?.();
        },
      },
    );
  });

  const isPending = computed(() => cancelarMutation.isPending.value);

  function submitDireto(zerar: boolean) {
    if (!opts.osNumber.value) return;
    cancelarMutation.mutate(
      {
        osNumber: opts.osNumber.value,
        cancelOs: { motivo: motivo.value ?? '', zerar_adiantamento: zerar },
      },
      {
        onSuccess: () => {
          resetForm();
          opts.onSuccess?.();
        },
      },
    );
  }

  return {
    motivo,
    errors,
    isPending,
    onSubmit,
    submitDireto,
    resetForm,
  };
}
