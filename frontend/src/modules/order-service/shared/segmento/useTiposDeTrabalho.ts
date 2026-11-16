import { computed } from 'vue';

import { useSegmento } from '@/shared/composables/useSegmento';
import { useOSFieldDefinition } from './useOSFieldDefinition.queries';
import type { SegmentField, SegmentWorkType } from './segmentDefinition.type';

/**
 * Tipos de trabalho do segmento — "o que é esta OS?", quando o segmento tem
 * mais de um processo.
 *
 * Existe separado de `useCapacidades` de propósito: aquele responde o que o
 * SEGMENTO faz, este responde o que ESTA OS é. Juntar os dois faria um
 * composable com duas responsabilidades e dois motivos para mudar.
 *
 * Segmento sem `tipos` (oficina, informática) responde `temTipos = false` e
 * tudo continua pelo caminho de sempre — é isso que mantém as duas lojas em
 * produção intocadas.
 */

/**
 * Segmentos SEM tipo criável à mão, usados SÓ enquanto o contrato carrega
 * (Spec 03B, D4): sem isto o botão "Nova OS" apareceria e sumiria um instante
 * depois. Repete o backend (app/core/segmentos/definicoes/marcenaria.py);
 * quando o contrato chega, ele manda. Mesmo padrão de `useCapacidades.ts`.
 */
const SEM_CRIACAO_MANUAL_FALLBACK: readonly string[] = ['marcenaria'];

export function useTiposDeTrabalho() {
  const { data, isPending } = useOSFieldDefinition();   // contrato do segmento (já em cache)
  const { segmento } = useSegmento();                   // segmento da empresa logada

  const tipos = computed<SegmentWorkType[]>(() => data.value?.definicao?.tipos ?? []);

  const temTipos = computed(() => tipos.value.length > 0);

  /** Opções prontas para o seletor. */
  const opcoes = computed(() =>
    tipos.value.map((tipo) => ({ value: tipo.id, label: tipo.label })),
  );

  /**
   * O tipo padrão é o primeiro declarado. Uma OS nova já abre com ele
   * escolhido — formulário vazio esperando uma escolha é o tipo de tela que
   * faz o atendente achar que o sistema travou.
   */
  const tipoPadrao = computed<string | null>(() => tipos.value[0]?.id ?? null);

  function tipoPorId(id: string | null | undefined): SegmentWorkType | null {
    if (!id) return null;
    return tipos.value.find((tipo) => tipo.id === id) ?? null;
  }

  /** Campos do tipo escolhido; vazio se o tipo não existe (ou não há tipos). */
  function camposDoTipo(id: string | null | undefined): SegmentField[] {
    return tipoPorId(id)?.campos ?? [];
  }

  /**
   * Os campos agrupados na ordem em que foram declarados, para o formulário
   * desenhar seção por seção. Campo sem `grupo` cai num bloco sem título, no
   * lugar em que apareceu.
   */
  function gruposDoTipo(id: string | null | undefined) {
    const grupos: { titulo: string | null; campos: SegmentField[] }[] = [];
    for (const campo of camposDoTipo(id)) {
      const titulo = campo.grupo ?? null;
      const ultimo = grupos[grupos.length - 1];
      if (ultimo && ultimo.titulo === titulo) {
        ultimo.campos.push(campo);
      } else {
        grupos.push({ titulo, campos: [campo] });
      }
    }
    return grupos;
  }

  /** Um tipo pode ser criado à mão? Ausente no contrato = sim (Spec 03B, D1). */
  const criavelAMao = (tipo: SegmentWorkType) => tipo.criacao_manual !== false;

  /**
   * O segmento deixa abrir OS pelo botão "Nova OS"? (Spec 03B, D2/D4)
   * Sim quando não há tipos (oficina, informática) ou quando pelo menos um
   * tipo é criável à mão (serigrafia). É a mesma regra do backend (03A, D5).
   */
  const podeCriarOSManual = computed<boolean>(() => {
    // Contrato carregando: decide pelo fallback, para o botão não piscar.
    if (isPending.value) return !SEM_CRIACAO_MANUAL_FALLBACK.includes(segmento.value ?? '');
    return !temTipos.value || tipos.value.some(criavelAMao);
  });

  /**
   * O tipo gravado numa OS pode ser trocado? (Spec 03B, D6) Tipo desconhecido
   * ou ausente: pode, como sempre. Só o tipo que nasce de outro documento trava.
   */
  function tipoPodeSerTrocado(id: string | null | undefined): boolean {
    const tipo = tipoPorId(id);
    return !tipo || criavelAMao(tipo);
  }

  return {
    tipos,
    temTipos,
    opcoes,
    tipoPadrao,
    tipoPorId,
    camposDoTipo,
    gruposDoTipo,
    podeCriarOSManual,
    tipoPodeSerTrocado,
  };
}
