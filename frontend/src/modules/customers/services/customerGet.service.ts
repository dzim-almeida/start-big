import api from '@/api/axios';

import { BASE_CUSTOMER_URL } from '../constants/customer.constant';

import {
  CustomerPaginationSchema,
  type CustomerPaginationDataType,
  type CustomerParamsDataType,
  type CustomerUnionReadSchemaDataType,
} from '../schemas/customerQuery.schema';

import { CustomerUnionReadSchema } from '@/shared/schemas/customer/customer.schema';

// ── Helpers ────────────────────────────────────────────────────────────────

function safeParseCustomer(data: unknown, fnName: string): CustomerUnionReadSchemaDataType {
  const result = CustomerUnionReadSchema.safeParse(data);
  if (!result.success) {
    console.warn(`[${fnName}] Zod validation warning:`, result.error.issues);
    return data as CustomerUnionReadSchemaDataType;
  }
  return result.data;
}

// ── GET All (paginado) ─────────────────────────────────────────────────────

export async function getAllCustomers(
  params: CustomerParamsDataType,
): Promise<CustomerPaginationDataType> {
  const queryParams: Record<string, string | number | boolean> = {};
  if (params.search) queryParams.buscar = params.search;
  if (params.only_active !== undefined) queryParams.only_active = params.only_active;
  if (params.page) queryParams.page = params.page;
  if (params.limit) queryParams.limit = params.limit;

  const { data } = await api.get<CustomerPaginationDataType>(
    `${BASE_CUSTOMER_URL}/`,
    { params: queryParams },
  );

  const result = CustomerPaginationSchema.safeParse(data);
  if (!result.success) {
    console.warn('[getAllCustomers] Zod validation warning:', result.error.issues);
    return data as CustomerPaginationDataType;
  }
  return result.data;
}

// ── GET By ID ──────────────────────────────────────────────────────────────

export async function getCustomerById(id: number): Promise<CustomerUnionReadSchemaDataType> {
  const { data } = await api.get<CustomerUnionReadSchemaDataType>(
    `${BASE_CUSTOMER_URL}/${id}`,
  );
  return safeParseCustomer(data, 'getCustomerById');
}

// ── GET Equipamentos (histórico de equipamentos do cliente) ────────────────

export interface EquipamentoHistorico {
  equipamento: string;
  marca: string | null;
  modelo: string | null;
  numero_serie: string | null;
}

export async function getClientEquipments(
  clienteId: number,
): Promise<EquipamentoHistorico[]> {
  const { data } = await api.get<EquipamentoHistorico[]>(
    `${BASE_CUSTOMER_URL}/${clienteId}/equipamentos`,
  );
  return data;
}
