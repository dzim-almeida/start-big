import api from "@/api/axios";

import { BASE_ORDER_SERVICE_URL } from "../constants/core.constant";

import { OsDeleteItem } from "../types/requests.type";

export async function deleteItemOS(itemData: OsDeleteItem): Promise<void> {
    return api.delete(`${BASE_ORDER_SERVICE_URL}/${itemData.osNumber}/itens/${itemData.itemOsId}`)
}