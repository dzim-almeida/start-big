import { computed } from 'vue';

import { useSegmento } from '@/shared/composables/useSegmento';
import {
  OS_ESTADO_CONFIG,
  montarFiltroStatus,
  montarOpcoesStatus,
  type OsEstadoKey,
} from '../../ordens/constants/ordemServico.constants';
import type {
  OsEquipSituacaoEnumDataType,
  OsStatusEnumDataType,
} from '../../ordens/schemas/enums/osEnums.schema';
import { getEstadoOS } from '../utils/formatters';
import type { RotuloStatus } from './segmentDefinition.type';
import { useOSFieldDefinition } from './useOSFieldDefinition.queries';

/**
 * Rótulos de STATUS da OS por segmento (Spec 01A/01B da marcenaria).
 *
 * O status gravado é o MESMO enum em todo segmento (transições, filtros,
 * relatórios). O segmento só pode trocar o TEXTO, declarando
 * `definicao.rotulos_status` no backend. Este composable é o único lugar do
 * frontend que lê isso: nenhum componente deve ter mapa próprio de rótulos de
 * OS nem `if` pelo nome do segmento.
 */

/** Rótulos por código do enum; ausente = texto padrão. */
type RotulosStatus = Partial<Record<OsStatusEnumDataType, RotuloStatus>>;

/**
 * Textos usados SÓ enquanto o contrato carrega (Spec 01B, D3/D4), para a lista
 * não abrir com "Em Andamento" e trocar para "Em Produção" um instante depois.
 * Repete a declaração do backend (app/core/segmentos/definicoes/marcenaria.py):
 * quando o contrato chega, ELE manda. Mudou lá? Mude aqui também.
 *
 * É o mesmo padrão do `FALLBACK_POR_SEGMENTO` de `useCapacidades.ts`: o nome do
 * segmento só aparece aqui, como fallback de carregamento.
 */
const ROTULOS_STATUS_FALLBACK_POR_SEGMENTO: Record<string, RotulosStatus> = {
  marcenaria: {
    EM_ANDAMENTO: { rotulo: 'Em Produção', curto: 'Em produção' },
    AGUARDANDO_PECAS: { rotulo: 'Aguardando Material', curto: 'Aguard. material' },
    AGUARDANDO_RETIRADA: { rotulo: 'Aguardando Entrega', curto: 'Aguard. entrega' },
  },
};

export function useRotulosStatusOS() {
  const { data, isPending } = useOSFieldDefinition();  // contrato do segmento (já em cache)
  const { segmento } = useSegmento();                  // segmento da empresa logada

  /** Rótulos em vigor: fallback enquanto carrega, contrato depois. */
  const rotulosStatus = computed<RotulosStatus>(() => {
    // Contrato ainda carregando: usa o fallback do segmento (ou nenhum).
    if (isPending.value) return ROTULOS_STATUS_FALLBACK_POR_SEGMENTO[segmento.value ?? ''] ?? {};
    // Contrato carregado: ele manda. Sem a chave = nenhum rótulo próprio.
    return data.value?.definicao?.rotulos_status ?? {};
  });

  /** Desfecho: o contrato já traz `rotulos_situacao` (serigrafia e marcenaria). */
  const rotulosSituacao = computed<Record<string, string>>(
    () => data.value?.definicao?.rotulos_situacao ?? {},
  );

  /**
   * Texto declarado pelo segmento, ou `undefined` quando ele não renomeia
   * (Spec 01B, D7). Para telas que têm um texto padrão próprio (ex.: Atividade
   * de Hoje, com "P/ Retirada"): elas só trocam quando o segmento declara.
   */
  function rotuloStatusProprio(status: OsStatusEnumDataType, curto = false): string | undefined {
    const proprio = rotulosStatus.value[status];   // rótulo do segmento para este status
    if (!proprio) return undefined;                // não renomeia: quem chama usa o seu padrão
    return curto ? proprio.curto : proprio.rotulo; // escolhe o tamanho pedido
  }

  /** Texto final: o do segmento ou o padrão de OS_ESTADO_CONFIG. */
  function rotuloStatus(status: OsStatusEnumDataType): string {
    return rotuloStatusProprio(status) ?? OS_ESTADO_CONFIG[status].label;
  }

  /** `getEstadoOS` já com os rótulos do segmento (cores intactas). */
  function estadoOS(
    status: OsStatusEnumDataType | null | undefined,
    situacao?: OsEquipSituacaoEnumDataType | null,
  ) {
    return getEstadoOS(status, situacao, {
      status: rotulosStatus.value,       // "Em Produção" no lugar de "Em Andamento"...
      situacao: rotulosSituacao.value,   // ..."Não produzido" no lugar de "Sem Reparo"
    });
  }

  /** Texto usado pelos montadores: status do fluxo E desfechos (SEM_REPARO/CONDENADO). */
  const texto = (chave: OsEstadoKey): string =>
    rotulosStatus.value[chave as OsStatusEnumDataType]?.rotulo   // status renomeado
    ?? rotulosSituacao.value[chave]                              // desfecho renomeado
    ?? OS_ESTADO_CONFIG[chave].label;                            // padrão

  /** Opções do select de status do modal (valor = código do enum). */
  const statusOptions = computed(() => montarOpcoesStatus(texto));
  /** Opções do menu de filtro da lista (chave = código do enum). */
  const statusFilterConfig = computed(() => montarFiltroStatus(texto));

  return { rotuloStatus, rotuloStatusProprio, estadoOS, statusOptions, statusFilterConfig };
}
