/**
 * @fileoverview Tipos da marcenaria-fábrica (backend: app/schemas/fabrica.py).
 */

/** M2 = chapa (rende mm²), M = fita/perfil (rende mm), UN = ferragem. */
export type UnidadeConsumo = 'M2' | 'M' | 'UN';

export interface InsumoRead {
  produto_id: number;
  /** Unidade do ESTOQUE — a de compra (chapa, rolo, UN). */
  unidade_medida: string | null;
  /** `null` = o produto não é insumo. */
  unidade_consumo: UnidadeConsumo | null;
  /** Rendimento de uma unidade de estoque: mm² (M2), mm (M) ou unidades (UN). */
  consumo_por_unidade: number | null;
  sofre_perda: boolean;
}

export interface InsumoEscrita {
  unidade_consumo: UnidadeConsumo | null;
  consumo_por_unidade: number | null;
  sofre_perda: boolean;
}

// ---------------------------------------------------------------------------
// F2 — orçamento por móvel (backend: OrcamentoRead e companhia)
// ---------------------------------------------------------------------------

export type SituacaoOrcamento = 'RASCUNHO' | 'ENVIADO' | 'APROVADO' | 'RECUSADO' | 'VENCIDO';

export interface InsumoBusca {
  id: number;
  nome: string;
  codigo_produto: string | null;
  unidade_medida: string | null;
  unidade_consumo: UnidadeConsumo;
  consumo_por_unidade: number;
  sofre_perda: boolean;
  /** Custo de hoje por unidade de compra — o que a linha nova vai copiar. Nulo sem permissão de custo. */
  custo_unitario: number | null;
}

export interface MaterialEscrita {
  id?: number | null;
  produto_id: number;
  /** Inteiro na unidade de consumo: mm², mm ou unidades. */
  consumo: number;
}

export interface MovelEscrita {
  nome: string;
  largura_mm: number | null;
  altura_mm: number | null;
  profundidade_mm: number | null;
  preco_venda: number;
  terceirizado: boolean;
  custo_terceiro: number | null;
  materiais: MaterialEscrita[];
}

export interface AmbienteEscrita {
  nome: string;
  moveis: MovelEscrita[];
}

export interface OrcamentoEscrita {
  perda_bp: number;
  sinal_bp: number;
  validade: string | null;
  observacao: string | null;
  ambientes: AmbienteEscrita[];
}

export interface MaterialRead {
  id: number;
  produto_id: number | null;
  descricao: string;
  consumo: number;
  unidade_consumo: UnidadeConsumo | null;
  consumo_por_unidade: number | null;
  sofre_perda: boolean;
  unidade_medida: string | null;
  /** Nulos sem a permissão de custo (linha Fábrica de Cargos). */
  custo_unitario: number | null;
  custo: number | null;
}

export interface MovelRead {
  id: number;
  nome: string;
  largura_mm: number | null;
  altura_mm: number | null;
  profundidade_mm: number | null;
  medidas: string | null;
  preco_venda: number;
  terceirizado: boolean;
  custo_terceiro: number | null;
  custo: number | null;
  materiais: MaterialRead[];
}

export interface AmbienteRead {
  id: number;
  nome: string;
  moveis: MovelRead[];
}

export interface InsumoDaAprovacao {
  produto_id: number;
  descricao: string;
  unidade_medida: string | null;
  consumo_total: number;
  /** Unidades de compra inteiras (chapas, rolos). */
  quantidade: number;
  custo_unitario: number | null;
}

export interface OrcamentoResumo {
  id: number;
  versao: number;
  situacao: SituacaoOrcamento;
  total: number;
  criado_em: string;
  enviado_em: string | null;
  aprovado_em: string | null;
}

export interface OrcamentoRead extends OrcamentoResumo {
  os_id: number;
  numero_os: string;
  perda_bp: number;
  sinal_bp: number;
  sinal_valor: number;
  validade: string | null;
  custo_total: number | null;
  observacao: string | null;
  aprovado_por: string | null;
  recusado_motivo: string | null;
  editavel: boolean;
  ambientes: AmbienteRead[];
  insumos: InsumoDaAprovacao[];
}

// ---------------------------------------------------------------------------
// F3 — o trilho
// ---------------------------------------------------------------------------

export interface TravaRead {
  codigo: string;
  texto: string;
  ok: boolean;
}

export interface EtapaRead {
  fase: string;
  rotulo: string;
  situacao: 'FEITA' | 'ATUAL' | 'A_FAZER';
}

export interface LogFaseRead {
  fase_anterior: string | null;
  fase_nova: string | null;
  evento: string;
  motivo: string | null;
  usuario: string | null;
  ocorrido_em: string;
}

export interface TrilhoRead {
  numero_os: string;
  fase: string;
  rotulo: string;
  status_os: string;
  aberta: boolean;
  /** true: pendência bloqueia; false: vira aviso e pede motivo. */
  travar_etapas: boolean;
  etapas: EtapaRead[];
  proxima: string | null;
  proxima_rotulo: string | null;
  /** Sair desta etapa é uma ação própria (enviar, aprovar, finalizar). */
  avanco_por_acao: string | null;
  travas: TravaRead[];
  sinal_exigido: number;
  recebido: number;
  pode_comprar: boolean;
  compra_liberada_em: string | null;
  compra_liberada_por: string | null;
  compra_liberada_motivo: string | null;
  data_instalacao: string | null;
  log: LogFaseRead[];
}
