import { FilterOption } from "@/shared/types/filter.types";

export const STATUS_COLORS = {
    ORCAMENTO: { bg: 'bg-blue-50', text: 'text-blue-700' },
    FINALIZADA: { bg: 'bg-green-50', text: 'text-green-700' },
    CANCELADA: { bg: 'bg-red-50', text: 'text-red-700' }
};

export const SALE_FILTERS: Record<string, FilterOption> = {
    ORCAMENTO: { label: 'Orçamento', class: 'bg-gray-100 text-gray-800', color: 'bg-gray-500' },
    FINALIZADA: { label: 'Finalizada', class: 'bg-green-100 text-green-800', color: 'bg-green-500' },
    CANCELADA: { label: 'Cancelada', class: 'bg-red-100 text-red-800', color: 'bg-red-500' }
};

export interface FilterChip {
    label: string;
    activeClass: string;
    dotColor: string;
}

export const SALE_FILTER_CHIPS: Record<string, FilterChip> = {
    FINALIZADA: {
        label: 'Finalizada',
        activeClass: 'bg-green-50 text-green-700 border-green-200',
        dotColor: 'bg-green-500',
    },
    ORCAMENTO: {
        label: 'Orçamento',
        activeClass: 'bg-blue-50 text-blue-700 border-blue-200',
        dotColor: 'bg-blue-500',
    },
    CANCELADA: {
        label: 'Cancelada',
        activeClass: 'bg-red-50 text-red-700 border-red-200',
        dotColor: 'bg-red-500',
    },
};

export interface ShortcutItem {
    keys: string;
    description: string;
}

export const SALE_SHORTCUTS: ShortcutItem[] = [
    { keys: 'F2', description: 'Nova venda' },
    { keys: 'F4', description: 'Produto avulso' },
    { keys: 'F6', description: 'Adicionar pagamento' },
    { keys: 'Ctrl+F', description: 'Buscar produto' },
    { keys: 'Ctrl+Enter', description: 'Finalizar venda' },
    { keys: 'Ctrl+Backspace', description: 'Cancelar venda' },
    { keys: 'Esc', description: 'Fechar modal atual' },
];

export const PRODUCT_TYPES = [
    {value: 'CADASTRADO', label: 'Cadastrado'},
    {value: 'AVULSO', label: 'Avulso'},
] as const;

export const PAYMENT_METHODS = [
    {value: 'DINHEIRO', label: 'Dinheiro'},
    {value: 'CARTAO_CREDITO', label: 'Cartão de Crédito'},
    {value: 'CARTAO_DEBITO', label: 'Cartão de Débito'},
    {value: 'PIX', label: 'Pix'},
    {value: 'BOLETO', label: 'Boleto'},
] as const;