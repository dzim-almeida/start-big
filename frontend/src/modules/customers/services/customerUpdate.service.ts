import api from '@/api/axios';

import { BASE_CUSTOMER_URL } from '../constants/customer.constant';

import { CustomerUnionReadSchema } from '@/shared/schemas/customer/customer.schema';
import type { CustomerUnionReadSchemaDataType } from '@/shared/schemas/customer/customer.schema';

import type { CustomerUpdateDataType } from '../schemas/customerMutate.schema';

// ── Helpers ────────────────────────────────────────────────────────────────

function safeParseCustomer(data: unknown, fnName: string): CustomerUnionReadSchemaDataType {
  const result = CustomerUnionReadSchema.safeParse(data);
  if (!result.success) {
    console.warn(`[${fnName}] Zod validation warning:`, result.error.issues);
    return data as CustomerUnionReadSchemaDataType;
  }
  return result.data;
}

// ── Update ─────────────────────────────────────────────────────────────────

export async function updateCustomer(
  id: number,
  data: CustomerUpdateDataType,
): Promise<CustomerUnionReadSchemaDataType> {
  const { data: response } = await api.put<CustomerUnionReadSchemaDataType>(
    `${BASE_CUSTOMER_URL}/${id}`,
    data,
  );
  return safeParseCustomer(response, 'updateCustomer');
}

// ── Toggle Ativo ───────────────────────────────────────────────────────────

export async function toggleCustomerAtivo(
  id: number,
): Promise<CustomerUnionReadSchemaDataType> {
  const { data } = await api.put<CustomerUnionReadSchemaDataType>(
    `${BASE_CUSTOMER_URL}/toggle_ativo/${id}`,
  );
  return safeParseCustomer(data, 'toggleCustomerAtivo');
}
