/**
 * @fileoverview Queries e mutations do módulo de Compras (fase 2).
 *
 * Toda mutation invalida o prefixo inteiro (`comprasKeys.todos`): enviar um
 * pedido muda a lista de pedidos E as Necessidades (o que está a caminho
 * desconta), e invalidar só uma das duas deixaria a outra mentindo.
 */
import { computed, unref, type MaybeRef } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';

import { REFETCH_CADASTROS } from '@/core/config/queryIntervals';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';

import { comprasKeys } from '../constants/queryKeys';
import * as service from '../services/compras.service';
import type {
  BaseNecessidade,
  GerarPedidoItem,
  PedidoEscrita,
  PedidoFiltros,
  RecebimentoEscrita,
} from '../types/compras.types';
import { FINANCEIRO_KEY, PRODUTOS_KEY } from '@/shared/constants/entityKeys';

function useInvalidarCompras() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: comprasKeys.todos });
}

function avisarErro(titulo: string) {
  const toast = useToast();
  return (erro: unknown) => toast.error(titulo, getErrorMessage(erro as never, 'Tente de novo.') as string);
}

// --- leitura -----------------------------------------------------------------------

export function useNecessidadesQuery(
  params: MaybeRef<{ base: BaseNecessidade; cobertura_dias: number }> = { base: 'MINIMO', cobertura_dias: 30 },
) {
  return useQuery({
    queryKey: computed(() => [...comprasKeys.necessidades(), unref(params)]),
    queryFn: () => service.getNecessidades(unref(params)),
    refetchInterval: REFETCH_CADASTROS,
  });
}

export function useComprasDaOSQuery(osId: MaybeRef<number | null>) {
  return useQuery({
    queryKey: computed(() => [...comprasKeys.todos, 'os', unref(osId)]),
    queryFn: () => service.getComprasDaOS(unref(osId) as number),
    enabled: computed(() => !!unref(osId)),
    refetchInterval: REFETCH_CADASTROS,
  });
}

export function useRelatorioComprasQuery(inicio: MaybeRef<string>, fim: MaybeRef<string>) {
  return useQuery({
    queryKey: computed(() => [...comprasKeys.todos, 'relatorio', unref(inicio), unref(fim)]),
    queryFn: () => service.getRelatorioCompras(unref(inicio), unref(fim)),
    enabled: computed(() => !!unref(inicio) && !!unref(fim) && unref(inicio) <= unref(fim)),
  });
}

export function usePedidosQuery(filtros: MaybeRef<PedidoFiltros>) {
  return useQuery({
    queryKey: computed(() => comprasKeys.pedidos(unref(filtros))),
    queryFn: () => service.listarPedidos(unref(filtros)),
    refetchInterval: REFETCH_CADASTROS,
  });
}

export function usePedidoQuery(id: MaybeRef<number | null>) {
  return useQuery({
    queryKey: computed(() => comprasKeys.pedido(unref(id) ?? 0)),
    queryFn: () => service.getPedido(unref(id) as number),
    enabled: computed(() => !!unref(id)),
  });
}

export function useBuscaProdutoQuery(termo: MaybeRef<string>) {
  return useQuery({
    queryKey: computed(() => comprasKeys.buscaProduto(unref(termo).trim())),
    queryFn: () => service.buscarProdutosParaPedido(unref(termo).trim()),
    enabled: computed(() => unref(termo).trim().length >= 2),
    staleTime: 30_000,
  });
}

// --- escrita -----------------------------------------------------------------------

export function useGerarPedidos() {
  const invalidar = useInvalidarCompras();
  const toast = useToast();
  return useMutation({
    mutationFn: (itens: GerarPedidoItem[]) => service.gerarPedidos(itens),
    onSuccess: (criados) => {
      invalidar();
      toast.success(
        criados.length === 1 ? `Rascunho ${criados[0].codigo} criado` : `${criados.length} rascunhos criados`,
        'Confira os preços e envie ao fornecedor.',
      );
    },
    onError: avisarErro('Não foi possível gerar os pedidos'),
  });
}

export function useSalvarPedido() {
  const invalidar = useInvalidarCompras();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ id, pedido }: { id: number | null; pedido: PedidoEscrita }) =>
      id ? service.atualizarPedido(id, pedido) : service.criarPedido(pedido),
    onSuccess: (salvo, { id }) => {
      invalidar();
      toast.success(id ? `Pedido ${salvo.codigo} salvo` : `Rascunho ${salvo.codigo} criado`);
    },
    onError: avisarErro('Não foi possível salvar o pedido'),
  });
}

export function useAtualizarDadosPedido() {
  const invalidar = useInvalidarCompras();
  const toast = useToast();
  return useMutation({
    mutationFn: (args: { id: number; previsao_entrega: string | null; observacao: string | null }) =>
      service.atualizarDadosPedido(args.id, {
        previsao_entrega: args.previsao_entrega,
        observacao: args.observacao,
      }),
    onSuccess: () => {
      invalidar();
      toast.success('Pedido atualizado');
    },
    onError: avisarErro('Não foi possível atualizar o pedido'),
  });
}

export function useEnviarPedido() {
  const invalidar = useInvalidarCompras();
  const toast = useToast();
  return useMutation({
    mutationFn: (id: number) => service.enviarPedido(id),
    onSuccess: (pedido) => {
      invalidar();
      toast.success(`Pedido ${pedido.codigo} marcado como enviado`);
    },
    onError: avisarErro('Não foi possível enviar o pedido'),
  });
}

export function useVoltarRascunho() {
  const invalidar = useInvalidarCompras();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) => service.voltarPedidoRascunho(id, motivo),
    onSuccess: (pedido) => {
      invalidar();
      toast.success(`Pedido ${pedido.codigo} voltou a rascunho`);
    },
    onError: avisarErro('Não foi possível voltar o pedido a rascunho'),
  });
}

export function useCancelarPedido() {
  const invalidar = useInvalidarCompras();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) => service.cancelarPedido(id, motivo),
    onSuccess: (pedido) => {
      invalidar();
      // "Cancelado", nunca "excluído": o pedido continua no histórico.
      toast.success(`Pedido ${pedido.codigo} cancelado`);
    },
    onError: avisarErro('Não foi possível cancelar o pedido'),
  });
}

// --- fase 3: recebimento -----------------------------------------------------------

/**
 * O recebimento mexe no ESTOQUE (produtos) e no FINANCEIRO (contas a pagar),
 * não só em compras: invalida os três prefixos, senão a tela de produtos e as
 * contas a pagar ficariam mostrando o antes.
 */
function useInvalidarAposRecebimento() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: comprasKeys.todos });
    queryClient.invalidateQueries({ queryKey: [PRODUTOS_KEY] });
    queryClient.invalidateQueries({ queryKey: [FINANCEIRO_KEY] });
  };
}

export function useReceberPedido() {
  const invalidar = useInvalidarAposRecebimento();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ id, recebimento }: { id: number; recebimento: RecebimentoEscrita }) =>
      service.receberPedido(id, recebimento),
    onSuccess: (pedido) => {
      invalidar();
      toast.success(
        pedido.situacao === 'RECEBIDO' ? `Pedido ${pedido.codigo} recebido` : `Entrada parcial do ${pedido.codigo}`,
        'O estoque já foi atualizado.',
      );
    },
    onError: avisarErro('Não foi possível dar entrada'),
  });
}

export function useEncerrarSaldo() {
  const invalidar = useInvalidarCompras();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) => service.encerrarSaldoPedido(id, motivo),
    onSuccess: (pedido) => {
      invalidar();
      toast.success(`Saldo do ${pedido.codigo} encerrado`);
    },
    onError: avisarErro('Não foi possível encerrar o saldo'),
  });
}
