/**
 * @fileoverview Tipos do orçamento de marcenaria num lugar só (Spec 06B §3).
 *
 * Os tipos da API nascem dos schemas zod (`z.infer`): assim o tipo e a
 * validação nunca discordam. Este arquivo só os reexporta para as telas
 * importarem de um endereço curto.
 */
export type {
  AcoesOrcamento,
  AjusteOrcamento,
  AmbienteDetalhe,
  AnexoOrcamento,
  ContagensOrcamento,
  EventoOrcamento,
  InsumoDetalhe,
  ItemListaOrcamento,
  ListaOrcamentos,
  MovelComCustos,
  MovelDetalhe,
  OrcamentoDetalhe,
  OrcamentoDetalheComCustos,
  PrecosDesatualizados,
  ProjetoCliente,
  SimulacaoMovel,
  VersaoOrcamento,
} from '../schemas/orcamentoDetalhe.schema';
export type { InsumoForm, MovelForm } from '../schemas/movelForm.schema';
export type { InsumoRapidoForm } from '../schemas/insumoRapido.schema';
export type { CabecalhoForm } from '../utils/diferencaCabecalho';
export type { DadosProposta } from '../utils/dadosProposta';
export type { StatusOrcamento } from '../constants/orcamento.constants';

/** Modo do desconto e do sinal (C7, C9). */
export type ModoAjuste = 'PERCENTUAL' | 'VALOR';
