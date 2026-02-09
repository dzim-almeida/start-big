import {
  computed,
  inject,
  provide,
  ref,
  watch,
  type ComputedRef,
  type InjectionKey,
  type Ref,
} from 'vue';
import { useForm } from 'vee-validate';
import type { ServicoCreate, ServicoFormData, ServicoUpdate } from '../types/servicos.types';
import { servicoFormValidationSchema } from '../schemas/servicos.schema';
import { toCents } from '../utils/servicos.utils';
import { useServicoActions } from './useServicoActions';
import { useServicoModal } from './useServicoModal';

const DEFAULT_FORM_VALUES: ServicoFormData = {
  descricao: '',
  valor: 0,
};

export interface ServicoFormContext {
  descricao: Ref<string>;
  valor: Ref<number>;
  submitCount: Ref<number>;
  errors: Ref<Record<string, string | undefined>>;
  apiError: Ref<string | null>;
  isPending: ComputedRef<boolean>;
  onSubmit: (e?: Event) => void;
  resetForm: () => void;
}

export const SERVICO_FORM_KEY: InjectionKey<ServicoFormContext> = Symbol('servico-form');

export function useServicoFormProvider() {
  const { selectedServico, isCreateMode, closeModal } = useServicoModal();
  const { handleSubmit, defineField, setValues, resetForm, submitCount, errors, setErrors } =
    useForm<ServicoFormData>({
      validationSchema: servicoFormValidationSchema,
      initialValues: { ...DEFAULT_FORM_VALUES },
    });

  const { createMutation, updateMutation } = useServicoActions(setErrors);
  const apiError = ref<string | null>(null);

  const [descricao] = defineField('descricao');
  const [valor] = defineField('valor');

  function populateForm() {
    if (!selectedServico.value) {
      resetForm({ values: { ...DEFAULT_FORM_VALUES } });
      return;
    }

    setValues({
      descricao: selectedServico.value.descricao,
      valor: selectedServico.value.valor / 100,
    });
  }

  watch(selectedServico, populateForm, { immediate: true });

  function transformToCreateRequest(formData: ServicoFormData): ServicoCreate {
    return {
      descricao: formData.descricao.trim(),
      valor: toCents(formData.valor) || 0,
    };
  }

  function transformToUpdateRequest(formData: ServicoFormData): ServicoUpdate {
    return {
      descricao: formData.descricao.trim(),
      valor: toCents(formData.valor),
    };
  }

  const onSubmit = handleSubmit(async (formData) => {
    apiError.value = null;

    if (isCreateMode.value) {
      const request = transformToCreateRequest(formData);
      createMutation.mutate(request, {
        onSuccess: () => {
          closeModal();
          resetForm({ values: { ...DEFAULT_FORM_VALUES } });
        },
        onError: () => {
          apiError.value = 'Erro ao cadastrar serviço';
        },
      });
      return;
    }

    if (selectedServico.value) {
      const request = transformToUpdateRequest(formData);
      updateMutation.mutate(
        { id: selectedServico.value.id, data: request },
        {
          onSuccess: () => {
            closeModal();
            resetForm({ values: { ...DEFAULT_FORM_VALUES } });
          },
          onError: () => {
            apiError.value = 'Erro ao atualizar serviço';
          },
        },
      );
    }
  });

  const isPending = computed(
    () => createMutation.isPending.value || updateMutation.isPending.value,
  );

  const context: ServicoFormContext = {
    descricao,
    valor,
    submitCount,
    errors,
    apiError,
    isPending,
    onSubmit,
    resetForm: () => resetForm({ values: { ...DEFAULT_FORM_VALUES } }),
  };

  provide(SERVICO_FORM_KEY, context);

  return context;
}

export function useServicoForm(): ServicoFormContext {
  const context = inject(SERVICO_FORM_KEY);

  if (!context) {
    throw new Error(
      'useServicoForm must be used within a component that has called useServicoFormProvider',
    );
  }

  return context;
}
