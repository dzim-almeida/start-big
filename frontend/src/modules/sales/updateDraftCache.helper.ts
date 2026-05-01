import type { QueryClient } from "@tanstack/vue-query";
import { SaleRead } from "./schemas/sale.schema";
import { ProductAlteration } from "./schemas/productSale.schema";
import { saleKeys } from "./sales.keys";

export function patchDraftCache(
    queryClient: QueryClient,
    saleId: number,
    response: ProductAlteration,
) {
    queryClient.setQueryData<SaleRead>(
        saleKeys.draft(saleId),
        (oldDraft) => {
            if (!oldDraft) return oldDraft;

            return {
                ...oldDraft,
                
                produtos: [
                    ...(oldDraft.produtos ?? []),
                    response.produto_adicionado
                ],

                descontos: response.financeiro_atualizado.descontos,
                entrega: response.financeiro_atualizado.entrega,
                subtotal: response.financeiro_atualizado.subtotal,
                total: response.financeiro_atualizado.total,
            }
        }
    )
}
