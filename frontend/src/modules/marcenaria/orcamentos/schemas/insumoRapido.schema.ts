/**
 * @fileoverview Cadastro rápido de insumo, sem sair do orçamento (Spec 06B
 * D31-D35, T4).
 *
 * Usa o `POST /produtos` que já existe. Só os campos que a marcenaria precisa;
 * o cadastro completo (fotos, fiscal, fornecedor) continua na tela de Produtos.
 */
import { z } from 'zod';

import type { ProdutoCreate } from '@/modules/products/inventory/types/products.types';

import { reaisParaCentavos } from '../utils/conversoes';

/**
 * Monta o schema conforme as regras da loja (D34): quando a configuração de
 * produtos exige categoria ou código de barras, o cadastro rápido também exige
 * (não pode ser um atalho para burlar a regra).
 */
export function insumoRapidoSchema(exigir: { categoria: boolean; codigoBarras: boolean }) {
  return z.object({
    nome: z.string().trim().min(1, 'Informe o nome do insumo.').max(150, 'O nome aceita até 150 caracteres.'),
    codigo: z.string().trim().min(1, 'Informe o código do insumo.').max(60, 'O código aceita até 60 caracteres.'),
    unidade: z.string().min(1, 'Escolha a unidade.'),
    /** Custo de compra em R$ (vira o "último preço de compra" do produto). */
    custo_reais: z
      .number({ invalid_type_error: 'Informe o custo de compra.' })
      .min(0, 'O custo não pode ser negativo.'),
    /** Preço de venda no balcão; vazio = igual ao custo (D33). */
    preco_venda_reais: z.number().min(0, 'O preço não pode ser negativo.').nullable(),
    sofre_perda: z.boolean(),
    categoria: exigir.categoria
      ? z.string().trim().min(1, 'Informe a categoria (exigida nas configurações de produtos).')
      : z.string(),
    codigo_barras: exigir.codigoBarras
      ? z.string().trim().min(1, 'Informe o código de barras (exigido nas configurações de produtos).')
      : z.string(),
  });
}
export type InsumoRapidoForm = z.infer<ReturnType<typeof insumoRapidoSchema>>;

/** Código sugerido (D32): "INS-" + 6 dígitos do relógio. Editável. */
export function sugerirCodigoInsumo(agora: number = Date.now()): string {
  return `INS-${String(agora).slice(-6)}`;
}

/** Formulário vazio, com o código sugerido e a unidade padrão da loja. */
export function insumoRapidoVazio(nome: string, unidadePadrao: string): InsumoRapidoForm {
  return {
    nome,
    codigo: sugerirCodigoInsumo(),
    unidade: unidadePadrao,
    custo_reais: 0,
    preco_venda_reais: null,
    sofre_perda: false,
    categoria: '',
    codigo_barras: '',
  };
}

/**
 * Formulário → corpo do `POST /produtos`.
 * - Estoque começa em zero (o insumo ainda não foi comprado, D31).
 * - Preço de venda vazio grava o CUSTO (D33): zero deixaria o item ser vendido
 *   de graça no PDV; igual ao custo é o erro menos caro.
 */
export function paraProdutoCreate(form: InsumoRapidoForm): ProdutoCreate {
  const custo = reaisParaCentavos(form.custo_reais);
  return {
    nome: form.nome.trim(),
    codigo_produto: form.codigo.trim(),
    unidade_medida: form.unidade,
    sofre_perda: form.sofre_perda,
    categoria: form.categoria.trim() || null,
    codigo_barras: form.codigo_barras.trim() || null,
    estoque: {
      quantidade: 0,
      valor_entrada: custo,
      valor_varejo: form.preco_venda_reais != null ? reaisParaCentavos(form.preco_venda_reais) : custo,
    },
  };
}
