import { computed, ref } from 'vue';
import { useForm } from 'vee-validate';
import type { Ref } from 'vue';

import { orderServiceCancelValidationSchema } from '../../schemas/orderServiceMutate.schema';

import type { OSCancelarFormContext } from '../../types/context.type';

import { useCancelOrderServiceMutation } from '../request/useOrderServiceUpdate.mutate';
import { useGerenteAprovacao } from '@/shared/composables/useGerenteAprovacao';
import { useToast } from '@/shared/composables/useToast';

export function useOSCancelarForm(opts: {
  osNumber: Ref<string | null>;
  zerarAdiantamento?: Ref<boolean>;
  onSuccess?: () => void;
}): OSCancelarFormContext {
  const zerarAdiantamento = opts.zerarAdiantamento ?? ref(false);
  const cancelarMutation = useCancelOrderServiceMutation();
  const gerenteCancelar = useGerenteAprovacao();
  const toast = useToast();

  const { handleSubmit, errors, defineField, resetForm: veeReset } = useForm({
    validationSchema: orderServiceCancelValidationSchema,
    initialValues: { motivo: '', zerar_adiantamento: false },
  });

  const [motivo] = defineField('motivo');

  const resetForm = () => {
    veeReset({ values: { motivo: '', zerar_adiantamento: false } });
  };

  async function executarCancelar(
    osNum: string,
    cancelData: { motivo: string; zerar_adiantamento: boolean },
    codigoGerente?: string,
  ): Promise<void> {
    try {
      await cancelarMutation.mutateAsync({
        osNumber: osNum,
        cancelOs: { ...cancelData, codigo_gerente: codigoGerente },
      });
      resetForm();
      opts.onSuccess?.();
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      if (detail === 'REQUER_APROVACAO_GERENTE') {
        const pin = await gerenteCancelar.pedirPin();
        if (pin) await executarCancelar(osNum, cancelData, pin);
      } else if (detail === 'PIN_GERENTE_INVALIDO') {
        toast.error('PIN do gerente inválido');
        const pin = await gerenteCancelar.pedirPin();
        if (pin) await executarCancelar(osNum, cancelData, pin);
      }
    }
  }

  const onSubmit = handleSubmit((formData) => {
    if (!opts.osNumber.value) return;
    void executarCancelar(opts.osNumber.value, {
      motivo: formData.motivo ?? '',
      zerar_adiantamento: zerarAdiantamento.value,
    });
  });

  const isPending = computed(() => cancelarMutation.isPending.value);

  function submitDireto(zerar: boolean) {
    if (!opts.osNumber.value) return;
    void executarCancelar(opts.osNumber.value, {
      motivo: motivo.value ?? '',
      zerar_adiantamento: zerar,
    });
  }

  return {
    motivo,
    errors,
    isPending,
    onSubmit,
    submitDireto,
    resetForm,
    gerenteCancelar,
  };
}
