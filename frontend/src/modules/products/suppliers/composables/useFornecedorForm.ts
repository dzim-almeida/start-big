// ============================================================================
// MÓDULO: FornecedorFormProvider (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Centralizar o estado do formulário, validações e mutações.
// TECNOLOGIAS: Vee-Validate (Form Handling), Provide/Inject API, Zod (Schema).
// FUNCIONALIDADES: Máscara/Desmascaramento de dados, população dinâmica para 
//                  edição, tratamento de payloads condicionais e controle de erros.
// ============================================================================
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
import type { FornecedorFormData, SupplierTipo } from '../types/fornecedor.types';
import {
  useCreateFornecedorMutation,
  useUpdateFornecedorMutation,
} from './useFornecedoresMutations';
import { useFornecedorModal } from './useFornecedorModal';

const DEFAULT_FORM_VALUES: FornecedorFormData = {
  tipo: 'produto',
  nome: '',
  cnpj: '',
  cpf: '',
  nome_fantasia: '',
  ie: '',
  telefone: '',
  celular: '',
  email: '',
  representante: '',
  veiculo: '',
  placa: '',
  observacao: '',
  banco: '',
  agencia: '',
  conta: '',
  tipo_conta: '',
  pix: '',
  endereco_id: null,
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  cidade: '',
  estado: '',
  cep: '',
};

const unmask = (v: string) => v.replace(/\D/g, '');

export interface FornecedorFormContext {
  tipo: Ref<SupplierTipo>;
  nome: Ref<string>;
  cnpj: Ref<string>;
  cpf: Ref<string>;
  nome_fantasia: Ref<string>;
  ie: Ref<string>;
  telefone: Ref<string>;
  celular: Ref<string>;
  email: Ref<string>;
  representante: Ref<string>;
  veiculo: Ref<string>;
  placa: Ref<string>;
  observacao: Ref<string>;
  banco: Ref<string>;
  agencia: Ref<string>;
  conta: Ref<string>;
  tipo_conta: Ref<string>;
  pix: Ref<string>;
  endereco_id: Ref<number | null>;
  logradouro: Ref<string>;
  numero: Ref<string>;
  complemento: Ref<string>;
  bairro: Ref<string>;
  cidade: Ref<string>;
  estado: Ref<string>;
  cep: Ref<string>;
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
  const { selectedFornecedor, selectedTipo, isCreateMode, closeModal } = useFornecedorModal();
  const { handleSubmit, defineField, setValues, resetForm, submitCount, errors } =
    useForm<FornecedorFormData>({
      validationSchema: fornecedorFormValidationSchema,
      initialValues: { ...DEFAULT_FORM_VALUES },
    });

  const createMutation = useCreateFornecedorMutation();
  const updateMutation = useUpdateFornecedorMutation();
  const apiError = ref<string | null>(null);

  const [tipo] = defineField('tipo');
  const [nome] = defineField('nome');
  const [cnpj] = defineField('cnpj');
  const [cpf] = defineField('cpf');
  const [nome_fantasia] = defineField('nome_fantasia');
  const [ie] = defineField('ie');
  const [telefone] = defineField('telefone');
  const [celular] = defineField('celular');
  const [email] = defineField('email');
  const [representante] = defineField('representante');
  const [veiculo] = defineField('veiculo');
  const [placa] = defineField('placa');
  const [observacao] = defineField('observacao');
  const [banco] = defineField('banco');
  const [agencia] = defineField('agencia');
  const [conta] = defineField('conta');
  const [tipo_conta] = defineField('tipo_conta');
  const [pix] = defineField('pix');
  const [endereco_id] = defineField('endereco_id');
  const [logradouro] = defineField('logradouro');
  const [numero] = defineField('numero');
  const [complemento] = defineField('complemento');
  const [bairro] = defineField('bairro');
  const [cidade] = defineField('cidade');
  const [estado] = defineField('estado');
  const [cep] = defineField('cep');

  function maskCnpj(value: string): string {
    const digits = value.replace(/\D/g, '').slice(0, 14);
    return digits
      .replace(/^(\d{2})(\d)/, '$1.$2')
      .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
      .replace(/\.(\d{3})(\d)/, '.$1/$2')
      .replace(/(\d{4})(\d)/, '$1-$2');
  }

  function maskCpf(value: string): string {
    const digits = value.replace(/\D/g, '').slice(0, 11);
    return digits
      .replace(/^(\d{3})(\d)/, '$1.$2')
      .replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
      .replace(/\.(\d{3})(\d)/, '.$1-$2');
  }

  function populateForm() {
    const tipoValue = selectedFornecedor.value
      ? ((selectedFornecedor.value.tipo as SupplierTipo) || 'produto')
      : (selectedTipo.value ?? 'produto');

    if (!selectedFornecedor.value) {
      resetForm({ values: { ...DEFAULT_FORM_VALUES, tipo: tipoValue } });
      return;
    }

    const f = selectedFornecedor.value;
    const enderecoPrincipal = f.endereco?.[0] ?? null;
    setValues({
      tipo: tipoValue,
      nome: f.nome ?? '',
      cnpj: f.cnpj ? maskCnpj(f.cnpj) : '',
      cpf: f.cpf ? maskCpf(f.cpf) : '',
      nome_fantasia: f.nome_fantasia ?? '',
      ie: f.ie ?? '',
      telefone: f.telefone ?? '',
      celular: f.celular ?? '',
      email: f.email ?? '',
      representante: f.representante ?? '',
      veiculo: f.veiculo ?? '',
      placa: f.placa ?? '',
      observacao: f.observacao ?? '',
      banco: f.banco ?? '',
      agencia: f.agencia ?? '',
      conta: f.conta ?? '',
      tipo_conta: f.tipo_conta ?? '',
      pix: f.pix ?? '',
      endereco_id: enderecoPrincipal?.id ?? null,
      logradouro: enderecoPrincipal?.logradouro ?? '',
      numero: enderecoPrincipal?.numero ?? '',
      complemento: enderecoPrincipal?.complemento ?? '',
      bairro: enderecoPrincipal?.bairro ?? '',
      cidade: enderecoPrincipal?.cidade ?? '',
      estado: enderecoPrincipal?.estado ?? '',
      cep: enderecoPrincipal?.cep ?? '',
    });
  }

  watch([selectedFornecedor, selectedTipo], populateForm, { immediate: true });

  const onSubmit = handleSubmit(async (formData) => {
    apiError.value = null;

    const isEntregador = formData.tipo === 'entregador';

    // Monta o endereço se os campos obrigatórios estiverem preenchidos
    const temEndereco = !!(formData.logradouro?.trim() && formData.cep?.trim());
    const enderecoPayload = temEndereco
      ? [
          {
            ...(formData.endereco_id ? { id: formData.endereco_id } : {}),
            logradouro: formData.logradouro!.trim(),
            numero: formData.numero?.trim() || 'S/N',
            complemento: formData.complemento?.trim() || undefined,
            bairro: formData.bairro?.trim() || '',
            cidade: formData.cidade?.trim() || '',
            estado: formData.estado || undefined,
            cep: unmask(formData.cep!),
          },
        ]
      : undefined;

    const payload = {
      tipo: formData.tipo,
      nome: formData.nome.trim(),
      cnpj: isEntregador ? undefined : unmask(formData.cnpj ?? '') || undefined,
      cpf: isEntregador ? unmask(formData.cpf ?? '') || undefined : undefined,
      nome_fantasia: isEntregador ? undefined : formData.nome_fantasia?.trim() || undefined,
      ie: isEntregador ? undefined : formData.ie?.trim() || undefined,
      telefone: formData.telefone ? unmask(formData.telefone) || undefined : undefined,
      celular: formData.celular ? unmask(formData.celular) || undefined : undefined,
      email: formData.email?.trim() || undefined,
      representante: isEntregador ? undefined : formData.representante?.trim() || undefined,
      veiculo: isEntregador ? formData.veiculo?.trim() || undefined : undefined,
      placa: isEntregador ? formData.placa?.trim() || undefined : undefined,
      observacao: formData.observacao?.trim() || undefined,
      banco: formData.banco?.trim() || undefined,
      agencia: formData.agencia?.trim() || undefined,
      conta: formData.conta?.trim() || undefined,
      tipo_conta: formData.tipo_conta || undefined,
      pix: formData.pix?.trim() || undefined,
      endereco: enderecoPayload,
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
    tipo: tipo as Ref<SupplierTipo>,
    nome,
    cnpj,
    cpf,
    nome_fantasia,
    ie,
    telefone,
    celular,
    email,
    representante,
    veiculo,
    placa,
    observacao,
    banco,
    agencia,
    conta,
    tipo_conta,
    pix,
    endereco_id,
    logradouro,
    numero,
    complemento,
    bairro,
    cidade,
    estado,
    cep,
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
