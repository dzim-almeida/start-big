import { computed } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import api from '@/api/axios';
import { formatCurrency } from '@/shared/utils/finance';

import { fiscalKeys, TIMEOUT_CONSULTA } from '../constants/fiscal.constants';
import type { FranquiaFiscal } from '../types/fiscal.types';

/**
 * A franquia fiscal do mês (docs/nfse-fase2-plano.md, G1): 70 notas somando
 * NF-e, NFC-e e NFS-e de produção. Só informa — quem barra é a plataforma.
 *
 * `null` = não deu para saber (plataforma antiga, rede fora): a tela esconde o
 * cartão em vez de mostrar um número inventado.
 */
export function useFranquiaFiscal() {
  const { data } = useQuery({
    queryKey: fiscalKeys.franquia(),
    queryFn: async () => (await api.get<FranquiaFiscal>('/fiscal/franquia', { timeout: TIMEOUT_CONSULTA })).data,
    staleTime: 60_000,
    retry: false,
  });

  const franquia = computed(() => (data.value?.consultou && data.value.vigente !== false ? data.value : null));

  /** "74 de 70 notas no mês · 4 extras (R$ 4,00 no dia 1º)" / "restam 3 de 70". */
  const resumo = computed(() => {
    const f = franquia.value;
    if (!f) return '';
    const base = `${f.emitidas} de ${f.franquia} notas no mês`;
    if (f.excedentes > 0) {
      return `${base} · ${f.excedentes} extra${f.excedentes === 1 ? '' : 's'} (${formatCurrency(f.valorExcedente * 100)} no dia 1º)`;
    }
    return `${base} · restam ${f.restantesNaFranquia}`;
  });

  /** Perto de parar: PIX sem folga, ou o teto de segurança do cartão chegando. */
  const alerta = computed(() => {
    const f = franquia.value;
    return !!f && f.restantes !== null && f.restantes <= 5;
  });

  /** 0–100 da franquia (passa de 100 no cartão, e a barra fica cheia). */
  const percentual = computed(() => {
    const f = franquia.value;
    return f ? Math.min(100, Math.round((f.emitidas / Math.max(1, f.franquia)) * 100)) : 0;
  });

  return { franquia, resumo, alerta, percentual };
}
