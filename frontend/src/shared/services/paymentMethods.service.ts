import api from '@/api/axios';

import { PaymentFormReadSchema, type PaymentFormReadDataType } from '@/shared/schemas/payments/payment.schema';

const BASE_URL = '/formas-pagamento';

export async function getPaymentMethodsAll(): Promise<PaymentFormReadDataType[]> {
  const { data } = await api.get<PaymentFormReadDataType[]>(`${BASE_URL}/`);
  const result = PaymentFormReadSchema.array().safeParse(data);
  if (!result.success) {
    console.warn('[getPaymentMethodsAll] Zod validation warning:', result.error.issues);
    return data as PaymentFormReadDataType[];
  }
  return result.data;
}
