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
import { precoDaEmbalagem, precoUnitarioNaEmbalagem } from '@/shared/utils/embalagem';

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
  | 'data.impressao'
  // Embalagem (fardo/caixa) — ver valoresDaEmbalagem
  | 'embalagem.descricao'
  | 'embalagem.conteudo'
  | 'preco.unidade'
  | 'preco.unidade_na_embalagem'
  // Envio (fase 5) — ver envio.ts
  | 'remetente.nome' | 'remetente.documento' | 'remetente.ie' | 'remetente.endereco' | 'remetente.bairro'
  | 'remetente.cidade_uf' | 'remetente.uf' | 'remetente.cep' | 'remetente.telefone'
  | 'destinatario.nome' | 'destinatario.documento' | 'destinatario.ie' | 'destinatario.endereco' | 'destinatario.bairro'
  | 'destinatario.cidade_uf' | 'destinatario.uf' | 'destinatario.cep' | 'destinatario.telefone'
  | 'envio.origem' | 'envio.codigo' | 'envio.peso' | 'envio.observacao'
  | 'volume.contador' | 'volume.rotulo'
  | 'nfe.numero' | 'nfe.chave' | 'nfe.chave_formatada' | 'nfe.protocolo' | 'nfe.data_emissao' | 'nfe.valor_total'
  | 'nfe.homologacao';

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
  // Só têm valor na etiqueta de uma embalagem (fardo/caixa).
  { campo: 'embalagem.descricao', rotulo: 'Embalagem (ex.: Fardo com 12)' },
  { campo: 'embalagem.conteudo', rotulo: 'Conteúdo (ex.: Contém 12 un)' },
  { campo: 'preco.unidade', rotulo: 'Preço da unidade avulsa' },
  { campo: 'preco.unidade_na_embalagem', rotulo: 'Preço da unidade dentro da embalagem' },
];

export const CAMPOS_VOLUME: { campo: CampoEtiqueta; rotulo: string }[] = [
  { campo: 'destinatario.nome', rotulo: 'Destinatário — nome' },
  { campo: 'destinatario.documento', rotulo: 'Destinatário — CPF/CNPJ' },
  { campo: 'destinatario.endereco', rotulo: 'Destinatário — rua e número' },
  { campo: 'destinatario.bairro', rotulo: 'Destinatário — bairro' },
  { campo: 'destinatario.cidade_uf', rotulo: 'Destinatário — cidade e UF' },
  { campo: 'destinatario.cep', rotulo: 'Destinatário — CEP' },
  { campo: 'destinatario.telefone', rotulo: 'Destinatário — telefone' },
  { campo: 'remetente.nome', rotulo: 'Remetente — nome' },
  { campo: 'remetente.documento', rotulo: 'Remetente — CNPJ' },
  { campo: 'remetente.endereco', rotulo: 'Remetente — rua e número' },
  { campo: 'remetente.cidade_uf', rotulo: 'Remetente — cidade e UF' },
  { campo: 'remetente.cep', rotulo: 'Remetente — CEP' },
  { campo: 'remetente.telefone', rotulo: 'Remetente — telefone' },
  { campo: 'volume.contador', rotulo: 'Volume (1/3)' },
  { campo: 'volume.rotulo', rotulo: 'Volume (VOLUME 1 DE 3)' },
  { campo: 'envio.origem', rotulo: 'Venda (número)' },
  { campo: 'envio.codigo', rotulo: 'Número da venda (para código de barras)' },
  { campo: 'envio.peso', rotulo: 'Peso' },
  { campo: 'envio.observacao', rotulo: 'Observação' },
  { campo: 'nfe.numero', rotulo: 'NF-e — número e série' },
  { campo: 'nfe.chave', rotulo: 'NF-e — chave (para código de barras)' },
  { campo: 'nfe.chave_formatada', rotulo: 'NF-e — chave (texto)' },
  { campo: 'data.impressao', rotulo: 'Data de impressão' },
];

export type OpcaoCampo = { campo: CampoEtiqueta; rotulo: string };

/** Campos que fazem sentido num CÓDIGO DE BARRAS, por fonte. */
export const CAMPOS_CODIGO_PRODUTO: OpcaoCampo[] = CAMPOS_PRODUTO.filter((c) =>
  (['produto.codigo_barras', 'produto.codigo_produto'] as CampoEtiqueta[]).includes(c.campo),
);
export const CAMPOS_CODIGO_VOLUME: OpcaoCampo[] = CAMPOS_VOLUME.filter((c) =>
  (['envio.codigo', 'nfe.chave'] as CampoEtiqueta[]).includes(c.campo),
);

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
    'preco.unidade': centavosParaTexto(produto.estoque?.valor_varejo),
    'preco.atacado': centavosParaTexto(produto.estoque?.valor_atacado),
    'empresa.nome': contexto.empresaNome ?? '',
    'data.impressao': (contexto.data ?? new Date()).toLocaleDateString('pt-BR'),
  };
}

/**
 * Valor do código de barras de uma etiqueta. Sem EAN, cai para o código
 * interno (§5.2) — produto sem nenhum dos dois não tem o que ler.
 *
 * Etiqueta de EMBALAGEM nunca cai para o código da unidade: o caixa bipava o
 * fardo e lançava uma lata. Sem código de fardo, a etiqueta sai sem barras.
 */
export function valorDoCodigo(valores: ValoresEtiqueta, campo: CampoEtiqueta): string {
  const valor = valores[campo] ?? '';
  if (valor || campo !== 'produto.codigo_barras' || valores['embalagem.conteudo']) return valor;
  return valores['produto.codigo_produto'] ?? '';
}

/** O mínimo da embalagem que a etiqueta usa — `EmbalagemRead` satisfaz. */
export interface EmbalagemParaEtiqueta {
  sigla: string;
  descricao: string | null;
  fator: number;
  codigo_barras: string | null;
  preco: number | null;
  desconto_bp: number | null;
}

/**
 * Valores da etiqueta de uma EMBALAGEM (fardo/caixa): o nome ganha a
 * embalagem, o código e o preço são os DELA. Os modelos de produto servem
 * sem mudança nenhuma — e o editor oferece os campos extras
 * ("Contém 12 un", preço da unidade dentro do fardo).
 */
export function valoresDaEmbalagem(
  produto: ProdutoParaEtiqueta,
  embalagem: EmbalagemParaEtiqueta,
  contexto: ContextoEtiqueta = {},
): ValoresEtiqueta {
  const base = valoresDoProduto(produto, contexto);
  const precoUnidade = produto.estoque?.valor_varejo ?? 0;
  const descricao = embalagem.descricao || `${embalagem.sigla} com ${embalagem.fator}`;
  return {
    ...base,
    'produto.nome': `${produto.nome} · ${descricao}`,
    'produto.codigo_barras': embalagem.codigo_barras ?? '',
    'preco.varejo': centavosParaTexto(precoDaEmbalagem(embalagem, precoUnidade)),
    'preco.atacado': '',
    'embalagem.descricao': descricao,
    'embalagem.conteudo': `Contém ${embalagem.fator} un`,
    'preco.unidade_na_embalagem': precoUnidade
      ? `${centavosParaTexto(precoUnitarioNaEmbalagem(embalagem, precoUnidade))} a unidade`
      : '',
  };
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
