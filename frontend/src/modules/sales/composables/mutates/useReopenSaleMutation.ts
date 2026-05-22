import { useMutation, useQueryClient } from "@tanstack/vue-query";
import type { AxiosError } from "axios";

import { useToast } from "@/shared/composables/useToast";
import { getErrorMessage } from "@/shared/utils/error.utils";
import type { ApiError } from "@/shared/types/axios.types";

import { saleService } from "../../api.service";
import { saleKeys } from "../../query.keys";

import { SaleRead } from "../../schemas/sale.schema";

export function useReopenSaleMutation() {
    const queryClient = useQueryClient();
    const toast = useToast();

    return useMutation<SaleRead, AxiosError<ApiError>, { saleId: number }>({
        mutationFn: ({ saleId }) => saleService.reopenSale(saleId),
        onSuccess: (reopenedSale) => {
            toast.success('Venda reaberta com sucesso');
            queryClient.setQueryData(saleKeys.draft(reopenedSale.id), reopenedSale);
            queryClient.invalidateQueries({
              queryKey: saleKeys.lists(),
            });
            queryClient.invalidateQueries({
              queryKey: saleKeys.status(),
            });
        },
        onError: (error) => {
            toast.error(getErrorMessage(error, 'Erro ao reabrir venda'));
        }
    })
}