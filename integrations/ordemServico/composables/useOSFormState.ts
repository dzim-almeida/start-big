import { ref, watch } from 'vue';
import type {
  OrdemServicoRead,
  OrdemServicoPrioridade,
  OrdemServicoStatus,
} from '../types/ordemServico.types';
import { formatCentsToInput } from '@/shared/utils/finance';
import { DEFAULT_OS_PRIORIDADE, DEFAULT_OS_STATUS } from '../constants';

export interface OSFormData {
  equipamento: string;
  marca: string;
  modelo: string;
  numero_serie: string;
  imei: string;
  cor: string;
  acessorios: string;
  senha_aparelho: string;
  condicoes_aparelho: string;
  defeito_relatado: string;
  diagnostico: string;
  solucao: string;
  observacoes: string;
  prioridade: OrdemServicoPrioridade;
  status: OrdemServicoStatus;
  funcionario_id: string;
  data_previsao: string;
  valor_orcamento: string;
  forma_pagamento: string;
  garantia: string;
  desconto: string;
  valor_entrada: string;
  data_finalizacao: string | undefined;
}

export interface OSItemForm {
  servico_id?: string;
  descricao: string;
  quantidade: number;
  valor_unitario: number;
}

const DEFAULT_FORM: OSFormData = {
  equipamento: '',
  marca: '',
  modelo: '',
  numero_serie: '',
  imei: '',
  cor: '',
  acessorios: '',
  senha_aparelho: '',
  condicoes_aparelho: '',
  defeito_relatado: '',
  diagnostico: '',
  solucao: '',
  observacoes: '',
  prioridade: DEFAULT_OS_PRIORIDADE,
  status: DEFAULT_OS_STATUS,
  funcionario_id: '',
  data_previsao: '',
  valor_orcamento: '',
  forma_pagamento: '',
  garantia: '',
  desconto: '',
  valor_entrada: '',
  data_finalizacao: '',
};

function formatDateForInput(date: string | Date | undefined): string {
  if (!date) return '';
  if (date instanceof Date) {
    return date.toISOString().split('T')[0];
  }
  return date.split('T')[0];
}

export function useOSFormState() {
  const form = ref<OSFormData>({ ...DEFAULT_FORM });
  const itens = ref<OSItemForm[]>([]);
  const apiError = ref<string | null>(null);

  function resetForm() {
    form.value = { ...DEFAULT_FORM };
    itens.value = [];
    apiError.value = null;
  }

  function populateForm(os: OrdemServicoRead) {
    form.value = {
      equipamento: os.equipamento || '',
      marca: os.marca || '',
      modelo: os.modelo || '',
      numero_serie: os.numero_serie || '',
      imei: os.imei || '',
      cor: os.cor || '',
      acessorios: os.acessorios || '',
      senha_aparelho: os.senha_aparelho || '',
      condicoes_aparelho: os.condicoes_aparelho || '',
      defeito_relatado: os.defeito_relatado || '',
      diagnostico: os.diagnostico || '',
      solucao: os.solucao || '',
      observacoes: os.observacoes || '',
      prioridade: os.prioridade,
      status: os.status,
      funcionario_id: os.funcionario_id ? String(os.funcionario_id) : '',
      data_previsao: formatDateForInput(os.data_previsao),
      valor_orcamento: '',
      forma_pagamento: os.forma_pagamento || '',
      garantia: os.garantia || '',
      desconto: formatCentsToInput(os.desconto || 0),
      valor_entrada: formatCentsToInput(os.valor_entrada || 0),
      data_finalizacao: formatDateForInput(os.data_finalizacao),
    };

    itens.value = os.itens?.map(item => ({
      servico_id: item.servico_id ? String(item.servico_id) : undefined,
      descricao: item.descricao,
      quantidade: item.quantidade,
      valor_unitario: item.valor_unitario,
    })) || [];
  }

  function removeItem(index: number) {
    itens.value.splice(index, 1);
  }

  function addItem(item: OSItemForm) {
    itens.value.push(item);
  }

  function updateItem(index: number, item: OSItemForm) {
    itens.value[index] = item;
  }

  function setError(error: string | null) {
    apiError.value = error;
  }

  function clearError() {
    apiError.value = null;
  }

  return {
    form,
    itens,
    apiError,
    resetForm,
    populateForm,
    removeItem,
    addItem,
    updateItem,
    setError,
    clearError,
  };
}
