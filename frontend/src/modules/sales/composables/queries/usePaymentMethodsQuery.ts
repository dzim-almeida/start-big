import { computed } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { getPaymentMethodsAll } from '@/shared/services/paymentMethods.service';
import type { PaymentFormReadDataType } from '@/shared/schemas/payments/payment.schema';

const PAYMENT_METHODS_QUERY_KEY = 'sales-payment-methods';
const STALE_TIME = 1000 * 60 * 5;

export function usePaymentMethodsQuery() {
  const query = useQuery({
    queryKey: [PAYMENT_METHODS_QUERY_KEY],
    queryFn: getPaymentMethodsAll,
    staleTime: STALE_TIME,
  });

  const formasPagamento = computed<PaymentFormReadDataType[]>(
    () => (query.data.value as PaymentFormReadDataType[] | undefined) ?? [],
  );

  return { formasPagamento, isLoading: query.isLoading };
}
