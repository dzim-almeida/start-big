/**
 * @fileoverview Imprimir a proposta (Spec 07 §6.3, D2, D4, D5, D7).
 *
 * 1. Grava o que está pendente (D4): a proposta tem de mostrar o que está
 *    GRAVADO. Com conflito ou erro de gravação, nada é impresso.
 * 2. Monta `DadosProposta` (só o que o cliente pode ver).
 * 3. Troca o título da página (vira o nome sugerido do PDF, D5).
 * 4. Espera a logo carregar e chama a impressão A4 (D2: sempre folha inteira).
 * 5. No `afterprint`, devolve o título e tira o documento da página.
 */
import { nextTick, ref, type Ref } from 'vue';

import { useToast } from '@/shared/composables/useToast';
import { aguardarImagensDaImpressao, imprimirComPagina } from '@/shared/utils/print.utils';

import type { OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';
import { montarDadosProposta, type DadosProposta } from '../utils/dadosProposta';
import { nomeArquivoProposta } from '../utils/nomeArquivoProposta';

/** Rede de segurança: se o `afterprint` nunca vier, limpa depois de 2 minutos. */
const LIMPEZA_FORCADA_MS = 2 * 60 * 1000;

interface Opcoes {
  detalhe: Ref<OrcamentoDetalhe | undefined>;
  /** Manda o pendente e espera a fila; devolve false se algo ficou sem gravar. */
  gravarPendencias: () => Promise<boolean>;
  /** Número da versão que substituiu esta (faixa "VERSÃO SUBSTITUÍDA pela v3"). */
  versaoSubstituta?: Ref<number | null>;
}

export function useImprimirProposta(opcoes: Opcoes) {
  const toast = useToast();
  /** O template só existe enquanto imprime (o editor faz `v-if`). */
  const dadosParaImprimir = ref<DadosProposta | null>(null);
  const imprimindo = ref(false);

  /**
   * Imprime a proposta. `atual` permite imprimir o detalhe que ACABOU de
   * voltar do envio (com a validade gravada, D7). Devolve true se o diálogo abriu.
   */
  async function imprimir(atual?: OrcamentoDetalhe): Promise<boolean> {
    if (imprimindo.value) return false;
    imprimindo.value = true;
    try {
      // D4: nunca imprime o que não está gravado.
      if (!(await opcoes.gravarPendencias())) {
        toast.error('A proposta não foi gerada', 'Há alterações que não foram salvas.');
        imprimindo.value = false;
        return false;
      }
      const detalhe = atual ?? opcoes.detalhe.value;
      if (!detalhe) {
        imprimindo.value = false;
        return false;
      }
      dadosParaImprimir.value = montarDadosProposta(detalhe, new Date(), {
        versaoSubstituta: opcoes.versaoSubstituta?.value ?? null,
      });

      const tituloOriginal = document.title;
      document.title = nomeArquivoProposta(dadosParaImprimir.value);   // D5: nome do PDF
      await nextTick();                                                // o template entra no DOM
      await aguardarImagensDaImpressao();                              // a logo precisa ter carregado

      // Depois do diálogo (imprimiu, salvou ou cancelou), tudo volta como estava.
      let limpezaForcada: ReturnType<typeof setTimeout> | null = null;
      const restaurar = () => {
        document.title = tituloOriginal;
        dadosParaImprimir.value = null;
        imprimindo.value = false;
        window.removeEventListener('afterprint', restaurar);
        if (limpezaForcada) clearTimeout(limpezaForcada);
      };
      window.addEventListener('afterprint', restaurar);
      limpezaForcada = setTimeout(restaurar, LIMPEZA_FORCADA_MS);
      imprimirComPagina('A4', { folha: 'A4' });                        // D2: sempre folha inteira
      return true;
    } catch (erro) {
      imprimindo.value = false;
      dadosParaImprimir.value = null;
      throw erro;
    }
  }

  /**
   * "Enviar e gerar proposta" (D7): primeiro envia; só com o envio gravado
   * (validade no papel = a gravada), imprime. Se o envio falhar, nada é impresso.
   */
  async function enviarEImprimir(enviar: () => Promise<OrcamentoDetalhe | null>): Promise<boolean> {
    const enviado = await enviar();
    if (!enviado) return false;
    return imprimir(enviado);
  }

  return { imprimir, enviarEImprimir, dadosParaImprimir, imprimindo };
}
