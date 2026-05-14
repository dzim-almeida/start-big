import type { QueryClient } from "@tanstack/vue-query";
import { SaleRead } from "./schemas/sale.schema";
import { ProductAlteration } from "./schemas/productSale.schema";
import { saleKeys } from "./query.keys";

export function patchDraftCache(
    queryClient: QueryClient,
    saleId: number,
    response: ProductAlteration,
) {
    queryClient.setQueryData<SaleRead>(
        saleKeys.draft(saleId),
        (oldDraft) => {
            if (!oldDraft) return oldDraft;

            const productsList = oldDraft.produtos;

            const oldProduct = productsList.find((product) => product.id === response.produto_adicionado.id);

            if (!oldProduct) {
                productsList.push(response.produto_adicionado);
            } else {
                const index = productsList.indexOf(oldProduct);
                productsList[index] = response.produto_adicionado;
            }

            return {
                ...oldDraft,
                produtos: productsList,
                descontos: response.financeiro_atualizado.descontos,
                entrega: response.financeiro_atualizado.entrega,
                subtotal: response.financeiro_atualizado.subtotal,
                total: response.financeiro_atualizado.total,
            }
        }
    )
    queryClient.invalidateQueries({
        queryKey: saleKeys.lists(),
    })
}
