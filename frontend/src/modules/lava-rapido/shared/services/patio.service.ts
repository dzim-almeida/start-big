/**
 * Chamadas do pátio e dos lavadores da OS (Spec 04A/10A do lava-rápido).
 */
import { z } from 'zod';

import api from '@/api/axios';

import { cartaoPatioSchema, lavadorSchema, patioSchema, type CartaoPatio, type Lavador, type Patio } from '../schemas/patio.schema';

const URL = '/lava-rapido';

/** Os veículos do dia por coluna: Aguardando, Lavando, Pronto, Entregues hoje. */
export async function getPatio(): Promise<Patio> {
  const { data } = await api.get(`${URL}/patio`);
  return patioSchema.parse(data);
}

/** Uma casa adiante (Aguardando → Lavando → Pronto). Do Pronto, 422: use Receber. */
export async function avancarNoPatio(numeroOs: string): Promise<CartaoPatio> {
  const { data } = await api.post(`${URL}/os/${numeroOs}/avancar`);
  return cartaoPatioSchema.parse(data);
}

/** Uma casa para trás (engano). */
export async function voltarNoPatio(numeroOs: string): Promise<CartaoPatio> {
  const { data } = await api.post(`${URL}/os/${numeroOs}/voltar`);
  return cartaoPatioSchema.parse(data);
}

export async function getLavadores(numeroOs: string): Promise<Lavador[]> {
  const { data } = await api.get(`${URL}/os/${numeroOs}/lavadores`);
  return z.array(lavadorSchema).parse(data);
}

/** Troca a lista INTEIRA de lavadores da OS (vazia = sem lavador). */
export async function definirLavadores(numeroOs: string, funcionarioIds: number[]): Promise<Lavador[]> {
  const { data } = await api.put(`${URL}/os/${numeroOs}/lavadores`, { funcionario_ids: funcionarioIds });
  return z.array(lavadorSchema).parse(data);
}
