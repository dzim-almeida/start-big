import { ref, toValue, watch, type MaybeRefOrGetter } from 'vue';
import { useQueryClient } from '@tanstack/vue-query';

import type { PrecoPorte } from '../../shared/schemas/porte.schema';
import { getPrecosDoServico, salvarPrecosDoServico } from '../../shared/services/portes.service';
import { SERVICOS_DO_PORTE_KEY } from '../../shared/composables/usePortes';

/** Uma linha da grade na tela. `valor` em REAIS (o MoneyInput trabalha em reais). */
export interface LinhaPreco {
  /**
   * Vazio (`undefined`; o MoneyInput limpo pode mandar `null`) = sem preço
   * próprio: o porte usa o valor base do serviço.
   */
  valor: number | undefined;
  /** Minutos como texto (campo numérico da casa é `type="text"`). */
  duracao: string;
}

/** Texto da duração → minutos inteiros, ou `null` quando vazio/ inválido. */
export function minutosDoTexto(texto: string): number | null {
  const n = Math.trunc(Number(String(texto).replace(',', '.').trim()));
  return Number.isFinite(n) && n > 0 ? Math.min(n, 24 * 60) : null;
}

/**
 * Grade → corpo do PUT. Porte SEM valor fica de fora: volta ao preço padrão
 * (Spec 02A, D4). Duração sem preço não é gravada — não há linha onde guardá-la.
 */
export function montarPrecos(linhas: Record<number, LinhaPreco>): PrecoPorte[] {
  return Object.entries(linhas)
    .filter(([, linha]) => linha.valor != null)   // null e undefined
    .map(([porteId, linha]) => ({
      porte_id: Number(porteId),
      valor: Math.round((linha.valor as number) * 100),          // reais → centavos (PR3)
      duracao_minutos: minutosDoTexto(linha.duracao),
    }));
}

/**
 * Estado da grade "porte → preço e duração" de um serviço (Spec 02B).
 *
 * É LOCAL ao modal: só vai para o servidor no salvar do serviço, pelo gancho
 * `aoSalvar` do formulário — antes disso o serviço novo nem tem id.
 */
export function usePrecosPorPorteForm(servicoId: MaybeRefOrGetter<number | null | undefined>) {
  const queryClient = useQueryClient();
  const linhas = ref<Record<number, LinhaPreco>>({});
  const carregando = ref(false);

  /**
   * Cria vazias as linhas que a tela vai mostrar. Fora do render de propósito:
   * mudar estado reativo no meio da renderização faz o Vue renderizar de novo.
   */
  function garantirLinhas(porteIds: number[]) {
    for (const id of porteIds) {
      if (!linhas.value[id]) linhas.value[id] = { valor: undefined, duracao: '' };
    }
  }

  // Abriu outro serviço (ou um novo): a grade recomeça do que está gravado.
  watch(
    () => toValue(servicoId),
    async (id) => {
      linhas.value = {};
      if (!id) return;
      carregando.value = true;
      try {
        for (const preco of await getPrecosDoServico(id)) {
          linhas.value[preco.porte_id] = {
            valor: preco.valor / 100,
            duracao: preco.duracao_minutos ? String(preco.duracao_minutos) : '',
          };
        }
      } finally {
        carregando.value = false;
      }
    },
    { immediate: true },
  );

  /** Grava a grade do serviço já salvo (chamado pelo gancho `aoSalvar`). */
  async function salvar(id: number) {
    await salvarPrecosDoServico(id, montarPrecos(linhas.value));
    queryClient.invalidateQueries({ queryKey: [SERVICOS_DO_PORTE_KEY] });   // comanda com o preço novo
  }

  return { linhas, garantirLinhas, carregando, salvar };
}
