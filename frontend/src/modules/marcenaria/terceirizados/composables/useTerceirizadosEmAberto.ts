/**
 * @fileoverview A lista geral dos terceirizados das OS abertas (Spec 11B
 * D10-D12): a aba "Terceirizados" da tela de Serviços.
 *
 * Os filtros vão para a API (11A D17): ela já devolve os atrasados primeiro.
 * Aqui só se AGRUPA por central, para o dono resolver todos os móveis da
 * mesma central numa ligação só.
 */
import { computed, type Ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { REFETCH_DASHBOARD } from '@/core/config/queryIntervals';

import type { ItemListaTerceirizados, SituacaoTerceirizado } from '../schemas/terceirizado.schema';
import { getTerceirizadosEmAberto } from '../services/terceirizado.service';
import { CHAVE_LISTA_TERCEIRIZADOS } from './useTerceirizadosDaOS';

/** Um grupo da lista: a central e os móveis dela. */
export interface GrupoDaCentral {
  chave: string;                       // id da central ("sem" quando o móvel não tem central)
  nome: string;
  telefone: string | null;
  itens: ItemListaTerceirizados[];
  pedidos: number;                     // quantos pedidos diferentes (D12: "3 pedidos")
  atrasados: number;                   // quantos móveis atrasados
}

/** Agrupa mantendo a ordem da API: a central do primeiro atrasado vem primeiro. */
export function agruparPorCentral(itens: ItemListaTerceirizados[]): GrupoDaCentral[] {
  const grupos = new Map<string, GrupoDaCentral>();
  for (const item of itens) {
    const chave = item.central ? String(item.central.id) : 'sem';
    let grupo = grupos.get(chave);
    if (!grupo) {
      grupo = {
        chave,
        nome: item.central?.nome ?? 'Sem central no orçamento',
        telefone: item.central?.telefone ?? null,
        itens: [], pedidos: 0, atrasados: 0,
      };
      grupos.set(chave, grupo);
    }
    grupo.itens.push(item);
    if (item.atrasado) grupo.atrasados += 1;
  }
  // "Pedidos" = quantos pedidos diferentes (um pedido cobre vários móveis, 11A D9).
  for (const grupo of grupos.values()) {
    const pedidos = new Set(grupo.itens.map(chaveDoPedido).filter((p): p is string => p !== null));
    grupo.pedidos = pedidos.size;
  }
  return [...grupos.values()];
}

/** O que identifica o pedido do móvel (o do Compras pelo id; o anotado pela OS + número). */
function chaveDoPedido(item: ItemListaTerceirizados): string | null {
  const pedido = item.pedido;
  if (!pedido) return null;
  if (pedido.origem === 'COMPRAS') return `C${pedido.id}`;
  return `M${item.numero_os}:${pedido.numero ?? item.enviado_em ?? ''}`;
}

export function useTerceirizadosEmAberto(
  situacao: Ref<SituacaoTerceirizado | null>, soAtrasados: Ref<boolean>,
) {
  const consulta = useQuery({
    queryKey: computed(() => [...CHAVE_LISTA_TERCEIRIZADOS, situacao.value, soAtrasados.value]),
    queryFn: () => getTerceirizadosEmAberto({ situacao: situacao.value, atrasados: soAtrasados.value }),
    refetchInterval: REFETCH_DASHBOARD,              // outro terminal pode ter recebido um móvel
  });
  const grupos = computed(() => agruparPorCentral(consulta.data.value ?? []));
  return { ...consulta, grupos };
}
