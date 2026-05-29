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