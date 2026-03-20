// ===========================================================================
// TIPOS COMPARTILHADOS (resumos usados em relacionamentos)
// ===========================================================================

export interface ClienteResumo {
  id: number;
  tipo: 'PF' | 'PJ';
  nome?: string | null;
  cpf?: string | null;
  razao_social?: string | null;
  cnpj?: string | null;
  nome_fantasia?: string | null;
  celular?: string | null;
  telefone?: string | null;
}

export interface FuncionarioResumo {
  id: number;
  nome: string;
}
