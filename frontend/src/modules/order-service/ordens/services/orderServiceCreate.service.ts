import api from "@/api/axios";

import { OrderServiceCreateSchemaDataType } from "../schemas/orderServiceMutate.schema";
import { OrderServiceReadSchema, OrderServiceReadDataType } from "../schemas/orderServiceQuery.schema";

import { OsItemCreateRequest } from "../types/requests.type";

import { BASE_ORDER_SERVICE_URL } from "../constants/core.constant";

export async function createOrderService(orderService: OrderServiceCreateSchemaDataType): Promise<OrderServiceReadDataType> {
    const { data } = await api.post<OrderServiceReadDataType>(`${BASE_ORDER_SERVICE_URL}/`, orderService)
    const result = OrderServiceReadSchema.safeParse(data)
    if (!result.success) {
        console.warn('[createOrderService] Zod validation warning:', result.error.issues)
        return data as OrderServiceReadDataType
    }
    return result.data
}

export async function createItemOS(osItemCreateRequest: OsItemCreateRequest): Promise<OrderServiceReadDataType> {
    const { data } = await api.post<OrderServiceReadDataType>(`${BASE_ORDER_SERVICE_URL}/${osItemCreateRequest.osNumber}/itens`, osItemCreateRequest.osItem)
    const validatedData = OrderServiceReadSchema.parse(data)
    return validatedData
}
