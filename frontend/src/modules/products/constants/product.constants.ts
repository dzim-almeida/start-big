import { FilterOption } from "@/shared/types/filter.types";
import { TabOption } from "../types/products.types";

export const TAB_OPTIONS: TabOption[] = [
    {
        id: 'product',
        label: 'Produtos',
    },
    {
        id: 'supplier',
        label: 'Fornecedores',
    },
];

export const FILTER_CONFIG: Record<string, FilterOption> = {
    active: {
        label: 'Ativos',
        class: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
        color: 'bg-emerald-500'
    },
    inactive: {
        label: 'Inativos',
        class: 'bg-red-50 text-red-600 border border-red-200',
        color: 'bg-red-500'
    }
}