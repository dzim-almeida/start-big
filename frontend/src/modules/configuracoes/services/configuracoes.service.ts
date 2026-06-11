import api from '@/api/axios'
import type { ConfiguracaoClientesRead, ConfiguracaoClientesUpdate, ConfiguracaoProdutosRead, ConfiguracaoProdutosUpdate, ConfiguracaoOSRead, ConfiguracaoOSUpdate, ConfiguracaoVendasRead, ConfiguracaoVendasUpdate, ConfiguracaoSegurancaRead, ConfiguracaoSegurancaUpdate } from '../schemas/configuracoes.schema'

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

export async function getConfiguracoesOS(): Promise<ConfiguracaoOSRead> {
  const response = await api.get<ConfiguracaoOSRead>(`${BASE_URL}/os`)
  return response.data
}

export async function updateConfiguracoesOS(
  data: ConfiguracaoOSUpdate,
): Promise<ConfiguracaoOSRead> {
  const response = await api.put<ConfiguracaoOSRead>(`${BASE_URL}/os`, data)
  return response.data
}

export async function getConfiguracoesVendas(): Promise<ConfiguracaoVendasRead> {
  const response = await api.get<ConfiguracaoVendasRead>(`${BASE_URL}/vendas`)
  return response.data
}

export async function updateConfiguracoesVendas(
  data: ConfiguracaoVendasUpdate,
): Promise<ConfiguracaoVendasRead> {
  const response = await api.put<ConfiguracaoVendasRead>(`${BASE_URL}/vendas`, data)
  return response.data
}

export async function getConfiguracoesSeguranca(): Promise<ConfiguracaoSegurancaRead> {
  const response = await api.get<ConfiguracaoSegurancaRead>(`${BASE_URL}/seguranca`)
  return response.data
}

export async function updateConfiguracoesSeguranca(
  data: ConfiguracaoSegurancaUpdate,
): Promise<ConfiguracaoSegurancaRead> {
  const response = await api.put<ConfiguracaoSegurancaRead>(`${BASE_URL}/seguranca`, data)
  return response.data
}

export async function verificarPinSeguranca(pin: string): Promise<void> {
  await api.post(`${BASE_URL}/seguranca/verificar-pin`, { pin })
}
