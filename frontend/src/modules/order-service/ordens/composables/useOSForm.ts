import { ref, computed, watch } from 'vue';
import type { ClienteSearchResult } from '@/shared/services/cliente.service';
import type { OrdemServicoRead } from '../types/ordemServico.types';
import type { OrdemServicoItemCreate } from '../types/ordemServico.types';
import { useOsEmployeesGet } from './request/relationship/useOSRelationshipGet.queries';
import { useServicosQuery } from '@/modules/order-service/servicos/composables/useServicosQuery';
import { useProductsQuery } from '@/modules/products/inventory/composables/useProductsQuery';
import { useCreateOrderServiceMutation } from './request/useOrderServiceCreate.mutate';
import { useUpdateOrderServiceMutation, useReopenOrderServiceMutation } from './request/useOrderServiceUpdate.mutate';

interface Props {
  isOpen: boolean;
  ordemServico?: OrdemServicoRead | null;
  selectedCliente?: ClienteSearchResult | null;
  autoShowReopen?: boolean;
}

interface UseOSFormOptions {
  onSuccess?: (os: OrdemServicoRead) => void;
}

const prioridadeOptions = [
  { label: 'Baixa', value: 'BAIXA' },
  { label: 'Normal', value: 'NORMAL' },
  { label: 'Alta', value: 'ALTA' },
  { label: 'Urgente', value: 'URGENTE' },
];

const statusOptions = [
  { label: 'Aberta', value: 'ABERTA' },
  { label: 'Em Andamento', value: 'EM_ANDAMENTO' },
  { label: 'Aguardando Peças', value: 'AGUARDANDO_PECAS' },
  { label: 'Aguardando Aprovação', value: 'AGUARDANDO_APROVACAO' },
  { label: 'Aguardando Retirada', value: 'AGUARDANDO_RETIRADA' },
  { label: 'Finalizada', value: 'FINALIZADA' },
  { label: 'Cancelada', value: 'CANCELADA' },
];

function defaultForm() {
  return {
    equipamento: '',
    marca: '',
    modelo: '',
    numero_serie: '',
    imei: '',
    cor: '',
    senha_aparelho: '',
    acessorios: '',
    defeito_relatado: '',
    condicoes_aparelho: '',
    status: 'ABERTA',
    funcionario_id: undefined as number | undefined,
    prioridade: 'NORMAL',
    data_previsao: undefined as string | undefined,
    diagnostico: '',
    data_finalizacao: undefined as string | undefined,
    valor_entrada: 0,
    desconto: 0,
  };
}

export function useOSForm(
  props: Props,
  emit: (event: string, ...args: any[]) => void,
  opts?: UseOSFormOptions,
) {
  const form = ref(defaultForm());
  const itens = ref<OrdemServicoItemCreate[]>([]);
  const apiError = ref<string | null>(null);

  const isEditMode = computed(() => !!props.ordemServico);

  // Queries
  const employeesQuery = useOsEmployeesGet();
  const servicosQueryResult = useServicosQuery({ limit: 100 });
  const produtosQueryResult = useProductsQuery();

  const isLoadingServicos = computed(() => servicosQueryResult.isLoading.value);
  const isLoadingProdutos = computed(() => (produtosQueryResult as any).isLoading?.value ?? false);

  const funcionariosOptions = computed(() => {
    const data = employeesQuery.data.value;
    if (!data) return [];
    const arr = Array.isArray(data) ? data : [data];
    return arr.map((f: any) => ({ label: f.nome, value: f.id }));
  });

  const servicosOptions = computed(() => {
    return servicosQueryResult.services.value.map((s: any) => ({
      label: s.descricao,
      value: s.id,
      preco: s.valor,
    }));
  });

  const produtosOptions = computed(() => {
    const data = (produtosQueryResult as any).data?.value;
    if (!data) return [];
    const arr = Array.isArray(data) ? data : data.items ?? [];
    return arr.map((p: any) => ({
      label: p.nome,
      value: p.id,
      preco: p.estoque?.valor_varejo ?? 0,
    }));
  });

  // Mutations
  const createMutation = useCreateOrderServiceMutation();
  const updateMutation = useUpdateOrderServiceMutation();
  const reopenMutation = useReopenOrderServiceMutation();

  const isPending = computed(
    () =>
      createMutation.isPending.value ||
      updateMutation.isPending.value ||
      reopenMutation.isPending.value,
  );

  // Financeiro
  const subtotal = computed(() =>
    itens.value.reduce((sum, item) => sum + item.quantidade * item.valor_unitario, 0),
  );

  const valorDesconto = computed(() => Number(form.value.desconto) || 0);

  const valorTotal = computed(() => Math.max(0, subtotal.value - valorDesconto.value));

  // Populate form from OS
  function populateFromOS(os: OrdemServicoRead) {
    form.value = {
      equipamento: (os as any).equipamento?.tipo_equipamento ?? '',
      marca: (os as any).equipamento?.marca ?? '',
      modelo: (os as any).equipamento?.modelo ?? '',
      numero_serie: (os as any).equipamento?.numero_serie ?? '',
      imei: (os as any).equipamento?.imei ?? '',
      cor: (os as any).equipamento?.cor ?? '',
      senha_aparelho: (os as any).senha_aparelho ?? '',
      acessorios: (os as any).acessorios ?? '',
      defeito_relatado: (os as any).defeito_relatado ?? '',
      condicoes_aparelho: (os as any).condicoes_aparelho ?? '',
      status: os.status,
      funcionario_id: (os as any).funcionario?.id,
      prioridade: (os as any).prioridade ?? 'NORMAL',
      data_previsao: (os as any).data_previsao ?? undefined,
      diagnostico: (os as any).diagnostico ?? '',
      data_finalizacao: (os as any).data_finalizacao ?? undefined,
      valor_entrada: 0,
      desconto: (os as any).desconto ?? 0,
    };
    itens.value = (os.itens ?? []).map((item: any) => ({
      ...item,
      servico_id: item.servico_id ? String(item.servico_id) : undefined,
    }));
  }

  function resetForm() {
    form.value = defaultForm();
    itens.value = [];
    apiError.value = null;
  }

  watch(
    () => props.ordemServico,
    (os) => {
      if (os) {
        populateFromOS(os);
      } else {
        resetForm();
      }
    },
    { immediate: true },
  );

  function handleClose() {
    emit('close');
  }

  function handleChangeCliente() {
    emit('changeCliente');
  }

  function removeItem(index: number) {
    itens.value.splice(index, 1);
  }

  async function handleSubmit() {
    apiError.value = null;

    try {
      if (isEditMode.value && props.ordemServico) {
        const os = await updateMutation.mutateAsync({
          osNumber: props.ordemServico.numero_os,
          updatedOS: {
            status: form.value.status as any,
            prioridade: form.value.prioridade as any,
            defeito_relatado: form.value.defeito_relatado,
            diagnostico: form.value.diagnostico || undefined,
            senha_aparelho: form.value.senha_aparelho || undefined,
            acessorios: form.value.acessorios || undefined,
            condicoes_aparelho: form.value.condicoes_aparelho || undefined,
            funcionario_id: form.value.funcionario_id,
            data_previsao: form.value.data_previsao,
            desconto: form.value.desconto,
          },
        });
        opts?.onSuccess?.(os);
        emit('saved', os);
      } else {
        if (!props.selectedCliente) {
          apiError.value = 'Selecione um cliente para continuar.';
          return;
        }
        const os = await createMutation.mutateAsync({
          prioridade: form.value.prioridade as any,
          defeito_relatado: form.value.defeito_relatado,
          diagnostico: form.value.diagnostico || undefined,
          senha_aparelho: form.value.senha_aparelho || undefined,
          acessorios: form.value.acessorios || undefined,
          condicoes_aparelho: form.value.condicoes_aparelho || undefined,
          desconto: form.value.desconto || undefined,
          data_previsao: form.value.data_previsao,
          cliente_id: props.selectedCliente.id,
          funcionario_id: form.value.funcionario_id as number,
          equipamento: {
            tipo_equipamento: (form.value.equipamento as any) || 'OUTROS',
            marca: form.value.marca || 'N/A',
            modelo: form.value.modelo || 'N/A',
            numero_serie: form.value.numero_serie || '0',
            imei: form.value.imei || '0',
            cor: form.value.cor || undefined,
          },
          itens: itens.value.map((item) => ({
            tipo: (item.tipo as any) ?? 'SERVICO',
            nome: item.nome ?? item.descricao ?? '',
            unidade_medida: (item.unidade_medida as any) ?? 'UN',
            quantidade: item.quantidade,
            valor_unitario: item.valor_unitario,
            item_id: item.item_id ?? (item.servico_id ? Number(item.servico_id) : undefined) ?? (item.produto_id ? Number(item.produto_id) : undefined),
          })),
        } as any);
        opts?.onSuccess?.(os);
        emit('saved', os);
      }
    } catch (err: any) {
      apiError.value = err?.message ?? 'Erro ao salvar a ordem de serviço';
    }
  }

  async function reopenOS() {
    if (!props.ordemServico) return;
    try {
      await reopenMutation.mutateAsync(props.ordemServico.numero_os);
    } catch (err: any) {
      apiError.value = err?.message ?? 'Erro ao reabrir a ordem de serviço';
    }
  }

  return {
    form,
    itens,
    apiError,
    isEditMode,
    servicosOptions,
    produtosOptions,
    funcionariosOptions,
    prioridadeOptions,
    statusOptions,
    subtotal,
    valorDesconto,
    valorTotal,
    isPending,
    isLoadingServicos,
    isLoadingProdutos,
    handleClose,
    handleChangeCliente,
    handleSubmit,
    removeItem,
    reopenOS,
  };
}
