import api from '@/api/axios';

import { OrderServiceReadSchema, OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';

import { OrderServiceUpdateRequest, OsCancelUpdateRequest, OsEquipUpdateResquest, OsItemUpdateRequest, OsReadyUpdateRequest } from '../types/requests.type';

import { BASE_ORDER_SERVICE_URL } from '../constants/core.constant';

export async function updateOrderService(orderService: OrderServiceUpdateRequest): Promise<OrderServiceReadDataType> {
    const { data } = await api.put<OrderServiceReadDataType>(`${BASE_ORDER_SERVICE_URL}/${orderService.osNumber}`, orderService.updatedOS)
    const validatedData = OrderServiceReadSchema.parse(data)
    return validatedData
}

export async function updateEquipOS(equipOs: OsEquipUpdateResquest): Promise<OrderServiceReadDataType> {
    const { data } = await api.put<OrderServiceReadDataType>(`${BASE_ORDER_SERVICE_URL}/${equipOs.osNumber}/equipamento`, equipOs.updatedEquip)
    const validatedData = OrderServiceReadSchema.parse(data)
    return validatedData
}

export async function updateItemOS(itemOs: OsItemUpdateRequest): Promise<OrderServiceReadDataType> {
    const { data } = await api.put<OrderServiceReadDataType>(`${BASE_ORDER_SERVICE_URL}/${itemOs.osNumber}/itens/${itemOs.osItemId}`, itemOs.updatedItem)
    const validatedData = OrderServiceReadSchema.parse(data)
    return validatedData
}

export async function updateReadyOS(readyOs: OsReadyUpdateRequest): Promise<OrderServiceReadDataType> {
    const { data } = await api.put<OrderServiceReadDataType>(`${BASE_ORDER_SERVICE_URL}/${readyOs.osNumber}/finalizar`, readyOs.readyOs)
    const validatedData = OrderServiceReadSchema.parse(data)
    return validatedData
}

export async function updateCancelOS(cancelOs: OsCancelUpdateRequest): Promise<OrderServiceReadDataType> {
    const { data } = await api.put<OrderServiceReadDataType>(`${BASE_ORDER_SERVICE_URL}/${cancelOs.osNumber}/cancelar`, cancelOs.cancelOs)
    const validatedData = OrderServiceReadSchema.parse(data)
    return validatedData
}

export async function updateReopen(os_number: string): Promise<OrderServiceReadDataType> {
    const { data } = await api.put<OrderServiceReadDataType>(`${BASE_ORDER_SERVICE_URL}/${os_number}/reabrir`)
    const validatedData = OrderServiceReadSchema.parse(data)
    return validatedData
}

