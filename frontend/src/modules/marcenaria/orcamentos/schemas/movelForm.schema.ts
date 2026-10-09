/**
 * @fileoverview Formulário do modal do móvel (Spec 06B §6.4, D23-D30).
 *
 * A tela trabalha com números "de gente" (R$, horas, 1,4 chapa); a API, só com
 * inteiros (centavos, centésimos, milésimos). `paraApiMovel` faz a troca na
 * saída e `movelParaForm` na entrada. Nenhum preço é calculado aqui (C8): a
 * prévia vem da API (`/moveis/simular`).
 *
 * As regras de validação são as MESMAS do backend (06A `MovelEntrada`), para
 * o erro aparecer no campo antes de ir ao servidor.
 */
import { z } from 'zod';

import { LIMITES } from '../constants/orcamento.constants';
import type { MovelDetalhe } from './orcamentoDetalhe.schema';
import type { MovelEntrada } from '../services/orcamentoMovel.service';
import {
  centavosParaReais,
  centesimosParaHoras,
  horasParaCentesimos,
  milesimosParaQuantidade,
  quantidadeParaMilesimos,
  reaisParaCentavos,
} from '../utils/conversoes';

/** Uma medida: vazia, ou inteira entre 1 mm e 100 m (o backend recusa fora disso). */
const medida = z
  .number({ invalid_type_error: 'Use só números inteiros (milímetros).' })
  .int('Use só números inteiros (milímetros).')
  .min(1, 'As medidas devem ficar entre 1 mm e 100 m.')
  .max(100_000, 'As medidas devem ficar entre 1 mm e 100 m.')
  .nullable();

/** Uma linha de insumo como a TELA a guarda. */
export const insumoFormSchema = z.object({
  /** Identificador só da tela (para o Vue não confundir as linhas). */
  chave: z.string(),
  /** Insumo já gravado: mantém o custo copiado (06A §6.4). */
  id: z.number().optional(),
  produto_id: z.number().nullable(),
  descricao: z.string(),
  codigo: z.string().nullable(),
  unidade: z.string().nullable(),
  sofre_perda: z.boolean(),
  /** Quantidade na unidade do produto, até 3 casas (D25). */
  quantidade: z
    .number({ invalid_type_error: 'Informe a quantidade.' })
    .gt(0, 'A quantidade do insumo deve ser maior que zero.'),
  /** Custo unitário em R$ (só para quem vê custos). */
  custo_reais: z.number().min(0, 'O custo do insumo não pode ser negativo.').nullable(),
  /** ULTIMA_COMPRA | CUSTO_MEDIO | SEM_CUSTO | MANUAL (selo da linha, D27). */
  custo_origem: z.string().nullable(),
  /** True quando o usuário digitou o custo à mão: só então ele vai para a API. */
  custo_editado: z.boolean(),
});
export type InsumoForm = z.infer<typeof insumoFormSchema>;

export const movelFormSchema = z
  .object({
    nome: z
      .string()
      .trim()
      .min(1, 'Informe o nome do móvel.')
      .max(LIMITES.nomeMovel, `O nome do móvel aceita até ${LIMITES.nomeMovel} caracteres.`),
    descricao: z.string().max(LIMITES.descricaoMovel, `A descrição aceita até ${LIMITES.descricaoMovel} caracteres.`),
    largura_mm: medida,
    altura_mm: medida,
    profundidade_mm: medida,
    quantidade: z
      .number({ invalid_type_error: 'Informe a quantidade.' })
      .int('A quantidade do móvel é um número inteiro.')
      .min(1, 'A quantidade do móvel deve ficar entre 1 e 9999.')
      .max(9999, 'A quantidade do móvel deve ficar entre 1 e 9999.'),
    ambiente_id: z.number(),
    tipo_producao: z.enum(['INTERNA', 'TERCEIRIZADA']),
    central_fornecedor_id: z.number().nullable(),
    /** Valor da central em R$ (só quem vê custos). */
    terceirizado_reais: z.number().min(0, 'O valor da central não pode ser negativo.'),
    mao_obra_modo: z.enum(['NENHUMA', 'FIXA', 'HORAS']),
    mao_obra_reais: z.number().min(0, 'A mão de obra não pode ser negativa.'),
    mao_obra_horas: z.number().min(0, 'As horas não podem ser negativas.'),
    insumos: z
      .array(insumoFormSchema)
      .max(LIMITES.insumosPorMovel, `Um móvel aceita até ${LIMITES.insumosPorMovel} insumos.`),
  })
  // Terceirizado é pedido a uma central parceira (E6): sem ela, não há a quem pedir.
  .refine((m) => m.tipo_producao !== 'TERCEIRIZADA' || m.central_fornecedor_id != null, {
    message: 'Móvel terceirizado precisa da central parceira.',
    path: ['central_fornecedor_id'],
  });
export type MovelForm = z.infer<typeof movelFormSchema>;

/** Contador para dar uma chave única a cada linha nova de insumo. */
let proximaChave = 0;
export const novaChaveInsumo = (): string => `novo-${++proximaChave}`;

/** Formulário de um móvel novo, no ambiente escolhido. */
export function movelVazio(ambienteId: number): MovelForm {
  return {
    nome: '',
    descricao: '',
    largura_mm: null,
    altura_mm: null,
    profundidade_mm: null,
    quantidade: 1,
    ambiente_id: ambienteId,
    tipo_producao: 'INTERNA',
    central_fornecedor_id: null,
    terceirizado_reais: 0,
    mao_obra_modo: 'NENHUMA',
    mao_obra_reais: 0,
    mao_obra_horas: 0,
    insumos: [],
  };
}

/** Móvel gravado → formulário (ao clicar em "Editar"). */
export function movelParaForm(movel: MovelDetalhe): MovelForm {
  // Os campos de custo só existem na resposta de quem vê custos (06A D23).
  const comCustos = 'mao_obra' in movel ? movel : null;
  return {
    nome: movel.nome,
    descricao: movel.descricao ?? '',
    largura_mm: movel.largura_mm,
    altura_mm: movel.altura_mm,
    profundidade_mm: movel.profundidade_mm,
    quantidade: movel.quantidade,
    ambiente_id: movel.ambiente_id,
    tipo_producao: movel.tipo_producao,
    central_fornecedor_id: movel.central?.fornecedor_id ?? null,
    terceirizado_reais: comCustos ? centavosParaReais(comCustos.terceirizado_centavos) : 0,
    mao_obra_modo: comCustos ? comCustos.mao_obra.modo : 'NENHUMA',
    mao_obra_reais: comCustos ? centavosParaReais(comCustos.mao_obra.centavos) : 0,
    mao_obra_horas: comCustos ? centesimosParaHoras(comCustos.mao_obra.horas_centesimos) : 0,
    insumos: movel.insumos.map((insumo) => ({
      chave: `gravado-${insumo.id}`,
      id: insumo.id,
      produto_id: insumo.produto_id,
      descricao: insumo.descricao,
      codigo: insumo.codigo,
      unidade: insumo.unidade,
      sofre_perda: insumo.sofre_perda,
      quantidade: milesimosParaQuantidade(insumo.quantidade_milesimos),
      custo_reais: 'custo_unit_centavos' in insumo ? centavosParaReais(insumo.custo_unit_centavos) : null,
      custo_origem: 'custo_origem' in insumo ? insumo.custo_origem : null,
      custo_editado: false,
    })),
  };
}

/** Texto vazio vira null (o backend guarda "sem descrição" como null). */
const textoOuNulo = (texto: string): string | null => (texto.trim() ? texto.trim() : null);

/**
 * Formulário → corpo da API (06A §6.4).
 *
 * Sem `incluiCustos`, as chaves de custo (`mao_obra`, `terceirizado_centavos`,
 * `custo_unit_centavos`) ficam AUSENTES: o backend mantém o que o dono lançou
 * (06A D24a). Mandar zero apagaria a mão de obra dele.
 */
export function paraApiMovel(form: MovelForm, incluiCustos: boolean): MovelEntrada {
  const terceirizado = form.tipo_producao === 'TERCEIRIZADA';
  const corpo: MovelEntrada = {
    nome: form.nome.trim(),
    descricao: textoOuNulo(form.descricao),
    largura_mm: form.largura_mm,
    altura_mm: form.altura_mm,
    profundidade_mm: form.profundidade_mm,
    quantidade: form.quantidade,
    tipo_producao: form.tipo_producao,
    central_fornecedor_id: terceirizado ? form.central_fornecedor_id : null,
    ambiente_id: form.ambiente_id,
    insumos: form.insumos.map((insumo) => {
      const linha: MovelEntrada['insumos'][number] = {
        quantidade_milesimos: quantidadeParaMilesimos(insumo.quantidade),
      };
      if (insumo.id != null) linha.id = insumo.id;              // gravado: mantém o custo copiado
      else linha.produto_id = insumo.produto_id;                 // novo: copia do produto
      // Custo digitado à mão vai só quando quem edita vê custos (06A D24).
      if (incluiCustos && insumo.custo_editado && insumo.custo_reais != null) {
        linha.custo_unit_centavos = reaisParaCentavos(insumo.custo_reais);
      }
      return linha;
    }),
  };
  if (incluiCustos) {
    corpo.terceirizado_centavos = terceirizado ? reaisParaCentavos(form.terceirizado_reais) : 0;
    corpo.mao_obra = {
      modo: form.mao_obra_modo,
      centavos: form.mao_obra_modo === 'FIXA' ? reaisParaCentavos(form.mao_obra_reais) : 0,
      horas_centesimos: form.mao_obra_modo === 'HORAS' ? horasParaCentesimos(form.mao_obra_horas) : 0,
    };
  }
  return corpo;
}

/** A prévia só é pedida com nome e quantidade válidos (o backend recusaria). */
export function movelSimulavel(form: MovelForm): boolean {
  return form.nome.trim().length > 0 && Number.isInteger(form.quantidade) && form.quantidade >= 1
    && form.insumos.every((i) => i.quantidade > 0)
    && (form.tipo_producao !== 'TERCEIRIZADA' || form.central_fornecedor_id != null);
}
