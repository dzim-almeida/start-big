import api from '@/api/axios';

import { OsImageReadSchema, OsImageReadDataType } from '../../schemas/relationship/osPhoto.schema';

import { OsFotoUploadRequest, OsFotoDeleteRequest } from '../../types/requests.type';

import { BASE_ORDER_SERVICE_URL } from '../../constants/core.constant';

export async function uploadFotoOS(req: OsFotoUploadRequest): Promise<OsImageReadDataType> {
    const formData = new FormData()
    formData.append('image_file', req.imageFile)

    const { data } = await api.post<OsImageReadDataType>(
        `${BASE_ORDER_SERVICE_URL}/${req.osNumber}/fotos`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
    )

    const validatedData = OsImageReadSchema.parse(data)
    return validatedData
}

export async function deleteFotoOS(req: OsFotoDeleteRequest): Promise<void> {
    await api.delete(`${BASE_ORDER_SERVICE_URL}/${req.osNumber}/fotos/${req.fotoId}`)
}
