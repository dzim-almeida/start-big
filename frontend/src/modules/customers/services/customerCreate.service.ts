import api from '@/api/axios';

import { BASE_CUSTOMER_URL } from '../constants/customer.constant';

import { CustomerUnionReadSchema } from '@/shared/schemas/customer/customer.schema';
import type { CustomerUnionReadSchemaDataType } from '@/shared/schemas/customer/customer.schema';

import type { CustomerPFCreateDataType, CustomerPJCreateDataType } from '../schemas/customerMutate.schema';

// ── Helpers ────────────────────────────────────────────────────────────────

function safeParseCustomer(data: unknown, fnName: string): CustomerUnionReadSchemaDataType {
  const result = CustomerUnionReadSchema.safeParse(data);
  if (!result.success) {
    console.warn(`[${fnName}] Zod validation warning:`, result.error.issues);
    return data as CustomerUnionReadSchemaDataType;
  }
  return result.data;
}

// ── Create PF ──────────────────────────────────────────────────────────────

export async function createCustomerPF(
  data: CustomerPFCreateDataType,
): Promise<CustomerUnionReadSchemaDataType> {
  const { data: response } = await api.post<CustomerUnionReadSchemaDataType>(
    `${BASE_CUSTOMER_URL}/cliente_pf`,
    data,
  );
  return safeParseCustomer(response, 'createCustomerPF');
}

// ── Create PJ ──────────────────────────────────────────────────────────────

export async function createCustomerPJ(
  data: CustomerPJCreateDataType,
): Promise<CustomerUnionReadSchemaDataType> {
  const { data: response } = await api.post<CustomerUnionReadSchemaDataType>(
    `${BASE_CUSTOMER_URL}/cliente_pj`,
    data,
  );
  return safeParseCustomer(response, 'createCustomerPJ');
}
