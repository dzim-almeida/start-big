import type { FilterOption } from "@/shared/types/filter.types";

export const SALES_TAB_OPTIONS = [
    { id: 'vendas', label: 'Vendas' },
    { id: 'orcamentos', label: 'Orçamentos' },
];

export const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
    ATIVA: { bg: 'bg-blue-50', text: 'text-blue-700' },
    FINALIZADA: { bg: 'bg-green-50', text: 'text-green-700' },
    CANCELADA: { bg: 'bg-red-50', text: 'text-red-700' },
};

export const SALE_FILTERS: Record<string, FilterOption> = {
    ATIVA: { label: 'Ativa', class: 'bg-blue-100 text-blue-800', color: 'bg-blue-500' },
    FINALIZADA: { label: 'Finalizada', class: 'bg-green-100 text-green-800', color: 'bg-green-500' },
    CANCELADA: { label: 'Cancelada', class: 'bg-red-100 text-red-800', color: 'bg-red-500' },
};

export const SALE_FILTER_CONFIG: Record<string, FilterOption> = {
    ATIVA: { label: 'Ativa', class: 'bg-blue-50 text-blue-700', color: 'bg-blue-500' },
    FINALIZADA: { label: 'Finalizada', class: 'bg-green-50 text-green-700', color: 'bg-green-500' },
    CANCELADA: { label: 'Cancelada', class: 'bg-red-50 text-red-700', color: 'bg-red-500' },
};

export const ORCAMENTO_FILTER_CONFIG: Record<string, FilterOption> = {
    ATIVO: { label: 'Ativo', class: 'bg-blue-50 text-blue-700', color: 'bg-blue-500' },
    CONVERTIDO: { label: 'Convertido', class: 'bg-green-50 text-green-700', color: 'bg-green-500' },
};

export interface ShortcutItem {
    keys: string;
    description: string;
}

export const SALE_SHORTCUTS: ShortcutItem[] = [
    { keys: 'F2', description: 'Nova venda' },
    { keys: 'Ctrl+E', description: 'Focar entrega' },
    { keys: 'Ctrl+D', description: 'Focar desconto' },
    { keys: 'F4', description: 'Produto avulso' },
    { keys: 'F6', description: 'Focar pagamentos' },
    { keys: 'Ctrl+F', description: 'Buscar produto' },
    { keys: 'Ctrl+Enter', description: 'Finalizar venda' },
    { keys: 'Ctrl+Backspace', description: 'Cancelar venda' },
    { keys: 'Esc', description: 'Fechar modal atual' },
];

export const PRODUCT_TYPES = [
    {value: 'CADASTRADO', label: 'Cadastrado'},
    {value: 'AVULSO', label: 'Avulso'},
] as const;

// --- Orcamento ---

export const ORCAMENTO_SHORTCUTS: ShortcutItem[] = [
    { keys: 'F2', description: 'Novo orçamento' },
    { keys: 'Ctrl+E', description: 'Focar entrega' },
    { keys: 'Ctrl+D', description: 'Focar desconto' },
    { keys: 'F4', description: 'Produto avulso' },
    { keys: 'Ctrl+F', description: 'Buscar produto' },
    { keys: 'Ctrl+Enter', description: 'Converter em venda' },
    { keys: 'Esc', description: 'Fechar modal atual' },
];

export const PAYMENT_METHODS = [
    {value: 'DINHEIRO', label: 'Dinheiro'},
    {value: 'CARTAO_CREDITO', label: 'Cartão de Crédito'},
    {value: 'CARTAO_DEBITO', label: 'Cartão de Débito'},
    {value: 'PIX', label: 'Pix'},
    {value: 'BOLETO', label: 'Boleto'},
] as const;