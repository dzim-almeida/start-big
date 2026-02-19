import { ref, computed, watch } from 'vue';
import type { OrdemServicoItemCreate } from '../types/ordemServico.types';

export interface SelectOption {
  value: string;
  label: string;
  price?: number;
}

export function useOSItemForm(props: {
  item: OrdemServicoItemCreate | null | undefined;
  servicosOptions: SelectOption[];
  produtosOptions: SelectOption[];
}) {
  const type = ref<'servicos' | 'produtos'>('servicos');
  const servicoId = ref<string | undefined>(undefined);
  const descricao = ref('');
  const quantidade = ref<number>(1);
  const valorUnitario = ref<string>('0,00');

  const isService = computed(() => type.value === 'servicos');

  const valorUnitarioCents = computed(() => {
    return Math.round(parseFloat(valorUnitario.value.replace(/\./g, '').replace(',', '.')) * 100);
  });

  const total = computed(() => {
    return quantidade.value * valorUnitarioCents.value;
  });

  const isValid = computed(() => {
    return !!servicoId.value && descricao.value.trim().length > 0 && quantidade.value > 0;
  });

  function reset() {
    type.value = 'servicos';
    servicoId.value = undefined;
    descricao.value = '';
    quantidade.value = 1;
    valorUnitario.value = '0,00';
  }

  function populate(item: OrdemServicoItemCreate) {
    const isProduct = props.produtosOptions.some(opt => opt.value === String(item.servico_id));
    type.value = isProduct ? 'produtos' : 'servicos';

    servicoId.value = item.servico_id ? String(item.servico_id) : undefined;
    descricao.value = item.descricao || '';
    quantidade.value = item.quantidade || 1;
    valorUnitario.value = (item.valor_unitario / 100).toFixed(2).replace('.', ',');
  }

  function handleValorInput(e: Event) {
    const target = e.target as HTMLInputElement;
    let value = target.value.replace(/\D/g, '');
    if (!value) value = '0';

    const floatVal = parseFloat(value) / 100;
    valorUnitario.value = floatVal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  watch(servicoId, (newId) => {
    if (!newId || props.item) return;

    const options = isService.value ? props.servicosOptions : props.produtosOptions;
    const selected = options.find(o => String(o.value) === String(newId));

    if (selected) {
      if (selected.price !== undefined) {
        valorUnitario.value = (selected.price / 100).toFixed(2).replace('.', ',');
      }

      const labelParts = selected.label.split(' - R$ ');
      if (labelParts.length > 0) {
        descricao.value = labelParts[0].trim();
      } else {
        descricao.value = selected.label;
      }
    }
  });

  return {
    type,
    servicoId,
    descricao,
    quantidade,
    valorUnitario,
    isService,
    valorUnitarioCents,
    total,
    isValid,
    reset,
    populate,
    handleValorInput,
  };
}
