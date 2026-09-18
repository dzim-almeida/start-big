import { useQueryClient } from '@tanstack/vue-query';
import { useRouter } from 'vue-router';

import { useToast } from '@/shared/composables/useToast';

import { fiscalKeys } from '../constants/fiscal.constants';
import type { FiscalConfiguracao } from '../types/fiscal.types';

export const MENSAGEM_NUMERACAO_NAO_CONFIRMADA = {
  titulo: 'Confirme a numeração fiscal antes de emitir',
  descricao:
    'Informe a série e o último número emitido em Centro Fiscal › Configurações › Emissão Estadual. ' +
    'Sem isso a primeira nota pode sair duplicada na SEFAZ (Rejeição 204).',
  acao: 'Configurar',
} as const;

interface DependenciasGuarda {
  /** Configuração já em cache; `undefined` quando ainda não foi carregada. */
  obterConfiguracao: () => FiscalConfiguracao | undefined;
  avisar: (titulo: string, descricao: string, acao: { label: string; onClick: () => void }) => void;
  irParaConfiguracoes: () => void;
}

/**
 * Monta a guarda a partir das dependências — separado do composable para ser
 * testável sem app Vue, QueryClient nem router.
 *
 * Só bloqueia quando a configuração está em cache E diz `false`. Sem cache
 * não adivinha: o gate do backend (`verificar_emitente`) é quem manda, e a
 * pendência chega pelo modal de pendências como qualquer outra.
 */
export function criarGuardaNumeracao(deps: DependenciasGuarda) {
  return function garantirNumeracaoConfirmada(): boolean {
    const config = deps.obterConfiguracao();
    if (!config || config.numeracao_confirmada) return true;

    deps.avisar(
      MENSAGEM_NUMERACAO_NAO_CONFIRMADA.titulo,
      MENSAGEM_NUMERACAO_NAO_CONFIRMADA.descricao,
      { label: MENSAGEM_NUMERACAO_NAO_CONFIRMADA.acao, onClick: deps.irParaConfiguracoes },
    );
    return false;
  };
}

/**
 * Guarda de emissão: evita a ida ao backend quando já se sabe, pelo cache da
 * configuração, que a numeração não foi confirmada — e leva o operador direto
 * para a tela que resolve.
 */
export function useNumeracaoConfirmada() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const toast = useToast();

  const garantirNumeracaoConfirmada = criarGuardaNumeracao({
    obterConfiguracao: () =>
      queryClient.getQueryData<FiscalConfiguracao>(fiscalKeys.configuracao()),
    avisar: (titulo, descricao, acao) => toast.warning(titulo, descricao, { action: acao }),
    irParaConfiguracoes: () => {
      router.push({ name: 'fiscal-configuracoes' });
    },
  });

  return { garantirNumeracaoConfirmada };
}
