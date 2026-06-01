import api from '@/api/axios'
import type { ConfiguracaoClientesRead, ConfiguracaoClientesUpdate } from '../schemas/configuracoes.schema'

const BASE_URL = '/configuracoes'

export async function getConfiguracoesClientes(): Promise<ConfiguracaoClientesRead> {
  const response = await api.get<ConfiguracaoClientesRead>(`${BASE_URL}/clientes`)
  return response.data
}

export async function updateConfiguracoesClientes(
  data: ConfiguracaoClientesUpdate,
): Promise<ConfiguracaoClientesRead> {
  const response = await api.put<ConfiguracaoClientesRead>(`${BASE_URL}/clientes`, data)
  return response.data
}
