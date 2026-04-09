import { computed, watch } from 'vue';
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import type {
  OrdemServicoCreate,
  OrdemServicoRead,
  OrdemServicoUpdate,
  OrdemServicoItemCreate,
  OrdemServicoPrioridade,
} from '../types/ordemServico.types';
import { OS_STATUS_OPTIONS, OS_PRIORIDADE_OPTIONS } from '../constants';
import type { ApiError } from '@/shared/types/axios.types';

import { parseCurrencyToCents, formatCurrency } from '@/shared/utils/finance';
import { ordemServicoService } from '../services/ordemServico.service';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';

import { useOSFormState, type OSItemForm } from './useOSFormState';
import { useOSFormQueries } from './useOSFormQueries';
import { useOSFinancials } from './useOSFinancials';

// Schemas Zod para validacao
import {
  OSFormDataSchema,
  OrdemServicoCreateSchema,
  OrdemServicoUpdateSchema,
} from '../schemas/ordemServico.schema';

export interface OSFormProps {
  isOpen: boolean;
  ordemServico?: OrdemServicoRead | null;
  selectedCliente?: { id: number; nome?: string; razao_social?: string } | null;
}

export interface OSFormEmits {
  (e: 'close'): void;
  (e: 'saved', data: OrdemServicoRead): void;
  (e: 'changeCliente'): void;
}

export function useOSForm(
  props: OSFormProps,
  emit: OSFormEmits,
  options?: { onSuccess?: (data: OrdemServicoRead) => void }
) {
  const toast = useToast();
  const queryClient = useQueryClient();

  // Composables especializados
  const {
    form,
    itens,
    apiError,
    hasAttemptedSubmit,
    fieldErrors,
    resetForm,
    populateForm,
    removeItem,
    addItem,
    setError,
    clearError,
    setFieldErrors,
    clearFieldErrors,
  } = useOSFormState();

  const {
    servicosOptions,
    produtosOptions,
    funcionariosOptions,
    isLoadingServicos,
    isLoadingProdutos,
  } = useOSFormQueries(() => props.isOpen);

  const descontoRef = computed(() => form.value.desconto);
  const valorEntradaRef = computed(() => form.value.valor_entrada);
  const taxaEntregaRef = computed(() => form.value.taxa_entrega);

  const {
    subtotal,
    valorDesconto,
    valorTaxaEntrega,
    valorTotal,
  } = useOSFinancials(itens, descontoRef, valorEntradaRef, taxaEntregaRef);

  // Computed
  const isEditMode = computed(() => !!props.ordemServico?.id);

  const modalTitle = computed(() => {
    if (isEditMode.value) {
      return `Editar OS #${props.ordemServico?.numero || props.ordemServico?.id}`;
    }
    return 'Nova Ordem de Serviço';
  });

  const modalSubtitle = computed(() => {
    if (isEditMode.value) {
      return 'Atualize as informações da ordem de serviço';
    }
    return 'Preencha os dados do equipamento e serviço';
  });

  const prioridadeOptions = OS_PRIORIDADE_OPTIONS;
  const statusOptions = OS_STATUS_OPTIONS;

  const isPending = computed(() => {
    return createMutation.isPending.value || updateMutation.isPending.value || reopenMutation.isPending.value;
  });

  // Mutations
  const createMutation = useMutation<OrdemServicoRead, AxiosError<ApiError>, OrdemServicoCreate>({
    mutationFn: (data) => ordemServicoService.create(data),
    onSuccess: (data) => {
      toast.success('Ordem de Servico criada com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['ordens-servico'] });

      if (options?.onSuccess) {
        options.onSuccess(data);
      } else {
        emit('saved', data);
        handleClose();
      }
    },
    onError: (error) => {
      setError(getErrorMessage(error, 'Erro ao criar ordem de servico'));
    },
  });

  const updateMutation = useMutation<
    OrdemServicoRead,
    AxiosError<ApiError>,
    { id: number; data: OrdemServicoUpdate }
  >({
    mutationFn: ({ id, data }) => ordemServicoService.update(id, data),
    onSuccess: (data) => {
      toast.success('Ordem de Servico atualizada com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['ordens-servico'] });

      if (options?.onSuccess) {
        options.onSuccess(data);
      } else {
        emit('saved', data);
        handleClose();
      }
    },
    onError: (error) => {
      setError(getErrorMessage(error, 'Erro ao atualizar ordem de servico'));
    },
  });

  const reopenMutation = useMutation<OrdemServicoRead, AxiosError<ApiError>, number>({
    mutationFn: (id: number) => ordemServicoService.reabrir(id),
    onSuccess: (data) => {
      toast.success('Ordem de Servico reaberta com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['ordens-servico'] });
      emit('saved', data);
    },
    onError: (error) => {
      setError(getErrorMessage(error, 'Erro ao reabrir ordem de servico'));
    },
  });

  // Actions
  function handleClose() {
    resetForm();
    emit('close');
  }

  function handleChangeCliente() {
    emit('changeCliente');
  }

  function validateForm(): boolean {
    clearError();
    clearFieldErrors();
    hasAttemptedSubmit.value = true;

    // Validacao com Zod — coleta TODOS os erros por campo
    const result = OSFormDataSchema.safeParse(form.value);

    if (!result.success) {
      const errors: Record<string, string> = {};
      for (const err of result.error.errors) {
        const field = err.path.join('.');
        if (!errors[field]) errors[field] = err.message;
      }
      setFieldErrors(errors);

      const firstMsg = Object.values(errors)[0];
      setError(firstMsg);
      toast.warning(firstMsg);
      return false;
    }

    // Validacao de cliente (nao faz parte do form state)
    const clienteId = props.selectedCliente?.id || props.ordemServico?.cliente_id;
    if (!clienteId) {
      const msg = 'Selecione um cliente';
      setError(msg);
      toast.warning(msg);
      return false;
    }

    return true;
  }

  function buildPayload(): { create?: OrdemServicoCreate; update?: OrdemServicoUpdate } {
    const clienteId = props.selectedCliente?.id || props.ordemServico?.cliente_id;

    const itensToSend: OrdemServicoItemCreate[] = itens.value
      .filter((item: OSItemForm) => item.descricao.trim())
      .map((item: OSItemForm) => ({
        servico_id: item.servico_id ? Number(item.servico_id) : undefined,
        descricao: item.descricao,
        quantidade: item.quantidade,
        valor_unitario: item.valor_unitario,
      }));

    const funcionarioId = form.value.funcionario_id ? Number(form.value.funcionario_id) : undefined;
    const prioridade = form.value.prioridade as OrdemServicoPrioridade;
    const descontoValue = parseCurrencyToCents(form.value.desconto);
    const valorEntradaValue = parseCurrencyToCents(form.value.valor_entrada);
    const taxaEntregaValue = parseCurrencyToCents(form.value.taxa_entrega);

    if (isEditMode.value) {
      return {
        update: {
          equipamento: form.value.equipamento,
          marca: form.value.marca || undefined,
          modelo: form.value.modelo || undefined,
          numero_serie: form.value.numero_serie || undefined,
          imei: form.value.imei || undefined,
          cor: form.value.cor || undefined,
          senha_aparelho: form.value.senha_aparelho || undefined,
          acessorios: form.value.acessorios || undefined,
          defeito_relatado: form.value.defeito_relatado,
          diagnostico: form.value.diagnostico || undefined,
          solucao: form.value.solucao || undefined,
          observacoes: form.value.observacoes || undefined,
          prioridade,
          status: form.value.status,
          funcionario_id: funcionarioId,
          data_previsao: form.value.data_previsao || undefined,
          data_finalizacao: form.value.data_finalizacao || undefined,
          desconto: descontoValue || undefined,
          valor_entrada: valorEntradaValue || undefined,
          taxa_entrega: taxaEntregaValue || undefined,
          forma_pagamento: form.value.forma_pagamento || undefined,
          garantia: form.value.garantia || undefined,
          itens: itensToSend,
        },
      };
    }

    return {
      create: {
        cliente_id: clienteId!,
        equipamento: form.value.equipamento,
        marca: form.value.marca || undefined,
        modelo: form.value.modelo || undefined,
        numero_serie: form.value.numero_serie || undefined,
        imei: form.value.imei || undefined,
        cor: form.value.cor || undefined,
        acessorios: form.value.acessorios || undefined,
        senha_aparelho: form.value.senha_aparelho || undefined,
        condicoes_aparelho: form.value.condicoes_aparelho || undefined,
        defeito_relatado: form.value.defeito_relatado,
        diagnostico: form.value.diagnostico || undefined,
        observacoes: form.value.observacoes || undefined,
        prioridade,
        funcionario_id: funcionarioId,
        data_previsao: form.value.data_previsao || undefined,
        desconto: descontoValue || undefined,
        valor_entrada: valorEntradaValue || undefined,
        taxa_entrega: taxaEntregaValue || undefined,
        forma_pagamento: form.value.forma_pagamento || undefined,
        garantia: form.value.garantia || undefined,
        itens: itensToSend.length > 0 ? itensToSend : undefined,
      },
    };
  }

  function handleSubmit() {
    if (!validateForm()) return;

    const payload = buildPayload();

    if (isEditMode.value && props.ordemServico && payload.update) {
      updateMutation.mutate({ id: props.ordemServico.id, data: payload.update });
    } else if (payload.create) {
      createMutation.mutate(payload.create);
    }
  }

  function reopenOS() {
    if (!props.ordemServico?.id) return;
    reopenMutation.mutate(props.ordemServico.id);
  }

  // Watchers
  watch(() => props.isOpen, (isOpen) => {
    if (isOpen) {
      if (props.ordemServico) {
        populateForm(props.ordemServico);
      } else {
        resetForm();
      }
    }
  });

  return {
    form,
    itens,
    apiError,
    hasAttemptedSubmit,
    fieldErrors,
    isEditMode,
    modalTitle,
    modalSubtitle,
    servicosOptions,
    produtosOptions,
    funcionariosOptions,
    prioridadeOptions,
    statusOptions,
    subtotal,
    valorDesconto,
    valorTaxaEntrega,
    valorTotal,
    isPending,
    isLoadingServicos,
    isLoadingProdutos,
    handleClose,
    handleChangeCliente,
    handleSubmit,
    addItem,
    removeItem,
    formatCurrency,
    reopenOS,
  };
}

export type { OSItemForm } from './useOSFormState';
