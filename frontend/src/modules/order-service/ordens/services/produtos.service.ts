import api from '@/api/axios';

export interface EstoqueRead {
  id: number;
  valor_varejo: number;
  quantidade: number;
  valor_entrada?: number;
  valor_atacado?: number;
  quantidade_ideal?: number;
  quantidade_minima?: number;
}

export interface ProdutoRead {
  id: number;
  nome: string;
  codigo_produto: string;
  codigo_barras?: string;
  unidade_medida?: string;
  observacao?: string;
  categoria?: string;
  marca?: string;
  fornecedor_id?: number;
  estoque: EstoqueRead;
  ativo: boolean;
}

class ProdutosService {
  private readonly BASE_URL = '/produtos';

  async getAll(buscar?: string): Promise<ProdutoRead[]> {
    const params = buscar ? { buscar } : {};
    const response = await api.get<ProdutoRead[]>(this.BASE_URL, { params });
    return response.data;
  }

  async getById(id: number): Promise<ProdutoRead> {
    const response = await api.get<ProdutoRead>(`${this.BASE_URL}/${id}`);
    return response.data;
  }
}

export const produtosService = new ProdutosService();

export const getProdutos = (buscar?: string) => produtosService.getAll(buscar);
export const getProdutoById = (id: number) => produtosService.getById(id);
