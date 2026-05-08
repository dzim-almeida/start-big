import { SaleSearch } from "./schemas/sale.schema"

export const saleKeys = {
    all: ['sales'] as const,
    lists: () => [...saleKeys.all, 'list'] as const,
    list: (filters?: SaleSearch, page: number = 1) => [...saleKeys.lists(), filters ?? {}, page] as const,
    detail: (saleId: number) => [...saleKeys.all, 'detail', saleId] as const,
    draft: (saleId: number) => [...saleKeys.all, 'draft', saleId] as const,
    status: () => [...saleKeys.all, 'status'] as const
}

export const productKeys = {
    all: ['products'] as const,
    search: (term: string) => [...productKeys.all, 'search', term] as const,
}

export const customerKeys = {
    all: ['customers'] as const,
    search: (term: string) => [...customerKeys.all, 'search', term] as const,
}