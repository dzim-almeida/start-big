import api from '@/api/axios'
import type { ConfiguracaoClientesRead, ConfiguracaoClientesUpdate, ConfiguracaoProdutosRead, ConfiguracaoProdutosUpdate } from '../schemas/configuracoes.schema'

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

export async function getConfiguracoesProdutos(): Promise<ConfiguracaoProdutosRead> {
  const response = await api.get<ConfiguracaoProdutosRead>(`${BASE_URL}/produtos`)
  return response.data
}

export async function updateConfiguracoesProdutos(
  data: ConfiguracaoProdutosUpdate,
): Promise<ConfiguracaoProdutosRead> {
  const response = await api.put<ConfiguracaoProdutosRead>(`${BASE_URL}/produtos`, data)
  return response.data
}
