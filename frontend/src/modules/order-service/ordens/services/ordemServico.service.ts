import api from '@/api/axios';
import { getUniqueOS } from './orderServiceGet.service';
import { BASE_ORDER_SERVICE_URL } from '../constants/core.constant';

export const ordemServicoService = {
  getById: (numero_os: string) => getUniqueOS(numero_os),
  getNextNumber: async (): Promise<{ numero: string }> => {
    const { data } = await api.get<{ numero: string }>(`${BASE_ORDER_SERVICE_URL}/proximo-numero`);
    return data;
  },
};
