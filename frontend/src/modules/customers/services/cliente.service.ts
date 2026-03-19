/**
 * ===========================================================================
 * ARQUIVO: cliente.service.ts
 * MODULO: Clientes
 * DESCRICAO: Camada de servico que faz a comunicacao com a API do backend.
 *            Contem todas as funcoes de CRUD (Create, Read, Update, Delete)
 *            para clientes PF e PJ.
 * ===========================================================================
 *
 * COMO FUNCIONA:
 * 1. Cada funcao faz uma requisicao HTTP para o backend usando Axios
 * 2. As funcoes retornam Promises que resolvem com os dados da API
 * 3. Erros sao propagados para serem tratados pelo chamador (usualmente Vue Query)
 *
 * ENDPOINTS UTILIZADOS:
 * - POST   /clientes/cliente_pf     -> Criar cliente PF
 * - POST   /clientes/cliente_pj     -> Criar cliente PJ
 * - GET    /clientes/               -> Listar todos os clientes
 * - GET    /clientes/:id            -> Buscar cliente por ID
 * - PUT    /clientes/:id            -> Atualizar cliente
 * - PUT    /clientes/toggle_ativo/:id -> Ativar/Desativar cliente
 * ===========================================================================
 */

import api from '@/api/axios';
import type {
  ClientePFCreate,
  ClientePJCreate,
  ClienteRead,
  ClienteUpdate,
  EquipamentoHistorico,
} from '../types/clientes.types';

// ===========================================================================
// CREATE - Funcoes para criar novos clientes
// ===========================================================================

/**
 * Cria um novo cliente Pessoa Fisica (PF)
 *
 * @param data - Dados do cliente PF a ser criado
 * @returns Promise com o cliente criado (incluindo ID gerado)
 *
 * @example
 * const novoCliente = await createClientePF({
 *   nome: 'Joao Silva',
 *   cpf: '12345678901',
 *   email: 'joao@email.com'
 * });
 */
export async function createClientePF(data: ClientePFCreate): Promise<ClienteRead> {
  const response = await api.post<ClienteRead>('/clientes/cliente_pf', data);
  return response.data;
}

/**
 * Cria um novo cliente Pessoa Juridica (PJ)
 *
 * @param data - Dados do cliente PJ a ser criado
 * @returns Promise com o cliente criado (incluindo ID gerado)
 *
 * @example
 * const novaEmpresa = await createClientePJ({
 *   razao_social: 'Empresa LTDA',
 *   cnpj: '12345678000101',
 *   nome_fantasia: 'Minha Empresa'
 * });
 */
export async function createClientePJ(data: ClientePJCreate): Promise<ClienteRead> {
  const response = await api.post<ClienteRead>('/clientes/cliente_pj', data);
  return response.data;
}

// ===========================================================================
// READ - Funcoes para buscar clientes
// ===========================================================================

/**
 * Lista todos os clientes ou busca por termo
 *
 * @param buscar - Termo de busca opcional
 * @param status - Filtro de status ('ativos', 'inativos', 'todos')
 * @returns Promise com array de clientes
 */
export async function getClientes(buscar?: string, status: string = 'ativos'): Promise<ClienteRead[]> {
  const params: Record<string, string | boolean | number> = {
    only_active: status === 'ativos',
    limit: 100,
  };
  if (buscar) params.buscar = buscar;

  const response = await api.get<{ items: ClienteRead[] }>('/clientes/', { params });
  return response.data.items;
}

/**
 * Busca um cliente especifico pelo ID
 *
 * @param id - ID do cliente
 * @returns Promise com os dados completos do cliente
 *
 * @example
 * const cliente = await getClienteById(123);
 * console.log(cliente.tipo); // 'PF' ou 'PJ'
 */
export async function getClienteById(id: number): Promise<ClienteRead> {
  const response = await api.get<ClienteRead>(`/clientes/${id}`);
  return response.data;
}

// ===========================================================================
// UPDATE - Funcoes para atualizar clientes
// ===========================================================================

/**
 * Atualiza os dados de um cliente existente
 * Funciona tanto para PF quanto PJ (polimorfico)
 *
 * @param id - ID do cliente a atualizar
 * @param data - Dados a atualizar (campos opcionais)
 * @returns Promise com o cliente atualizado
 *
 * @example
 * // Atualizar cliente PF
 * await updateCliente(123, {
 *   tipo: 'PF',
 *   email: 'novo@email.com'
 * });
 */
export async function updateCliente(id: number, data: ClienteUpdate): Promise<ClienteRead> {
  const response = await api.put<ClienteRead>(`/clientes/${id}`, data);
  return response.data;
}

// ===========================================================================
// DELETE - Funcoes para soft delete (ativar/desativar)
// ===========================================================================

/**
 * Alterna o status ativo/inativo de um cliente (Soft Delete)
 * Se o cliente esta ativo, desativa. Se esta inativo, ativa.
 *
 * @param id - ID do cliente
 * @returns Promise com o cliente atualizado (novo status)
 *
 * @example
 * const cliente = await toggleClienteAtivo(123);
 * console.log(cliente.ativo); // true ou false
 */
export async function toggleClienteAtivo(id: number): Promise<ClienteRead> {
  const response = await api.put<ClienteRead>(`/clientes/toggle_ativo/${id}`);
  return response.data;
}

export async function getClientEquipments(clienteId: number): Promise<EquipamentoHistorico[]> {
  const response = await api.get<EquipamentoHistorico[]>(`/clientes/${clienteId}/equipamentos`);
  return response.data;
}
