/**
 * @fileoverview Salvamento automático do CABEÇALHO do orçamento (Spec 06B D8-D12, §7.5).
 *
 * - 800 ms depois da última mudança, manda SÓ os campos que mudaram num PATCH.
 * - Ambientes e móveis NÃO passam por aqui: são ações que gravam na hora.
 * - Erro de rede: tenta de novo em 2 s, 5 s e 10 s; depois, "Tentar agora".
 * - Erro de validação (422): não tenta de novo; o campo fica com a mensagem.
 * - Detalhe novo do servidor (outro computador, outra ação) só entra no
 *   formulário quando nada está pendente: nunca apaga o que o usuário digita.
 * - Na tela de "novo orçamento" (D5), o primeiro salvamento CRIA (POST).
 */
import { computed, reactive, ref, watch, type Ref } from 'vue';
import { useDebounceFn } from '@vueuse/core';

import { ESPERA_SALVAR_MS, ROTULO_CAMPO } from '../constants/orcamento.constants';
import type { OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';
import { patchOrcamento } from '../services/orcamento.service';
import { cabecalhoDoDetalhe, diferencaCabecalho, type CabecalhoForm } from '../utils/diferencaCabecalho';
import { campoDoErro, codigoDoErro, ehErroDeRede, mensagemDoErro } from '../utils/erros';
import { ConflitoRevisao, type FilaOrcamento } from './useFilaOrcamento';

/** Estados do indicador ao lado do código (D9). */
export type EstadoSalvamento = 'salvo' | 'esperando' | 'salvando' | 'erro' | 'invalido';

/** Novas tentativas depois de erro de rede (D9). */
export const ESPERAS_NOVA_TENTATIVA_MS = [2000, 5000, 10000];

/** Formulário de um orçamento que ainda não existe (tela "novo", D5). */
export function cabecalhoVazio(): CabecalhoForm {
  return {
    cliente_id: null,
    funcionario_id: null,
    objeto_id: null,
    projeto_nome: null,
    endereco_obra: null,
    medicao_observacoes: null,
    observacoes_proposta: null,
    validade_dias: 15,
    prazo_entrega_dias: 30,
    desconto: { modo: 'PERCENTUAL', valor: 0 },
    sinal: { modo: 'PERCENTUAL', valor: 0 },
  };
}

/** Cópia sem nada compartilhado (desconto e sinal são objetos: editar um não pode mudar o outro). */
function cabecalhoCopiado(cabecalho: CabecalhoForm): CabecalhoForm {
  return { ...cabecalho, desconto: { ...cabecalho.desconto }, sinal: { ...cabecalho.sinal } };
}

/** Campos que contam como "informação real" para criar o orçamento (D5). */
const CAMPOS_QUE_CRIAM: (keyof CabecalhoForm)[] = ['cliente_id', 'projeto_nome', 'endereco_obra', 'objeto_id'];

interface Opcoes {
  /** Tela "novo": cria o orçamento (POST) com os primeiros campos e devolve o detalhe. */
  criar?: (corpo: Partial<CabecalhoForm>) => Promise<OrcamentoDetalhe>;
}

export function useSalvamentoAutomatico(
  detalhe: Ref<OrcamentoDetalhe | undefined>,
  fila: FilaOrcamento,
  opcoes: Opcoes = {},
) {
  const inicial = detalhe.value ? cabecalhoDoDetalhe(detalhe.value) : cabecalhoVazio();
  const form = reactive<CabecalhoForm>(cabecalhoCopiado(inicial)); // cópia editável dos campos
  let ultimoSalvo: CabecalhoForm = cabecalhoCopiado(inicial);       // o que o servidor tem
  const estado = ref<EstadoSalvamento>('salvo');
  const salvoEm = ref<Date | null>(null);                     // "Salvo às 14:32"
  const errosPorCampo = ref<Record<string, string>>({});     // 422 com `campo` (06A Revisão 1)
  const mensagemErro = ref('');
  let tentativa = 0;                                          // quantas novas tentativas de rede já foram
  let timerNovaTentativa: ReturnType<typeof setTimeout> | null = null;
  const tentandoDeNovo = ref(false);                          // true enquanto espera a próxima tentativa (D9)
  let aplicandoDoServidor = false;                            // true enquanto o form recebe o detalhe novo
  let descartarNaProxima = false;                             // "Recarregar orçamento" depois de um conflito (D12)

  /** Os campos que ainda não chegaram ao servidor, com o nome da tela (ConflitoModal, D12). */
  const camposPendentes = computed(() =>
    Object.keys(diferencaCabecalho(ultimoSalvo, form)).map((chave) => ROTULO_CAMPO[chave] ?? chave),
  );

  function limparNovaTentativa() {
    if (timerNovaTentativa) clearTimeout(timerNovaTentativa);
    timerNovaTentativa = null;
    tentandoDeNovo.value = false;
  }

  async function executarSalvamento(): Promise<void> {
    limparNovaTentativa();
    const mudancas = diferencaCabecalho(ultimoSalvo, form);   // só o que mudou (D8)
    if (!Object.keys(mudancas).length) {
      estado.value = 'salvo';
      return;
    }
    // Tela "novo": só cria quando há informação real (cliente, projeto); senão, espera.
    if (!detalhe.value && !CAMPOS_QUE_CRIAM.some((c) => c in mudancas && mudancas[c] != null)) {
      estado.value = 'esperando';
      return;
    }
    estado.value = 'salvando';
    try {
      if (!detalhe.value && opcoes.criar) {
        await opcoes.criar(mudancas);                          // POST; o editor troca a rota
        // O POST aceita só alguns campos; os outros seguem num PATCH logo depois.
        ultimoSalvo = { ...ultimoSalvo, ...pickCriados(mudancas) };
      } else {
        const id = detalhe.value!.id;
        await fila.enfileirar((revisao) => patchOrcamento(id, revisao, mudancas));
        ultimoSalvo = { ...ultimoSalvo, ...mudancas };        // o servidor agora tem isso
      }
      errosPorCampo.value = {};
      mensagemErro.value = '';
      tentativa = 0;
      salvoEm.value = new Date();
      // Algo mudou enquanto salvava? Salva de novo; senão, "Salvo".
      estado.value = Object.keys(diferencaCabecalho(ultimoSalvo, form)).length ? 'esperando' : 'salvo';
      if (estado.value === 'esperando') salvar();
    } catch (erro) {
      mensagemErro.value = mensagemDoErro(erro);
      const campo = campoDoErro(erro);                        // 'desconto', 'sinal'... ou null
      if (campo) errosPorCampo.value = { [campo]: mensagemErro.value };
      if (erro instanceof ConflitoRevisao || codigoDoErro(erro) === 'REVISAO_DESATUALIZADA') {
        estado.value = 'erro';                                // o ConflitoModal toma conta (D12)
      } else if (ehErroDeRede(erro) && tentativa < ESPERAS_NOVA_TENTATIVA_MS.length) {
        estado.value = 'erro';                                // "tentando de novo"
        timerNovaTentativa = setTimeout(() => void executarSalvamento(), ESPERAS_NOVA_TENTATIVA_MS[tentativa]);
        tentandoDeNovo.value = true;
        tentativa++;
      } else if (ehErroDeRede(erro)) {
        estado.value = 'erro';                                // acabaram as tentativas: botão "Tentar agora"
      } else {
        estado.value = 'invalido';                            // 422: espera o usuário corrigir
      }
    }
  }

  /** Na criação, os campos aceitos pelo POST ficam gravados; o resto vai num PATCH em seguida. */
  function pickCriados(mudancas: Partial<CabecalhoForm>): Partial<CabecalhoForm> {
    const aceitos: (keyof CabecalhoForm)[] = ['cliente_id', 'objeto_id', 'projeto_nome', 'endereco_obra', 'funcionario_id'];
    return Object.fromEntries(aceitos.filter((k) => k in mudancas).map((k) => [k, mudancas[k]])) as Partial<CabecalhoForm>;
  }

  /** Espera 800 ms depois da última mudança (várias mudanças viram um PATCH só). */
  const salvar = useDebounceFn(() => executarSalvamento(), ESPERA_SALVAR_MS);

  /** "Tentar agora" (depois das 3 tentativas) e ao sair da tela (D10). */
  async function salvarAgora(): Promise<void> {
    tentativa = 0;
    await executarSalvamento();
  }

  // Qualquer mudança no formulário (feita pelo usuário) agenda o salvamento.
  watch(form, () => {
    if (aplicandoDoServidor) return;
    estado.value = 'esperando';
    void salvar();
  }, { deep: true });

  /**
   * Detalhe novo do servidor (polling, resposta de outra ação, criação): D11.
   * - campo que o usuário mudou e ainda não foi salvo: FICA como ele digitou;
   * - os outros seguem o servidor (ex.: o vendedor padrão e a validade da
   *   configuração que o POST preencheu). Se ficassem com o valor velho da
   *   tela, a diferença os mandaria de volta num PATCH, desfazendo o servidor.
   */
  watch(detalhe, (novo) => {
    if (!novo) return;
    const doServidor = cabecalhoDoDetalhe(novo);
    // Depois de um conflito, o que ficou pendente é descartado: a trava avisa, não junta (06A §8).
    const pendentes = descartarNaProxima ? {} : diferencaCabecalho(ultimoSalvo, form); // o que só a tela tem
    aplicandoDoServidor = true;                               // não agenda salvamento por isto
    for (const chave of Object.keys(doServidor) as (keyof CabecalhoForm)[]) {
      if (!(chave in pendentes)) {
        (form as unknown as Record<string, unknown>)[chave] = copia(doServidor[chave]);
      }
    }
    ultimoSalvo = { ...ultimoSalvo, ...doServidor };          // o servidor tem isto agora
    if (descartarNaProxima) {
      descartarNaProxima = false;
      estado.value = 'salvo';                                 // a tela agora é igual ao servidor
      errosPorCampo.value = {};
      mensagemErro.value = '';
    }
    queueMicrotask(() => { aplicandoDoServidor = false; });
  });

  /**
   * Botão "Recarregar orçamento" do ConflitoModal (D12): busca a versão atual e
   * troca o formulário inteiro por ela (o usuário refaz o que foi listado).
   */
  async function recarregarDescartando(): Promise<void> {
    limparNovaTentativa();
    descartarNaProxima = true;
    await fila.recarregar();
  }

  /** Cópia de um valor (o desconto/sinal é objeto: a tela não pode dividir o mesmo com o "salvo"). */
  function copia<T>(valor: T): T {
    return valor && typeof valor === 'object' ? { ...valor } : valor;
  }

  /** Tem algo esperando ir para o servidor? (para o polling não recarregar, D11) */
  const temPendencia = computed(() => estado.value !== 'salvo' || fila.pendentes.value > 0);

  return {
    form, estado, salvoEm, errosPorCampo, mensagemErro, camposPendentes, temPendencia, tentandoDeNovo,
    salvar, salvarAgora, recarregarDescartando,
  };
}
