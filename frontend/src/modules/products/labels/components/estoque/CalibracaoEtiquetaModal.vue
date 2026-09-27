<script setup lang="ts">
/**
 * @fileoverview Impressora de etiquetas DESTE terminal: por onde sai (driver
 * do Windows ou direto na linguagem da térmica), qual impressora, e o ajuste
 * fino de posição.
 *
 * Tudo fica no `impressao.store` (localStorage, por máquina), e não no modelo,
 * que é da loja: cada computador tem a sua impressora, e cada impressora puxa
 * o papel com a sua folga.
 *
 * O "Imprimir teste" usa o que está NA TELA, antes de salvar — é assim que se
 * descobre, na frente da impressora, qual linguagem ela fala.
 */
import { computed, ref, watch } from 'vue';
import { Ruler, RefreshCw } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import { useImpressaoStore, type ConfigImpressao } from '@/shared/stores/impressao.store';
import { useToast } from '@/shared/composables/useToast';
import { impressaoDisponivel, listarImpressoras, type ImpressoraInfo } from '@/shared/services/impressao.service';

const LIMITE_MM = 20;

const props = defineProps<{ isOpen: boolean }>();

const emit = defineEmits<{
  close: [];
  /** Imprime a página de teste com a configuração em edição (ainda não salva). */
  testar: [config: ConfigImpressao];
}>();

const impressaoStore = useImpressaoStore();
const toast = useToast();
const noAplicativo = impressaoDisponivel();

const form = ref<ConfigImpressao>({ ...impressaoStore.config });
const impressoras = ref<ImpressoraInfo[]>([]);
const carregandoImpressoras = ref(false);

async function carregarImpressoras() {
  if (!noAplicativo) return;
  carregandoImpressoras.value = true;
  try {
    impressoras.value = await listarImpressoras();
  } catch {
    impressoras.value = [];
  } finally {
    carregandoImpressoras.value = false;
  }
}

watch(
  () => props.isOpen,
  (aberto) => {
    if (!aberto) return;
    form.value = { ...impressaoStore.config };
    carregarImpressoras();
  },
);

const opcoesSaida = [
  { value: 'driver', label: 'Pelo Windows (abre o diálogo de impressão)' },
  { value: 'zpl', label: 'Direto — ZPL (Zebra, Elgin, a maioria das térmicas)' },
  { value: 'tspl', label: 'Direto — TSPL (TSC, Elgin, várias nacionais e chinesas)' },
  { value: 'epl', label: 'Direto — EPL / PPLB (Zebra antigas, Argox em PPLB)' },
];
const opcoesConexao = [
  { value: 'windows', label: 'Instalada neste computador (USB)' },
  { value: 'rede', label: 'Na rede (IP)' },
];
const opcoesDpi = [
  { value: 203, label: '203 dpi (8 pontos/mm) — a mais comum' },
  { value: 300, label: '300 dpi (12 pontos/mm)' },
];
const opcoesEscuridao = [
  { value: -1, label: 'Padrão da impressora' },
  ...Array.from({ length: 16 }, (_, i) => ({ value: i, label: String(i) })),
];

const direto = computed(() => form.value.etiqueta_saida !== 'driver');
const opcoesImpressora = computed(() =>
  impressoras.value.map((i) => ({ value: i.nome, label: i.padrao ? `${i.nome} (padrão)` : i.nome })),
);

const impressora = computed({
  get: () => form.value.etiqueta_impressora ?? '',
  set: (valor: string | number) => (form.value.etiqueta_impressora = valor ? String(valor) : null),
});

// O select não aceita null: -1 representa "padrão da impressora".
const escuridao = computed({
  get: () => form.value.etiqueta_escuridao ?? -1,
  set: (valor: string | number) => (form.value.etiqueta_escuridao = Number(valor) < 0 ? null : Number(valor)),
});

function limitar(valor: unknown, min: number, max: number, padrao = 0): number {
  const n = Number(valor);
  if (!Number.isFinite(n)) return padrao;
  return Math.max(min, Math.min(max, n));
}

/** A configuração em edição, com os números saneados. */
function rascunho(): ConfigImpressao {
  const f = form.value;
  return {
    ...f,
    etiqueta_dpi: Number(f.etiqueta_dpi) === 300 ? 300 : 203,
    etiqueta_porta: limitar(f.etiqueta_porta, 1, 65535, 9100),
    etiqueta_gap_mm: limitar(f.etiqueta_gap_mm, 0, 20, 2),
    etiqueta_deslocamento_x_mm: limitar(f.etiqueta_deslocamento_x_mm, -LIMITE_MM, LIMITE_MM),
    etiqueta_deslocamento_y_mm: limitar(f.etiqueta_deslocamento_y_mm, -LIMITE_MM, LIMITE_MM),
  };
}

function salvar() {
  impressaoStore.salvar(rascunho());
  toast.success('Impressora de etiquetas salva', 'Vale só para este computador.');
  emit('close');
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Impressora de etiquetas"
    subtitle="Configuração deste computador — não muda os modelos da loja"
    size="lg"
    @close="emit('close')"
  >
    <div class="space-y-6">
      <!-- Saída -->
      <section class="space-y-3">
        <h4 class="text-xs font-bold uppercase tracking-wider text-zinc-500">Como imprimir</h4>
        <BaseSelect v-model="form.etiqueta_saida" :options="opcoesSaida" label="Saída" />
        <p v-if="!direto" class="text-xs text-zinc-500">
          Funciona com qualquer impressora que tenha driver no Windows. Cada impressão abre o diálogo.
        </p>
        <p v-else-if="!noAplicativo" class="text-xs text-amber-700">
          A impressão direta só funciona no aplicativo instalado. Aqui (navegador) as etiquetas seguem pelo diálogo.
        </p>
        <p v-else class="text-xs text-zinc-500">
          Sai sem diálogo, direto na térmica. Não sabe a linguagem? Imprima o teste em
          <strong>ZPL</strong>; se sair em branco ou em código, tente <strong>TSPL</strong> e depois <strong>EPL</strong>.
          Folhas A4/Carta continuam pelo diálogo.
        </p>
      </section>

      <!-- Impressora (só na saída direta) -->
      <section v-if="direto" class="space-y-3">
        <h4 class="text-xs font-bold uppercase tracking-wider text-zinc-500">Impressora</h4>
        <BaseSelect v-model="form.etiqueta_conexao" :options="opcoesConexao" label="Onde ela está" />
        <div v-if="form.etiqueta_conexao === 'windows'" class="flex items-end gap-2">
          <BaseSelect
            v-model="impressora"
            :options="opcoesImpressora"
            label="Impressora"
            placeholder="Escolha a térmica de etiquetas"
            empty-message="Nenhuma impressora encontrada no Windows"
            class="flex-1"
          />
          <button
            type="button"
            class="h-11 w-11 shrink-0 flex items-center justify-center rounded-lg border border-zinc-200 text-zinc-500 hover:text-brand-primary hover:border-brand-primary cursor-pointer"
            title="Procurar de novo"
            @click="carregarImpressoras"
          >
            <RefreshCw :size="16" :class="carregandoImpressoras && 'animate-spin'" />
          </button>
        </div>
        <div v-else class="grid grid-cols-3 gap-4">
          <BaseInput v-model="form.etiqueta_ip" class="col-span-2" label="IP" placeholder="192.168.0.50" />
          <BaseInput v-model.number="form.etiqueta_porta" type="number" label="Porta" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <BaseSelect v-model="form.etiqueta_dpi" :options="opcoesDpi" label="Resolução" />
          <BaseInput
            v-model.number="form.etiqueta_gap_mm"
            type="number"
            step="0.5"
            label="Espaço entre etiquetas (mm)"
            ajuda="O vão do rolo entre uma etiqueta e outra. Costuma ser 2 ou 3 mm."
          />
          <BaseSelect v-model="escuridao" :options="opcoesEscuridao" label="Escuridão" />
        </div>
        <div class="flex flex-col gap-2">
          <BaseCheckbox v-model="form.etiqueta_girar_180" label="Girar 180° (a etiqueta sai de cabeça para baixo)" />
          <BaseCheckbox v-model="form.etiqueta_inverter" label="Inverter cores (o teste saiu com o fundo preto)" />
        </div>
      </section>

      <!-- Ajuste fino -->
      <section class="space-y-3">
        <h4 class="text-xs font-bold uppercase tracking-wider text-zinc-500">Ajuste fino da posição</h4>
        <p class="text-xs text-zinc-500">
          Imprima o teste: ele desenha o contorno da etiqueta e uma cruz no centro. Se sair deslocado, meça com a régua
          e informe abaixo.
        </p>
        <div class="grid grid-cols-2 gap-4">
          <BaseInput
            v-model.number="form.etiqueta_deslocamento_x_mm"
            type="number"
            step="0.5"
            :min="-LIMITE_MM"
            :max="LIMITE_MM"
            label="Horizontal (mm)"
            ajuda="Positivo empurra para a direita; negativo, para a esquerda."
          />
          <BaseInput
            v-model.number="form.etiqueta_deslocamento_y_mm"
            type="number"
            step="0.5"
            :min="-LIMITE_MM"
            :max="LIMITE_MM"
            label="Vertical (mm)"
            ajuda="Positivo empurra para baixo; negativo, para cima."
          />
        </div>
        <p v-if="!direto" class="text-xs text-zinc-500">
          Etiqueta cortada ou fora de escala pelo Windows costuma ser o <strong>papel no driver</strong>: ele precisa ter
          o tamanho do rolo (ou a folha certa) e a opção de ajustar à página desligada.
        </p>
      </section>
    </div>

    <template #footer>
      <div class="flex justify-between gap-2">
        <BaseButton variant="ghost" class="flex items-center gap-2" @click="emit('testar', rascunho())">
          <Ruler :size="16" />
          Imprimir teste
        </BaseButton>
        <BaseButton @click="salvar">Salvar</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
