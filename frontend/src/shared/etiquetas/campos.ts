/**
 * @fileoverview Catálogo dos dados que uma etiqueta pode imprimir
 * (docs/etiquetas-plano.md §5.3).
 *
 * O modelo guarda só a CHAVE do campo (`produto.nome`); o valor é resolvido na
 * hora de imprimir, a partir do produto da fila. Assim um preço alterado de
 * manhã já sai certo na etiqueta da tarde, sem reeditar modelo nenhum.
 *
 * O remetente/empresa vem SEMPRE do cadastro da Empresa — nada de cidade ou
 * nome escritos no modelo.
 */

import { formatCurrency } from '@/shared/utils/finance';

export type CampoEtiqueta =
  | 'produto.nome'
  | 'produto.codigo_produto'
  | 'produto.codigo_barras'
  | 'produto.marca'
  | 'produto.categoria'
  | 'produto.unidade_medida'
  | 'produto.localizacao_estoque'
  | 'preco.varejo'
  | 'preco.atacado'
  | 'empresa.nome'
  | 'data.impressao';

export const CAMPOS_PRODUTO: { campo: CampoEtiqueta; rotulo: string }[] = [
  { campo: 'produto.nome', rotulo: 'Nome do produto' },
  { campo: 'produto.codigo_produto', rotulo: 'Código interno' },
  { campo: 'produto.codigo_barras', rotulo: 'Código de barras (EAN)' },
  { campo: 'produto.marca', rotulo: 'Marca' },
  { campo: 'produto.categoria', rotulo: 'Categoria' },
  { campo: 'produto.unidade_medida', rotulo: 'Unidade' },
  { campo: 'produto.localizacao_estoque', rotulo: 'Localização no estoque' },
  { campo: 'preco.varejo', rotulo: 'Preço de varejo' },
  { campo: 'preco.atacado', rotulo: 'Preço de atacado' },
  { campo: 'empresa.nome', rotulo: 'Nome da empresa' },
  { campo: 'data.impressao', rotulo: 'Data de impressão' },
];

export type ValoresEtiqueta = Partial<Record<CampoEtiqueta, string>>;

/** O mínimo do produto que a etiqueta usa — `ProdutoRead` satisfaz. */
export interface ProdutoParaEtiqueta {
  nome: string;
  codigo_produto?: string | null;
  codigo_barras?: string | null;
  marca?: string | null;
  categoria?: string | null;
  unidade_medida?: string | null;
  localizacao_estoque?: string | null;
  estoque?: { valor_varejo?: number | null; valor_atacado?: number | null } | null;
}

export interface ContextoEtiqueta {
  empresaNome?: string | null;
  data?: Date;
}

function centavosParaTexto(centavos: number | null | undefined): string {
  return centavos ? formatCurrency(centavos) : '';
}

export function valoresDoProduto(produto: ProdutoParaEtiqueta, contexto: ContextoEtiqueta = {}): ValoresEtiqueta {
  return {
    'produto.nome': produto.nome,
    'produto.codigo_produto': produto.codigo_produto ?? '',
    'produto.codigo_barras': produto.codigo_barras ?? '',
    'produto.marca': produto.marca ?? '',
    'produto.categoria': produto.categoria ?? '',
    'produto.unidade_medida': produto.unidade_medida ?? '',
    'produto.localizacao_estoque': produto.localizacao_estoque ?? '',
    'preco.varejo': centavosParaTexto(produto.estoque?.valor_varejo),
    'preco.atacado': centavosParaTexto(produto.estoque?.valor_atacado),
    'empresa.nome': contexto.empresaNome ?? '',
    'data.impressao': (contexto.data ?? new Date()).toLocaleDateString('pt-BR'),
  };
}

/**
 * Valor do código de barras de uma etiqueta. Sem EAN, cai para o código
 * interno (§5.2) — produto sem nenhum dos dois não tem o que ler.
 */
export function valorDoCodigo(valores: ValoresEtiqueta, campo: CampoEtiqueta): string {
  const valor = valores[campo] ?? '';
  if (valor || campo !== 'produto.codigo_barras') return valor;
  return valores['produto.codigo_produto'] ?? '';
}

/** Valores de exemplo para o preview de um modelo sem fila. */
export const VALORES_EXEMPLO: ValoresEtiqueta = valoresDoProduto(
  {
    nome: 'Produto de exemplo com nome comprido',
    codigo_produto: 'PRD-0001',
    codigo_barras: '7891000100103',
    marca: 'Marca',
    categoria: 'Categoria',
    unidade_medida: 'UN',
    localizacao_estoque: 'Corredor 3 · Prateleira B',
    estoque: { valor_varejo: 1290, valor_atacado: 1090 },
  },
  { empresaNome: 'Minha Loja' },
);
