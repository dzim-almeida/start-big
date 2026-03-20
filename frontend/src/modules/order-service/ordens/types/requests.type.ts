import { OrderServiceUpdateDataType, OrderServiceReadyDataType, OrderServiceCancelDataType } from "../schemas/orderServiceMutate.schema";

import { OsItemCreateSchemaDataType, OsItemUpdateSchemaDataType } from "../schemas/relationship/osItem.schema";
import { OsEquipUpdateSchemaDataType } from "../schemas/relationship/osEquip.schema";

export interface OsItemCreateRequest {
    osNumber: string,
    osItem: OsItemCreateSchemaDataType
}

export interface OsItemUpdateRequest {
    osNumber: string,
    osItemId: number,
    updatedItem: OsItemUpdateSchemaDataType
}

export interface OrderServiceUpdateRequest {
    osNumber: string,
    updatedOS: OrderServiceUpdateDataType
}

export interface OsEquipUpdateRequest {
    osNumber: string,
    updatedEquip: OsEquipUpdateSchemaDataType
}

export interface OsReadyUpdateRequest {
    osNumber: string,
    readyOs: OrderServiceReadyDataType
}

export interface OsCancelUpdateRequest {
    osNumber: string,
    cancelOs: OrderServiceCancelDataType
}

export interface OsDeleteItem {
    osNumber: string,
    itemOsId: number
}

export interface OsFotoUploadRequest {
    osNumber: string,
    imageFile: File
}

export interface OsFotoDeleteRequest {
    osNumber: string,
    fotoId: number
}