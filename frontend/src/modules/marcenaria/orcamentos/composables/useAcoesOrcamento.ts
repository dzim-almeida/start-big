/**
 * @fileoverview Ações do orçamento que gravam NA HORA (Spec 06B D8, D36-D43):
 * ambientes, móveis, transições de status, atualizar preços e excluir.
 *
 * Toda ação passa pela fila de escrita (D7), que manda a revisão certa e
 * guarda a resposta no cache. Aqui só se decide a MENSAGEM de cada erro:
 * - conflito de revisão: quem fala é o ConflitoModal (D12), não um toast;
 * - qualquer outro erro: toast com a frase do backend.
 */
import { useQueryClient } from '@tanstack/vue-query';
import type { Ref } from 'vue';

import { useToast } from '@/shared/composables/useToast';

import { CHAVE_RAIZ, chaveDetalhe } from '../constants/orcamento.constants';
import type { OrcamentoDetalhe, PrecosDesatualizados } from '../schemas/orcamentoDetalhe.schema';
import * as servico from '../services/orcamento.service';
import * as moveis from '../services/orcamentoMovel.service';
import { atualizarPrecos as atualizarPrecosApi, getPrecosDesatualizados } from '../services/orcamentoPrecos.service';
import { codigoDoErro, mensagemDoErro } from '../utils/erros';
import { ConflitoRevisao, type FilaOrcamento } from './useFilaOrcamento';

export function useAcoesOrcamento(id: Ref<number | null>, fila: FilaOrcamento) {
  const toast = useToast();
  const queryClient = useQueryClient();

  /**
   * Roda uma escrita na fila e cuida do erro.
   * Devolve o detalhe novo, ou null se não deu certo (a tela não precisa de try/catch).
   */
  async function gravar(
    escrita: (orcamentoId: number, revisao: number) => Promise<OrcamentoDetalhe>,
    sucesso?: string,
  ): Promise<OrcamentoDetalhe | null> {
    const orcamentoId = id.value;
    if (orcamentoId == null) return null;                  // tela "novo" sem orçamento criado
    try {
      const novo = await fila.enfileirar((revisao) => escrita(orcamentoId, revisao));
      if (sucesso) toast.success(sucesso);
      return novo;
    } catch (erro) {
      avisarErro(erro);
      return null;
    }
  }

  /** Conflito de revisão abre o ConflitoModal (D12); o resto vira toast. */
  function avisarErro(erro: unknown) {
    if (erro instanceof ConflitoRevisao || codigoDoErro(erro) === 'REVISAO_DESATUALIZADA') return;
    toast.error(mensagemDoErro(erro));
  }

  // --- Ambientes (D19, D20) -------------------------------------------------

  const criarAmbiente = (nome: string) =>
    gravar((oid, rev) => moveis.criarAmbiente(oid, rev, nome));
  const renomearAmbiente = (ambienteId: number, nome: string) =>
    gravar((oid, rev) => moveis.renomearAmbiente(oid, ambienteId, rev, nome));
  const removerAmbiente = (ambienteId: number) =>
    gravar((oid, rev) => moveis.removerAmbiente(oid, ambienteId, rev), 'Ambiente excluído.');
  const ordenarAmbientes = (ids: number[]) =>
    gravar((oid, rev) => moveis.ordenarAmbientes(oid, rev, ids));

  // --- Móveis (D23) -----------------------------------------------------------

  const criarMovel = (ambienteId: number, movel: moveis.MovelEntrada) =>
    gravar((oid, rev) => moveis.criarMovel(oid, ambienteId, rev, movel), 'Móvel incluído.');
  const salvarMovel = (movelId: number, movel: moveis.MovelEntrada) =>
    gravar((oid, rev) => moveis.salvarMovel(oid, movelId, rev, movel), 'Móvel salvo.');
  const removerMovel = (movelId: number) =>
    gravar((oid, rev) => moveis.removerMovel(oid, movelId, rev), 'Móvel excluído.');
  const duplicarMovel = (movelId: number) =>
    gravar((oid, rev) => moveis.duplicarMovel(oid, movelId, rev), 'Móvel duplicado.');
  const ordenarMoveis = (ambienteId: number, ids: number[]) =>
    gravar((oid, rev) => moveis.ordenarMoveis(oid, ambienteId, rev, ids));

  // --- Arquiteto (Spec 09B D7) ----------------------------------------------
  /**
   * Escolhe (ou tira) o arquiteto: salva na hora. Só o fornecedor vai; o %
   * fica com o backend (o gravado, se era o mesmo, ou o padrão do orçamento).
   */
  const definirArquiteto = (fornecedorId: number | null) =>
    gravar((oid, rev) => servico.putRt(oid, rev, fornecedorId ? [{ fornecedor_id: fornecedorId }] : []));

  // --- Ciclo de vida (D36-D42) ----------------------------------------------

  const enviar = () => gravar(servico.enviarOrcamento, 'Orçamento enviado ao cliente.');
  const voltarAEditar = () => gravar(servico.voltarAEditar, 'Orçamento de volta ao rascunho.');
  const recusar = (motivo: string) =>
    gravar((oid, rev) => servico.recusarOrcamento(oid, rev, motivo), 'Recusa registrada.');
  const renovar = () => gravar(servico.renovarOrcamento, 'Orçamento renovado.');
  /** Devolve o detalhe da versão NOVA (a tela navega até ela). */
  const novaVersao = () => gravar(servico.novaVersao, 'Nova versão criada.');
  const atualizarPrecos = (insumoIds: number[]) =>
    gravar((oid, rev) => atualizarPrecosApi(oid, rev, insumoIds), 'Preços atualizados.');

  /**
   * Insumos com preço diferente do cadastro hoje (O3). Só quem vê custos pode
   * perguntar; erro aqui não atrapalha nada (devolve null e a tela segue).
   */
  async function conferirPrecos(orcamentoId: number): Promise<PrecosDesatualizados | null> {
    try {
      return await getPrecosDesatualizados(orcamentoId);
    } catch {
      return null;
    }
  }

  /**
   * Excluir (D41). Não devolve detalhe, então não usa `gravar`: espera a fila
   * esvaziar, lê a revisão do cache e apaga. True se apagou.
   */
  async function excluir(): Promise<boolean> {
    const orcamentoId = id.value;
    if (orcamentoId == null) return false;
    await fila.esvaziar();                                  // nada pendente antes de apagar
    const atual = queryClient.getQueryData<OrcamentoDetalhe>(chaveDetalhe(orcamentoId));
    if (!atual) return false;
    try {
      await servico.excluirOrcamento(orcamentoId, atual.revisao);
      queryClient.removeQueries({ queryKey: chaveDetalhe(orcamentoId) });  // o detalhe não existe mais
      await queryClient.invalidateQueries({ queryKey: [CHAVE_RAIZ, 'lista'] });
      await queryClient.invalidateQueries({ queryKey: [CHAVE_RAIZ, 'contagens'] });
      toast.success('Orçamento excluído.');
      return true;
    } catch (erro) {
      if (codigoDoErro(erro) === 'REVISAO_DESATUALIZADA') fila.conflito.value = true;
      avisarErro(erro);
      return false;
    }
  }

  return {
    criarAmbiente, renomearAmbiente, removerAmbiente, ordenarAmbientes,
    criarMovel, salvarMovel, removerMovel, duplicarMovel, ordenarMoveis, definirArquiteto,
    enviar, voltarAEditar, recusar, renovar, novaVersao, atualizarPrecos, conferirPrecos, excluir,
  };
}
