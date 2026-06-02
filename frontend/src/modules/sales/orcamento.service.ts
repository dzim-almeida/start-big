import api from '@/api/axios';

import { parseSchema } from './parseSchema.util';

import {
  OrcamentoCreate,
  OrcamentoUpdate,
  OrcamentoUpdateSchema,
  OrcamentoSearch,
  OrcamentoList,
  OrcamentoListSchema,
  OrcamentoRead,
  OrcamentoReadSchema,
  OrcamentosStatus,
  OrcamentosStatusSchema,
  ConverterOrcamento,
} from './schemas/orcamento.schema';

import {
  ProductSaleCreate,
  ProductSaleUpdate,
  ProductAlteration,
  ProductAlterationSchema,
} from './schemas/productSale.schema';

import { SaleRead, SaleReadSchema } from './schemas/sale.schema';

const ORCAMENTO_ENDPOINT = '/orcamentos';

export const orcamentoService = {
  async createOrcamento(orcamento: OrcamentoCreate): Promise<OrcamentoRead> {
    const { data } = await api.post<OrcamentoRead>(ORCAMENTO_ENDPOINT, orcamento);
    return parseSchema(OrcamentoReadSchema, data, 'orcamentoService.createOrcamento.response');
  },

  async updateOrcamento(orcamento_id: number, orcamento: OrcamentoUpdate): Promise<OrcamentoRead> {
    const parsedOrcamento = parseSchema(OrcamentoUpdateSchema, orcamento, 'orcamentoService.updateOrcamento.request');
    const { data } = await api.patch<OrcamentoRead>(`${ORCAMENTO_ENDPOINT}/${orcamento_id}`, parsedOrcamento);
    return parseSchema(OrcamentoReadSchema, data, 'orcamentoService.updateOrcamento.response');
  },

  async addItemInOrcamento(orcamento_id: number, product: ProductSaleCreate): Promise<ProductAlteration> {
    const { data } = await api.post<ProductAlteration>(
      `${ORCAMENTO_ENDPOINT}/${orcamento_id}/itens`,
      product,
    );
    return parseSchema(ProductAlterationSchema, data, 'orcamentoService.addItemInOrcamento.response');
  },

  async deleteItemInOrcamento(orcamento_id: number, product_id: number): Promise<OrcamentoRead> {
    const { data } = await api.delete<OrcamentoRead>(`${ORCAMENTO_ENDPOINT}/${orcamento_id}/itens/${product_id}`);
    return parseSchema(OrcamentoReadSchema, data, 'orcamentoService.deleteItemInOrcamento.response');
  },

  async updateItemInOrcamento(
    orcamento_id: number,
    product_id: number,
    product: ProductSaleUpdate,
  ): Promise<ProductAlteration> {
    const { data } = await api.patch<ProductAlteration>(
      `${ORCAMENTO_ENDPOINT}/${orcamento_id}/itens/${product_id}`,
      product,
    );
    return parseSchema(ProductAlterationSchema, data, 'orcamentoService.updateItemInOrcamento.response');
  },

  async deleteOrcamento(orcamento_id: number): Promise<void> {
    await api.delete(`${ORCAMENTO_ENDPOINT}/${orcamento_id}`);
  },

  async converterOrcamento(orcamento_id: number, payload: ConverterOrcamento): Promise<SaleRead> {
    const { data } = await api.post<SaleRead>(`${ORCAMENTO_ENDPOINT}/${orcamento_id}/converter`, payload);
    return parseSchema(SaleReadSchema, data, 'orcamentoService.converterOrcamento.response');
  },

  async getOrcamento(orcamento_id: number): Promise<OrcamentoRead> {
    const { data } = await api.get<OrcamentoRead>(`${ORCAMENTO_ENDPOINT}/${orcamento_id}`);
    return parseSchema(OrcamentoReadSchema, data, 'orcamentoService.getOrcamento.response');
  },

  async listOrcamentos(query?: OrcamentoSearch, page: number = 1): Promise<OrcamentoList> {
    const params = {
      ...(query?.search && { search: query.search }),
      ...(query?.convertido !== undefined && query?.convertido !== null && { convertido: query.convertido }),
      page: page,
    };

    const { data } = await api.get<OrcamentoList>(`${ORCAMENTO_ENDPOINT}/`, { params });
    return parseSchema(OrcamentoListSchema, data, 'orcamentoService.listOrcamentos.response');
  },

  async getOrcamentosStatus(): Promise<OrcamentosStatus> {
    const { data } = await api.get<OrcamentosStatus>(`${ORCAMENTO_ENDPOINT}/status/`);
    return parseSchema(OrcamentosStatusSchema, data, 'orcamentoService.getOrcamentosStatus.response');
  },
};
