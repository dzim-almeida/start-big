import { useMutation, useQueryClient } from "@tanstack/vue-query";

import { saleService } from "../../sales.service";
import { saleKeys } from "../../sales.keys";

import { PaymentSaleCreate } from "../../schemas/paymentSale.schema";
import { SaleRead } from "../../schemas/sale.schema";

export function useFinishSaleMutation() {
    const queryClient = useQueryClient();

    return useMutation<SaleRead, Error, { saleId: number; payments: PaymentSaleCreate }>({
        mutationFn: (variables) => saleService.finishSale(variables.saleId, variables.payments),
        onSuccess: (finishedSale) => {
          queryClient.invalidateQueries({
            queryKey: saleKeys.draft(finishedSale.id)
          });
          queryClient.setQueryData(saleKeys.detail(finishedSale.id), finishedSale);
          queryClient.invalidateQueries({
            queryKey: saleKeys.lists(),
          })
        },
        onError: (error) => {
          console.error('[useFinishSaleMutation] Error finishing sale:', error);
        }
    })
}