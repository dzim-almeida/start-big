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
import { fornecedorFormValidationSchema } from '../schemas/fornecedor.schema';
import type { FornecedorFormData } from '../types/fornecedor.types';
import {
  useCreateFornecedorMutation,
  useUpdateFornecedorMutation,
} from './useFornecedoresMutations';
import { useFornecedorModal } from './useFornecedorModal';

const DEFAULT_FORM_VALUES: FornecedorFormData = {
  nome: '',
  cnpj: '',
  nome_fantasia: '',
  ie: '',
  telefone: '',
  celular: '',
  email: '',
  representante: '',
};

const unmask = (v: string) => v.replace(/\D/g, '');

export interface FornecedorFormContext {
  nome: Ref<string>;
  cnpj: Ref<string>;
  nome_fantasia: Ref<string>;
  ie: Ref<string>;
  telefone: Ref<string>;
  celular: Ref<string>;
  email: Ref<string>;
  representante: Ref<string>;
  submitCount: Ref<number>;
  errors: Ref<Partial<Record<keyof FornecedorFormData, string | undefined>>>;
  apiError: Ref<string | null>;
  isPending: ComputedRef<boolean>;
  onSubmit: (e?: Event) => void;
  resetForm: () => void;
}

export const FORNECEDOR_FORM_KEY: InjectionKey<FornecedorFormContext> =
  Symbol('fornecedor-form');

export function useFornecedorFormProvider() {
  const { selectedFornecedor, isCreateMode, closeModal } = useFornecedorModal();
  const { handleSubmit, defineField, setValues, resetForm, submitCount, errors } =
    useForm<FornecedorFormData>({
      validationSchema: fornecedorFormValidationSchema,
      initialValues: { ...DEFAULT_FORM_VALUES },
    });

  const createMutation = useCreateFornecedorMutation();
  const updateMutation = useUpdateFornecedorMutation();
  const apiError = ref<string | null>(null);

  const [nome] = defineField('nome');
  const [cnpj] = defineField('cnpj');
  const [nome_fantasia] = defineField('nome_fantasia');
  const [ie] = defineField('ie');
  const [telefone] = defineField('telefone');
  const [celular] = defineField('celular');
  const [email] = defineField('email');
  const [representante] = defineField('representante');

  function maskCnpj(value: string): string {
    const digits = value.replace(/\D/g, '').slice(0, 14);
    return digits
      .replace(/^(\d{2})(\d)/, '$1.$2')
      .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
      .replace(/\.(\d{3})(\d)/, '.$1/$2')
      .replace(/(\d{4})(\d)/, '$1-$2');
  }

  function populateForm() {
    if (!selectedFornecedor.value) {
      resetForm({ values: { ...DEFAULT_FORM_VALUES } });
      return;
    }
    const f = selectedFornecedor.value;
    setValues({
      nome: f.nome ?? '',
      cnpj: maskCnpj(f.cnpj ?? ''),
      nome_fantasia: f.nome_fantasia ?? '',
      ie: f.ie ?? '',
      telefone: f.telefone ?? '',
      celular: f.celular ?? '',
      email: f.email ?? '',
      representante: f.representante ?? '',
    });
  }

  watch(selectedFornecedor, populateForm, { immediate: true });

  const onSubmit = handleSubmit(async (formData) => {
    apiError.value = null;

    const payload = {
      nome: formData.nome.trim(),
      cnpj: unmask(formData.cnpj),
      nome_fantasia: formData.nome_fantasia?.trim() || undefined,
      ie: formData.ie?.trim() || undefined,
      telefone: formData.telefone?.trim() || undefined,
      celular: formData.celular?.trim() || undefined,
      email: formData.email?.trim() || undefined,
      representante: formData.representante?.trim() || undefined,
    };

    if (isCreateMode.value) {
      createMutation.mutate(payload, {
        onSuccess: () => {
          closeModal();
          resetForm({ values: { ...DEFAULT_FORM_VALUES } });
        },
        onError: () => {
          apiError.value = 'Erro ao cadastrar fornecedor. Verifique os dados e tente novamente.';
        },
      });
      return;
    }

    if (selectedFornecedor.value) {
      updateMutation.mutate(
        { id: selectedFornecedor.value.id, data: payload },
        {
          onSuccess: () => {
            closeModal();
            resetForm({ values: { ...DEFAULT_FORM_VALUES } });
          },
          onError: () => {
            apiError.value = 'Erro ao atualizar fornecedor. Verifique os dados e tente novamente.';
          },
        },
      );
    }
  });

  const isPending = computed(
    () => createMutation.isPending.value || updateMutation.isPending.value,
  );

  const context: FornecedorFormContext = {
    nome,
    cnpj,
    nome_fantasia,
    ie,
    telefone,
    celular,
    email,
    representante,
    submitCount,
    errors,
    apiError,
    isPending,
    onSubmit,
    resetForm: () => resetForm({ values: { ...DEFAULT_FORM_VALUES } }),
  };

  provide(FORNECEDOR_FORM_KEY, context);

  return context;
}

export function useFornecedorForm(): FornecedorFormContext {
  const context = inject(FORNECEDOR_FORM_KEY);
  if (!context) {
    throw new Error(
      'useFornecedorForm must be used within a component that called useFornecedorFormProvider',
    );
  }
  return context;
}
