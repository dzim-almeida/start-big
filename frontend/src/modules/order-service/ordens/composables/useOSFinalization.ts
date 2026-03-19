import { ref, computed, watch } from 'vue';
import type { Ref } from 'vue';
import { formatCurrency } from '@/shared/utils/finance';
import type { OrdemServicoRead } from '../types/ordemServico.types';
import { useReadyOrderServiceMutation } from './request/useOrderServiceUpdate.mutate';

interface Props {
  isOpen: boolean;
  ordemServico: OrdemServicoRead | null;
  valorTotal?: number;
}

interface FormaPagamento {
  id: number;
  tipo: string;
  nome: string;
  permite_parcelamento: boolean;
}

interface AddedPayment {
  detalhes: FormaPagamento;
  valor: number;
  parcelas: number;
}

const formasPagamento: FormaPagamento[] = [
  { id: 1, tipo: 'DINHEIRO', nome: 'Dinheiro', permite_parcelamento: false },
  { id: 2, tipo: 'PIX', nome: 'Pix', permite_parcelamento: false },
  { id: 3, tipo: 'CARTAO_CREDITO', nome: 'Cartão de Crédito', permite_parcelamento: true },
  { id: 4, tipo: 'CARTAO_DEBITO', nome: 'Cartão de Débito', permite_parcelamento: false },
  { id: 5, tipo: 'BOLETO', nome: 'Boleto', permite_parcelamento: false },
];

export function useOSFinalization(
  props: Props,
  emit: (event: string, ...args: any[]) => void,
) {
  const readyMutation = useReadyOrderServiceMutation();

  const form = ref({
    solucao: '',
    observacoes: '',
    desconto: '0',
    garantia_dias: 0,
  });

  const errors = ref({
    solucao: '',
  });

  const confirmacao = ref(false);
  const apiError = ref<string | null>(null);

  const addedPayments = ref<AddedPayment[]>([]);
  const currentPaymentMethod = ref<FormaPagamento | null>(null);
  const paymentDetails = ref({ valor: 0, parcelas: 1 });
  const showPaymentDetails = ref(false);

  const subtotalItens = computed(() => {
    const itens = props.ordemServico?.itens ?? [];
    return itens.reduce((sum, item) => {
      const total = (item as any).valor_total ?? item.quantidade * item.valor_unitario;
      return sum + total;
    }, 0);
  });

  const descontoNum = computed(() => {
    const parsed = parseFloat(form.value.desconto);
    return isNaN(parsed) ? 0 : Math.round(parsed * 100);
  });

  const valorTotalComputed = computed(() => {
    const base = props.valorTotal ?? subtotalItens.value;
    return Math.max(0, base - descontoNum.value);
  });

  const valorTotalDisplay = computed(() => formatCurrency(valorTotalComputed.value));

  const totalPago = computed(() =>
    addedPayments.value.reduce((sum, p) => sum + p.valor, 0),
  );

  const restante = computed(() => Math.max(0, valorTotalComputed.value - totalPago.value));

  const troco = computed(() => Math.max(0, totalPago.value - valorTotalComputed.value));

  const canSubmit = computed(
    () => confirmacao.value && addedPayments.value.length > 0 && restante.value <= 0,
  );

  const isPending = computed(() => readyMutation.isPending.value);

  function handleAddPaymentClick(method: FormaPagamento) {
    currentPaymentMethod.value = method;
    paymentDetails.value = { valor: restante.value, parcelas: 1 };
    showPaymentDetails.value = true;
  }

  function confirmAddPayment() {
    if (!currentPaymentMethod.value) return;
    addedPayments.value.push({
      detalhes: currentPaymentMethod.value,
      valor: paymentDetails.value.valor,
      parcelas: paymentDetails.value.parcelas,
    });
    showPaymentDetails.value = false;
    currentPaymentMethod.value = null;
  }

  function removePayment(idx: number) {
    addedPayments.value.splice(idx, 1);
  }

  function handleDescontoInput() {
    // noop - desconto parsing handled via computed
  }

  function resetState() {
    form.value = { solucao: '', observacoes: '', desconto: '0', garantia_dias: 0 };
    errors.value = { solucao: '' };
    confirmacao.value = false;
    apiError.value = null;
    addedPayments.value = [];
    currentPaymentMethod.value = null;
    paymentDetails.value = { valor: 0, parcelas: 1 };
    showPaymentDetails.value = false;
  }

  function handleClose() {
    resetState();
    emit('close');
  }

  async function handleSubmit() {
    errors.value.solucao = '';
    if (!form.value.solucao || form.value.solucao.trim().length < 5) {
      errors.value.solucao = 'Descreva uma solução válida';
      return;
    }
    if (!props.ordemServico) return;

    const pagamentos = addedPayments.value.map((p) => ({
      forma_pagamento_id: p.detalhes.id,
      valor: p.valor,
      parcelas: p.parcelas,
    }));

    try {
      const os = await readyMutation.mutateAsync({
        osNumber: props.ordemServico.numero_os,
        readyOs: {
          solucao: form.value.solucao,
          observacoes: form.value.observacoes,
          desconto: descontoNum.value,
          pagamentos,
        },
      });
      emit('finalized', { os, shouldPrint: false });
      resetState();
    } catch (err: any) {
      apiError.value = err?.message ?? 'Erro ao finalizar a ordem de serviço';
    }
  }

  watch(
    () => props.isOpen,
    (open) => {
      if (!open) resetState();
    },
  );

  return {
    form,
    errors,
    confirmacao,
    apiError,
    formasPagamento,
    addedPayments,
    currentPaymentMethod,
    paymentDetails,
    showPaymentDetails,
    subtotalItens,
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
