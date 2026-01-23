// Vue - funcoes reativas do framework
import { ref, computed, watch } from 'vue';

// Composables e utilitarios
import { getErrorMessage } from '@/shared/utils/error.utils';
import { unmaskCep, unmaskPhone, unmaskDocument } from '@/shared/utils/unmask.utils';

// Shared Actions
import { useClienteActions } from '@/shared/composables/cliente/useClienteActions';

// Tipos TypeScript
import type {
  ClientePFCreate,
  ClientePJCreate,
  ClientePFUpdate,
  ClientePJUpdate,
  TipoCliente,
  Cliente,
  Gender,
  State,
} from '../types/clientes.types';
import { GENEROS } from '../types/clientes.types';

// ===========================================================================
// CONSTANTES UI
// ===========================================================================

export const TABS_CLIENTE = [
  { id: 'PF', label: 'Pessoa Física' },
  { id: 'PJ', label: 'Pessoa Jurídica' },
];

export const GENERO_OPTIONS = GENEROS.map((g) => ({ value: g.value, label: g.label }));

// ===========================================================================
// INTERFACES INTERNAS
// ===========================================================================

interface EnderecoForm {
  id?: number;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  estado: string;
}

interface CommonForm {
  email: string;
  celular: string;
  telefone: string;
  observacoes: string;
}

interface PFSpecificForm {
  nome: string;
  cpf: string;
  rg: string;
  genero: Gender | '';
  data_nascimento: string;
}

interface PJSpecificForm {
  razao_social: string;
  nome_fantasia: string;
  cnpj: string;
  ie: string;
  im: string;
  regime_tributario: string;
  responsavel: string;
}

// ===========================================================================
// COMPOSABLE
// ===========================================================================

interface UseClientFormProps {
  cliente?: Cliente | null;
}

type UseClientFormEmit = (e: 'close') => void;

export function useClientForm(props: UseClientFormProps, emit: UseClientFormEmit) {
  // Importa acoes compartilhadas
  const { createPFMutation, createPJMutation, updateMutation } = useClienteActions();

  // ===========================================================================
  // STATE
  // ===========================================================================

  const tipoCliente = ref<TipoCliente>('PF');
  const apiError = ref<string | null>(null);

  const formCommon = ref<CommonForm>({
    email: '',
    celular: '',
    telefone: '',
    observacoes: '',
  });

  const formPF = ref<PFSpecificForm>({
    nome: '',
    cpf: '',
    rg: '',
    genero: '',
    data_nascimento: '',
  });

  const formPJ = ref<PJSpecificForm>({
    razao_social: '',
    nome_fantasia: '',
    cnpj: '',
    ie: '',
    im: '',
    regime_tributario: '',
    responsavel: '',
  });

  const enderecos = ref<EnderecoForm[]>([]);

  // ===========================================================================
  // COMPUTED
  // ===========================================================================

  const isEditMode = computed(() => !!props.cliente);

  const modalTitle = computed(() => {
    if (isEditMode.value) {
      return tipoCliente.value === 'PF' ? 'Editar Cliente PF' : 'Editar Cliente PJ';
    }
    return tipoCliente.value === 'PF' ? 'Novo Cliente PF' : 'Novo Cliente PJ';
  });

  const modalSubtitle = computed(() => {
    if (isEditMode.value && props.cliente) {
      if (props.cliente.tipo === 'PF') {
        return props.cliente.nome;
      }
      return props.cliente.nome_fantasia || props.cliente.razao_social;
    }
    return 'Preencha os dados do cliente';
  });

  const submitButtonText = computed(() => {
    return isEditMode.value ? 'Atualizar' : 'Cadastrar';
  });

  const isPending = computed(() =>
    createPFMutation.isPending.value ||
    createPJMutation.isPending.value ||
    updateMutation.isPending.value
  );

  // ===========================================================================
  // HELPERS
  // ===========================================================================

  function prepareEnderecos(addrs: EnderecoForm[], isUpdate: boolean) {
    if (addrs.length === 0) return undefined;

    return addrs.map((addr) => ({
      ...(isUpdate && addr.id ? { id: addr.id } : {}),
      cep: unmaskCep(addr.cep),
      logradouro: addr.logradouro,
      numero: addr.numero,
      complemento: addr.complemento || undefined,
      bairro: addr.bairro,
      cidade: addr.cidade,
      estado: addr.estado as State,
    }));
  }

  function prepareDataForApi(
    tipo: TipoCliente,
    common: CommonForm,
    specific: PFSpecificForm | PJSpecificForm,
    addrs: EnderecoForm[],
    isUpdate: boolean
  ): ClientePFCreate | ClientePJCreate | ClientePFUpdate | ClientePJUpdate {
    const enderecoData = prepareEnderecos(addrs, isUpdate);

    const baseData = {
      email: common.email || undefined,
      celular: unmaskPhone(common.celular) || undefined,
      telefone: unmaskPhone(common.telefone) || undefined,
      observacoes: common.observacoes || undefined,
      endereco: enderecoData,
    };

    if (tipo === 'PF') {
      const pfSpecific = specific as PFSpecificForm;
      return {
        tipo: 'PF' as const,
        nome: pfSpecific.nome,
        cpf: unmaskDocument(pfSpecific.cpf) || undefined,
        rg: pfSpecific.rg || undefined,
        genero: pfSpecific.genero || undefined,
        data_nascimento: pfSpecific.data_nascimento || undefined,
        ...baseData,
      };
    } else {
      const pjSpecific = specific as PJSpecificForm;
      return {
        tipo: 'PJ' as const,
        razao_social: pjSpecific.razao_social,
        nome_fantasia: pjSpecific.nome_fantasia || undefined,
        cnpj: unmaskDocument(pjSpecific.cnpj) || undefined,
        ie: pjSpecific.ie || undefined,
        im: pjSpecific.im || undefined,
        regime_tributario: pjSpecific.regime_tributario || undefined,
        responsavel: pjSpecific.responsavel || undefined,
        ...baseData,
      };
    }
  }

  function populateForm(cliente: Cliente) {
    tipoCliente.value = cliente.tipo;

    formCommon.value = {
      email: cliente.email || '',
      celular: cliente.celular || '',
      telefone: cliente.telefone || '',
      observacoes: cliente.observacoes || '',
    };

    if (cliente.tipo === 'PF') {
      formPF.value = {
        nome: cliente.nome,
        cpf: cliente.cpf || '',
        rg: cliente.rg || '',
        genero: cliente.genero || '',
        data_nascimento: cliente.data_nascimento || '',
      };
    } else {
      formPJ.value = {
        razao_social: cliente.razao_social,
        nome_fantasia: cliente.nome_fantasia || '',
        cnpj: cliente.cnpj || '',
        ie: cliente.ie || '',
        im: cliente.im || '',
        regime_tributario: cliente.regime_tributario || '',
        responsavel: cliente.responsavel || '',
      };
    }

    // Popula enderecos
    if (cliente.endereco && cliente.endereco.length > 0) {
      enderecos.value = cliente.endereco.map((end) => ({
        id: end.id,
        cep: end.cep || '',
        logradouro: end.logradouro || '',
        numero: end.numero || '',
        complemento: end.complemento || '',
        bairro: end.bairro || '',
        cidade: end.cidade || '',
        estado: end.estado || '',
      }));
    }
  }

  function resetForms() {
    formCommon.value = { email: '', celular: '', telefone: '', observacoes: '' };
    formPF.value = { nome: '', cpf: '', rg: '', genero: '', data_nascimento: '' };
    formPJ.value = {
      razao_social: '',
      nome_fantasia: '',
      cnpj: '',
      ie: '',
      im: '',
      regime_tributario: '',
      responsavel: '',
    };
    enderecos.value = [];
  }

  // ===========================================================================
  // HANDLERS
  // ===========================================================================

  function handleError(error: any) {
    apiError.value = getErrorMessage(error, 'Erro ao salvar cliente') as string;
  }

  function handleSuccess() {
    handleClose();
  }

  async function handleSubmit() {
    apiError.value = null;
    const isUpdate = isEditMode.value && !!props.cliente;
    const specific = tipoCliente.value === 'PF' ? formPF.value : formPJ.value;

    // Validacao basica
    if (tipoCliente.value === 'PF' && !formPF.value.nome.trim()) {
      apiError.value = 'O nome é obrigatório';
      return;
    }
    if (tipoCliente.value === 'PJ' && !formPJ.value.razao_social.trim()) {
      apiError.value = 'A razão social é obrigatória';
      return;
    }

    const payload = prepareDataForApi(
      tipoCliente.value,
      formCommon.value,
      specific,
      enderecos.value,
      isUpdate
    );

    try {
      if (isUpdate && props.cliente) {
        await updateMutation.mutateAsync({
          id: props.cliente.id,
          data: payload as ClientePFUpdate | ClientePJUpdate
        });
      } else {
        if (tipoCliente.value === 'PF') {
          await createPFMutation.mutateAsync(payload as ClientePFCreate);
        } else {
          await createPJMutation.mutateAsync(payload as ClientePJCreate);
        }
      }
      handleSuccess();
    } catch (error) {
      handleError(error);
    }
  }

  function handleClose() {
    resetForms();
    apiError.value = null;
    tipoCliente.value = 'PF';
    emit('close');
  }

  // ===========================================================================
  // WATCHERS
  // ===========================================================================

  watch(
    () => props.cliente,
    (newCliente) => {
      if (newCliente) {
        populateForm(newCliente);
      } else {
        resetForms();
        tipoCliente.value = 'PF';
      }
    },
    { immediate: true }
  );

  // ===========================================================================
  // RETURN
  // ===========================================================================

  return {
    // State
    formCommon,
    formPF,
    formPJ,
    enderecos,
    tipoCliente,
    apiError,

    // Computed
    isEditMode,
    isPending,
    modalTitle,
    modalSubtitle,
    submitButtonText,

    // Actions
    handleSubmit,
    handleClose,
  };
}
