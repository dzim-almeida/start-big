<script setup lang="ts">
/**
 * @fileoverview Propriedades do elemento selecionado no editor.
 *
 * Emite `atualizar` a cada tecla (o canvas acompanha ao vivo) e `concluir`
 * quando o campo perde o foco ou muda de verdade — é aí que o desfazer
 * fotografa, e não a cada dígito.
 */
import { computed } from 'vue';
import { Wand2 } from 'lucide-vue-next';

import type { CampoEtiqueta, OpcaoCampo } from '../campos';
import { fontePara } from '../layoutAuto';
import { mover, redimensionar, PASSO_FINO_MM } from './operacoes';
import type { ElementoEtiqueta, ElementoTexto, PaginaEtiqueta } from '../modelo';
import type { SimbologiaPreferida } from '../codigoBarras';

const props = defineProps<{
  elemento: ElementoEtiqueta;
  numero: number;
  pagina: PaginaEtiqueta;
  /** Dados que a fonte do modelo oferece (produto ou envio). */
  campos: OpcaoCampo[];
  camposCodigo: OpcaoCampo[];
}>();

const emit = defineEmits<{
  atualizar: [elemento: ElementoEtiqueta];
  concluir: [];
}>();

const TITULO: Record<ElementoEtiqueta['tipo'], string> = {
  texto: 'Texto',
  barras: 'Código de barras',
  qr: 'QR Code',
  linha: 'Linha',
  caixa: 'Moldura',
};

const SIMBOLOGIAS: { valor: SimbologiaPreferida; rotulo: string }[] = [
  { valor: 'auto', rotulo: 'Automático (pelo código)' },
  { valor: 'EAN13', rotulo: 'EAN-13' },
  { valor: 'EAN8', rotulo: 'EAN-8' },
  { valor: 'UPC', rotulo: 'UPC-A' },
  { valor: 'ITF14', rotulo: 'ITF-14 (caixa/fardo)' },
  { valor: 'CODE128', rotulo: 'Code 128 (qualquer texto)' },
];

const el = computed(() => props.elemento);
const texto = computed(() => (el.value.tipo === 'texto' ? el.value : null));

function num(evento: Event): number {
  const n = Number((evento.target as HTMLInputElement).value.replace(',', '.'));
  return Number.isFinite(n) ? n : 0;
}

function valor(evento: Event): string {
  return (evento.target as HTMLInputElement | HTMLSelectElement).value;
}

function atualizar(mudanca: Partial<ElementoEtiqueta>) {
  emit('atualizar', { ...el.value, ...mudanca } as ElementoEtiqueta);
}

function posicao(eixo: 'x' | 'y', evento: Event) {
  const x = eixo === 'x' ? num(evento) : el.value.x;
  const y = eixo === 'y' ? num(evento) : el.value.y;
  emit('atualizar', mover(el.value, props.pagina, x, y, PASSO_FINO_MM));
}

function tamanho(eixo: 'w' | 'h', evento: Event) {
  const w = eixo === 'w' ? num(evento) : el.value.w;
  const h = eixo === 'h' ? num(evento) : el.value.h;
  emit('atualizar', redimensionar(el.value, props.pagina, w, h, PASSO_FINO_MM));
}

// "Dado" ou "texto fixo": o mesmo elemento de texto, com ou sem campo.
function conteudo(evento: Event) {
  const escolha = valor(evento);
  const atual = texto.value!;
  if (escolha === 'fixo') {
    atualizar({ campo: undefined, texto: atual.texto || 'Texto' } as Partial<ElementoTexto>);
  } else {
    atualizar({ campo: escolha as CampoEtiqueta, texto: atual.campo ? atual.texto : '' } as Partial<ElementoTexto>);
  }
  emit('concluir');
}

function ajustarFonte() {
  const t = texto.value!;
  atualizar({ fonte_pt: fontePara(t.h, t.linhas_max ?? 1) } as Partial<ElementoTexto>);
  emit('concluir');
}
</script>

<template>
  <div class="space-y-4 text-sm">
    <div class="flex items-center gap-2">
      <span class="w-6 h-6 rounded-md bg-brand-primary text-white text-xs font-bold flex items-center justify-center">
        {{ numero }}
      </span>
      <h4 class="font-semibold text-zinc-800">{{ TITULO[el.tipo] }}</h4>
    </div>

    <!-- Posição e tamanho -->
    <div class="grid grid-cols-2 gap-2">
      <label class="campo">
        <span>X (mm)</span>
        <input type="number" step="0.1" :value="el.x" @input="posicao('x', $event)" @change="emit('concluir')" />
      </label>
      <label class="campo">
        <span>Y (mm)</span>
        <input type="number" step="0.1" :value="el.y" @input="posicao('y', $event)" @change="emit('concluir')" />
      </label>
      <label v-if="!(el.tipo === 'caixa' && el.w === 0)" class="campo">
        <span>Largura (mm)</span>
        <input type="number" step="0.1" :value="el.w" @input="tamanho('w', $event)" @change="emit('concluir')" />
      </label>
      <label v-if="el.tipo !== 'linha'" class="campo">
        <span>Altura (mm)</span>
        <input type="number" step="0.1" :value="el.h" @input="tamanho('h', $event)" @change="emit('concluir')" />
      </label>
    </div>

    <!-- Texto -->
    <template v-if="texto">
      <label class="campo">
        <span>Conteúdo</span>
        <select :value="texto.campo ?? 'fixo'" @change="conteudo">
          <option v-for="c in campos" :key="c.campo" :value="c.campo">{{ c.rotulo }}</option>
          <option value="fixo">Texto fixo</option>
        </select>
      </label>
      <label class="campo">
        <span>{{ texto.campo ? 'Texto antes do dado (opcional)' : 'Texto' }}</span>
        <input
          type="text"
          :value="texto.texto ?? ''"
          :placeholder="texto.campo ? 'Ex: Cód. ' : ''"
          @input="atualizar({ texto: valor($event) } as Partial<ElementoTexto>)"
          @change="emit('concluir')"
        />
      </label>
      <div class="grid grid-cols-2 gap-2">
        <label class="campo">
          <span>Fonte (pt)</span>
          <div class="flex gap-1">
            <input
              type="number"
              step="0.5"
              min="4"
              max="72"
              :value="texto.fonte_pt"
              @input="atualizar({ fonte_pt: Math.max(4, Math.min(72, num($event))) } as Partial<ElementoTexto>)"
              @change="emit('concluir')"
            />
            <button type="button" class="botao-icone" title="Maior fonte que cabe na caixa" @click="ajustarFonte">
              <Wand2 :size="14" />
            </button>
          </div>
        </label>
        <label class="campo">
          <span>Linhas</span>
          <input
            type="number"
            min="1"
            max="6"
            :value="texto.linhas_max ?? 1"
            @input="atualizar({ linhas_max: Math.max(1, Math.min(6, Math.round(num($event)))) } as Partial<ElementoTexto>)"
            @change="emit('concluir')"
          />
        </label>
        <label class="campo">
          <span>Alinhamento</span>
          <select
            :value="texto.alinhamento ?? 'esquerda'"
            @change="atualizar({ alinhamento: valor($event) } as Partial<ElementoTexto>); emit('concluir')"
          >
            <option value="esquerda">Esquerda</option>
            <option value="centro">Centro</option>
            <option value="direita">Direita</option>
          </select>
        </label>
        <label class="flex items-center gap-2 mt-5 text-xs text-zinc-600 cursor-pointer select-none">
          <input
            type="checkbox"
            class="accent-brand-primary"
            :checked="!!texto.negrito"
            @change="atualizar({ negrito: ($event.target as HTMLInputElement).checked } as Partial<ElementoTexto>); emit('concluir')"
          />
          Negrito
        </label>
      </div>
    </template>

    <!-- Código de barras -->
    <template v-else-if="el.tipo === 'barras'">
      <label class="campo">
        <span>Código impresso</span>
        <select :value="el.campo" @change="atualizar({ campo: valor($event) as CampoEtiqueta }); emit('concluir')">
          <option v-for="c in camposCodigo" :key="c.campo" :value="c.campo">{{ c.rotulo }}</option>
        </select>
      </label>
      <label class="campo">
        <span>Tipo de código</span>
        <select
          :value="el.simbologia"
          @change="atualizar({ simbologia: valor($event) as SimbologiaPreferida }); emit('concluir')"
        >
          <option v-for="s in SIMBOLOGIAS" :key="s.valor" :value="s.valor">{{ s.rotulo }}</option>
        </select>
      </label>
      <label class="flex items-center gap-2 text-xs text-zinc-600 cursor-pointer select-none">
        <input
          type="checkbox"
          class="accent-brand-primary"
          :checked="el.legenda"
          @change="atualizar({ legenda: ($event.target as HTMLInputElement).checked }); emit('concluir')"
        />
        Mostrar o número embaixo das barras
      </label>
      <p class="text-[11px] text-zinc-400">
        Um código que não bate com o tipo escolhido sai em Code 128 — nunca um EAN errado.
      </p>
    </template>

    <!-- QR -->
    <label v-else-if="el.tipo === 'qr'" class="campo">
      <span>Conteúdo do QR</span>
      <select :value="el.campo" @change="atualizar({ campo: valor($event) as CampoEtiqueta }); emit('concluir')">
        <option v-for="c in campos" :key="c.campo" :value="c.campo">{{ c.rotulo }}</option>
      </select>
    </label>

    <!-- Linha e moldura -->
    <label v-else-if="el.tipo === 'linha' || el.tipo === 'caixa'" class="campo">
      <span>Espessura (mm)</span>
      <input
        type="number"
        step="0.1"
        min="0.1"
        max="3"
        :value="el.espessura_mm"
        @input="atualizar({ espessura_mm: Math.max(0.1, Math.min(3, num($event))) })"
        @change="emit('concluir')"
      />
    </label>
  </div>
</template>

<style scoped>
.campo {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}
.campo > span {
  font-size: 0.6875rem;
  font-weight: 600;
  color: #71717a;
}
.campo input,
.campo select {
  width: 100%;
  min-width: 0;
  padding: 0.375rem 0.5rem;
  font-size: 0.8125rem;
  border: 1px solid #e4e4e7;
  border-radius: 0.5rem;
  background: #fff;
  outline: none;
}
.campo input:focus,
.campo select:focus {
  border-color: var(--color-brand-primary, #0b5cab);
}
.botao-icone {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  border: 1px solid #e4e4e7;
  border-radius: 0.5rem;
  color: #71717a;
  cursor: pointer;
}
.botao-icone:hover {
  color: var(--color-brand-primary, #0b5cab);
  border-color: var(--color-brand-primary, #0b5cab);
}
</style>
