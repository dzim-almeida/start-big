<script setup lang="ts">
/**
 * @fileoverview Formulário de modelo de etiqueta: medidas do papel + o que imprimir.
 *
 * É a "configuração fácil" antes do editor visual (plano §9, fase 3): o
 * lojista mede o rolo ou a folha, marca os dados, e o layout automático
 * posiciona tudo. Mesmo roteiro de medidas do Tiny/Olist (largura, altura,
 * margem, espaço entre colunas, nº de colunas), com preview ao vivo.
 */
import { computed, reactive, watch } from 'vue';
import { AlertTriangle } from 'lucide-vue-next';

import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import EtiquetaPreview from '@/shared/etiquetas/components/EtiquetaPreview.vue';
import { PRESETS } from '@/shared/etiquetas/presets';
import { BLOCOS_AUTO, gerarElementos, type BlocoAuto } from '@/shared/etiquetas/layoutAuto';
import { problemasDaPagina, type DefinicaoEtiqueta, type PaginaEtiqueta } from '@/shared/etiquetas/modelo';
import { VALORES_EXEMPLO } from '@/shared/etiquetas/campos';
import type { ModeloEtiquetaPayload } from '../../types/etiquetas.types';

const props = defineProps<{
  /** Modelo em edição; nulo para criar. */
  inicial: { nome: string; definicao: DefinicaoEtiqueta } | null;
}>();

const FOLHAS = {
  A4: { largura_mm: 210, altura_mm: 297 },
  CARTA: { largura_mm: 215.9, altura_mm: 279.4 },
};

function copiarPagina(pagina: PaginaEtiqueta): PaginaEtiqueta {
  return { ...pagina, folha: pagina.folha ? { ...pagina.folha } : null };
}

const base = props.inicial?.definicao ?? PRESETS[1].definicao;

const form = reactive({
  nome: props.inicial?.nome ?? '',
  preset: '',
  pagina: copiarPagina(base.pagina),
  blocos: new Set<BlocoAuto>(base.layout_auto?.blocos ?? ['nome', 'preco_varejo', 'barras']),
});

const opcoesPreset = PRESETS.map((p) => ({ value: p.chave, label: p.nome }));
const opcoesTipo = [
  { value: 'bobina', label: 'Rolo (impressora térmica)' },
  { value: 'folha', label: 'Folha adesiva (impressora comum)' },
];
const opcoesFolha = [
  { value: 'A4', label: 'A4 (210 × 297 mm)' },
  { value: 'CARTA', label: 'Carta (215,9 × 279,4 mm)' },
];

watch(
  () => form.preset,
  (chave) => {
    const preset = PRESETS.find((p) => p.chave === chave);
    if (!preset) return;
    form.pagina = copiarPagina(preset.definicao.pagina);
    form.blocos = new Set(preset.definicao.layout_auto?.blocos ?? []);
    if (!form.nome.trim()) form.nome = preset.nome;
  },
);

watch(
  () => form.pagina.tipo,
  (tipo) => {
    if (tipo === 'folha' && !form.pagina.folha) form.pagina.folha = { ...FOLHAS.A4, linhas: 10 };
    if (tipo === 'bobina') form.pagina.folha = null;
  },
);

const papelFolha = computed({
  get: () => (form.pagina.folha?.largura_mm === FOLHAS.CARTA.largura_mm ? 'CARTA' : 'A4'),
  set: (valor: string) => {
    if (form.pagina.folha) Object.assign(form.pagina.folha, FOLHAS[valor as keyof typeof FOLHAS]);
  },
});

function alternarBloco(bloco: BlocoAuto, marcado: boolean) {
  const novos = new Set(form.blocos);
  if (marcado) novos.add(bloco);
  else novos.delete(bloco);
  form.blocos = novos;
}

// Campo apagado no meio da digitação chega como null — conta como zero.
function num(valor: unknown): number {
  const n = Number(valor);
  return Number.isFinite(n) ? n : 0;
}

const paginaNormalizada = computed<PaginaEtiqueta>(() => {
  const p = form.pagina;
  return {
    tipo: p.tipo,
    largura_mm: num(p.largura_mm),
    altura_mm: num(p.altura_mm),
    colunas: Math.max(1, Math.round(num(p.colunas))),
    espaco_colunas_mm: num(p.espaco_colunas_mm),
    espaco_linhas_mm: p.tipo === 'folha' ? num(p.espaco_linhas_mm) : 0,
    margem_esq_mm: num(p.margem_esq_mm),
    margem_topo_mm: p.tipo === 'folha' ? num(p.margem_topo_mm) : 0,
    folha: p.tipo === 'folha' && p.folha
      ? { largura_mm: p.folha.largura_mm, altura_mm: p.folha.altura_mm, linhas: Math.max(1, Math.round(num(p.folha.linhas))) }
      : null,
  };
});

const problemas = computed(() => {
  const lista = problemasDaPagina(paginaNormalizada.value);
  if (form.blocos.size === 0) lista.push('Marque pelo menos um dado para imprimir.');
  if (!form.nome.trim()) lista.push('Dê um nome ao modelo.');
  return lista;
});

const definicao = computed<DefinicaoEtiqueta>(() => {
  const opcoes = { blocos: BLOCOS_AUTO.map((b) => b.bloco).filter((b) => form.blocos.has(b)) };
  const pagina = paginaNormalizada.value;
  const valida = pagina.largura_mm >= 5 && pagina.altura_mm >= 5;
  return { pagina, elementos: valida ? gerarElementos(pagina, opcoes) : [], layout_auto: opcoes };
});

/** O payload, ou nulo se o formulário ainda tem problema. */
function payload(): ModeloEtiquetaPayload | null {
  if (problemas.value.length) return null;
  return { nome: form.nome.trim(), fonte: 'produto', definicao: definicao.value };
}

defineExpose({ payload, problemas });
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
    <div class="lg:col-span-3 space-y-5">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseInput v-model="form.nome" label="Nome do modelo" placeholder="Ex: Gôndola da loja" :required="true" />
        <BaseSelect
          v-model="form.preset"
          :options="opcoesPreset"
          label="Partir de um modelo pronto"
          placeholder="Escolha para copiar as medidas"
        />
      </div>

      <section class="space-y-3">
        <h4 class="text-xs font-bold uppercase tracking-wider text-zinc-500">Papel</h4>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <BaseSelect v-model="form.pagina.tipo" :options="opcoesTipo" label="Tipo" />
          <BaseSelect v-if="form.pagina.tipo === 'folha'" v-model="papelFolha" :options="opcoesFolha" label="Tamanho da folha" />
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <BaseInput v-model.number="form.pagina.largura_mm" type="number" step="0.1" label="Largura (mm)" />
          <BaseInput v-model.number="form.pagina.altura_mm" type="number" step="0.1" label="Altura (mm)" />
          <BaseInput v-model.number="form.pagina.colunas" type="number" min="1" max="10" label="Colunas" />
          <BaseInput
            v-if="form.pagina.folha"
            v-model.number="form.pagina.folha.linhas"
            type="number"
            min="1"
            label="Linhas"
          />
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <BaseInput
            v-model.number="form.pagina.margem_esq_mm"
            type="number"
            step="0.1"
            label="Margem lateral (mm)"
            ajuda="Da borda do papel até a primeira etiqueta."
          />
          <BaseInput
            v-model.number="form.pagina.espaco_colunas_mm"
            type="number"
            step="0.1"
            label="Entre colunas (mm)"
          />
          <template v-if="form.pagina.tipo === 'folha'">
            <BaseInput v-model.number="form.pagina.margem_topo_mm" type="number" step="0.1" label="Margem do topo (mm)" />
            <BaseInput v-model.number="form.pagina.espaco_linhas_mm" type="number" step="0.1" label="Entre linhas (mm)" />
          </template>
        </div>
        <p v-if="form.pagina.tipo === 'bobina'" class="text-xs text-zinc-500">
          No rolo, meça com a régua: largura e altura de <strong>uma</strong> etiqueta, a margem até a primeira coluna e o
          espaço entre colunas. No driver da impressora, o papel deve ter a largura do rolo inteiro.
        </p>
      </section>

      <section class="space-y-3">
        <h4 class="text-xs font-bold uppercase tracking-wider text-zinc-500">O que imprimir</h4>
        <div class="grid grid-cols-2 gap-2">
          <BaseCheckbox
            v-for="b in BLOCOS_AUTO"
            :key="b.bloco"
            :model-value="form.blocos.has(b.bloco)"
            :label="b.rotulo"
            @update:model-value="alternarBloco(b.bloco, $event)"
          />
        </div>
      </section>
    </div>

    <div class="lg:col-span-2 space-y-3">
      <h4 class="text-xs font-bold uppercase tracking-wider text-zinc-500">Pré-visualização</h4>
      <div class="flex justify-center rounded-xl bg-zinc-50 border border-zinc-100 p-4 min-h-40 items-center">
        <EtiquetaPreview
          v-if="definicao.elementos.length"
          :definicao="definicao"
          :valores="VALORES_EXEMPLO"
          :largura-max-px="280"
          :altura-max-px="220"
        />
      </div>
      <p class="text-[11px] text-zinc-400 text-center">
        O layout se ajusta sozinho ao tamanho. Posicionar à mão chega com o editor visual.
      </p>
      <div
        v-if="problemas.length"
        class="flex items-start gap-2 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900"
      >
        <AlertTriangle :size="15" class="shrink-0 mt-0.5" />
        <ul class="space-y-1">
          <li v-for="p in problemas" :key="p">{{ p }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>
