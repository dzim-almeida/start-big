import { useMutation, useQueryClient } from "@tanstack/vue-query";

import { saleService } from "../../sales.service";
import { saleKeys } from "../../sales.keys";

import { SaleRead } from "../../schemas/sale.schema";

export function useReopenSaleMutation() {
    const queryClient = useQueryClient();
    
    return useMutation<SaleRead, Error, { saleId: number }>({
        mutationFn: ({ saleId }) => saleService.reopenSale(saleId),
        onSuccess: ( reopenedSale ) => {
            queryClient.setQueryData(saleKeys.draft(reopenedSale.id), reopenedSale);
        },
        onError: (error) => {
          console.error('[useReopenSaleMutation] Error reopening sale:', error);
        } 
    })
}