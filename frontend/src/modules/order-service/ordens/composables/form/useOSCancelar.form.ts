import { computed } from 'vue';
import { useForm } from 'vee-validate';
import type { Ref } from 'vue';

import { orderServiceCancelValidationSchema } from '../../schemas/orderServiceMutate.schema';

import type { OSCancelarFormContext } from '../../types/context.type';

import { useCancelOrderServiceMutation } from '../request/useOrderServiceUpdate.mutate';


export function useOSCancelarForm(opts: {
  osNumber: Ref<string | null>;
  onSuccess?: () => void;
}): OSCancelarFormContext {
  const cancelarMutation = useCancelOrderServiceMutation();

  const { handleSubmit, errors, defineField, resetForm: veeReset } = useForm({
    validationSchema: orderServiceCancelValidationSchema,
    initialValues: { motivo: '' },
  });

  const [motivo] = defineField('motivo');

  const resetForm = () => {
    veeReset({ values: { motivo: '' } });
  };

  const onSubmit = handleSubmit((formData) => {
    if (!opts.osNumber.value) return;
    cancelarMutation.mutate(
      { osNumber: opts.osNumber.value, cancelOs: formData },
      {
        onSuccess: () => {
          resetForm();
          opts.onSuccess?.();
        },
      },
    );
  });

  const isPending = computed(() => cancelarMutation.isPending.value);

  return {
    motivo,
    errors,
    isPending,
    onSubmit,
    resetForm,
  };
}
