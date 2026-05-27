import api from '@/api/axios';
import { safeParseResponse } from '@/shared/utils/parse.utils';

import type { PeriodFilter } from '../types/dashboard.types';
import type {
  DashboardStatsData,
  OSVencendoResponseData,
  EstoqueBaixoResponseData,
  UltimasVendasResponseData,
} from '../schemas/dashboard.schema';
import {
  DashboardStatsSchema,
  OSVencendoResponseSchema,
  EstoqueBaixoResponseSchema,
  UltimasVendasResponseSchema,
} from '../schemas/dashboard.schema';

const DASHBOARD_URL = '/dashboard';

export const dashboardService = {
  async getStats(periodo: PeriodFilter): Promise<DashboardStatsData> {
    const { data } = await api.get<DashboardStatsData>(`${DASHBOARD_URL}/stats`, {
      params: { periodo },
    });
    return safeParseResponse(DashboardStatsSchema, data, 'dashboardService.getStats');
  },

  async getOSVencendo(): Promise<OSVencendoResponseData> {
    const { data } = await api.get<OSVencendoResponseData>(`${DASHBOARD_URL}/os-vencendo`);
    return safeParseResponse(OSVencendoResponseSchema, data, 'dashboardService.getOSVencendo');
  },

  async getEstoqueBaixo(): Promise<EstoqueBaixoResponseData> {
    const { data } = await api.get<EstoqueBaixoResponseData>(`${DASHBOARD_URL}/estoque-baixo`);
    return safeParseResponse(
      EstoqueBaixoResponseSchema,
      data,
      'dashboardService.getEstoqueBaixo',
    );
  },

  async getUltimasVendas(): Promise<UltimasVendasResponseData> {
    const { data } = await api.get<UltimasVendasResponseData>(`${DASHBOARD_URL}/ultimas-vendas`);
    return safeParseResponse(
      UltimasVendasResponseSchema,
      data,
      'dashboardService.getUltimasVendas',
    );
  },
};
