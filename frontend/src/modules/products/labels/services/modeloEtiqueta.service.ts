/**
 * @fileoverview API service dos modelos de etiqueta da loja (/etiquetas/modelos)
 */

import api from '@/api/axios';
import type { ModeloEtiquetaApi, ModeloEtiquetaPayload } from '../types/etiquetas.types';

const BASE_URL = 'etiquetas/modelos' as const;

export async function getModelosEtiqueta(): Promise<ModeloEtiquetaApi[]> {
  const { data } = await api.get<ModeloEtiquetaApi[]>(BASE_URL);
  return data;
}

export async function createModeloEtiqueta(payload: ModeloEtiquetaPayload): Promise<ModeloEtiquetaApi> {
  const { data } = await api.post<ModeloEtiquetaApi>(BASE_URL, payload);
  return data;
}

export async function updateModeloEtiqueta(id: number, payload: ModeloEtiquetaPayload): Promise<ModeloEtiquetaApi> {
  const { data } = await api.put<ModeloEtiquetaApi>(`${BASE_URL}/${id}`, payload);
  return data;
}

export async function deleteModeloEtiqueta(id: number): Promise<void> {
  await api.delete(`${BASE_URL}/${id}`);
}
