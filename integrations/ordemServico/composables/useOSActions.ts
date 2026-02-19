/**
 * ===========================================================================
 * ARQUIVO: useOSActions.ts
 * MODULO: Ordem de Servico
 * DESCRICAO: Composable para acoes em Ordens de Servico como cancelar e
 *            alternar status ativo/inativo. Gerencia mutations do Vue Query.
 * ===========================================================================
 *
 * FUNCIONALIDADES:
 * - Cancelamento de OS com motivo obrigatorio
 * - Toggle de status ativo/inativo
 * - Atualizacao otimista do cache
 * - Feedback via toast notifications
 *
 * MUTATIONS:
 * - cancelarMutation: Cancela uma OS informando o motivo
 * - toggleAtivoMutation: Alterna status ativo/inativo da OS
 * ===========================================================================
 */
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { useToast } from '@/shared/composables/useToast';
import { ordemServicoService } from '@/modules/ordemServico/services/ordemServico.service';
import type { OrdemServicoListRead } from '@/modules/ordemServico/types/ordemServico.types';

export function useOSActions() {
    const toast = useToast();
    const queryClient = useQueryClient();

    // ===========================================================================
    // CANCELAR
    // ===========================================================================
    const cancelarMutation = useMutation({
        mutationFn: ({ id, motivo }: { id: number; motivo: string }) => ordemServicoService.cancelar(id, motivo),
        onSuccess: (data) => {
            toast.success('Ordem de Serviço cancelada com sucesso!');
            // Update cache optimistically or invalidate
            queryClient.setQueryData<OrdemServicoListRead[]>(['ordens-servico'], (oldData) => {
                if (!oldData) return [];
                return oldData.map(os => os.id === data.id ? { ...os, status: 'CANCELADA' } : os);
            });
            queryClient.invalidateQueries({ queryKey: ['ordens-servico'] });
        },
        onError: () =>  toast.error('Erro ao cancelar OS')
    });

    // ===========================================================================
    // REABRIR (Placeholder - lógica geralmente é edição de status)
    // ===========================================================================
    // Se houver endpoint específico, adicionar aqui. Por enquanto, a UI apenas abre o modal de edição.

    // ===========================================================================
    // TOGGLE ATIVO
    // ===========================================================================
    const toggleAtivoMutation = useMutation({
        mutationFn: (id: number) => ordemServicoService.toggleAtivo(id),
        onSuccess: (data) => {
            const action = data.ativo ? 'ativada' : 'desativada';
            toast.success(`OS ${action} com sucesso!`);
            queryClient.invalidateQueries({ queryKey: ['ordens-servico'] });
        },
        onError: () => toast.error('Erro ao alterar status da OS')
    });

    return {
        cancelarMutation,
        toggleAtivoMutation,
        // Helpers
        isPending: (cancelarMutation.isPending.value || toggleAtivoMutation.isPending.value)
    };
}
