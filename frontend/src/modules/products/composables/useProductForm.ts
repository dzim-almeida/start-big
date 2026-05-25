/**
 * @fileoverview Product form composable with provide/inject pattern
 * @description Manages form state, validation, and submission for create/edit
 */

import {
  ref,
  watch,
  computed,
  provide,
  inject,
  type InjectionKey,
  type Ref,
  type ComputedRef,
} from 'vue';
import { useForm } from 'vee-validate';
import { productValidationSchema } from '../schemas/product.schema';
import type {
  ProductFormData,
  ProdutoCreate,
  ProdutoUpdate,
  ProdutoRead,
} from '../types/products.types';
import { useCreateProductMutation, useUpdateProductMutation } from './useProductsQuery';
import { useProductModal } from './useProductModal';

// =============================================
// Constants
// =============================================

const DEFAULT_FORM_VALUES: ProductFormData = {
  nome: '',
  codigo_produto: '',
  codigo_barras: '',
  unidade_medida: '',
  categoria: '',
  marca: '',
  fornecedor_id: '',
  localizacao_estoque: '',
  observacao: '',

  valor_entrada: 0,
  valor_varejo: 0,
  valor_atacado: 0,
  quantidade: 0,
  quantidade_minima: 0,
  quantidade_ideal: 0,
};

// =============================================
// Helpers
// =============================================

function toCents(value?: number): number | undefined {
  if (value === null || value === undefined) return undefined;
  return Math.round(value * 100);
}

function toNumberOrUndefined(value?: string): number | undefined {
  if (!value) return undefined;
  const parsed = parseInt(value, 10);
  return Number.isNaN(parsed) ? undefined : parsed;
}

// =============================================
// Types for Injection
// =============================================

export interface ProductFormContext {
  nome: Ref<string>;
  codigo_produto: Ref<string>;
  codigo_barras: Ref<string>;
  unidade_medida: Ref<string>;
  categoria: Ref<string>;
  marca: Ref<string>;
  fornecedor_id: Ref<string>;
  localizacao_estoque: Ref<string>;
  observacao: Ref<string>;

  valor_entrada: Ref<number>;
  valor_varejo: Ref<number>;
  valor_atacado: Ref<number>;
  quantidade: Ref<number>;
  quantidade_minima: Ref<number>;
  quantidade_ideal: Ref<number>;

  imageFile: Ref<File | null>;

  errors: Ref<Record<string, string | undefined>>;
  submitCount: Ref<number>;
  values: ProductFormData;
  apiError: Ref<string | null>;
  isPending: ComputedRef<boolean>;

  onSubmit: (e?: Event) => void;
  resetForm: () => void;
}

export const PRODUCT_FORM_KEY: InjectionKey<ProductFormContext> = Symbol('product-form');

// =============================================
// Provider Composable (call in parent component)
// =============================================

export function useProductFormProvider() {
  const { selectedProduct, isCreateMode, closeModal } = useProductModal();

  const {
    handleSubmit,
    errors,
    defineField,
    setValues,
    resetForm,
    submitCount,
    values,
    setErrors,
  } = useForm<ProductFormData>({
    validationSchema: productValidationSchema,
    initialValues: { ...DEFAULT_FORM_VALUES },
  });

  const imageFile = ref<File | null>(null);

  const createMutation = useCreateProductMutation(setErrors, imageFile);
  const updateMutation = useUpdateProductMutation(setErrors, imageFile);

  const [nome] = defineField('nome');
  const [codigo_produto] = defineField('codigo_produto');
  const [codigo_barras] = defineField('codigo_barras');
  const [unidade_medida] = defineField('unidade_medida');
  const [categoria] = defineField('categoria');
  const [marca] = defineField('marca');
  const [fornecedor_id] = defineField('fornecedor_id');
  const [localizacao_estoque] = defineField('localizacao_estoque');
  const [observacao] = defineField('observacao');

  const [valor_entrada] = defineField('valor_entrada');
  const [valor_varejo] = defineField('valor_varejo');
  const [valor_atacado] = defineField('valor_atacado');
  const [quantidade] = defineField('quantidade');
  const [quantidade_minima] = defineField('quantidade_minima');
  const [quantidade_ideal] = defineField('quantidade_ideal');

  const apiError = ref<string | null>(null);

  function populateForm(product: ProdutoRead) {
    setValues({
      nome: product.nome,
      codigo_produto: product.codigo_produto,
      codigo_barras: product.codigo_barras || '',
      unidade_medida: product.unidade_medida || '',
      categoria: product.categoria || '',
      marca: product.marca || '',
      fornecedor_id: product.fornecedor_id ? String(product.fornecedor_id) : '',
      localizacao_estoque: product.localizacao_estoque || '',
      observacao: product.observacao || '',

      valor_entrada: product.estoque.valor_entrada ? product.estoque.valor_entrada / 100 : 0,
      valor_varejo: product.estoque.valor_varejo / 100,
      valor_atacado: product.estoque.valor_atacado ? product.estoque.valor_atacado / 100 : 0,
      quantidade: product.estoque.quantidade,
      quantidade_minima: product.estoque.quantidade_minima || 0,
      quantidade_ideal: product.estoque.quantidade_ideal || 0,
    });
  }

  watch(
    selectedProduct,
    (product) => {
      if (product) {
        populateForm(product);
      } else {
        resetForm({ values: { ...DEFAULT_FORM_VALUES } });
      }
    },
    { immediate: true },
  );

  function transformToCreateRequest(formData: ProductFormData): ProdutoCreate {
    return {
      nome: formData.nome,
      codigo_produto: formData.codigo_produto,
      codigo_barras: formData.codigo_barras || undefined,
      unidade_medida: formData.unidade_medida || undefined,
      observacao: formData.observacao || undefined,
      categoria: formData.categoria || undefined,
      marca: formData.marca || undefined,
      fornecedor_id: toNumberOrUndefined(formData.fornecedor_id),
      localizacao_estoque: formData.localizacao_estoque || undefined,
      estoque: {
        valor_varejo: toCents(formData.valor_varejo) || 0,
        quantidade: formData.quantidade || undefined,
        valor_entrada: toCents(formData.valor_entrada),
        valor_atacado: toCents(formData.valor_atacado),
        quantidade_minima: formData.quantidade_minima || undefined,
        quantidade_ideal: formData.quantidade_ideal || undefined,
      },
    };
  }

  const onSubmit = handleSubmit(
    async (formData) => {
      apiError.value = null;

      if (isCreateMode.value) {
        const request = transformToCreateRequest(formData);
        createMutation.mutate(request, {
          onSuccess: () => {
            closeModal();
            resetForm({ values: { ...DEFAULT_FORM_VALUES } });
          },
        });
      } else if (selectedProduct.value) {
        const updateData: ProdutoUpdate = {
          nome: formData.nome,
          codigo_produto: formData.codigo_produto,
          codigo_barras: formData.codigo_barras || undefined,
          unidade_medida: formData.unidade_medida || undefined,
          observacao: formData.observacao || undefined,
          categoria: formData.categoria || undefined,
          marca: formData.marca || undefined,
          fornecedor_id: toNumberOrUndefined(formData.fornecedor_id),
          localizacao_estoque: formData.localizacao_estoque || undefined,
          estoque: {
            valor_varejo: toCents(formData.valor_varejo),
            quantidade: formData.quantidade,
            valor_entrada: toCents(formData.valor_entrada),
            valor_atacado: toCents(formData.valor_atacado),
            quantidade_minima: formData.quantidade_minima || undefined,
            quantidade_ideal: formData.quantidade_ideal || undefined,
          },
        };

        updateMutation.mutate(
          { id: selectedProduct.value.id, data: updateData },
          {
            onSuccess: () => {
              closeModal();
              resetForm({ values: { ...DEFAULT_FORM_VALUES } });
            },
          },
        );
      }
    },
    (validationErrors) => {
      console.log('[DEBUG] Validation errors:', validationErrors);
    },
  );

  const isPending = computed(
    () => createMutation.isPending.value || updateMutation.isPending.value,
  );

  const context: ProductFormContext = {
    nome,
    codigo_produto,
    codigo_barras,
    unidade_medida,
    categoria,
    marca,
    fornecedor_id,
    localizacao_estoque,
    observacao,
    valor_entrada,
    valor_varejo,
    valor_atacado,
    quantidade,
    quantidade_minima,
    quantidade_ideal,
    imageFile,
    errors,
    submitCount,
    values,
    apiError,
    isPending,
    onSubmit,
    resetForm: () => resetForm({ values: { ...DEFAULT_FORM_VALUES } }),
  };

  provide(PRODUCT_FORM_KEY, context);

  return context;
}

// =============================================
// Consumer Composable (call in child components)
// =============================================

export function useProductForm(): ProductFormContext {
  const context = inject(PRODUCT_FORM_KEY);

  if (!context) {
    throw new Error(
      'useProductForm must be used within a component that has called useProductFormProvider',
    );
  }

  return context;
}
