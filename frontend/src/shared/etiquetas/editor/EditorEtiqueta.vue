<script setup lang="ts">
/**
 * @fileoverview Editor visual de etiqueta (plano §5.5, fase 3).
 *
 * O desenho do canvas é o MESMO `EtiquetaView` da impressão, ampliado; por
 * cima dele ficam só as alças de seleção. Não existe um segundo renderizador
 * que possa divergir do papel.
 *
 * Mouse: arrastar move, a alça do canto redimensiona, Alt solta o ímã de
 * 0,5 mm. Teclado (com o canvas focado): setas movem 0,5 mm (Shift: 0,1 mm),
 * Delete apaga, Ctrl+D duplica, Ctrl+Z / Ctrl+Y desfazem e refazem.
 */
import { computed, ref, watch } from 'vue';
import { Plus, Undo2, Redo2, Copy, Trash2, ZoomIn, ZoomOut, Maximize, Shrink, ChevronUp, ChevronDown } from 'lucide-vue-next';

import EtiquetaView from '../components/EtiquetaView.vue';
import PropriedadesElemento from './PropriedadesElemento.vue';
import {
  NOVOS_ELEMENTOS,
  PASSO_FINO_MM,
  PASSO_MM,
  encaixar,
  mover,
  novoElemento,
  redimensionar,
  saiDaEtiqueta,
  type TipoNovoElemento,
} from './operacoes';
import { useHistorico } from './useHistorico';
import type { ElementoEtiqueta, PaginaEtiqueta } from '../modelo';
import type { ValoresEtiqueta } from '../campos';

const PX_POR_MM = 96 / 25.4;
const LARGURA_UTIL_PX = 560;
const ALTURA_UTIL_PX = 340;
// Alça mínima clicável: uma linha de 0,3 mm não dá para pegar com o mouse.
const ALVO_MINIMO_PX = 10;

const props = defineProps<{
  pagina: PaginaEtiqueta;
  valores: ValoresEtiqueta;
}>();

const elementos = defineModel<ElementoEtiqueta[]>('elementos', { required: true });

// Cópia local, sempre em dia. Com v-model, o valor escrito só VOLTA pelo prop
// no próximo ciclo: lendo o prop logo depois de escrever, o histórico
// fotografava o estado anterior e o Ctrl+Z desfazia o passo errado.
const local = ref<ElementoEtiqueta[]>(elementos.value);
watch(elementos, (valor) => (local.value = valor));
const lista = computed<ElementoEtiqueta[]>({
  get: () => local.value,
  set: (valor) => {
    local.value = valor;
    elementos.value = valor;
  },
});

const selecionado = ref<number | null>(null);
const menuAberto = ref(false);
const canvas = ref<HTMLElement | null>(null);

const historico = useHistorico(lista);

// --- Zoom ---

const escalaAjustada = computed(() =>
  Math.min(LARGURA_UTIL_PX / (props.pagina.largura_mm * PX_POR_MM), ALTURA_UTIL_PX / (props.pagina.altura_mm * PX_POR_MM), 8),
);
const zoom = ref(1);
const escala = computed(() => escalaAjustada.value * zoom.value);
const pxPorMm = computed(() => PX_POR_MM * escala.value);

function ajustarZoom(fator: number) {
  zoom.value = Math.max(0.5, Math.min(4, zoom.value * fator));
}

// --- Alterações ---

const elementoSelecionado = computed(() =>
  selecionado.value === null ? null : (lista.value[selecionado.value] ?? null),
);

function substituir(indice: number, novo: ElementoEtiqueta) {
  lista.value = lista.value.map((el, i) => (i === indice ? novo : el));
}

function adicionar(tipo: TipoNovoElemento) {
  lista.value = [...lista.value, novoElemento(tipo, props.pagina)];
  selecionado.value = lista.value.length - 1;
  menuAberto.value = false;
  historico.registrar();
  canvas.value?.focus();
}

function remover() {
  if (selecionado.value === null) return;
  const alvo = selecionado.value;
  lista.value = lista.value.filter((_, i) => i !== alvo);
  selecionado.value = null;
  historico.registrar();
}

function duplicar() {
  const el = elementoSelecionado.value;
  if (!el) return;
  const copia = mover(el, props.pagina, el.x + 1, el.y + 1);
  lista.value = [...lista.value, copia];
  selecionado.value = lista.value.length - 1;
  historico.registrar();
}

/** Muda a ordem de desenho: quem vem depois fica por cima. */
function reordenar(delta: -1 | 1) {
  const i = selecionado.value;
  if (i === null) return;
  const j = i + delta;
  if (j < 0 || j >= lista.value.length) return;
  const ordem = [...lista.value];
  [ordem[i], ordem[j]] = [ordem[j], ordem[i]];
  lista.value = ordem;
  selecionado.value = j;
  historico.registrar();
}

const algumFora = computed(() => lista.value.some((el) => saiDaEtiqueta(el, props.pagina)));

function trazerParaDentro() {
  lista.value = lista.value.map((el) => encaixar(el, props.pagina));
  historico.registrar();
}

function desfazer() {
  historico.desfazer();
  if (selecionado.value !== null && selecionado.value >= lista.value.length) selecionado.value = null;
}

function refazer() {
  historico.refazer();
  if (selecionado.value !== null && selecionado.value >= lista.value.length) selecionado.value = null;
}

// --- Arraste ---

interface Gesto {
  indice: number;
  modo: 'mover' | 'redimensionar';
  x0: number;
  y0: number;
  original: ElementoEtiqueta;
}
let gesto: Gesto | null = null;

function iniciar(evento: PointerEvent, indice: number, modo: Gesto['modo']) {
  if (evento.button !== 0) return;
  evento.preventDefault();
  selecionado.value = indice;
  canvas.value?.focus();
  (evento.currentTarget as HTMLElement).setPointerCapture?.(evento.pointerId);
  gesto = { indice, modo, x0: evento.clientX, y0: evento.clientY, original: lista.value[indice] };
}

function arrastar(evento: PointerEvent) {
  if (!gesto) return;
  const dx = (evento.clientX - gesto.x0) / pxPorMm.value;
  const dy = (evento.clientY - gesto.y0) / pxPorMm.value;
  const passo = evento.altKey ? PASSO_FINO_MM : PASSO_MM;
  const o = gesto.original;
  substituir(
    gesto.indice,
    gesto.modo === 'mover'
      ? mover(o, props.pagina, o.x + dx, o.y + dy, passo)
      : redimensionar(o, props.pagina, o.w + dx, o.h + dy, passo),
  );
}

function soltar() {
  if (!gesto) return;
  gesto = null;
  historico.registrar();
}

// --- Teclado ---

function teclado(evento: KeyboardEvent) {
  const ctrl = evento.ctrlKey || evento.metaKey;
  const tecla = evento.key.toLowerCase();

  if (ctrl && tecla === 'z' && !evento.shiftKey) return prevenir(evento, desfazer);
  if (ctrl && (tecla === 'y' || (tecla === 'z' && evento.shiftKey))) return prevenir(evento, refazer);
  if (ctrl && tecla === 'd') return prevenir(evento, duplicar);
  if (evento.key === 'Delete' || evento.key === 'Backspace') return prevenir(evento, remover);
  if (evento.key === 'Escape') return (selecionado.value = null);

  const setas: Record<string, [number, number]> = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
  const direcao = setas[evento.key];
  const el = elementoSelecionado.value;
  if (!direcao || !el || selecionado.value === null) return;
  evento.preventDefault();
  const passo = evento.shiftKey ? PASSO_FINO_MM : PASSO_MM;
  substituir(selecionado.value, mover(el, props.pagina, el.x + direcao[0] * passo, el.y + direcao[1] * passo, passo));
  historico.registrar();
}

function prevenir(evento: KeyboardEvent, acao: () => void) {
  evento.preventDefault();
  acao();
}

// --- Desenho das alças ---

function estiloAlca(el: ElementoEtiqueta) {
  const k = pxPorMm.value;
  const largura = el.w * k;
  const altura = el.h * k;
  const extraX = Math.max(0, ALVO_MINIMO_PX - largura) / 2;
  const extraY = Math.max(0, ALVO_MINIMO_PX - altura) / 2;
  return {
    left: `${el.x * k - extraX}px`,
    top: `${el.y * k - extraY}px`,
    width: `${largura + extraX * 2}px`,
    height: `${altura + extraY * 2}px`,
  };
}

const estiloGrade = computed(() => {
  const passo = pxPorMm.value * 5;
  return {
    backgroundSize: `${passo}px ${passo}px`,
    backgroundImage:
      'linear-gradient(to right, rgba(4,92,161,0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(4,92,161,0.08) 1px, transparent 1px)',
  };
});

const definicaoCanvas = computed(() => ({ pagina: props.pagina, elementos: lista.value }));

defineExpose({ reiniciarHistorico: historico.reiniciar });
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
    <div class="lg:col-span-2 space-y-3 min-w-0">
      <!-- Barra de ferramentas -->
      <div class="flex flex-wrap items-center gap-1.5">
        <div class="relative">
          <button type="button" class="ferramenta ferramenta--primaria" @click="menuAberto = !menuAberto">
            <Plus :size="15" />
            Adicionar
          </button>
          <div
            v-if="menuAberto"
            class="absolute left-0 top-full mt-1 z-10 w-48 py-1 bg-white border border-zinc-200 rounded-xl shadow-lg"
          >
            <button
              v-for="n in NOVOS_ELEMENTOS"
              :key="n.tipo"
              type="button"
              class="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 cursor-pointer"
              @click="adicionar(n.tipo)"
            >
              {{ n.rotulo }}
            </button>
          </div>
        </div>

        <span class="w-px h-6 bg-zinc-200 mx-1" />
        <button type="button" class="ferramenta" title="Desfazer (Ctrl+Z)" :disabled="!historico.podeDesfazer.value" @click="desfazer">
          <Undo2 :size="15" />
        </button>
        <button type="button" class="ferramenta" title="Refazer (Ctrl+Y)" :disabled="!historico.podeRefazer.value" @click="refazer">
          <Redo2 :size="15" />
        </button>
        <span class="w-px h-6 bg-zinc-200 mx-1" />
        <button type="button" class="ferramenta" title="Duplicar (Ctrl+D)" :disabled="!elementoSelecionado" @click="duplicar">
          <Copy :size="15" />
        </button>
        <button type="button" class="ferramenta" title="Trazer para frente" :disabled="!elementoSelecionado" @click="reordenar(1)">
          <ChevronUp :size="15" />
        </button>
        <button type="button" class="ferramenta" title="Mandar para trás" :disabled="!elementoSelecionado" @click="reordenar(-1)">
          <ChevronDown :size="15" />
        </button>
        <button type="button" class="ferramenta ferramenta--perigo" title="Apagar (Delete)" :disabled="!elementoSelecionado" @click="remover">
          <Trash2 :size="15" />
        </button>

        <div class="ml-auto flex items-center gap-1.5">
          <button type="button" class="ferramenta" title="Diminuir zoom" @click="ajustarZoom(1 / 1.25)">
            <ZoomOut :size="15" />
          </button>
          <span class="text-xs text-zinc-500 w-10 text-center">{{ Math.round(zoom * 100) }}%</span>
          <button type="button" class="ferramenta" title="Aumentar zoom" @click="ajustarZoom(1.25)">
            <ZoomIn :size="15" />
          </button>
          <button type="button" class="ferramenta" title="Ajustar à tela" @click="zoom = 1">
            <Maximize :size="15" />
          </button>
        </div>
      </div>

      <!-- Canvas -->
      <div class="overflow-auto rounded-xl bg-zinc-100 border border-zinc-200 p-6 max-h-105" @click.self="selecionado = null">
        <div
          ref="canvas"
          tabindex="0"
          class="relative mx-auto bg-white shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/40"
          :style="{
            width: `${pagina.largura_mm * pxPorMm}px`,
            height: `${pagina.altura_mm * pxPorMm}px`,
          }"
          @pointerdown.self="selecionado = null"
          @pointermove="arrastar"
          @pointerup="soltar"
          @pointercancel="soltar"
          @keydown="teclado"
        >
          <div class="absolute left-0 top-0 origin-top-left pointer-events-none" :style="{ transform: `scale(${escala})` }">
            <EtiquetaView :definicao="definicaoCanvas" :valores="valores" />
          </div>
          <div class="absolute inset-0 pointer-events-none" :style="estiloGrade" />

          <div
            v-for="(el, i) in lista"
            :key="i"
            class="alca"
            :class="{ 'alca--selecionada': selecionado === i, 'alca--fora': saiDaEtiqueta(el, pagina) }"
            :style="estiloAlca(el)"
            @pointerdown="iniciar($event, i, 'mover')"
          >
            <span class="alca-numero">{{ i + 1 }}</span>
            <span
              v-if="selecionado === i"
              class="alca-canto"
              title="Arraste para redimensionar"
              @pointerdown.stop="iniciar($event, i, 'redimensionar')"
            />
          </div>
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-2 text-[11px] text-zinc-400">
        <span>Arraste para mover · canto para redimensionar · Alt solta o ímã · setas movem 0,5 mm</span>
        <button
          v-if="algumFora"
          type="button"
          class="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-semibold text-amber-800 bg-amber-50 border border-amber-200 cursor-pointer"
          @click="trazerParaDentro"
        >
          <Shrink :size="13" />
          Trazer tudo para dentro
        </button>
      </div>
    </div>

    <!-- Propriedades -->
    <div class="rounded-xl border border-zinc-100 bg-zinc-50/60 p-4 min-w-0">
      <PropriedadesElemento
        v-if="elementoSelecionado && selecionado !== null"
        :elemento="elementoSelecionado"
        :numero="selecionado + 1"
        :pagina="pagina"
        @atualizar="substituir(selecionado!, $event)"
        @concluir="historico.registrar()"
      />
      <div v-else class="h-full flex flex-col items-center justify-center text-center gap-2 py-8 text-sm text-zinc-400">
        <p>Clique num elemento da etiqueta para editar.</p>
        <p class="text-xs">{{ lista.length }} {{ lista.length === 1 ? 'elemento' : 'elementos' }} na etiqueta</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ferramenta {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  height: 2rem;
  padding: 0 0.5rem;
  border: 1px solid #e4e4e7;
  border-radius: 0.5rem;
  background: #fff;
  color: #52525b;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
}
.ferramenta:hover:not(:disabled) {
  color: var(--color-brand-primary);
  border-color: var(--color-brand-primary);
}
.ferramenta:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.ferramenta--primaria {
  background: var(--color-brand-primary);
  border-color: var(--color-brand-primary);
  color: #fff;
}
.ferramenta--primaria:hover:not(:disabled) {
  color: #fff;
  background: var(--color-brand-primary-hover);
}
.ferramenta--perigo:hover:not(:disabled) {
  color: #dc2626;
  border-color: #dc2626;
}

.alca {
  position: absolute;
  box-sizing: border-box;
  border: 1px dashed transparent;
  cursor: move;
  touch-action: none;
}
.alca:hover {
  border-color: rgba(4, 92, 161, 0.5);
}
.alca--selecionada,
.alca--selecionada:hover {
  border: 1.5px solid var(--color-brand-primary);
  background: rgba(4, 92, 161, 0.05);
}
.alca--fora {
  border: 1.5px dashed #d97706;
}
.alca-numero {
  position: absolute;
  top: -0.9rem;
  left: -1px;
  padding: 0 0.25rem;
  font-size: 0.625rem;
  font-weight: 700;
  line-height: 0.9rem;
  color: #fff;
  background: var(--color-brand-primary);
  border-radius: 0.25rem 0.25rem 0 0;
  opacity: 0;
  pointer-events: none;
}
.alca:hover .alca-numero,
.alca--selecionada .alca-numero {
  opacity: 1;
}
.alca-canto {
  position: absolute;
  right: -5px;
  bottom: -5px;
  width: 10px;
  height: 10px;
  background: #fff;
  border: 1.5px solid var(--color-brand-primary);
  border-radius: 2px;
  cursor: nwse-resize;
}
</style>
