/**
 * @fileoverview API service for cargos
 * @description Handles cargo-related API calls
 */

import api from '@/api/axios';
import { ENDPOINT_PERMISSION_MAP } from '@/shared/constants/permissions.constants';
import type { CargoCreate, CargoRead, CargoUpdate } from '../types/positions.types';

const BASE_URL = 'cargos' as const;
export const POSITION_PERMISSION = ENDPOINT_PERMISSION_MAP[BASE_URL];

/**
 * Lista todos os cargos ou filtra por termo
 * @param buscar - Termo de busca opcional (nome)
 */
export async function getCargos(buscar?: string): Promise<CargoRead[]> {
  const params = buscar ? { buscar_cargo: buscar } : undefined;
  const { data } = await api.get<CargoRead[]>(`${BASE_URL}/`, { params });
  return data;
}

/**
 * Cria um novo cargo
 * @param cargo - Dados do cargo
 */
export async function createCargo(cargo: CargoCreate): Promise<CargoRead> {
  const { data } = await api.post<CargoRead>(`${BASE_URL}/`, cargo);
  return data;
}

/**
 * Atualiza um cargo existente
 * @param id - ID do cargo
 * @param cargo - Dados para atualizar
 */
export async function updateCargo(
  id: number,
  cargo: CargoUpdate,
): Promise<CargoRead> {
  const { data } = await api.put<CargoRead>(`${BASE_URL}/${id}`, cargo);
  return data;
}

/**
 * Remove um cargo
 * @param id - ID do cargo
 */
export async function deleteCargo(id: number): Promise<void> {
  await api.delete(`${BASE_URL}/${id}`);
}
