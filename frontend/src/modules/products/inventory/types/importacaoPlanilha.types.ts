/** Importação de produtos por planilha Excel. */

export type SituacaoLinha = 'novo' | 'existe' | 'ignorado' | 'erro';

export interface LinhaImportacao {
  linha: number;
  codigo: string;
  nome: string;
  unidade?: string | null;
  ncm?: string | null;
  /** Em centavos. */
  custo?: number | null;
  /** Em centavos. */
  preco?: number | null;
  estoque: number;
  situacao: SituacaoLinha;
  mensagens: string[];
}

export interface PreviaImportacao {
  novos: number;
  ja_existem: number;
  ignorados: number;
  com_erro: number;
  fiscal_disponivel: boolean;
  planilha_tem_fiscal: boolean;
  linhas: LinhaImportacao[];
}

export interface ResultadoImportacaoPlanilha {
  criados: number;
  ja_existiam: number;
  ignorados: number;
  com_erro: number;
}
