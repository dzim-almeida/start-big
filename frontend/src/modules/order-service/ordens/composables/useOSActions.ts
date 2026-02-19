import { computed } from 'vue';
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { useToast } from '@/shared/composables/useToast';
import { ordemServicoService } from '../services/ordemServico.service';
import {
  ORDENS_SERVICO_QUERY_KEY,
  ORDENS_SERVICO_STATS_QUERY_KEY,
} from '../../shared/constants/queryKeys';

export function useOSActions() {
  const toast = useToast();
  const queryClient = useQueryClient();

  const cancelarMutation = useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) => ordemServicoService.cancelar(id, motivo),
    onSuccess: () => {
      toast.success('Ordem de Serviço cancelada com sucesso!');
      queryClient.invalidateQueries({ queryKey: [ORDENS_SERVICO_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [ORDENS_SERVICO_STATS_QUERY_KEY] });
    },
    onError: () => toast.error('Erro ao cancelar OS'),
  });

  const toggleAtivoMutation = useMutation({
    mutationFn: (id: number) => ordemServicoService.toggleAtivo(id),
    onSuccess: (data) => {
      const action = data.ativo ? 'ativada' : 'desativada';
      toast.success(`OS ${action} com sucesso!`);
      queryClient.invalidateQueries({ queryKey: [ORDENS_SERVICO_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [ORDENS_SERVICO_STATS_QUERY_KEY] });
    },
    onError: () => toast.error('Erro ao alterar status da OS'),
  });

  const isPending = computed(() =>
    cancelarMutation.isPending.value || toggleAtivoMutation.isPending.value
  );

  return {
    cancelarMutation,
    toggleAtivoMutation,
    isPending,
  };
}
