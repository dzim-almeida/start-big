<script setup lang="ts">
/**
 * @component EditorOrcamento
 * @description O editor de UM orçamento em página inteira (Spec 06B §6.2).
 *
 * Junta os blocos, liga `acoes` aos botões e trata o conflito. NÃO calcula
 * valor nenhum (C8): todo número vem da API.
 *
 * Peças principais:
 * - fila de escrita (D7): toda gravação sai uma por vez, com a revisão certa;
 * - salvamento automático do cabeçalho (D8-D11);
 * - criação preguiçosa (D5): na tela "novo", o POST só acontece na primeira
 *   informação real; depois a rota vira `/orcamentos/:id` (quem troca é a view);
 * - ao sair, espera a fila e pergunta se algo não foi salvo (D10).
 *
 * A view monta este componente com `:key` do orçamento: abrir OUTRA versão
 * recomeça tudo do zero (formulário, fila, conflito).
 */
import { computed, onMounted, ref, watch, watchEffect } from 'vue';
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute, useRouter, type RouteLocationNormalized } from 'vue-router';
import { useQueryClient } from '@tanstack/vue-query';
import { Printer } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import GerenteAprovacaoModal from '@/shared/components/commons/GerenteAprovacaoModal/GerenteAprovacaoModal.vue';
import { useConfirmacao } from '@/shared/composables/useConfirmacao';
import { useGerenteAprovacao } from '@/shared/composables/useGerenteAprovacao';
import { useToast } from '@/shared/composables/useToast';
import { useRotulosStatusOS } from '@/modules/order-service/shared/segmento/useRotulosStatusOS';
import type { OsStatusEnumDataType } from '@/modules/order-service/ordens/schemas/enums/osEnums.schema';

import { chaveDetalhe } from '../../constants/orcamento.constants';
import { useAbrirOS } from '../../composables/useAbrirOS';
import { useAcoesOrcamento } from '../../composables/useAcoesOrcamento';
import { useAprovacao } from '../../composables/useAprovacao';
import { proverEditor } from '../../composables/useEditorContexto';
import { useFilaOrcamento } from '../../composables/useFilaOrcamento';
import { useImprimirProposta } from '../../composables/useImprimirProposta';
import { useOrcamentoDaOS } from '../../composables/useOrcamentoDaOS';
import { useOrcamentoQuery, useVersoesQuery } from '../../composables/useOrcamentoQuery';
import { usePermissoesOrcamento } from '../../composables/usePermissoesOrcamento';
import { useSalvamentoAutomatico } from '../../composables/useSalvamentoAutomatico';
import type { AcoesOrcamento, MovelDetalhe, OrcamentoDetalhe, PrecosDesatualizados } from '../../schemas/orcamentoDetalhe.schema';
import { criarOrcamento } from '../../services/orcamento.service';
import { montarDadosProposta } from '../../utils/dadosProposta';
import type { AprovacaoEntrada, DesfazerEntrada } from '../../schemas/aprovacao.schema';
import type { CabecalhoForm } from '../../utils/diferencaCabecalho';
import { codigoDoErro, mensagemDoErro, statusDoErro } from '../../utils/erros';
import type { PendenciaEnvio } from '../../utils/pendenciasEnvio';
import AprovarModal from '../modais/AprovarModal.vue';
import AtualizarPrecosModal from '../modais/AtualizarPrecosModal.vue';
import DesfazerAprovacaoModal from '../modais/DesfazerAprovacaoModal.vue';
import OSCriadaModal from '../modais/OSCriadaModal.vue';
import ConflitoModal from '../modais/ConflitoModal.vue';
import EnviarModal from '../modais/EnviarModal.vue';
import HistoricoDrawer from '../modais/HistoricoDrawer.vue';
import MovelModal, { type MovelParaSalvar } from '../modais/MovelModal.vue';
import RecusarModal from '../modais/RecusarModal.vue';
import VoltarEditarModal from '../modais/VoltarEditarModal.vue';
import PropostaPrintTemplate from '../print/PropostaPrintTemplate.vue';
import BlocoAmbientes from './BlocoAmbientes.vue';
import BlocoClienteProjeto from './BlocoClienteProjeto.vue';
import BlocoCondicoes from './BlocoCondicoes.vue';
import BlocoInstalacao from './BlocoInstalacao.vue';
import BlocoMedicao from './BlocoMedicao.vue';
import EditorAvisos from './EditorAvisos.vue';
import EditorCabecalho from './EditorCabecalho.vue';
import EditorFaixaStatus from './EditorFaixaStatus.vue';
import PainelCustos from './PainelCustos.vue';
import PainelResumo from './PainelResumo.vue';
import VisaoClienteView from './VisaoClienteView.vue';

const props = defineProps<{ idInicial: number | null }>();
const emit = defineEmits<{ criado: [id: number] }>();

const route = useRoute();
const router = useRouter();
const queryClient = useQueryClient();
const { podeGerir, podeVerCustos, podeCriarProduto } = usePermissoesOrcamento();

// --- Dados, fila e salvamento ------------------------------------------------------
const id = ref<number | null>(props.idInicial);
const fila = useFilaOrcamento(id);
// O polling pergunta "tem algo pendente?" ao salvamento, que só existe depois do detalhe.
const pendente = ref(false);
const { data: detalhe, isLoading, isError, error } = useOrcamentoQuery(id, pendente);

/** Uma criação só, mesmo que o salvamento e o "+ Ambiente" peçam juntos (D5). */
let criacao: Promise<OrcamentoDetalhe> | null = null;
function criar(corpo: Partial<CabecalhoForm>): Promise<OrcamentoDetalhe> {
  if (!criacao) {
    criacao = criarOrcamento(corpo)
      .then((novo) => {
        queryClient.setQueryData(chaveDetalhe(novo.id), novo);   // a tela já tem o detalhe
        id.value = novo.id;
        fila.invalidarLista();
        emit('criado', novo.id);                                 // a view troca a rota
        return novo;
      })
      .catch((erro) => {
        criacao = null;                                          // falhou: pode tentar de novo
        throw erro;
      });
  }
  return criacao;
}

const salvamento = useSalvamentoAutomatico(detalhe, fila, { criar });
watchEffect(() => { pendente.value = salvamento.temPendencia.value; });

const acoesOrcamento = useAcoesOrcamento(id, fila);
const aprovacao = useAprovacao(id, fila);
const toast = useToast();

// --- O que pode ser feito (D13) ------------------------------------------------------
/** Na tela "novo" ainda não há `acoes`: só editar (se puder gerir). */
const SEM_ACOES: AcoesOrcamento = {
  editar: false, enviar: false, voltar_a_editar: false, recusar: false, renovar: false,
  nova_versao: false, excluir: false, anexos: false, aprovar: false, desfazer_aprovacao: false,
};
const acoes = computed<AcoesOrcamento>(() =>
  detalhe.value?.acoes ?? { ...SEM_ACOES, editar: id.value == null && podeGerir.value },
);
const editavel = computed(() => acoes.value.editar);
const incluiCustos = computed(() => (detalhe.value ? detalhe.value.inclui_custos : podeVerCustos.value));

// --- Confirmações (um modal só) ------------------------------------------------------
const confirmacao = useConfirmacao();

/** Tela "novo": cria agora, com o que já foi digitado (ex.: ao incluir o 1º ambiente). */
async function garantirOrcamento(): Promise<number | null> {
  if (id.value != null) return id.value;
  try {
    const novo = await criar({ ...salvamento.form });
    return novo.id;
  } catch {
    return null;                                                 // o toast já explicou
  }
}

// --- Modal do móvel -------------------------------------------------------------------
const movelModal = ref<{ aberto: boolean; ambienteId: number; movel: MovelDetalhe | null }>({
  aberto: false, ambienteId: 0, movel: null,
});
function abrirMovel(ambienteId: number, movel?: MovelDetalhe) {
  movelModal.value = { aberto: true, ambienteId, movel: movel ?? null };
}
async function salvarMovel(dados: MovelParaSalvar): Promise<boolean> {
  const novo = dados.movelId != null
    ? await acoesOrcamento.salvarMovel(dados.movelId, dados.movel)
    : await acoesOrcamento.criarMovel(dados.ambienteId, dados.movel);
  return novo != null;
}
const ambientesDoModal = computed(() => (detalhe.value?.ambientes ?? []).map((a) => ({ id: a.id, nome: a.nome })));
const custoHora = computed(() => (detalhe.value?.inclui_custos ? detalhe.value.parametros.custo_hora_centavos : null));

proverEditor({
  id,
  detalhe,
  form: salvamento.form,
  errosPorCampo: salvamento.errosPorCampo,
  editavel,
  incluiCustos,
  acoes,
  acoesOrcamento,
  garantirOrcamento,
  confirmar: confirmacao.pedirConfirmacao,
  abrirMovel,
});

// --- Versão que substituiu esta (faixa "Abrir v3", D42) -----------------------------
const substituido = computed(() => detalhe.value?.status === 'SUBSTITUIDO');
const { data: versoes } = useVersoesQuery(id, substituido);
const versaoSubstituta = computed(() => {
  if (!substituido.value || !versoes.value?.length) return null;
  const maisNova = versoes.value.reduce((a, b) => (b.versao > a.versao ? b : a));
  return maisNova.id !== id.value ? { id: maisNova.id, versao: maisNova.versao } : null;
});

// --- Visão do cliente (D14) --------------------------------------------------------------
const visaoCliente = ref(false);
const dados = computed(() =>
  detalhe.value
    ? montarDadosProposta(detalhe.value, new Date(), { versaoSubstituta: versaoSubstituta.value?.versao ?? null })
    : null,
);

// --- Ciclo de vida (D36-D43) -------------------------------------------------------------
const enviarAberto = ref(false);
const recusarAberto = ref(false);
const voltarAberto = ref(false);
const historicoAberto = ref(false);
const gravandoTransicao = ref(false);
/** Depois de excluir, sair não pergunta nada (não há o que salvar). */
let saindoPorExclusao = false;

/** Grava o que está pendente antes de uma ação que depende do estado salvo. */
async function gravarPendencias() {
  await salvamento.salvarAgora();
  await fila.esvaziar();
}

/** Igual, e diz se TUDO ficou gravado (sem conflito e sem campo pendente). */
async function gravarTudo(): Promise<boolean> {
  await gravarPendencias();
  return !fila.conflito.value && !salvamento.temPendencia.value;
}

// --- Proposta (Spec 07) -------------------------------------------------------------
const { imprimir, enviarEImprimir, dadosParaImprimir, imprimindo } = useImprimirProposta({
  detalhe,
  gravarPendencias: gravarTudo,                                   // D4: só imprime o que está gravado
  versaoSubstituta: computed(() => versaoSubstituta.value?.versao ?? null),
});

async function abrirEnviar() {
  await gravarPendencias();
  enviarAberto.value = true;
}

/** Roda uma transição com o botão em "carregando"; fecha o modal se deu certo. */
async function transicao(executar: () => Promise<OrcamentoDetalhe | null>, fechar: () => void) {
  gravandoTransicao.value = true;
  try {
    const novo = await executar();
    if (novo) fechar();
    return novo;
  } finally {
    gravandoTransicao.value = false;
  }
}

/**
 * Enviar (D36). Com `gerarProposta`, imprime DEPOIS do envio, com a validade
 * já gravada (Spec 07 D7); cancelar o diálogo de impressão não desfaz o envio.
 */
async function enviar(gerarProposta: boolean) {
  const envio = () => transicao(acoesOrcamento.enviar, () => { enviarAberto.value = false; });
  if (gerarProposta) await enviarEImprimir(envio);
  else await envio();
}
const voltarAEditar = () => transicao(acoesOrcamento.voltarAEditar, () => { voltarAberto.value = false; });
const recusar = (motivo: string) => transicao(() => acoesOrcamento.recusar(motivo), () => { recusarAberto.value = false; });

async function renovar() {
  const novo = await transicao(acoesOrcamento.renovar, () => undefined);
  if (novo) await conferirPrecos(novo.id);                       // D39
}

async function novaVersao() {
  const ok = await confirmacao.pedirConfirmacao({
    titulo: 'Nova versão',
    descricao: 'A versão atual fica guardada, somente leitura, e uma cópia em rascunho é criada para editar.',
    confirmLabel: 'Criar nova versão',
    variant: 'info',
  });
  if (!ok) return;
  const nova = await transicao(acoesOrcamento.novaVersao, () => undefined);
  // A versão nova abre com a conferência de preços (D39); a view recomeça o editor.
  if (nova) await router.push({ name: 'marcenaria-orcamento', params: { id: nova.id }, query: { conferirPrecos: '1' } });
}

async function excluir() {
  const ok = await confirmacao.pedirConfirmacao({
    titulo: 'Excluir orçamento',
    descricao: 'Este rascunho nunca foi enviado e será apagado. Esta ação não pode ser desfeita.',
    confirmLabel: 'Excluir',
    variant: 'danger',
  });
  if (!ok) return;
  if (await acoesOrcamento.excluir()) {
    saindoPorExclusao = true;                                    // nada a salvar: não pergunta
    await router.push({ name: 'marcenaria-orcamentos' });
  }
}

// --- Aprovação (Spec 08B) -------------------------------------------------------------
const aprovarAberto = ref(false);
const osCriadaAberto = ref(false);
const desfazerAberto = ref(false);
const desfazendo = ref(false);
const gerente = useGerenteAprovacao();                            // PIN quando a loja exige (D17)
const { abrirOS } = useAbrirOS();

async function abrirAprovar() {
  await gravarPendencias();                                      // a aprovação usa o que está gravado
  aprovarAberto.value = true;
}

/** Aprova pela fila (D6). Devolve true se deu certo (o modal fecha e vem o OSCriadaModal, D7). */
async function aprovar(entrada: AprovacaoEntrada): Promise<boolean> {
  try {
    await aprovacao.aprovar(entrada);
    osCriadaAberto.value = true;
    return true;
  } catch (erro) {
    if (codigoDoErro(erro) !== 'REVISAO_DESATUALIZADA') toast.error('Não foi possível aprovar.', mensagemDoErro(erro));
    return false;
  }
}

/** Desfaz (D16, D17): com a loja exigindo PIN, o modal do gerente pede e reenvia. */
async function desfazer(entrada: DesfazerEntrada) {
  desfazendo.value = true;
  try {
    const novo = await aprovacao.desfazer(entrada, (pinErrado) => {
      if (pinErrado) toast.error('PIN do gerente inválido');
      return gerente.pedirPin();
    });
    if (novo) {
      desfazerAberto.value = false;
      toast.success('Aprovação desfeita. A OS foi cancelada.');
    }
  } catch (erro) {
    if (codigoDoErro(erro) !== 'REVISAO_DESATUALIZADA') toast.error('Não foi possível desfazer a aprovação.', mensagemDoErro(erro));
  } finally {
    desfazendo.value = false;
  }
}

// Aprovado: quem aprovou e por que não dá para desfazer vêm do resumo da OS (08A Revisão 1).
const numeroOs = computed(() => (detalhe.value?.status === 'APROVADO' ? detalhe.value.os?.numero_os ?? null : null));
const { data: resumoOs } = useOrcamentoDaOS(numeroOs, computed(() => numeroOs.value != null));
const { rotuloStatus } = useRotulosStatusOS();
const rotuloStatusOs = computed(() =>
  detalhe.value?.os ? rotuloStatus(detalhe.value.os.status as OsStatusEnumDataType) : null,
);

// --- Atualizar preços (O3, D39, D40) -------------------------------------------------
const precos = ref<PrecosDesatualizados | null>(null);
const precosAbertos = ref(false);
const avisoPrecos = ref(false);                                  // faixa para quem não vê custos
const gravandoPrecos = ref(false);

async function conferirPrecos(orcamentoId: number, avisarSemDiferenca = false) {
  if (!incluiCustos.value) {
    avisoPrecos.value = true;                                    // não vê custo: só avisa
    return;
  }
  const resultado = await acoesOrcamento.conferirPrecos(orcamentoId);
  if (resultado?.itens.length) {
    precos.value = resultado;
    precosAbertos.value = true;
  } else if (avisarSemDiferenca) {
    await confirmacao.pedirConfirmacao({
      titulo: 'Preços em dia',
      descricao: 'Os custos dos insumos deste orçamento são os mesmos do cadastro de produtos.',
      confirmLabel: 'Ok',
      variant: 'info',
    });
  }
}

async function atualizarPrecos(insumoIds: number[]) {
  gravandoPrecos.value = true;
  try {
    if (await acoesOrcamento.atualizarPrecos(insumoIds)) precosAbertos.value = false;
  } finally {
    gravandoPrecos.value = false;
  }
}

// Chegou de "Nova versão" (?conferirPrecos=1): confere assim que o detalhe chegar.
onMounted(() => {
  if (route.query.conferirPrecos !== '1') return;
  const parar = watch(detalhe, async (atual) => {
    if (!atual) return;
    parar();
    await router.replace({ query: {} });                         // não repete ao recarregar
    await conferirPrecos(atual.id);
  }, { immediate: true });
});

// --- Conflito (D12) --------------------------------------------------------------------
const recarregando = ref(false);
async function recarregar() {
  recarregando.value = true;
  try {
    await salvamento.recarregarDescartando();
  } finally {
    recarregando.value = false;
  }
}

// --- Navegação ---------------------------------------------------------------------------
function irPara(bloco: PendenciaEnvio['bloco']) {
  enviarAberto.value = false;
  document.getElementById(bloco)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
const voltarALista = () => router.push({ name: 'marcenaria-orcamentos' });
const abrirVersao = (outroId: number) => router.push({ name: 'marcenaria-orcamento', params: { id: outroId } });

/**
 * Antes de sair (outra tela ou outra versão): manda o que está esperando e
 * espera a fila (D10). Se ainda sobrar algo sem salvar, pergunta.
 */
async function podeSair(destino: RouteLocationNormalized): Promise<boolean> {
  // A própria tela trocou "/novo" por "/orcamentos/:id" (ou limpou a URL): não é saída.
  if (saindoPorExclusao || (destino.name === 'marcenaria-orcamento' && Number(destino.params.id) === id.value)) return true;
  try {
    await gravarPendencias();
  } catch {
    // O erro já está no indicador; a pergunta abaixo decide.
  }
  if (!salvamento.temPendencia.value) return true;
  return confirmacao.pedirConfirmacao({
    titulo: 'Alterações não salvas',
    descricao: 'Há alterações que não foram salvas. Sair mesmo assim?',
    confirmLabel: 'Sair',
    cancelLabel: 'Ficar',
    variant: 'warning',
  });
}
onBeforeRouteLeave(podeSair);
onBeforeRouteUpdate(podeSair);

/** Não encontrado (excluído, outro segmento) ou sem permissão. */
const erroCarregar = computed(() => {
  if (!isError.value) return '';
  const status = statusDoErro(error.value);
  if (status === 403) return 'Você não tem permissão para ver orçamentos.';
  if (status === 404) return 'Orçamento não encontrado. Ele pode ter sido excluído.';
  return 'Não foi possível abrir o orçamento.';
});
</script>

<template>
  <div class="flex flex-col gap-5">
    <EditorCabecalho
      :detalhe="detalhe"
      :estado="salvamento.estado.value"
      :salvo-em="salvamento.salvoEm.value"
      :tentando-de-novo="salvamento.tentandoDeNovo.value"
      :gravando-acao="fila.pendentes.value > 0"
      :visao-cliente="visaoCliente"
      @voltar="voltarALista"
      @alternar-visao-cliente="visaoCliente = !visaoCliente"
      @historico="historicoAberto = true"
      @enviar="abrirEnviar"
      @aprovar="abrirAprovar"
      @excluir="excluir"
      @tentar-agora="salvamento.salvarAgora()"
      @abrir-versao="abrirVersao"
    >
      <!-- Spec 07: a proposta em qualquer status (com a faixa do status, D6) -->
      <template #acoes>
        <BaseButton variant="secondary" size="sm" :is-loading="imprimindo" data-testid="imprimir-proposta" @click="imprimir()">
          <Printer :size="14" class="mr-1" /> Proposta
        </BaseButton>
      </template>
    </EditorCabecalho>

    <!-- Carregando / erro -->
    <p v-if="id != null && isLoading" class="text-sm text-zinc-400 animate-pulse">Carregando orçamento…</p>
    <div v-else-if="erroCarregar" class="flex flex-col items-start gap-3 rounded-2xl border border-zinc-200 bg-white p-6">
      <p class="text-sm text-red-600" data-testid="erro-carregar">{{ erroCarregar }}</p>
      <BaseButton variant="secondary" size="sm" @click="voltarALista">Voltar aos orçamentos</BaseButton>
    </div>

    <!-- Visão do cliente (D14): troca o editor pela tela de proposta -->
    <VisaoClienteView v-else-if="visaoCliente && dados" :dados="dados" @voltar="visaoCliente = false" />

    <template v-else>
      <EditorFaixaStatus
        v-if="detalhe"
        :detalhe="detalhe"
        :versao-substituta="versaoSubstituta"
        :aprovado-por="resumoOs?.aprovado_por ?? null"
        :rotulo-status-os="rotuloStatusOs"
        :motivos-desfazer="resumoOs?.motivos_desfazer ?? []"
        @abrir-os="detalhe?.os && abrirOS(detalhe.os.numero_os)"
        @proposta-aprovada="imprimir(undefined, 'aprovada')"
        @desfazer="desfazerAberto = true"
        @voltar-a-editar="voltarAberto = true"
        @recusar="recusarAberto = true"
        @nova-versao="novaVersao"
        @renovar="renovar"
        @abrir-versao="abrirVersao"
      />

      <EditorAvisos :codigos="detalhe?.avisos ?? []" :inclui-custos="incluiCustos" :aviso-precos="avisoPrecos" />

      <div class="grid grid-cols-1 items-start gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div class="flex min-w-0 flex-col gap-5">
          <BlocoClienteProjeto />
          <BlocoAmbientes />
          <BlocoInstalacao v-if="detalhe" />
          <BlocoMedicao />
          <BlocoCondicoes />
        </div>
        <!-- Coluna lateral fixa ao rolar; em janela estreita, desce para baixo -->
        <aside class="flex flex-col gap-5 lg:sticky lg:top-4">
          <PainelResumo />
          <PainelCustos v-if="incluiCustos" @conferir-precos="detalhe && conferirPrecos(detalhe.id, true)" />
        </aside>
      </div>
    </template>

    <!-- Modais -->
    <MovelModal
      :is-open="movelModal.aberto"
      :orcamento-id="id"
      :ambiente-id="movelModal.ambienteId"
      :movel="movelModal.movel"
      :ambientes="ambientesDoModal"
      :inclui-custos="incluiCustos"
      :custo-hora-centavos="custoHora"
      :editavel="editavel"
      :pode-cadastrar-insumo="podeCriarProduto"
      :salvar="salvarMovel"
      @close="movelModal.aberto = false"
    />
    <EnviarModal v-if="detalhe" :is-open="enviarAberto" :detalhe="detalhe" :enviando="gravandoTransicao" @close="enviarAberto = false" @enviar="enviar" @ir-para="irPara" />
    <RecusarModal :is-open="recusarAberto" :gravando="gravandoTransicao" @close="recusarAberto = false" @recusar="recusar" />
    <VoltarEditarModal
      v-if="detalhe"
      :is-open="voltarAberto"
      :total-centavos="detalhe.calculo.total_centavos"
      :gravando="gravandoTransicao"
      @close="voltarAberto = false"
      @confirmar="voltarAEditar"
    />
    <AtualizarPrecosModal :is-open="precosAbertos" :precos="precos" :gravando="gravandoPrecos" @close="precosAbertos = false" @atualizar="atualizarPrecos" />
    <HistoricoDrawer :id="id" :aberto="historicoAberto" @fechar="historicoAberto = false" />
    <!-- Aprovação (Spec 08B) -->
    <AprovarModal v-if="detalhe && acoes.aprovar" :is-open="aprovarAberto" :detalhe="detalhe" :aprovar="aprovar" @close="aprovarAberto = false" />
    <OSCriadaModal
      :is-open="osCriadaAberto"
      :detalhe="detalhe"
      @close="osCriadaAberto = false"
      @abrir-os="osCriadaAberto = false; detalhe?.os && abrirOS(detalhe.os.numero_os)"
      @imprimir-aprovada="osCriadaAberto = false; imprimir(undefined, 'aprovada')"
    />
    <DesfazerAprovacaoModal
      v-if="detalhe?.os"
      :is-open="desfazerAberto"
      :numero-os="detalhe.os.numero_os"
      :sinal-recebido-centavos="resumoOs?.sinal_recebido_centavos ?? detalhe.aprovacao?.sinal_recebido_centavos ?? 0"
      :gravando="desfazendo"
      @close="desfazerAberto = false"
      @confirmar="desfazer"
    />
    <GerenteAprovacaoModal
      :is-open="gerente.isOpen.value"
      motivo="Cancelar a OS"
      descricao="Desfazer a aprovação cancela a OS. Insira o PIN do gerente para autorizar."
      @confirmar="gerente.confirmar"
      @cancelar="gerente.cancelar"
    />
    <ConflitoModal :is-open="fila.conflito.value" :campos-perdidos="salvamento.camposPendentes.value" :recarregando="recarregando" @recarregar="recarregar" />
    <!-- O documento só existe enquanto imprime (Spec 07 §6.3). -->
    <PropostaPrintTemplate v-if="dadosParaImprimir" :dados="dadosParaImprimir" />
    <BaseConfirmModal
      :is-open="confirmacao.isOpen.value"
      :title="confirmacao.opcoes.value.titulo"
      :description="confirmacao.opcoes.value.descricao"
      :confirm-label="confirmacao.opcoes.value.confirmLabel"
      :cancel-label="confirmacao.opcoes.value.cancelLabel"
      :variant="confirmacao.opcoes.value.variant"
      overlay
      @close="confirmacao.cancelar"
      @confirm="confirmacao.confirmar"
    />
  </div>
</template>
