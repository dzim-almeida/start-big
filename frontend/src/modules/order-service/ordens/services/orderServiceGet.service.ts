import api from '@/api/axios';

import { OrderServiceParamsDataType } from '../schemas/orderServiceQuery.schema';
import {
  OrderServiceReadSchema,
  OrderServicePaginationSchema,
  OrderServiceStatsSchema,
  OrderServiceReadDataType,
  OrderServicePaginationDataType,
  OrderServiceStatsDataType,
} from '../schemas/orderServiceQuery.schema';

import { BASE_ORDER_SERVICE_URL } from '../constants/core.constant';

export async function getAllOs(
  query: OrderServiceParamsDataType,
): Promise<OrderServicePaginationDataType | void> {
  const params: Record<string, string | number | boolean> = {};
  if (query.search) params.search = query.search;
  if (query.priority_sort !== undefined) params.priority_sort = query.priority_sort;
  if (query.status) params.status = query.status;

  const { data } = await api.get<OrderServicePaginationDataType>(`${BASE_ORDER_SERVICE_URL}/`, {
    params,
  });
  const result = OrderServicePaginationSchema.safeParse(data);
  if (!result.success) {
    console.warn('[getAllOs] Zod validation warning:', result.error.issues);
    return data as OrderServicePaginationDataType;
  }
  return result.data;
}

export async function getUniqueOS(numero_os: string): Promise<OrderServiceReadDataType> {
  const { data } = await api.get<OrderServiceReadDataType>(
    `${BASE_ORDER_SERVICE_URL}/${numero_os}`,
  );
  const result = OrderServiceReadSchema.safeParse(data);
  if (!result.success) {
    console.warn('[getUniqueOS] Zod validation warning:', result.error.issues);
    return data as OrderServiceReadDataType;
  }
  return result.data;
}

export async function getStatsOS(): Promise<OrderServiceStatsDataType> {
  const { data } = await api.get<OrderServiceStatsDataType>(`${BASE_ORDER_SERVICE_URL}/stats`);
  const result = OrderServiceStatsSchema.safeParse(data);
  if (!result.success) {
    console.warn('[getStatsOS] Zod validation warning:', result.error.issues);
    return data as OrderServiceStatsDataType;
  }
  return result.data;
}
