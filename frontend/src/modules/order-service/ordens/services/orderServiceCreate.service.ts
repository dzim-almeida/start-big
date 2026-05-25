import api from "@/api/axios";

import { OrderServiceCreateSchemaDataType } from "../schemas/orderServiceMutate.schema";
import { OrderServiceReadSchema, OrderServiceReadDataType } from "../schemas/orderServiceQuery.schema";

import { OsItemCreateRequest } from "../types/requests.type";

import { BASE_ORDER_SERVICE_URL } from "../constants/core.constant";
import { safeParseResponse } from '@/shared/utils/parse.utils';

export async function createOrderService(orderService: OrderServiceCreateSchemaDataType): Promise<OrderServiceReadDataType> {
    const { data } = await api.post<OrderServiceReadDataType>(`${BASE_ORDER_SERVICE_URL}/`, orderService)
    return safeParseResponse(OrderServiceReadSchema, data, 'createOrderService')
}

export async function createItemOS(osItemCreateRequest: OsItemCreateRequest): Promise<OrderServiceReadDataType> {
    const { data } = await api.post<OrderServiceReadDataType>(`${BASE_ORDER_SERVICE_URL}/${osItemCreateRequest.osNumber}/itens`, osItemCreateRequest.osItem)
    return safeParseResponse(OrderServiceReadSchema, data, 'createItemOS');
}
