<script setup lang="ts">
/**
 * @component InsumosEditor
 * @description As linhas de insumo do móvel (Spec 06B D25-D27).
 *
 * Cada linha: descrição, quantidade (até 3 casas: "1,4" chapa, "26" m de
 * fita), unidade do produto e, para quem vê custos, o custo unitário
 * EDITÁVEL (ao editar, selo "manual") com o selo de origem ("última compra",
 * "custo médio", "sem custo" em vermelho).
 *
 * Insumo já gravado mantém o custo copiado (06A §6.4): só a quantidade muda,
 * a não ser que o custo seja editado à mão.
 */
import { nextTick, reactive, ref, watch } from 'vue';
import { Trash2 } from 'lucide-vue-next';

import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';

import { novaChaveInsumo, type InsumoForm } from '../../schemas/movelForm.schema';
import { centavosParaReais, lerNumeroDigitado, numeroParaTexto } from '../../utils/conversoes';
import { custoPelaRegraO3a, ROTULO_ORIGEM } from '../../utils/custoProduto';
import InsumoBusca from './InsumoBusca.vue';

defineProps<{
  incluiCustos: boolean;
  editavel: boolean;
  podeCadastrar: boolean;
  /** Erros por linha (índice → mensagem), da validação do formulário. */
  erros: Record<number, string>;
}>();

const emit = defineEmits<{ cadastrar: [nome: string] }>();

const insumos = defineModel<InsumoForm[]>({ required: true });

// --- Texto de cada campo enquanto o usuário digita (chave da linha → texto) ---
const textoQuantidade = reactive<Record<string, string>>({});
const textoCusto = reactive<Record<string, string>>({});

/** Linha nova ou trocada: preenche o texto a partir do número. */
watch(insumos, (linhas) => {
  for (const linha of linhas) {
    if (!(linha.chave in textoQuantidade)) textoQuantidade[linha.chave] = numeroParaTexto(linha.quantidade, 3);
    if (!(linha.chave in textoCusto)) textoCusto[linha.chave] = linha.custo_reais != null ? numeroParaTexto(linha.custo_reais, 2) : '';
  }
}, { immediate: true, deep: true });

function digitarQuantidade(linha: InsumoForm, texto: string) {
  textoQuantidade[linha.chave] = texto;
  // Texto inválido vira 0: a validação mostra "maior que zero" e a prévia espera.
  linha.quantidade = lerNumeroDigitado(texto) ?? 0;
}

/** Custo digitado à mão (D27): passa a valer e ganha o selo "manual". */
function digitarCusto(linha: InsumoForm, texto: string) {
  textoCusto[linha.chave] = texto;
  const reais = lerNumeroDigitado(texto);
  if (reais == null) return;
  linha.custo_reais = reais;
  linha.custo_editado = true;
  linha.custo_origem = 'MANUAL';
}

function remover(indice: number) {
  insumos.value = insumos.value.filter((_, i) => i !== indice);
}

// --- Inclusão pela busca -------------------------------------------------------
const camposQuantidade = ref<Record<string, HTMLInputElement | null>>({});

/** Produto escolhido na busca vira uma linha nova (quantidade 1). */
async function incluir(produto: ProdutoRead) {
  const custo = custoPelaRegraO3a(produto);               // o que o backend vai copiar (O3a)
  const linha: InsumoForm = {
    chave: novaChaveInsumo(),
    produto_id: produto.id,
    descricao: produto.nome,
    codigo: produto.codigo_produto,
    unidade: produto.unidade_medida || 'UN',
    sofre_perda: !!produto.sofre_perda,
    quantidade: 1,
    custo_reais: centavosParaReais(custo.centavos),
    custo_origem: custo.origem,
    custo_editado: false,
  };
  insumos.value = [...insumos.value, linha];
  await focarQuantidade(produto.id);                       // pronto para digitar a quantidade
}

/** Produto que já está no móvel: foco na quantidade da linha existente (D26). */
async function focarQuantidade(produtoId: number) {
  await nextTick();
  const linha = insumos.value.find((i) => i.produto_id === produtoId);
  if (!linha) return;
  const campo = camposQuantidade.value[linha.chave];
  campo?.focus();
  campo?.select();
}

defineExpose({ incluir, focarQuantidade });
</script>

<template>
  <div>
    <div class="mb-2 flex items-center justify-between gap-3">
      <p class="text-xs font-semibold text-zinc-700">Insumos</p>
    </div>

    <InsumoBusca
      v-if="editavel"
      class="mb-3"
      :produtos-no-movel="insumos.map((i) => i.produto_id).filter((id): id is number => id != null)"
      :inclui-custos="incluiCustos"
      :pode-cadastrar="podeCadastrar"
      @escolher="incluir"
      @existente="focarQuantidade"
      @cadastrar="emit('cadastrar', $event)"
    />

    <p v-if="!insumos.length" class="text-xs text-zinc-400">Nenhum insumo. Busque no cadastro acima.</p>
    <ul v-else class="divide-y divide-zinc-100 rounded-lg border border-zinc-200">
      <li v-for="(linha, indice) in insumos" :key="linha.chave" class="flex flex-wrap items-center gap-3 px-3 py-2" :data-testid="`insumo-${linha.produto_id}`">
        <div class="min-w-40 flex-1">
          <p class="truncate text-sm text-zinc-800">{{ linha.descricao }}</p>
          <p class="text-[11px] text-zinc-400">
            {{ linha.codigo ?? '' }}
            <span v-if="linha.sofre_perda" class="ml-1 rounded bg-zinc-100 px-1 text-zinc-600">sofre perda</span>
          </p>
        </div>

        <label class="flex items-center gap-1 text-xs text-zinc-500">
          <input
            :ref="(el) => { camposQuantidade[linha.chave] = el as HTMLInputElement | null; }"
            :value="textoQuantidade[linha.chave]"
            type="text"
            inputmode="decimal"
            :disabled="!editavel"
            :aria-label="`Quantidade de ${linha.descricao}`"
            class="w-20 rounded-md border px-2 py-1 text-right text-sm tabular-nums focus:outline-none focus:ring-2 focus:ring-brand-primary/30 disabled:bg-zinc-50"
            :class="erros[indice] ? 'border-red-400' : 'border-zinc-200'"
            :data-testid="`quantidade-${linha.produto_id}`"
            @input="digitarQuantidade(linha, ($event.target as HTMLInputElement).value)"
          />
          {{ linha.unidade ?? 'UN' }}
        </label>

        <!-- Custo: só para quem vê custos (D16). -->
        <div v-if="incluiCustos" class="flex items-center gap-1 text-xs" data-testid="custo-insumo">
          <span class="text-zinc-400">R$</span>
          <input
            :value="textoCusto[linha.chave]"
            type="text"
            inputmode="decimal"
            :disabled="!editavel"
            :aria-label="`Custo unitário de ${linha.descricao}`"
            class="w-24 rounded-md border border-zinc-200 px-2 py-1 text-right text-sm tabular-nums focus:outline-none focus:ring-2 focus:ring-brand-primary/30 disabled:bg-zinc-50"
            @input="digitarCusto(linha, ($event.target as HTMLInputElement).value)"
          />
          <span
            v-if="linha.custo_origem"
            class="rounded px-1.5 py-0.5 text-[10px] font-semibold"
            :class="linha.custo_origem === 'SEM_CUSTO' ? 'bg-red-50 text-red-700' : 'bg-zinc-100 text-zinc-600'"
          >
            {{ ROTULO_ORIGEM[linha.custo_origem] ?? linha.custo_origem }}
          </span>
        </div>

        <button
          v-if="editavel"
          type="button"
          class="rounded-md p-1.5 text-zinc-400 hover:bg-red-50 hover:text-red-600 cursor-pointer"
          :aria-label="`Remover ${linha.descricao}`"
          @click="remover(indice)"
        >
          <Trash2 :size="14" />
        </button>

        <p v-if="erros[indice]" class="w-full text-[11px] text-red-600">{{ erros[indice] }}</p>
      </li>
    </ul>
  </div>
</template>
