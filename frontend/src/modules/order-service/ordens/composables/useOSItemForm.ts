import { ref, computed } from 'vue';
import type { OrdemServicoItemCreate } from '../types/ordemServico.types';

export interface SelectOption {
  label: string;
  value: string | number;
  preco?: number;
}

export function useOSItemForm() {
  const type = ref<string>('SERVICO');
  const servicoId = ref<string | number | undefined>(undefined);
  const descricao = ref<string>('');
  const quantidade = ref<number>(1);
  const valorUnitarioNum = ref<number>(0);

  const isService = computed(() => type.value !== 'PRODUTO');

  const valorUnitarioCents = computed(() => Math.round(valorUnitarioNum.value * 100));

  const total = computed(() => quantidade.value * valorUnitarioCents.value);

  const isValid = computed(() => {
    return quantidade.value > 0 && valorUnitarioCents.value > 0;
  });

  function reset() {
    type.value = 'SERVICO';
    servicoId.value = undefined;
    descricao.value = '';
    quantidade.value = 1;
    valorUnitarioNum.value = 0;
  }

  function populate(item: OrdemServicoItemCreate) {
    type.value = item.tipo ?? 'SERVICO';
    servicoId.value = item.servico_id;
    descricao.value = item.descricao ?? '';
    quantidade.value = item.quantidade;
    valorUnitarioNum.value = item.valor_unitario / 100;
  }

  return {
    type,
    servicoId,
    descricao,
    quantidade,
    valorUnitarioNum,
    isService,
    valorUnitarioCents,
    total,
    isValid,
    reset,
    populate,
  };
}
