/**
 * ===========================================================================
 * ARQUIVO: useServicoActions.ts
 * MODULO: Ordem de Servico
 * DESCRICAO: Composable para acoes no catalogo de Servicos, como alternar
 *            status ativo/inativo. Gerencia mutations do Vue Query.
 * ===========================================================================
 *
 * FUNCIONALIDADES:
 * - Toggle de status ativo/inativo do servico
 * - Atualizacao otimista do cache
 * - Feedback via toast notifications
 *
 * MUTATIONS:
 * - toggleAtivoMutation: Alterna status ativo/inativo do servico
 *
 * RETORNO:
 * - toggleAtivoMutation: Mutation para toggle de status
 * - isPending: Estado de carregamento
 * ===========================================================================
 */
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { useToast } from '@/shared/composables/useToast';
import { toggleServicoAtivo } from '@/modules/ordemServico/services/servicos.service';
import type { ServicoRead } from '@/modules/ordemServico/types/servicos.types';

export function useServicoActions() {
    const toast = useToast();
    const queryClient = useQueryClient();

    // ===========================================================================
    // TOGGLE ATIVO
    // ===========================================================================
    const toggleAtivoMutation = useMutation({
        mutationFn: (id: number) => toggleServicoAtivo(id),
        onSuccess: (data) => {
            const action = data.ativo ? 'ativado' : 'desativado';
            toast.success(`Serviço ${action} com sucesso!`);
            
            // Otimista / Invalidação
            queryClient.setQueryData<ServicoRead[]>(['servicos'], (oldData) => {
                if (!oldData) return [];
                return oldData.map(s => s.id === data.id ? data : s);
            });
            
            queryClient.invalidateQueries({ queryKey: ['servicos'] });
        },
        onError: () => toast.error('Erro ao alterar status do serviço')
    });

    return {
        toggleAtivoMutation,
        isPending: toggleAtivoMutation.isPending
    };
}
