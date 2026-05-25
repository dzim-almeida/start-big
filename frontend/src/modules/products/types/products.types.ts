/**
 * @fileoverview Types for the products module
 * @description Matches backend schemas for Produto and Estoque
 */

import type { Component } from 'vue';

// =============================================
// API TYPES (matching produto.py and estoque.py)
// =============================================

export interface ProdutoFotoRead {
  id: number;
  nome_arquivo?: string | null;
  url: string;
  principal?: boolean;
}

export interface EstoqueCreate {
  valor_varejo: number;
  quantidade?: number;
  valor_entrada?: number;
  valor_atacado?: number;
  quantidade_ideal?: number;
  quantidade_minima?: number;
}

export interface EstoqueRead extends EstoqueCreate {
  id: number;
}

export interface EstoqueUpdate {
  valor_varejo?: number;
  quantidade?: number;
  valor_entrada?: number;
  valor_atacado?: number;
  quantidade_ideal?: number;
  quantidade_minima?: number;
}

export interface ProdutoBase {
  nome: string;
  codigo_produto: string;
  codigo_barras?: string | null;
  unidade_medida?: string | null;
  observacao?: string | null;
  categoria?: string | null;
  marca?: string | null;
  fornecedor_id?: number | null;
  localizacao_estoque?: string | null;
}

export interface ProdutoCreate extends ProdutoBase {
  estoque: EstoqueCreate;
}

export interface ProdutoRead extends ProdutoBase {
  id: number;
  estoque: EstoqueRead;
  ativo: boolean;
  fotos?: ProdutoFotoRead[];
}

export interface ProdutoUpdate extends Partial<ProdutoBase> {
  estoque?: EstoqueUpdate;
}

// =============================================
// UI TYPES
// =============================================

export interface TabOption {
  id: string;
  label: string;
}

export type ModalMode = 'create' | 'edit' | 'view';

export interface ModalState {
  isOpen: boolean;
  mode: ModalMode;
  productId: number | null;
}

export interface CardInfo {
  key: string;
  icon: Component;
  label: string;
}

// =============================================
// FORM TYPES
// =============================================

export interface ProductFormData {
  nome: string;
  codigo_produto: string;
  codigo_barras: string;
  unidade_medida: string;
  categoria: string;
  marca: string;
  fornecedor_id: string;
  localizacao_estoque: string;
  observacao: string;

  valor_entrada: number;
  valor_varejo: number;
  valor_atacado: number;
  quantidade: number;
  quantidade_minima: number;
  quantidade_ideal: number;
}
