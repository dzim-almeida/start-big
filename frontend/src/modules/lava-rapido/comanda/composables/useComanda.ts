import { computed, ref, watch } from 'vue';

import type { CustomerUnionReadSchemaDataType } from '@/modules/order-service/ordens/schemas/relationship/customer/customer.schema';
import type { ObjetoBuscaItemDataType } from '@/modules/order-service/ordens/schemas/relationship/objetoBusca.schema';
import type { OsPriorityEnumDataType } from '@/modules/order-service/ordens/schemas/enums/osEnums.schema';
import { buscarObjetosPorIdentificador } from '@/modules/order-service/ordens/services/orderServiceGet.service';
import { getCustomerByIdForOS } from '@/modules/order-service/ordens/services/relationship/osRelationshipGet.service';
import { useTiposDeTrabalho } from '@/modules/order-service/shared/segmento/useTiposDeTrabalho';
import { useAuthStore } from '@/shared/stores/auth.store';

import { usePortesQuery, useServicosDoPorteQuery } from '../../shared/composables/usePortes';
import { normalizarPlaca, previsaoDeEntrega } from '../../shared/utils/lavaRapido';
import type { Agendamento } from '../../shared/schemas/agenda.schema';
import { abrirLavagem, type ItemComanda } from '../services/comanda.service';

/** Nome de exibição de um cliente PF ou PJ. */
export function nomeDoCliente(cliente: CustomerUnionReadSchemaDataType): string {
  const c = cliente as unknown as { nome?: string; razao_social?: string };
  return c.nome ?? c.razao_social ?? '';
}

/** Data local "AAAA-MM-DD" (o formato do campo Previsão da OS). */
export function dataLocalISO(data: Date): string {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${data.getFullYear()}-${p(data.getMonth() + 1)}-${p(data.getDate())}`;
}

/**
 * Estado e regras da comanda (Spec 03B, SPEC-00 U2), no PADRÃO da OS:
 * situação, responsável, prioridade e previsão em cima; resumo de cobrança e
 * cliente na lateral; veículo, serviços, lavadores e avarias no corpo.
 */
export function useComanda() {
  const { opcoes: tiposDeVeiculo, tipoPorId } = useTiposDeTrabalho();
  const { data: portes, ativosDoTipo } = usePortesQuery();
  const authStore = useAuthStore();

  // --- Controles (o cartão de cima, igual ao da OS) --------------------------------
  const responsavelId = ref<string>('');
  const prioridade = ref<OsPriorityEnumDataType>('NORMAL');
  /** "AAAA-MM-DD". Acompanha a previsão calculada até alguém mexer à mão. */
  const dataPrevisao = ref<string>(dataLocalISO(new Date()));
  const previsaoEditada = ref(false);

  // --- Cobrança (o resumo da lateral, igual ao da OS) --------------------------------
  const valorEntrada = ref(0);                         // centavos
  const formaPagamentoEntradaId = ref<number | null>(null);
  const taxaEntrega = ref(0);                          // centavos (leva-e-traz)

  // --- Veículo e cliente -------------------------------------------------------------
  const placa = ref('');
  const veiculo = ref<ObjetoBuscaItemDataType | null>(null);
  const buscandoPlaca = ref(false);
  const cliente = ref<CustomerUnionReadSchemaDataType | null>(null);
  const tipo = ref<string>('');
  const porteId = ref<number | null>(null);
  const modelo = ref('');
  const marca = ref('');
  const cor = ref('');

  // --- Serviços, execução e entrada ----------------------------------------------------
  /** servico_id → valor em centavos (o atendente pode mudar o preço, C1a). */
  const selecionados = ref<Record<number, number>>({});
  const lavadores = ref<number[]>([]);
  const avarias = ref<string[]>([]);
  const fotos = ref<File[]>([]);
  const observacao = ref('');
  const salvando = ref(false);

  watch(tiposDeVeiculo, (lista) => { if (!tipo.value && lista.length) tipo.value = lista[0].value; }, { immediate: true });

  // --- Derivados ------------------------------------------------------------------------
  const portesDoTipo = computed(() => ativosDoTipo(tipo.value));
  const porte = computed(() => (portes.value ?? []).find((p) => p.id === porteId.value) ?? null);
  const { data: servicosDoPorte, isLoading: carregandoServicos } = useServicosDoPorteQuery(porteId);
  const avariasDoTipo = computed(() => tipoPorId(tipo.value)?.avarias ?? []);
  const placaObrigatoria = computed(() =>
    tipoPorId(tipo.value)?.campos.find((c) => c.nome === 'placa')?.obrigatorio ?? true);

  watch(tipo, (novo, antigo) => {
    if (!antigo || novo === antigo) return;
    if (porte.value && porte.value.tipo_veiculo !== novo) porteId.value = null;
    avarias.value = avarias.value.filter((a) => avariasDoTipo.value.includes(a));
  });

  // Trocou o porte: os serviços escolhidos passam para o preço do porte novo.
  watch(servicosDoPorte, (lista) => {
    if (!lista) return;
    const novos: Record<number, number> = {};
    for (const id of Object.keys(selecionados.value).map(Number)) {
      const servico = lista.find((s) => s.servico_id === id);
      if (servico) novos[id] = servico.valor;
    }
    selecionados.value = novos;
  });

  const itens = computed<ItemComanda[]>(() =>
    (servicosDoPorte.value ?? [])
      .filter((s) => s.servico_id in selecionados.value)
      .map((s) => ({ servico_id: s.servico_id, nome: s.descricao, valor: selecionados.value[s.servico_id] })));

  const subtotal = computed(() => itens.value.reduce((soma, i) => soma + i.valor, 0));
  const total = computed(() => subtotal.value + (taxaEntrega.value || 0));

  /** Hora prevista pela soma das durações (SPEC-00 O4). */
  const previsao = computed(() =>
    previsaoDeEntrega(
      new Date(),
      (servicosDoPorte.value ?? []).filter((s) => s.servico_id in selecionados.value).map((s) => s.duracao_minutos),
    ));
  watch(previsao, (p) => { if (!previsaoEditada.value && p) dataPrevisao.value = dataLocalISO(p); });

  function mudarDataPrevisao(valor: string) {
    dataPrevisao.value = valor;
    previsaoEditada.value = true;
  }

  const faltando = computed<string[]>(() => {
    const lista: string[] = [];
    if (placaObrigatoria.value && !normalizarPlaca(placa.value)) lista.push('Placa');
    if (!cliente.value) lista.push('Cliente');
    if (!porteId.value) lista.push('Porte');
    if (!modelo.value.trim()) lista.push(tipo.value === 'outros' ? 'Descrição' : 'Modelo');
    if (!itens.value.length) lista.push('Serviço');
    return lista;
  });

  // --- Placa: acha o veículo e o dono --------------------------------------------------
  let temporizador: ReturnType<typeof setTimeout> | undefined;
  watch(placa, (texto) => {
    clearTimeout(temporizador);
    const alvo = normalizarPlaca(texto);
    if (alvo.length < 7) {
      if (veiculo.value) veiculo.value = null;
      return;
    }
    temporizador = setTimeout(() => procurarVeiculo(alvo), 350);
  });

  async function procurarVeiculo(alvo: string) {
    buscandoPlaca.value = true;
    try {
      const achados = await buscarObjetosPorIdentificador(alvo);
      if (normalizarPlaca(placa.value) !== alvo) return;
      const exato = achados.find((o) => normalizarPlaca(o.numero_serie ?? '') === alvo) ?? null;
      veiculo.value = exato;
      if (exato) await aplicarVeiculo(exato);
    } catch {
      veiculo.value = null;
    } finally {
      buscandoPlaca.value = false;
    }
  }

  /** Segunda visita: veículo, dono e porte vêm prontos. */
  async function aplicarVeiculo(objeto: ObjetoBuscaItemDataType) {
    modelo.value = objeto.modelo ?? '';
    marca.value = objeto.marca ?? '';
    cor.value = objeto.cor ?? '';
    const nomePorte = String((objeto.dados_adicionais ?? {}).porte ?? '').toLowerCase();
    const achado = (portes.value ?? []).find((p) => p.ativo && p.nome.toLowerCase() === nomePorte);
    if (achado) {
      tipo.value = achado.tipo_veiculo;
      porteId.value = achado.id;
    }
    if (!cliente.value || cliente.value.id !== objeto.cliente_id) {
      try {
        cliente.value = await getCustomerByIdForOS(objeto.cliente_id);
      } catch {
        // Sem o cliente: o atendente escolhe pela busca.
      }
    }
  }

  // --- Cliente e veículo vindos da busca (padrão da OS) ------------------------------
  /**
   * O cliente vem da busca de cliente/placa de sempre, ANTES da comanda
   * (`useEntradaLavagem`). Achado pela placa, o veículo vem junto.
   */
  async function aplicarEntrada(c: CustomerUnionReadSchemaDataType | null, o: ObjetoBuscaItemDataType | null) {
    cliente.value = c;
    if (o) {
      placa.value = o.numero_serie ?? '';
      veiculo.value = o;
      await aplicarVeiculo(o);
    }
  }

  // --- Ações ------------------------------------------------------------------------------
  function alternarServico(servicoId: number, valor: number) {
    const atual = { ...selecionados.value };
    if (servicoId in atual) delete atual[servicoId];
    else atual[servicoId] = valor;
    selecionados.value = atual;
  }

  function mudarPreco(servicoId: number, valorCentavos: number) {
    if (!(servicoId in selecionados.value)) return;
    selecionados.value = { ...selecionados.value, [servicoId]: Math.max(0, Math.round(valorCentavos)) };
  }

  function alternarAvaria(avaria: string) {
    avarias.value = avarias.value.includes(avaria)
      ? avarias.value.filter((a) => a !== avaria)
      : [...avarias.value, avaria];
  }

  function limpar() {
    placa.value = '';
    veiculo.value = null;
    cliente.value = null;
    porteId.value = null;
    modelo.value = '';
    marca.value = '';
    cor.value = '';
    selecionados.value = {};
    lavadores.value = [];
    avarias.value = [];
    fotos.value = [];
    observacao.value = '';
    prioridade.value = 'NORMAL';
    dataPrevisao.value = dataLocalISO(new Date());
    previsaoEditada.value = false;
    valorEntrada.value = 0;
    formaPagamentoEntradaId.value = null;
    taxaEntrega.value = 0;
    // Responsável padrão: quem está usando o sistema (como na OS de sempre).
    const meu = authStore.userData?.funcionario_id;
    responsavelId.value = meu ? String(meu) : '';
    tipo.value = tiposDeVeiculo.value[0]?.value ?? '';
  }

  /**
   * O cliente agendado chegou (Spec 08B): a comanda abre com o combinado.
   * Devolve nome e contato quando o cliente ainda não tem cadastro, para a
   * tela já abrir o "cliente novo" preenchido.
   */
  function preencherDeAgendamento(a: Agendamento) {
    if (a.tipo_veiculo) tipo.value = a.tipo_veiculo;
    porteId.value = a.porte_id;
    modelo.value = a.veiculo ?? '';
    observacao.value = a.observacao ?? '';
    selecionados.value = Object.fromEntries(
      a.servicos.filter((s) => s.servico_id).map((s) => [s.servico_id as number, s.valor]));
    placa.value = a.placa ?? '';                     // dispara a busca do veículo
  }

  /**
   * Previsão que vai para a OS: a hora calculada quando o dia bate com o do
   * campo; se alguém escolheu outro dia à mão, o dia escolhido.
   */
  function previsaoParaGravar(): Date | string | null {
    if (previsao.value && dataLocalISO(previsao.value) === dataPrevisao.value) return previsao.value;
    return dataPrevisao.value || null;
  }

  async function salvar(): Promise<{ numero_os: string; avisos: string[] }> {
    if (faltando.value.length) throw new Error(`Preencha: ${faltando.value.join(', ')}.`);
    salvando.value = true;
    try {
      return await abrirLavagem(
        {
          cliente_id: cliente.value!.id,
          // Responsável escolhido; sem ele, o 1º lavador (Spec 03B, D4).
          funcionario_id: Number(responsavelId.value) || lavadores.value[0] || null,
          prioridade: prioridade.value,
          tipo_veiculo: tipo.value,
          placa: normalizarPlaca(placa.value),
          modelo: modelo.value,
          marca: marca.value,
          cor: cor.value,
          dados_objeto: { ...(veiculo.value?.dados_adicionais ?? {}) },
          porte: porte.value?.nome ?? '',
          itens: itens.value,
          avarias: avarias.value,
          observacao: observacao.value,
          previsao: previsaoParaGravar(),
          valor_entrada: valorEntrada.value,
          forma_pagamento_entrada_id: formaPagamentoEntradaId.value,
          taxa_entrega: taxaEntrega.value,
        },
        lavadores.value,
        fotos.value,
      );
    } finally {
      salvando.value = false;
    }
  }

  return {
    tiposDeVeiculo, portesDoTipo, servicosDoPorte, carregandoServicos, avariasDoTipo,
    responsavelId, prioridade, dataPrevisao, mudarDataPrevisao,
    valorEntrada, formaPagamentoEntradaId, taxaEntrega,
    placa, veiculo, buscandoPlaca, placaObrigatoria,
    cliente, aplicarEntrada,
    tipo, porteId, modelo, marca, cor,
    selecionados, alternarServico, mudarPreco, itens, subtotal, total, previsao,
    lavadores, avarias, alternarAvaria, fotos, observacao,
    faltando, salvando, salvar, limpar, preencherDeAgendamento,
  };
}
