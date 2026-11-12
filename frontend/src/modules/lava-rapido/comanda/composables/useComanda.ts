import { computed, ref, watch } from 'vue';

import type { CustomerUnionReadSchemaDataType } from '@/modules/order-service/ordens/schemas/relationship/customer/customer.schema';
import type { ObjetoBuscaItemDataType } from '@/modules/order-service/ordens/schemas/relationship/objetoBusca.schema';
import { buscarObjetosPorIdentificador } from '@/modules/order-service/ordens/services/orderServiceGet.service';
import { getCustomersBySearch } from '@/modules/order-service/ordens/services/relationship/osRelationshipGet.service';
import { useTiposDeTrabalho } from '@/modules/order-service/shared/segmento/useTiposDeTrabalho';

import { usePortesQuery, useServicosDoPorteQuery } from '../../shared/composables/usePortes';
import { normalizarPlaca, previsaoDeEntrega } from '../../shared/utils/lavaRapido';
import { abrirLavagem, criarClienteRapido, type ItemComanda } from '../services/comanda.service';

/** Cliente escolhido na comanda: um que já existe, ou um novo (nome + celular). */
export interface ClienteDaComanda {
  id: number | null;
  nome: string;
  celular: string;
}

/** Nome de exibição de um cliente PF ou PJ. */
export function nomeDoCliente(cliente: CustomerUnionReadSchemaDataType): string {
  const c = cliente as unknown as { nome?: string; razao_social?: string };
  return c.nome ?? c.razao_social ?? '';
}

/**
 * Estado e regras da comanda de uma tela (Spec 03B, SPEC-00 U2).
 *
 * A ordem da tela é a ordem do balcão: placa → (veículo e dono aparecem) →
 * tipo → porte → serviços com o preço do porte → lavador → avarias → Entrar.
 * Meta: ≤ 30 s para quem já veio (PR10).
 */
export function useComanda() {
  const { tipos, opcoes: tiposDeVeiculo, tipoPorId } = useTiposDeTrabalho();
  const { data: portes, ativosDoTipo } = usePortesQuery();

  // --- Estado ------------------------------------------------------------------
  const placa = ref('');
  const veiculo = ref<ObjetoBuscaItemDataType | null>(null);     // achado pela placa
  const buscandoPlaca = ref(false);

  const cliente = ref<ClienteDaComanda | null>(null);
  const tipo = ref<string>('');
  const porteId = ref<number | null>(null);
  const modelo = ref('');
  const marca = ref('');
  const cor = ref('');
  /** servico_id → valor em centavos (o atendente pode mudar o preço, C1a). */
  const selecionados = ref<Record<number, number>>({});
  const lavadores = ref<number[]>([]);
  const avarias = ref<string[]>([]);
  const fotos = ref<File[]>([]);
  const observacao = ref('');
  const salvando = ref(false);

  // Tipo padrão: o primeiro (Carro), como na OS dinâmica.
  watch(tiposDeVeiculo, (lista) => { if (!tipo.value && lista.length) tipo.value = lista[0].value; }, { immediate: true });

  // --- Derivados ------------------------------------------------------------------
  const portesDoTipo = computed(() => ativosDoTipo(tipo.value));
  const porte = computed(() => (portes.value ?? []).find((p) => p.id === porteId.value) ?? null);
  const { data: servicosDoPorte, isLoading: carregandoServicos } = useServicosDoPorteQuery(porteId);
  const avariasDoTipo = computed(() => tipoPorId(tipo.value)?.avarias ?? []);

  /** A placa é obrigatória neste tipo? (Bicicleta e Outros: não — o sistema gera.) */
  const placaObrigatoria = computed(() =>
    tipoPorId(tipo.value)?.campos.find((c) => c.nome === 'placa')?.obrigatorio ?? true);

  // Trocou o tipo: porte e avarias de outro tipo não servem mais.
  watch(tipo, (novo, antigo) => {
    if (!antigo || novo === antigo) return;
    if (porte.value && porte.value.tipo_veiculo !== novo) porteId.value = null;
    avarias.value = avarias.value.filter((a) => avariasDoTipo.value.includes(a));
  });

  // Trocou o porte: os serviços já escolhidos passam para o preço do porte novo.
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

  const total = computed(() => itens.value.reduce((soma, i) => soma + i.valor, 0));

  const previsao = computed(() =>
    previsaoDeEntrega(
      new Date(),
      (servicosDoPorte.value ?? []).filter((s) => s.servico_id in selecionados.value).map((s) => s.duracao_minutos),
    ));

  /** O que falta para poder entrar, em palavras da tela. Vazio = pode salvar. */
  const faltando = computed<string[]>(() => {
    const lista: string[] = [];
    if (placaObrigatoria.value && !normalizarPlaca(placa.value)) lista.push('Placa');
    if (!cliente.value || !cliente.value.nome.trim()) lista.push('Cliente');
    if (!porteId.value) lista.push('Porte');
    if (!modelo.value.trim()) lista.push(tipo.value === 'outros' ? 'Descrição' : 'Modelo');
    if (!itens.value.length) lista.push('Serviço');
    return lista;
  });

  // --- Placa: acha o veículo e o dono --------------------------------------------
  let temporizador: ReturnType<typeof setTimeout> | undefined;
  watch(placa, (texto) => {
    clearTimeout(temporizador);
    const alvo = normalizarPlaca(texto);
    if (alvo.length < 7) {
      if (veiculo.value) veiculo.value = null;               // apagou a placa: solta o veículo
      return;
    }
    temporizador = setTimeout(() => procurarVeiculo(alvo), 350);
  });

  async function procurarVeiculo(alvo: string) {
    buscandoPlaca.value = true;
    try {
      const achados = await buscarObjetosPorIdentificador(alvo);
      if (normalizarPlaca(placa.value) !== alvo) return;     // o atendente já digitou outra
      const exato = achados.find((o) => normalizarPlaca(o.numero_serie ?? '') === alvo) ?? null;
      veiculo.value = exato;
      if (exato) aplicarVeiculo(exato);
    } catch {
      veiculo.value = null;                                   // sem rede: segue como veículo novo
    } finally {
      buscandoPlaca.value = false;
    }
  }

  /** Segunda visita: veículo, dono e porte vêm prontos. */
  function aplicarVeiculo(objeto: ObjetoBuscaItemDataType) {
    modelo.value = objeto.modelo ?? '';
    marca.value = objeto.marca ?? '';
    cor.value = objeto.cor ?? '';
    cliente.value = { id: objeto.cliente_id, nome: objeto.cliente_nome ?? 'Cliente', celular: '' };
    const nomePorte = String((objeto.dados_adicionais ?? {}).porte ?? '').toLowerCase();
    const achado = (portes.value ?? []).find((p) => p.ativo && p.nome.toLowerCase() === nomePorte);
    if (achado) {
      tipo.value = achado.tipo_veiculo;
      porteId.value = achado.id;
    }
  }

  // --- Cliente (placa nova) --------------------------------------------------------
  const buscaCliente = ref('');
  const clientesAchados = ref<CustomerUnionReadSchemaDataType[]>([]);
  let temporizadorCliente: ReturnType<typeof setTimeout> | undefined;
  watch(buscaCliente, (texto) => {
    clearTimeout(temporizadorCliente);
    if (texto.trim().length < 2) {
      clientesAchados.value = [];
      return;
    }
    temporizadorCliente = setTimeout(async () => {
      try {
        clientesAchados.value = (await getCustomersBySearch(texto)).slice(0, 6);
      } catch {
        clientesAchados.value = [];
      }
    }, 300);
  });

  function escolherCliente(c: CustomerUnionReadSchemaDataType) {
    cliente.value = { id: c.id, nome: nomeDoCliente(c), celular: '' };
    buscaCliente.value = '';
    clientesAchados.value = [];
  }

  function clienteNovo(nome: string, celular: string) {
    cliente.value = { id: null, nome, celular };
  }

  // --- Ações ------------------------------------------------------------------------
  function alternarServico(servicoId: number, valor: number) {
    const atual = { ...selecionados.value };
    if (servicoId in atual) delete atual[servicoId];
    else atual[servicoId] = valor;
    selecionados.value = atual;
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
    buscaCliente.value = '';
    clientesAchados.value = [];
    tipo.value = tiposDeVeiculo.value[0]?.value ?? '';
  }

  /** Abre a lavagem. Devolve o número da OS e o que não deu para gravar junto. */
  async function salvar(): Promise<{ numero_os: string; avisos: string[] }> {
    if (faltando.value.length) throw new Error(`Preencha: ${faltando.value.join(', ')}.`);
    salvando.value = true;
    try {
      const c = cliente.value!;
      const clienteId = c.id ?? await criarClienteRapido({ nome: c.nome, celular: c.celular });
      return await abrirLavagem(
        {
          cliente_id: clienteId,
          // O 1º lavador é o responsável (Spec 03B, D4): na loja pequena, quem
          // abre é quem lava. Sem lavador, a OS fica sem responsável.
          funcionario_id: lavadores.value[0] ?? null,
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
          previsao: previsao.value,
        },
        lavadores.value,
        fotos.value,
      );
    } finally {
      salvando.value = false;
    }
  }

  return {
    tipos, tiposDeVeiculo, portesDoTipo, servicosDoPorte, carregandoServicos, avariasDoTipo,
    placa, veiculo, buscandoPlaca, placaObrigatoria,
    cliente, buscaCliente, clientesAchados, escolherCliente, clienteNovo,
    tipo, porteId, modelo, marca, cor,
    selecionados, alternarServico, itens, total, previsao,
    lavadores, avarias, alternarAvaria, fotos, observacao,
    faltando, salvando, salvar, limpar,
  };
}
