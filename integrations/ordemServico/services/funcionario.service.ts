import api from '@/shared/libs/axios';

export interface FuncionarioResumo {
  id: number;
  nome: string;
  cargo_id?: number;
  ativo: boolean;
}

/**
 * Service Singleton para funcionarios
 */
class FuncionarioService {
  private readonly BASE_URL = '/funcionarios';

  async getAll(): Promise<FuncionarioResumo[]> {
    const response = await api.get<FuncionarioResumo[]>(this.BASE_URL);
    return response.data;
  }

  async getAtivos(): Promise<FuncionarioResumo[]> {
    const response = await api.get<FuncionarioResumo[]>(this.BASE_URL);
    return response.data.filter(f => f.ativo);
  }
}

export const funcionarioService = new FuncionarioService();

// Legacy export para compatibilidade
export const getFuncionarios = () => funcionarioService.getAtivos();
