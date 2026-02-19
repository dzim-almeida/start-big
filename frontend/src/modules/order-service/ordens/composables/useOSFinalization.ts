import { ref, computed, watch } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import {
  ORDENS_SERVICO_QUERY_KEY,
  ORDENS_SERVICO_STATS_QUERY_KEY,
  FORMAS_PAGAMENTO_QUERY_KEY,
} from '../../shared/constants/queryKeys';
import type { AxiosError } from 'axios';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { ordemServicoService } from '../services/ordemServico.service';
import type {
  OrdemServicoRead,
  OrdemServicoFinalizar,
  FormaPagamentoRead,
  OSPagamentoCreate,
} from '../types/ordemServico.types';
import type { ApiError } from '@/shared/types/axios.types';
import { formatCurrency } from '@/shared/utils/finance';
import { z } from 'zod';

export interface UseOSFinalizationProps {
  ordemServico: OrdemServicoRead | null;
  valorTotal?: number;
  isOpen: boolean;
}

export interface UseOSFinalizationEmits {
  (e: 'close'): void;
  (e: 'finalized', payload: { os: OrdemServicoRead; shouldPrint: boolean }): void;
}

export function useOSFinalization(props: UseOSFinalizationProps, emit: UseOSFinalizationEmits) {
  const toast = useToast();
  const queryClient = useQueryClient();

  const { data: formasPagamento } = useQuery({
    queryKey: [FORMAS_PAGAMENTO_QUERY_KEY],
    queryFn: () => ordemServicoService.getFormasPagamento(),
    staleTime: 1000 * 60 * 60,
  });

  const apiError = ref<string | null>(null);
  const confirmacao = ref(false);
  const shouldPrint = ref(true);

  const form = ref({
    solucao: '',
    observacoes: '',
    garantia_dias: 90,
    desconto: '0,00',
  });

  const errors = ref({
    solucao: '',
  });

  const schema = z.object({
    solucao: z.string().min(3, "A solução aplicada deve ter pelo menos 3 caracteres."),
  });

  function validate() {
    const result = schema.safeParse(form.value);
    if (!result.success) {
      const formatted = result.error.format();
      errors.value.solucao = formatted.solucao?._errors[0] || '';
      return false;
    }
    errors.value.solucao = '';
    return true;
  }

  const addedPayments = ref<OSPagamentoCreate[]>([]);
  const currentPaymentMethod = ref<FormaPagamentoRead | null>(null);
  const paymentDetails = ref({
    valor: '0,00',
    parcelas: 1,
    bandeira: '',
  });
  const showPaymentDetails = ref(false);

  const subtotalItens = computed(() => {
    if (!props.ordemServico?.itens) return 0;
    return props.ordemServico.itens.reduce((acc, item) => acc + item.valor_total, 0);
  });

  const descontoCents = computed(() => {
    return Math.round(parseFloat(form.value.desconto.replace(/\./g, '').replace(',', '.')) * 100);
  });

  const valorTotalFinal = computed(() => {
    const base = subtotalItens.value > 0 ? subtotalItens.value : (props.valorTotal || 0);
    return Math.max(0, base - descontoCents.value);
  });

  const totalPago = computed(() => addedPayments.value.reduce((acc, p) => acc + p.valor, 0));
  const restante = computed(() => Math.max(0, valorTotalFinal.value - totalPago.value));
  const troco = computed(() => Math.max(0, totalPago.value - valorTotalFinal.value));

  const valorTotalDisplay = computed(() => formatCurrency(valorTotalFinal.value));

  const canSubmit = computed(() => {
    const isSolucaoValid = form.value.solucao.trim().length >= 3;
    return (
      isSolucaoValid &&
      confirmacao.value &&
      totalPago.value >= valorTotalFinal.value
    );
  });

  function handleAddPaymentClick(method: FormaPagamentoRead) {
    currentPaymentMethod.value = method;
    paymentDetails.value = {
      valor: (restante.value / 100).toFixed(2).replace('.', ','),
      parcelas: 1,
      bandeira: '',
    };
    showPaymentDetails.value = true;
  }

  function confirmAddPayment() {
    if (!currentPaymentMethod.value) return;

    const valorCents = Math.round(parseFloat(paymentDetails.value.valor.replace(/\./g, '').replace(',', '.')) * 100);

    if (valorCents <= 0) {
      toast.error('Valor deve ser maior que zero');
      return;
    }

    addedPayments.value.push({
      forma_pagamento_id: currentPaymentMethod.value.id,
      valor: valorCents,
      parcelas: paymentDetails.value.parcelas,
      bandeira_cartao: paymentDetails.value.bandeira || undefined,
      detalhes: {
        tipo: currentPaymentMethod.value.tipo,
        nome: currentPaymentMethod.value.nome,
      },
    });

    showPaymentDetails.value = false;
    currentPaymentMethod.value = null;
  }

  function removePayment(index: number) {
    addedPayments.value.splice(index, 1);
  }

  function handleDescontoInput(e: Event) {
    const target = e.target as HTMLInputElement;
    let value = target.value.replace(/\D/g, '');
    if (!value) value = '0';
    const floatVal = parseFloat(value) / 100;
    form.value.desconto = floatVal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  const finalizarMutation = useMutation<
    OrdemServicoRead,
    AxiosError<ApiError>,
    { id: number; data: OrdemServicoFinalizar }
  >({
    mutationFn: ({ id, data }) => ordemServicoService.finalizar(id, data),
    onSuccess: (data) => {
      toast.success('Ordem de Serviço finalizada com sucesso!');
      queryClient.invalidateQueries({ queryKey: [ORDENS_SERVICO_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [ORDENS_SERVICO_STATS_QUERY_KEY] });
      emit('finalized', { os: data, shouldPrint: shouldPrint.value });
      handleClose();
    },
    onError: (error) => {
      apiError.value = getErrorMessage(error, 'Erro ao finalizar OS') as string;
    },
  });

  const isPending = computed(() => finalizarMutation.isPending.value);

  function resetForm() {
    form.value = {
      solucao: '',
      observacoes: '',
      garantia_dias: 90,
      desconto: '0,00',
    };
    addedPayments.value = [];
    confirmacao.value = false;
    apiError.value = null;
  }

  function populateForm(os: OrdemServicoRead) {
    form.value = {
      solucao: os.solucao || '',
      observacoes: os.observacoes || '',
      garantia_dias: 90,
      desconto: (os.desconto / 100).toFixed(2).replace('.', ','),
    };
    addedPayments.value = [];
    confirmacao.value = false;
    apiError.value = null;
  }

  function handleClose() {
    resetForm();
    showPaymentDetails.value = false;
    emit('close');
  }

  function handleSubmit() {
    if (!validate()) {
      toast.error('Verifique os campos obrigatórios');
      return;
    }
    if (!props.ordemServico || !canSubmit.value) return;

    apiError.value = null;

    let observacoesFinais = form.value.observacoes || '';
    if (form.value.garantia_dias > 0) {
      const garantiaText = `Garantia de ${form.value.garantia_dias} dias a partir desta data.`;
      observacoesFinais = observacoesFinais
        ? `${observacoesFinais}\n\n${garantiaText}`
        : garantiaText;
    }

    const data: OrdemServicoFinalizar = {
      solucao: form.value.solucao,
      observacoes: observacoesFinais || undefined,
      pagamentos: addedPayments.value.map(p => ({
        forma_pagamento_id: p.forma_pagamento_id,
        valor: p.valor,
        parcelas: p.parcelas,
        bandeira_cartao: p.bandeira_cartao,
        detalhes: p.detalhes,
      })),
      desconto: descontoCents.value,
    };

    finalizarMutation.mutate({ id: props.ordemServico.id, data });
  }

  watch(
    () => props.isOpen,
    (isOpen) => {
      if (isOpen) {
        if (props.ordemServico) {
          populateForm(props.ordemServico);
        } else {
          resetForm();
        }
      }
    }
  );

  return {
    form,
    errors,
    confirmacao,
    shouldPrint,
    apiError,
    formasPagamento,
    addedPayments,
    currentPaymentMethod,
    paymentDetails,
    showPaymentDetails,
    subtotalItens,
    valorTotalFinal,
    valorTotalDisplay,
    totalPago,
    restante,
    troco,
    canSubmit,
    isPending,
    handleAddPaymentClick,
    confirmAddPayment,
    removePayment,
    handleDescontoInput,
    handleClose,
    handleSubmit,
  };
}
