<script setup lang="ts">
/**
 * @fileoverview Sub-aba Envio da Central de Etiquetas (plano, fase 5).
 *
 * 1. De onde vem o envio: OS ou venda (dados do sistema) ou avulsa.
 * 2. Destinatário, editável só para esta remessa.
 * 3. Volumes, peso e observação.
 * A impressão abre num painel pela direita (mesmo padrão da fila do Estoque):
 * etiqueta de volume (modelo editável) ou DANFE Simplificado – Etiqueta
 * (layout fixo da NT 2020.004, só com NF-e autorizada).
 */
import { computed, ref, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import {
  Printer,
  Ruler,
  Settings2,
  MousePointer2,
  X,
  PencilLine,
  Package,
  FileText,
  AlertTriangle,
  Truck,
} from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { useToast } from '@/shared/composables/useToast';
import { useImpressaoStore } from '@/shared/stores/impressao.store';
import EtiquetaPreview from '@/shared/etiquetas/components/EtiquetaPreview.vue';
import EtiquetasImpressao from '@/shared/etiquetas/components/EtiquetasImpressao.vue';
import { useImpressaoEtiquetas } from '@/shared/etiquetas/useImpressaoEtiquetas';
import { definicaoDeTeste, etiquetasDeTeste } from '@/shared/etiquetas/teste';
import { PRESETS_DANFE, PRESETS_VOLUME } from '@/shared/etiquetas/presets';
import { etiquetasPorPagina, type ModeloEtiqueta } from '@/shared/etiquetas/modelo';
import {
  DADOS_EXEMPLO,
  etiquetasDosVolumes,
  valoresDoDanfe,
  valoresDoEnvio,
  type DadosEnvio,
  type OrigemEnvioItem,
  type ParteEnvio,
  type TipoOrigemEnvio,
} from '@/shared/etiquetas/envio';
import { LARGURA_MINIMA_DANFE_MM } from '@/shared/etiquetas/layoutEnvio';

import OrigemEnvioBusca from './OrigemEnvioBusca.vue';
import DestinatarioEnvioForm from './DestinatarioEnvioForm.vue';
import CalibracaoEtiquetaModal from '../estoque/CalibracaoEtiquetaModal.vue';
import ModelosEtiquetaModal from '../modelo/ModelosEtiquetaModal.vue';
import { useModelosEtiqueta } from '../../composables/useModelosEtiqueta';
import { getDadosEnvio, getRemetenteEnvio } from '../../services/envio.service';
import { usePermissoesEtiqueta } from '@/shared/etiquetas/usePermissoesEtiqueta';

const MAX_VOLUMES = 200;

const props = defineProps<{
  /** Atalho vindo da OS ou da venda: já abre com a origem escolhida. */
  origemInicial?: { tipo: TipoOrigemEnvio; id: number } | null;
}>();

const toast = useToast();
const { podeGerenciar } = usePermissoesEtiqueta();
const impressaoStore = useImpressaoStore();
const { trabalho, imprimir } = useImpressaoEtiquetas();
const { todos: modelosVolume, modelosDaLoja } = useModelosEtiqueta('volume');

// --- Origem ---

type Origem = { tipo: TipoOrigemEnvio; id: number } | 'avulsa' | null;
const origem = ref<Origem>(props.origemInicial ?? null);
watch(
  () => props.origemInicial,
  (nova) => {
    if (nova) origem.value = nova;
  },
);

const {
  data: dadosPedido,
  isLoading: carregandoPedido,
  isError: erroPedido,
} = useQuery({
  queryKey: computed(() => ['etiquetas-envio-dados', origem.value]),
  queryFn: () => {
    const o = origem.value as { tipo: TipoOrigemEnvio; id: number };
    return getDadosEnvio(o.tipo, o.id);
  },
  enabled: computed(() => origem.value !== null && origem.value !== 'avulsa'),
  staleTime: 1000 * 30,
});

const { data: remetente } = useQuery({
  queryKey: ['etiquetas-envio-remetente'],
  queryFn: getRemetenteEnvio,
  enabled: computed(() => origem.value === 'avulsa'),
  staleTime: 1000 * 60 * 5,
});

const DESTINATARIO_VAZIO: ParteEnvio = {
  nome: '',
  documento: null,
  inscricao_estadual: null,
  telefone: null,
  endereco: null,
};

const dados = computed<DadosEnvio | null>(() => {
  if (origem.value === 'avulsa') {
    if (!remetente.value) return null;
    return {
      tipo: 'venda',
      id: 0,
      numero: '',
      identificador: null,
      remetente: remetente.value,
      destinatario: null,
      nfe: null,
    };
  }
  return dadosPedido.value ?? null;
});

// Cópia editável do destinatário — reiniciada a cada origem nova.
const destinatario = ref<ParteEnvio>({ ...DESTINATARIO_VAZIO });
watch(
  () => dados.value,
  (novos) => {
    destinatario.value = JSON.parse(JSON.stringify(novos?.destinatario ?? DESTINATARIO_VAZIO));
  },
  { immediate: true },
);

// Painel da impressão. Não abre sozinho ao escolher a origem: cobriria o
// destinatário e os volumes, que vêm antes de imprimir.
const painelAberto = ref(false);

function selecionar(item: OrigemEnvioItem) {
  origem.value = { tipo: item.tipo, id: item.id };
}

function trocarOrigem() {
  origem.value = null;
  tipo.value = 'volume';
}

const tituloOrigem = computed(() => {
  if (origem.value === 'avulsa') return 'Envio avulso';
  const d = dadosPedido.value;
  if (!d) return 'Carregando...';
  return d.tipo === 'os' ? d.numero : `Venda ${d.numero}`;
});

// --- Volumes ---

const volumes = ref(1);
const pesoKg = ref<number | null>(null);
const observacao = ref('');

const volumesValidos = computed(() =>
  Math.max(1, Math.min(MAX_VOLUMES, Math.round(Number(volumes.value) || 1))),
);

// --- Tipo e modelo ---

const tipo = ref<'volume' | 'danfe'>('volume');
const temNfe = computed(() => !!dados.value?.nfe);

watch(temNfe, (tem) => {
  if (!tem) tipo.value = 'volume';
});

const lembrado = impressaoStore.config.etiqueta_modelo_envio;
const chaveVolume = ref(
  lembrado && !lembrado.startsWith('preset:danfe') ? lembrado : PRESETS_VOLUME[0].chave,
);
const chaveDanfe = ref(lembrado?.startsWith('preset:danfe') ? lembrado : PRESETS_DANFE[0].chave);

const opcoesModelo = computed(() =>
  (tipo.value === 'danfe' ? PRESETS_DANFE : modelosVolume.value).map((m) => ({
    value: m.chave,
    label: m.id ? `${m.nome} (da loja)` : m.nome,
  })),
);

const chaveModelo = computed({
  get: () => (tipo.value === 'danfe' ? chaveDanfe.value : chaveVolume.value),
  set: (valor: string) => {
    if (tipo.value === 'danfe') chaveDanfe.value = valor;
    else chaveVolume.value = valor;
    impressaoStore.salvar({ ...impressaoStore.config, etiqueta_modelo_envio: valor });
  },
});

const modelo = computed<ModeloEtiqueta>(() => {
  if (tipo.value === 'danfe')
    return PRESETS_DANFE.find((m) => m.chave === chaveDanfe.value) ?? PRESETS_DANFE[0];
  return modelosVolume.value.find((m) => m.chave === chaveVolume.value) ?? PRESETS_VOLUME[0];
});

const pular = ref(0);
watch(chaveModelo, () => (pular.value = 0));
const ehFolha = computed(() => modelo.value.definicao.pagina.tipo === 'folha');
const porPagina = computed(() => etiquetasPorPagina(modelo.value.definicao.pagina));

// --- Etiquetas ---

const etiquetas = computed(() => {
  const d = dados.value;
  if (!d) return [];
  if (tipo.value === 'danfe') {
    // Um DANFE por volume: cada caixa precisa levar o seu.
    return Array.from({ length: volumesValidos.value }, () => valoresDoDanfe(d));
  }
  const base = valoresDoEnvio(
    { ...d, destinatario: destinatario.value },
    {
      volumes: volumesValidos.value,
      pesoKg: pesoKg.value ? Number(pesoKg.value) : null,
      observacao: observacao.value,
    },
  );
  return etiquetasDosVolumes(base, volumesValidos.value);
});

const valoresPreview = computed(() => {
  if (etiquetas.value.length) return etiquetas.value[0];
  const exemplo = valoresDoEnvio(DADOS_EXEMPLO, { volumes: 3, pesoKg: 12.5, observacao: 'Frágil' });
  return tipo.value === 'danfe'
    ? valoresDoDanfe(DADOS_EXEMPLO)
    : etiquetasDosVolumes(exemplo, 3)[0];
});

const avisos = computed(() => {
  const lista: string[] = [];
  const d = destinatario.value;
  if (dados.value && tipo.value === 'volume') {
    if (!d.nome.trim()) lista.push('Informe o nome do destinatário.');
    if (!d.endereco?.logradouro || !d.endereco?.cidade)
      lista.push('O endereço do destinatário está incompleto.');
  }
  if (
    tipo.value === 'danfe' &&
    modelo.value.definicao.pagina.largura_mm < LARGURA_MINIMA_DANFE_MM
  ) {
    lista.push(
      `O DANFE Simplificado precisa de pelo menos ${LARGURA_MINIMA_DANFE_MM} mm de largura.`,
    );
  }
  return lista;
});

// --- Impressão ---

function deslocamento() {
  return {
    deslocamentoX: impressaoStore.config.etiqueta_deslocamento_x_mm ?? 0,
    deslocamentoY: impressaoStore.config.etiqueta_deslocamento_y_mm ?? 0,
  };
}

function imprimirEnvio() {
  if (!etiquetas.value.length) return;
  if (tipo.value === 'volume' && avisos.value.length) {
    toast.warning('Confira o destinatário', avisos.value.join(' '));
    return;
  }
  imprimir({
    definicao: modelo.value.definicao,
    etiquetas: etiquetas.value,
    pular: pular.value,
    ...deslocamento(),
  });
}

function imprimirTeste(ajuste?: { deslocamentoX: number; deslocamentoY: number }) {
  const definicao = definicaoDeTeste(modelo.value.definicao, modelo.value.nome);
  imprimir({
    definicao,
    etiquetas: etiquetasDeTeste(definicao),
    pular: 0,
    ...(ajuste ?? deslocamento()),
  });
}

// --- Modelos e calibração ---

const isModelosOpen = ref(false);
const isCalibracaoOpen = ref(false);
const modeloParaEditor = ref<ModeloEtiqueta | null>(null);

function abrirModelos(noEditor: ModeloEtiqueta | null) {
  modeloParaEditor.value = noEditor;
  isModelosOpen.value = true;
}
</script>

<template>
  <div class="space-y-6">
    <!-- Barra: resumo + abrir a impressão -->
    <div class="flex flex-wrap items-center gap-3 p-4 bg-white rounded-2xl">
      <div
        class="w-9 h-9 rounded-xl bg-brand-primary/10 text-brand-primary flex items-center justify-center"
      >
        <Truck :size="18" />
      </div>
      <div class="min-w-0">
        <p class="text-sm font-semibold text-zinc-800">
          {{ origem ? tituloOrigem : 'Etiquetas de envio' }}
        </p>
        <p class="text-xs text-zinc-500">
          <template v-if="dados">
            {{ volumesValidos }} {{ volumesValidos === 1 ? 'volume' : 'volumes' }} ·
            {{ tipo === 'danfe' ? 'DANFE Simplificado' : modelo.nome }}
          </template>
          <template v-else>Escolha uma OS, venda ou envio avulso.</template>
        </p>
      </div>
      <button
        type="button"
        class="ml-auto flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-primary text-white text-sm font-semibold hover:bg-brand-primary-hover transition-colors cursor-pointer shrink-0"
        @click="painelAberto = true"
      >
        <Printer :size="16" />
        Imprimir
        <span
          v-if="dados"
          class="min-w-6 px-1.5 py-0.5 rounded-full bg-white/20 text-xs font-bold text-center"
        >
          {{ etiquetas.length }}
        </span>
      </button>
    </div>

    <section class="bg-white rounded-2xl p-5 space-y-4">
      <div class="flex items-center justify-between gap-3">
        <h3 class="text-sm font-bold text-zinc-800">1. De onde vem o envio</h3>
        <button
          v-if="origem"
          type="button"
          class="flex items-center gap-1 text-xs font-semibold text-zinc-500 hover:text-brand-primary cursor-pointer"
          @click="trocarOrigem"
        >
          <X :size="14" />
          Trocar
        </button>
      </div>

      <template v-if="!origem">
        <OrigemEnvioBusca @selecionar="selecionar" />
        <button
          type="button"
          class="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-dashed border-zinc-300 text-sm font-medium text-zinc-600 hover:border-brand-primary hover:text-brand-primary cursor-pointer"
          @click="origem = 'avulsa'"
        >
          <PencilLine :size="15" />
          Envio avulso — digitar o destinatário
        </button>
      </template>

      <div v-else class="flex items-center gap-3 p-3 rounded-xl bg-zinc-50 border border-zinc-100">
        <div
          class="w-9 h-9 rounded-xl bg-brand-primary/10 text-brand-primary flex items-center justify-center"
        >
          <Package :size="18" />
        </div>
        <div class="min-w-0">
          <p class="text-sm font-semibold text-zinc-800">{{ tituloOrigem }}</p>
          <p class="text-xs text-zinc-500 truncate">
            <template v-if="erroPedido">Não foi possível carregar os dados.</template>
            <template v-else-if="carregandoPedido">Buscando cliente e nota...</template>
            <template v-else-if="origem === 'avulsa'">Destinatário digitado abaixo.</template>
            <template v-else>
              {{ dados?.destinatario?.nome || 'Sem cliente vinculado' }}
              <template v-if="dados?.identificador"> · {{ dados.identificador }}</template>
              <template v-if="dados?.nfe"> · NF-e {{ dados.nfe.numero }}</template>
            </template>
          </p>
        </div>
      </div>
    </section>

    <template v-if="dados">
      <section class="bg-white rounded-2xl p-5 space-y-4">
        <h3 class="text-sm font-bold text-zinc-800">2. Destinatário</h3>
        <DestinatarioEnvioForm v-model="destinatario" />
      </section>

      <section class="bg-white rounded-2xl p-5 space-y-4">
        <h3 class="text-sm font-bold text-zinc-800">3. Volumes</h3>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <BaseInput
            v-model.number="volumes"
            type="number"
            :min="1"
            :max="MAX_VOLUMES"
            label="Quantos volumes"
            ajuda="Uma etiqueta por volume: 1/3, 2/3, 3/3."
          />
          <BaseInput
            v-model.number="pesoKg"
            type="number"
            step="0.1"
            :min="0"
            label="Peso total (kg)"
            placeholder="Opcional"
          />
          <BaseInput v-model="observacao" label="Observação" placeholder="Ex: Frágil" />
        </div>
        <div class="flex justify-end">
          <BaseButton class="flex items-center gap-2" @click="painelAberto = true">
            <Printer :size="16" />
            Continuar para a impressão
          </BaseButton>
        </div>
      </section>
    </template>
  </div>

  <!-- Painel da impressão, pela direita -->
  <Teleport to="body">
    <Transition name="panel">
      <div v-if="painelAberto" class="fixed inset-0 z-40 flex justify-end">
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" @click="painelAberto = false" />

        <div class="relative z-50 w-full max-w-lg bg-white shadow-2xl flex flex-col h-full">
          <div
            class="flex items-center justify-between gap-3 px-6 py-4 border-b border-zinc-100 shrink-0"
          >
            <div class="flex items-center gap-3 min-w-0">
              <div
                class="w-9 h-9 shrink-0 rounded-xl bg-brand-primary/10 text-brand-primary flex items-center justify-center"
              >
                <Truck :size="18" />
              </div>
              <div class="min-w-0">
                <h2 class="text-lg font-semibold text-zinc-800">Impressão do envio</h2>
                <p class="text-xs text-zinc-400 truncate">
                  {{
                    dados
                      ? `${tituloOrigem} · ${etiquetas.length} ${etiquetas.length === 1 ? 'etiqueta' : 'etiquetas'}`
                      : 'Exemplo — escolha a origem do envio'
                  }}
                </p>
              </div>
            </div>
            <button
              class="p-2 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 transition-colors cursor-pointer"
              title="Fechar"
              @click="painelAberto = false"
            >
              <X :size="20" />
            </button>
          </div>

          <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
            <div class="inline-flex w-full p-0.5 rounded-lg bg-zinc-100">
              <button
                type="button"
                :class="['tipo', tipo === 'volume' && 'tipo--ativo']"
                @click="tipo = 'volume'"
              >
                <Package :size="14" />
                Etiqueta de volume
              </button>
              <button
                type="button"
                :class="['tipo', tipo === 'danfe' && 'tipo--ativo']"
                :disabled="!temNfe"
                :title="
                  temNfe
                    ? 'DANFE Simplificado – Etiqueta (NT 2020.004)'
                    : 'Só para OS ou venda com NF-e autorizada'
                "
                @click="tipo = 'danfe'"
              >
                <FileText :size="14" />
                DANFE Simplificado
              </button>
            </div>

            <div class="space-y-2">
              <div class="flex items-end gap-2">
                <BaseSelect
                  v-model="chaveModelo"
                  :options="opcoesModelo"
                  label="Modelo"
                  class="flex-1"
                />
                <button
                  v-if="tipo === 'volume' && podeGerenciar"
                  type="button"
                  class="h-11 w-11 shrink-0 flex items-center justify-center rounded-lg border border-zinc-200 text-zinc-500 hover:text-brand-primary hover:border-brand-primary cursor-pointer"
                  title="Criar e editar modelos de envio da loja"
                  @click="abrirModelos(null)"
                >
                  <Settings2 :size="18" />
                </button>
                <button
                  type="button"
                  class="h-11 w-11 shrink-0 flex items-center justify-center rounded-lg border border-zinc-200 text-zinc-500 hover:text-brand-primary hover:border-brand-primary cursor-pointer"
                  title="Calibrar a impressão neste computador"
                  @click="isCalibracaoOpen = true"
                >
                  <Ruler :size="18" />
                </button>
              </div>
              <div class="flex flex-wrap items-center justify-between gap-2">
                <p class="text-xs text-zinc-500">
                  {{
                    tipo === 'danfe'
                      ? 'Layout fixo da NT 2020.004 — só o papel muda.'
                      : modelo.descricao || 'Modelo de volume'
                  }}
                </p>
                <button
                  v-if="tipo === 'volume' && podeGerenciar"
                  type="button"
                  class="flex items-center gap-1 text-xs font-semibold text-brand-primary hover:underline cursor-pointer"
                  @click="abrirModelos(modelo)"
                >
                  <MousePointer2 :size="13" />
                  Editar layout
                </button>
              </div>
            </div>

            <div
              class="flex flex-col items-center gap-2 rounded-xl bg-zinc-50 border border-zinc-100 p-4"
            >
              <EtiquetaPreview
                :definicao="modelo.definicao"
                :valores="valoresPreview"
                :largura-max-px="300"
                :altura-max-px="380"
              />
              <span class="text-[11px] text-zinc-400">
                {{
                  dados ? 'Primeira etiqueta' : 'Exemplo — escolha uma OS, venda ou envio avulso'
                }}
              </span>
            </div>

            <BaseInput
              v-if="ehFolha"
              v-model.number="pular"
              type="number"
              :min="0"
              :max="porPagina - 1"
              label="Pular posições na primeira folha"
            />

            <div
              v-if="avisos.length"
              class="flex items-start gap-2 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900"
            >
              <AlertTriangle :size="15" class="shrink-0 mt-0.5" />
              <ul class="space-y-1">
                <li v-for="a in avisos" :key="a">{{ a }}</li>
              </ul>
            </div>
          </div>

          <div class="flex gap-2 px-6 py-4 border-t border-zinc-100 shrink-0">
            <BaseButton
              variant="ghost"
              class="flex items-center justify-center gap-2 flex-1"
              @click="imprimirTeste()"
            >
              <Ruler :size="16" />
              Imprimir teste
            </BaseButton>
            <BaseButton
              variant="primary"
              class="flex items-center justify-center gap-2 flex-2"
              :disabled="!dados"
              @click="imprimirEnvio"
            >
              <Printer :size="16" />
              Imprimir {{ dados ? etiquetas.length : '' }}
              {{ etiquetas.length === 1 ? 'etiqueta' : 'etiquetas' }}
            </BaseButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <ModelosEtiquetaModal
    :is-open="isModelosOpen"
    :modelos="modelosDaLoja"
    :abrir-no-editor="modeloParaEditor"
    fonte="volume"
    @close="isModelosOpen = false"
    @salvo="chaveModelo = $event"
  />

  <CalibracaoEtiquetaModal
    :is-open="isCalibracaoOpen"
    @close="isCalibracaoOpen = false"
    @testar="(x, y) => imprimirTeste({ deslocamentoX: x, deslocamentoY: y })"
  />

  <EtiquetasImpressao v-if="trabalho" v-bind="trabalho" />
</template>

<style scoped>
.panel-enter-active,
.panel-leave-active {
  transition: opacity 0.2s ease;
}
.panel-enter-from,
.panel-leave-to {
  opacity: 0;
}
.panel-enter-active > div:last-child,
.panel-leave-active > div:last-child {
  transition: transform 0.25s ease;
}
.panel-enter-from > div:last-child,
.panel-leave-to > div:last-child {
  transform: translateX(100%);
}
.tipo {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #71717a;
  cursor: pointer;
}
.tipo:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.tipo--ativo {
  background: #fff;
  color: var(--color-brand-primary);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}
</style>
