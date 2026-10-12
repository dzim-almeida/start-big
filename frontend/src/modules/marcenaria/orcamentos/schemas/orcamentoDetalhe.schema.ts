/**
 * @fileoverview Zod das respostas da API do orçamento (Spec 06A §6, 08A §6.4, 09A).
 *
 * O detalhe vem em DUAS formas, decididas por `inclui_custos` (06A D23):
 * - sem custos: nenhuma chave de custo, margem, RT, markup ou perda;
 * - com custos: tudo.
 * A união discriminada (`z.discriminatedUnion`) confere a forma certa e deixa o
 * TypeScript saber, depois de um `if (detalhe.inclui_custos)`, quais campos
 * existem. Chave desconhecida é removida pelo zod (não chega à tela).
 */
import { z } from 'zod';

const centavos = z.number().int();
const dataTexto = z.string().nullable();             // datas chegam como texto ISO

// ---------------------------------------------------------------------------
// Insumo, móvel e ambiente
// ---------------------------------------------------------------------------

const insumoBase = z.object({
  id: z.number(),
  produto_id: z.number().nullable(),
  descricao: z.string(),
  codigo: z.string().nullable(),
  unidade: z.string().nullable(),
  quantidade_milesimos: z.number().int(),            // 1,4 chapa = 1400
  sofre_perda: z.boolean(),
});
const insumoComCustos = insumoBase.extend({
  custo_unit_centavos: centavos,
  custo_origem: z.string(),                          // ULTIMA_COMPRA | CUSTO_MEDIO | SEM_CUSTO | MANUAL
});

const calculoMovelBase = z.object({                  // o que todos veem
  preco_unit_centavos: centavos,                     // preço de uma unidade do móvel
  preco_total_centavos: centavos,                    // preço × quantidade
});
const calculoMovelComCustos = calculoMovelBase.extend({   // só com view_custos (06A D23)
  material_centavos: centavos,
  perda_centavos: centavos,
  mao_obra_centavos: centavos,
  custo_unit_centavos: centavos,
  custo_total_centavos: centavos,
  rt_linha_centavos: centavos,
});

const maoObra = z.object({
  modo: z.enum(['FIXA', 'HORAS', 'NENHUMA']),
  centavos,
  horas_centesimos: z.number().int(),
});

const movelBase = z.object({
  id: z.number(),
  ambiente_id: z.number(),
  nome: z.string(),
  descricao: z.string().nullable(),
  largura_mm: z.number().nullable(),
  altura_mm: z.number().nullable(),
  profundidade_mm: z.number().nullable(),
  quantidade: z.number().int(),
  ordem: z.number(),
  tipo_producao: z.enum(['INTERNA', 'TERCEIRIZADA']),
  central: z.object({ fornecedor_id: z.number(), nome: z.string() }).nullable(),
  aprovado: z.boolean().nullable(),                  // null até a aprovação (08A)
  os_item_id: z.number().nullable().optional(),      // o item da OS que o móvel virou (08A)
  insumos: z.array(insumoBase),
  calculo: calculoMovelBase.nullable(),
});
const movelComCustos = movelBase.extend({
  terceirizado_centavos: centavos,
  mao_obra: maoObra,
  insumos: z.array(insumoComCustos),
  calculo: calculoMovelComCustos.nullable(),
});

const ambienteBase = z.object({
  id: z.number(),
  nome: z.string(),
  ordem: z.number(),
  subtotal_centavos: centavos,                       // bruto, antes do desconto (T5)
  moveis: z.array(movelBase),
});
const ambienteComCustos = ambienteBase.extend({
  custo_centavos: centavos,
  moveis: z.array(movelComCustos),
});

// ---------------------------------------------------------------------------
// Totais, parâmetros, arquitetos
// ---------------------------------------------------------------------------

const calculoBase = z.object({
  bruto_centavos: centavos,
  desconto_centavos: centavos,
  total_centavos: centavos,
  sinal_centavos: centavos,
  saldo_centavos: centavos,
  desconto_bp_efetivo: z.number().int(),             // "≈ 5%" quando o desconto é em R$ (D18)
  sinal_bp_efetivo: z.number().int(),
  instalacao: z.object({ preco_centavos: centavos }).nullable(),
});
const calculoComCustos = calculoBase.extend({
  custo_total_centavos: centavos,
  margem_bruta_centavos: centavos,
  rt_total_centavos: centavos,
  margem_liquida_centavos: centavos,
  margem_liquida_bp: z.number().int(),
  instalacao: z.object({ preco_centavos: centavos, custo_centavos: centavos }).nullable(),
});

const parametrosBase = z.object({ validade_dias: z.number(), prazo_entrega_dias: z.number() });
const parametrosComCustos = parametrosBase.extend({
  markup_bp: z.number().int(),
  perda_bp: z.number().int(),
  custo_hora_centavos: centavos,
  rt_padrao_bp: z.number().int(),
  rt_modo: z.enum(['MARGEM', 'PRECO']),
});

const arquitetoBase = z.object({ fornecedor_id: z.number(), nome: z.string() });
const arquitetoComCustos = arquitetoBase.extend({
  rt_bp: z.number().int(),
  valor_previsto_centavos: centavos,
  // A conta a pagar do RT, depois da finalização da OS (09A Revisão 1).
  conta: z.object({ id: z.number(), status: z.string(), valor_centavos: centavos, vencimento: z.string() })
    .nullable().optional(),
});

const ajuste = z.object({ modo: z.enum(['PERCENTUAL', 'VALOR']), valor: z.number().int() });

const acoes = z.object({
  editar: z.boolean(),
  enviar: z.boolean(),
  voltar_a_editar: z.boolean(),
  recusar: z.boolean(),
  renovar: z.boolean(),
  nova_versao: z.boolean(),
  excluir: z.boolean(),
  anexos: z.boolean().default(false),
  aprovar: z.boolean().default(false),
  desfazer_aprovacao: z.boolean().default(false),
});

// ---------------------------------------------------------------------------
// Detalhe (06A §6.2)
// ---------------------------------------------------------------------------

/** Campos iguais nas duas formas (nenhum é custo). */
const comum = {
  id: z.number(),
  codigo: z.string(),
  versao: z.number(),
  status: z.enum(['RASCUNHO', 'ENVIADO', 'APROVADO', 'RECUSADO', 'VENCIDO', 'SUBSTITUIDO']),
  revisao: z.number(),                                // trava otimista (06A D20)
  cliente: z.object({
    id: z.number(),
    nome: z.string(),
    documento: z.string().nullable(),
    telefone: z.string().nullable(),
    email: z.string().nullable(),
    endereco: z.string(),
  }).nullable(),
  vendedor: z.object({ id: z.number(), nome: z.string(), telefone: z.string().nullable() }).nullable(),
  projeto: z.object({
    objeto_id: z.number().nullable(),
    nome: z.string().nullable(),
    endereco_obra: z.string().nullable(),
  }),
  medicao_observacoes: z.string().nullable(),
  observacoes_proposta: z.string().nullable(),
  desconto: ajuste,
  sinal: ajuste,
  avisos: z.array(z.string()),
  datas: z.object({
    criacao: dataTexto,
    atualizacao: dataTexto,
    envio: dataTexto,
    validade: dataTexto,
    recusa: dataTexto,
    aprovacao: dataTexto,
  }),
  motivo_recusa: z.string().nullable(),
  os: z.object({ id: z.number(), numero_os: z.string(), status: z.string() }).nullable().optional(),
  acoes,
};

const aprovacaoBase = z.object({
  data: dataTexto,
  instalacao_aprovada: z.boolean().nullable(),
  total_centavos: centavos.nullable(),
  sinal_combinado_centavos: centavos.nullable(),
  sinal_recebido_centavos: centavos.nullable(),
  calculo: calculoBase.nullable(),
});
const aprovacaoComCustos = aprovacaoBase.extend({ calculo: calculoComCustos.nullable() });

export const detalheSemCustosSchema = z.object({
  ...comum,
  parametros: parametrosBase,
  arquitetos: z.array(arquitetoBase),
  ambientes: z.array(ambienteBase),
  calculo: calculoBase,
  aprovacao: aprovacaoBase.nullable().optional(),
  inclui_custos: z.literal(false),
});

export const detalheComCustosSchema = z.object({
  ...comum,
  parametros: parametrosComCustos,
  arquitetos: z.array(arquitetoComCustos),
  instalacao_custo_centavos: centavos.nullable(),
  ambientes: z.array(ambienteComCustos),
  calculo: calculoComCustos,
  aprovacao: aprovacaoComCustos.nullable().optional(),
  inclui_custos: z.literal(true),
});

export const orcamentoDetalheSchema = z.discriminatedUnion('inclui_custos', [
  detalheSemCustosSchema,                             // vendedor sem custos
  detalheComCustosSchema,                             // dono, gerente
]);

export type OrcamentoDetalhe = z.infer<typeof orcamentoDetalheSchema>;
export type OrcamentoDetalheComCustos = z.infer<typeof detalheComCustosSchema>;
export type AmbienteDetalhe = OrcamentoDetalhe['ambientes'][number];
export type MovelDetalhe = AmbienteDetalhe['moveis'][number];
export type MovelComCustos = z.infer<typeof movelComCustos>;
export type InsumoDetalhe = MovelDetalhe['insumos'][number];
export type AcoesOrcamento = z.infer<typeof acoes>;
export type AjusteOrcamento = z.infer<typeof ajuste>;

// ---------------------------------------------------------------------------
// Lista, contagens, versões, histórico, projetos, anexos, preços, simulação
// ---------------------------------------------------------------------------

export const itemListaSchema = z.object({
  id: z.number(),
  codigo: z.string(),
  versao: z.number(),
  status: comum.status,
  cliente_nome: z.string().nullable(),
  projeto_nome: z.string().nullable(),
  vendedor_nome: z.string().nullable(),
  resumo_total_centavos: centavos,
  resumo_qtd_moveis: z.number(),
  data_validade: dataTexto,
  data_atualizacao: dataTexto,
  os_numero: z.string().nullable().optional(),        // aprovado: a OS gerada (08A)
  resumo_margem_bp: z.number().optional(),             // só com custos
});
export type ItemListaOrcamento = z.infer<typeof itemListaSchema>;

export const listaSchema = z.object({
  items: z.array(itemListaSchema),
  total_items: z.number(),
  page: z.number(),
  limit: z.number(),
  total_pages: z.number(),
});
export type ListaOrcamentos = z.infer<typeof listaSchema>;

export const contagensSchema = z.object({
  RASCUNHO: z.number(),
  ENVIADO: z.number(),
  VENCIDO: z.number(),
  RECUSADO: z.number(),
  APROVADO: z.number(),
  vence_em_3_dias: z.number(),
  total: z.number(),
});
export type ContagensOrcamento = z.infer<typeof contagensSchema>;

export const versaoSchema = z.object({
  id: z.number(),
  versao: z.number(),
  status: comum.status,
  resumo_total_centavos: centavos,
  data_criacao: dataTexto,
  data_envio: dataTexto,
  data_validade: dataTexto,
  data_recusa: dataTexto,
});
export type VersaoOrcamento = z.infer<typeof versaoSchema>;

export const eventoSchema = z.object({
  id: z.number(),
  orcamento_id: z.number().nullable(),
  tipo: z.string(),
  descricao: z.string(),
  usuario_nome: z.string(),
  ocorrido_em: z.string(),
});
export type EventoOrcamento = z.infer<typeof eventoSchema>;

export const projetoSchema = z.object({
  objeto_id: z.number(),
  identificador: z.string().nullable(),
  nome: z.string(),
  endereco_obra: z.string().nullable(),
  ultimo_uso: z.string(),
});
export type ProjetoCliente = z.infer<typeof projetoSchema>;

/**
 * Um arquiteto do select "Quem indicou" (Spec 09B D4). Só o necessário para
 * escolher: o PIX e os dados bancários ficam no cadastro de fornecedores.
 */
export const arquitetoOpcaoSchema = z.object({
  id: z.number(),
  nome: z.string(),
  nome_fantasia: z.string().nullable(),               // o escritório
});
export type ArquitetoOpcao = z.infer<typeof arquitetoOpcaoSchema>;

export const anexoSchema = z.object({
  id: z.number(),
  tipo: z.enum(['FOTO', 'PDF']),
  nome_arquivo: z.string(),
  url: z.string(),
  legenda: z.string().nullable(),
  data_criacao: z.string(),
});
export type AnexoOrcamento = z.infer<typeof anexoSchema>;

export const precosDesatualizadosSchema = z.object({
  itens: z.array(z.object({
    insumo_id: z.number(),
    movel: z.string(),
    descricao: z.string(),
    custo_atual_orcamento: centavos,
    custo_produto_hoje: centavos,
    origem_hoje: z.string(),
    sofre_perda_orcamento: z.boolean(),
    sofre_perda_hoje: z.boolean(),
  })),
  total_atual_centavos: centavos,
  total_com_precos_novos_centavos: centavos,
  diferenca_centavos: centavos,
});
export type PrecosDesatualizados = z.infer<typeof precosDesatualizadosSchema>;

/** Prévia de um móvel (06A §6.6): sem custos, só os preços e o que não é custo. */
export const simulacaoSchema = z.object({
  calculo: z.object({
    preco_unit_centavos: centavos,
    preco_total_centavos: centavos,
    custo_unit_centavos: centavos.optional(),
    material_centavos: centavos.optional(),
    perda_centavos: centavos.optional(),
    mao_obra_centavos: centavos.optional(),
  }),
  insumos: z.array(z.object({
    produto_id: z.number().nullable(),
    sofre_perda: z.boolean(),
    custo_unit_centavos: centavos.optional(),
    custo_origem: z.string().optional(),
  })),
  avisos: z.array(z.string()),
});
export type SimulacaoMovel = z.infer<typeof simulacaoSchema>;
