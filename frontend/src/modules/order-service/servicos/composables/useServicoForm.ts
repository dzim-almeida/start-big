import {
  computed,
  inject,
  provide,
  ref,
  watch,
  type ComputedRef,
  type InjectionKey,
  type Ref,
} from 'vue';
import { useForm } from 'vee-validate';
import type { ServiceCreateZod, ServiceUpdateZod } from '../schemas/servicos.schema';
import { ServicoFormData } from '../types/servicos.types';
import { servicoFormValidationSchema } from '../schemas/servicos.schema';
import { toCents } from '../utils/servicos.utils';
import { useCreateServicoMutation, useUpdateServicoMutation } from './useServicosMutations';
import { useServicoModal } from './useServicoModal';
import { recursoDisponivel } from '@/shared/config/planos';
import { getServicoFiscal } from '../services/servicos.service';

const DEFAULT_FORM_VALUES: ServicoFormData = {
  descricao: '',
  valor: 0,
  fiscal_codigo_servico_lc116: '',
  fiscal_cnae: '',
  fiscal_aliquota_iss_display: '',
  fiscal_codigo_tributacao_municipio: '',
  fiscal_c_class_trib: '',
  fiscal_cst_ibs_cbs: '',
  fiscal_aliquota_ibs_display: '',
  fiscal_aliquota_cbs_display: '',
  fiscal_c_benef: '',
  fiscal_codigo_tributacao_nacional: '',
  fiscal_codigo_nbs: '',
};

export interface ServicoFormContext {
  descricao: Ref<string>;
  valor: Ref<number>;
  // Dados fiscais
  fiscal_codigo_servico_lc116: Ref<string>;
  fiscal_cnae: Ref<string>;
  fiscal_aliquota_iss_display: Ref<string>;
  fiscal_codigo_tributacao_municipio: Ref<string>;
  fiscal_c_class_trib: Ref<string>;
  fiscal_cst_ibs_cbs: Ref<string>;
  fiscal_aliquota_ibs_display: Ref<string>;
  fiscal_aliquota_cbs_display: Ref<string>;
  fiscal_c_benef: Ref<string>;
  fiscal_codigo_tributacao_nacional: Ref<string>;
  fiscal_codigo_nbs: Ref<string>;
  nfeDisponivel: boolean;
  nfseDisponivel: boolean;
  submitCount: Ref<number>;
  errors: Ref<Record<string, string | undefined>>;
  apiError: Ref<string | null>;
  isPending: ComputedRef<boolean>;
  onSubmit: (e?: Event) => void;
  resetForm: () => void;
}

export const SERVICO_FORM_KEY: InjectionKey<ServicoFormContext> = Symbol('servico-form');

export function useServicoFormProvider() {
  const { selectedServico, isCreateMode, closeModal } = useServicoModal();
  const { handleSubmit, defineField, setValues, resetForm, submitCount, errors, setErrors } =

    useForm<ServicoFormData>({
      validationSchema: servicoFormValidationSchema,
      initialValues: { ...DEFAULT_FORM_VALUES },
    });

  const createMutation = useCreateServicoMutation(setErrors);
  const updateMutation = useUpdateServicoMutation(setErrors);

  const apiError = ref<string | null>(null);
  const nfeDisponivel = recursoDisponivel('nfe');
  const nfseDisponivel = recursoDisponivel('nfse');
  // O cadastro fiscal do serviço serve às duas notas: o prestador MEI tem só
  // a NFS-e, e precisa preencher o serviço do mesmo jeito.
  const fiscalDisponivel = nfeDisponivel || nfseDisponivel;

  const [descricao] = defineField('descricao');
  const [valor] = defineField('valor');

  // Campos fiscais
  const [fiscal_codigo_servico_lc116] = defineField('fiscal_codigo_servico_lc116');
  const [fiscal_cnae] = defineField('fiscal_cnae');
  const [fiscal_aliquota_iss_display] = defineField('fiscal_aliquota_iss_display');
  const [fiscal_codigo_tributacao_municipio] = defineField('fiscal_codigo_tributacao_municipio');
  const [fiscal_c_class_trib] = defineField('fiscal_c_class_trib');
  const [fiscal_cst_ibs_cbs] = defineField('fiscal_cst_ibs_cbs');
  const [fiscal_aliquota_ibs_display] = defineField('fiscal_aliquota_ibs_display');
  const [fiscal_aliquota_cbs_display] = defineField('fiscal_aliquota_cbs_display');
  const [fiscal_c_benef] = defineField('fiscal_c_benef');
  const [fiscal_codigo_tributacao_nacional] = defineField('fiscal_codigo_tributacao_nacional');
  const [fiscal_codigo_nbs] = defineField('fiscal_codigo_nbs');

  // O item da LC 116 está dentro do código nacional (01.07.01 → 01.07): ao
  // trocar o código, o item acompanha — a não ser que alguém o tenha digitado
  // diferente de propósito (rota municipal que pede outro).
  const itemDaLc116 = (codigo: string | undefined) =>
    /^\d{6}$/.test(codigo ?? '') ? `${codigo!.slice(0, 2)}.${codigo!.slice(2, 4)}` : '';
  watch(fiscal_codigo_tributacao_nacional, (novo, antigo) => {
    const item = itemDaLc116(novo);
    if (!item) return;
    const atual = fiscal_codigo_servico_lc116.value ?? '';
    if (!atual || atual === itemDaLc116(antigo)) fiscal_codigo_servico_lc116.value = item;
  });

  async function populateForm() {
    if (!selectedServico.value) {
      resetForm({ values: { ...DEFAULT_FORM_VALUES } });
      return;
    }

    setValues({
      descricao: selectedServico.value.descricao,
      valor: selectedServico.value.valor / 100,
    });

    // Carrega dados fiscais (se módulo ativo)
    if (fiscalDisponivel) {
      try {
        const fiscal = await getServicoFiscal(selectedServico.value.id);
        if (fiscal) {
          setValues({
            fiscal_codigo_servico_lc116: fiscal.codigo_servico_lc116
              ? fiscal.codigo_servico_lc116.replace(/^(\d{2})(\d{2})$/, '$1.$2')
              : '',
            fiscal_cnae: fiscal.cnae
              ? fiscal.cnae.replace(/^(\d{4})(\d)(\d{2})$/, '$1-$2/$3')
              : '',
            fiscal_aliquota_iss_display: fiscal.aliquota_iss != null ? String(Math.round(fiscal.aliquota_iss / 100)) : '',
            fiscal_codigo_tributacao_municipio: fiscal.codigo_tributacao_municipio ?? '',
            fiscal_c_class_trib: fiscal.c_class_trib ?? '',
            fiscal_cst_ibs_cbs: fiscal.cst_ibs_cbs ?? '',
            fiscal_aliquota_ibs_display: fiscal.aliquota_ibs != null ? String(Math.round(fiscal.aliquota_ibs / 100)) : '',
            fiscal_aliquota_cbs_display: fiscal.aliquota_cbs != null ? String(Math.round(fiscal.aliquota_cbs / 100)) : '',
            fiscal_c_benef: fiscal.c_benef ?? '',
            fiscal_codigo_tributacao_nacional: fiscal.codigo_tributacao_nacional ?? '',
            fiscal_codigo_nbs: fiscal.codigo_nbs ?? '',
          } as any, false);
        }
      } catch {
        // Falha ao carregar fiscal não deve bloquear a edição
      }
    }
  }

  watch(selectedServico, populateForm, { immediate: true });

  function transformToCreateRequest(formData: ServicoFormData): ServiceCreateZod {
    return {
      descricao: formData.descricao.trim(),
      valor: toCents(formData.valor) || 0,
    };
  }

  function transformToUpdateRequest(formData: ServicoFormData): ServiceUpdateZod {
    return {
      descricao: formData.descricao.trim(),
      valor: toCents(formData.valor),
    };
  }

  const onSubmit = handleSubmit(async (formData) => {
    apiError.value = null;

    if (isCreateMode.value) {
      const request = transformToCreateRequest(formData);
      createMutation.mutate(request, {
        onSuccess: () => {
          closeModal();
          resetForm({ values: { ...DEFAULT_FORM_VALUES } });
        },
        onError: () => {
          apiError.value = 'Erro ao cadastrar serviço';
        },
      });
      return;
    }

    if (selectedServico.value) {
      const request: Record<string, unknown> = { ...transformToUpdateRequest(formData) };

      // Inclui dados fiscais no payload (o service chama o endpoint separado)
      if (fiscalDisponivel) {
        const stripSeparadores = (v: string) => v.replace(/[.\-/]/g, '');
        request.fiscal = {
          codigo_servico_lc116: formData.fiscal_codigo_servico_lc116
            ? stripSeparadores(formData.fiscal_codigo_servico_lc116)
            : null,
          cnae: formData.fiscal_cnae
            ? stripSeparadores(formData.fiscal_cnae)
            : null,
          aliquota_iss: formData.fiscal_aliquota_iss_display
            ? Math.round(Number(formData.fiscal_aliquota_iss_display) * 100)
            : null,
          codigo_tributacao_municipio: formData.fiscal_codigo_tributacao_municipio || null,
          // CFOP, CST, CSOSN e unidade não vão: fora do payload, o backend
          // (exclude_unset) não os apaga.
          c_class_trib: formData.fiscal_c_class_trib || null,
          cst_ibs_cbs: formData.fiscal_cst_ibs_cbs || null,
          aliquota_ibs: formData.fiscal_aliquota_ibs_display
            ? Math.round(Number(formData.fiscal_aliquota_ibs_display) * 100)
            : null,
          aliquota_cbs: formData.fiscal_aliquota_cbs_display
            ? Math.round(Number(formData.fiscal_aliquota_cbs_display) * 100)
            : null,
          c_benef: formData.fiscal_c_benef || null,
        };
        // Só quem vê os campos da NFS-e os envia: sem o módulo eles ficam
        // de fora do payload, e o backend (exclude_unset) não os apaga.
        if (nfseDisponivel) {
          Object.assign(request.fiscal as Record<string, unknown>, {
            codigo_tributacao_nacional: formData.fiscal_codigo_tributacao_nacional || null,
            codigo_nbs: formData.fiscal_codigo_nbs || null,
          });
        }
      }

      updateMutation.mutate(
        { id: selectedServico.value.id, data: request as any },
        {
          onSuccess: () => {
            closeModal();
            resetForm({ values: { ...DEFAULT_FORM_VALUES } });
          },
          onError: () => {
            apiError.value = 'Erro ao atualizar serviço';
          },
        },
      );
    }
  });

  const isPending = computed(
    () => createMutation.isPending.value || updateMutation.isPending.value,
  );

  const context: ServicoFormContext = {
    descricao,
    valor,
    fiscal_codigo_servico_lc116,
    fiscal_cnae,
    fiscal_aliquota_iss_display,
    fiscal_codigo_tributacao_municipio,
    fiscal_c_class_trib,
    fiscal_cst_ibs_cbs,
    fiscal_aliquota_ibs_display,
    fiscal_aliquota_cbs_display,
    fiscal_c_benef,
    fiscal_codigo_tributacao_nacional,
    fiscal_codigo_nbs,
    nfeDisponivel,
    nfseDisponivel,
    submitCount,
    errors,
    apiError,
    isPending,
    onSubmit,
    resetForm: () => resetForm({ values: { ...DEFAULT_FORM_VALUES } }),
  };

  provide(SERVICO_FORM_KEY, context);

  return context;
}

export function useServicoForm(): ServicoFormContext {
  const context = inject(SERVICO_FORM_KEY);

  if (!context) {
    throw new Error(
      'useServicoForm must be used within a component that has called useServicoFormProvider',
    );
  }

  return context;
}
