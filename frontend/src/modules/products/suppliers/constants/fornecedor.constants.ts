// ============================================================================
// MÓDULO: FornecedorConstants (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Centralizar as configurações visuais e rótulos de filtros.
// FUNCIONALIDADES: Definição de cores (Tailwind), labels e estilos para os 
//                  estados de fornecedores (Ativos/Inativos).
// ============================================================================
import type { StatusFilter } from '../types/fornecedor.types';

export const STATUS_FILTER_CONFIG: Record<
  StatusFilter,
  { label: string; class: string; color: string }
> = {
  ativos: {
    label: 'Ativos',
    class: 'bg-emerald-50 text-emerald-600',
    color: 'bg-emerald-500',
  },
  inativos: {
    label: 'Desativados',
    class: 'bg-red-50 text-red-600',
    color: 'bg-red-500',
  },
};