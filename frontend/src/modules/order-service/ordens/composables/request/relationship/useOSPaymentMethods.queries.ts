import { computed } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { getPaymentMethodsAll } from '../../../services/relationship/osPaymentMethods.service';
import type { PaymentFormReadDataType } from '@/shared/schemas/payments/payment.schema';

const OS_PAYMENT_METHODS_QUERY_KEY = 'os-payment-methods-query';
const OS_PAYMENT_METHODS_STALE_TIME = 1000 * 60 * 5;

export function useOsPaymentMethodsGet() {
  const query = useQuery({
    queryKey: [OS_PAYMENT_METHODS_QUERY_KEY],
    queryFn: getPaymentMethodsAll,
    staleTime: OS_PAYMENT_METHODS_STALE_TIME,
  });

  const formasPagamento = computed<PaymentFormReadDataType[]>(
    () => (query.data.value as PaymentFormReadDataType[] | undefined) ?? [],
  );

  return { formasPagamento, isLoading: query.isLoading };
}
