<script setup lang="ts">
/**
 * @component BlocoAmbientes
 * @description Seção "Ambientes e móveis" do editor (Spec 06B D19, D20;
 * redesign 10/2026): UMA tabela, agrupada por ambiente, com "Novo ambiente"
 * no cabeçalho e, no rodapé, o custo (só com custos) e o total dos móveis.
 *
 * O nome do ambiente tem SUGESTÕES (Cozinha, Closet...) e aceita texto livre.
 * Na tela "novo", adicionar o primeiro ambiente cria o orçamento (D5).
 *
 * "Móvel avulso" (remodelação item 3): para o móvel que não é de um cômodo
 * (uma mesa, um painel solto), sem precisar inventar um ambiente antes.
 */
import { computed, nextTick, ref } from 'vue';
import { PackagePlus, Plus } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { formatCurrency } from '@/shared/utils/finance';

import { AMBIENTE_AVULSO, LIMITES, SUGESTOES_AMBIENTE } from '../../constants/orcamento.constants';
import { useEditor } from '../../composables/useEditorContexto';
import type { AmbienteDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import AmbienteCard from './AmbienteCard.vue';
import { gradeMoveis } from './gradeMoveis';

const { detalhe, editavel, incluiCustos, acoesOrcamento, garantirOrcamento, abrirMovel } = useEditor();

const ambientes = computed<AmbienteDetalhe[]>(() => detalhe.value?.ambientes ?? []);

/** "4 móveis em 3 ambientes": a contagem do cabeçalho da seção. */
const totalMoveis = computed(() => ambientes.value.reduce<number>((soma, a) => soma + a.moveis.length, 0));
const resumoContagem = computed(() => {
  const m = totalMoveis.value;
  const a = ambientes.value.length;
  return `${m} ${m === 1 ? 'móvel' : 'móveis'} em ${a} ${a === 1 ? 'ambiente' : 'ambientes'}`;
});
/** Rodapé: soma dos subtotais (bruto) e dos custos que a API mandou — só soma, nada de regra (C8). */
const totalMoveisCentavos = computed(() => ambientes.value.reduce<number>((soma, a) => soma + a.subtotal_centavos, 0));
const custoMoveisCentavos = computed(() =>
  ambientes.value.reduce<number>((soma, a) => soma + ('custo_centavos' in a ? a.custo_centavos : 0), 0),
);

// --- Novo ambiente --------------------------------------------------------------
const adicionando = ref(false);
const nome = ref('');
const campo = ref<HTMLInputElement | null>(null);
const gravando = ref(false);

async function abrirCampo() {
  adicionando.value = true;
  nome.value = '';
  await nextTick();
  campo.value?.focus();                               // foco no nome do ambiente (§7.12)
}

async function confirmar() {
  const texto = nome.value.trim();
  if (!texto || gravando.value) return;
  gravando.value = true;
  try {
    // Tela "novo": o primeiro ambiente cria o orçamento (D5).
    const id = await garantirOrcamento();
    if (id == null) return;
    const novo = await acoesOrcamento.criarAmbiente(texto);
    if (novo) adicionando.value = false;
  } finally {
    gravando.value = false;
  }
}

// --- Móvel avulso (remodelação item 3) ---------------------------------------------
/** Compara nomes sem ligar para maiúsculas e espaços: "avulso " é o mesmo que "Avulso". */
const ehAvulso = (a: AmbienteDetalhe) => a.nome.trim().toLowerCase() === AMBIENTE_AVULSO.toLowerCase();

/**
 * Abre o cadastro de um móvel no ambiente "Avulso". Se ele ainda não existe,
 * cria primeiro (e, na tela "novo", isso também cria o orçamento, como em D5).
 */
async function adicionarMovelAvulso() {
  if (gravando.value) return;                         // evita dois cliques criarem dois ambientes
  gravando.value = true;
  try {
    const id = await garantirOrcamento();
    if (id == null) return;                           // não deu para criar o orçamento
    // Já existe um "Avulso"? Usa ele.
    let avulso = ambientes.value.find(ehAvulso);
    if (!avulso) {
      // Não existe: cria. A API devolve o orçamento inteiro; o "Avulso" novo vem dentro dele.
      const novoDetalhe = await acoesOrcamento.criarAmbiente(AMBIENTE_AVULSO);
      avulso = novoDetalhe?.ambientes.find(ehAvulso);
    }
    if (avulso) abrirMovel(avulso.id);                // abre o modal do móvel já nesse ambiente
  } finally {
    gravando.value = false;
  }
}

/** Troca o ambiente de lugar com o vizinho e manda a nova ordem (D20). */
async function mover(indice: number, direcao: -1 | 1) {
  const ids = ambientes.value.map((a) => a.id);
  const alvo = indice + direcao;
  if (alvo < 0 || alvo >= ids.length) return;
  [ids[indice], ids[alvo]] = [ids[alvo], ids[indice]];
  await acoesOrcamento.ordenarAmbientes(ids);
}
</script>

<template>
  <section id="secao-ambientes" class="scroll-mt-40 overflow-hidden rounded-2xl border border-zinc-200 bg-white" aria-labelledby="titulo-ambientes">
    <header class="flex flex-wrap items-end justify-between gap-4 px-6 pb-4 pt-5">
      <div>
        <h2 id="titulo-ambientes" class="text-base font-semibold text-zinc-900">Ambientes e móveis</h2>
        <p class="text-xs text-zinc-500">
          <template v-if="ambientes.length">{{ resumoContagem }} · os preços já incluem perda e markup.</template>
          <template v-else>Os móveis do projeto, agrupados por ambiente.</template>
        </p>
      </div>
      <div v-if="editavel && !adicionando" class="flex flex-wrap gap-2">
        <!-- Móvel solto, sem cômodo: vai para o ambiente "Avulso" (item 3) -->
        <BaseButton variant="secondary" size="sm" :is-loading="gravando" data-testid="movel-avulso" @click="adicionarMovelAvulso">
          <PackagePlus :size="14" class="mr-1" /> Móvel avulso
        </BaseButton>
        <BaseButton variant="secondary" size="sm" data-testid="novo-ambiente" @click="abrirCampo">
          <Plus :size="14" class="mr-1" /> Novo ambiente
        </BaseButton>
      </div>
    </header>

    <!-- Nome com sugestões (datalist): escolher ou digitar livre (D19). -->
    <div v-if="adicionando" class="flex flex-wrap items-center gap-2 border-t border-zinc-100 px-6 py-3">
      <input
        ref="campo"
        v-model="nome"
        list="sugestoes-ambiente"
        :maxlength="LIMITES.nomeAmbiente"
        placeholder="Nome do ambiente (ex.: Cozinha)"
        aria-label="Nome do ambiente"
        class="min-w-60 flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 outline-none placeholder:text-gray-400 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary"
        data-testid="nome-ambiente"
        @keydown.enter.prevent="confirmar"
        @keydown.esc="adicionando = false"
      />
      <datalist id="sugestoes-ambiente">
        <option v-for="sugestao in SUGESTOES_AMBIENTE" :key="sugestao" :value="sugestao" />
      </datalist>
      <BaseButton variant="primary" size="sm" :is-loading="gravando" :disabled="!nome.trim()" @click="confirmar">Adicionar</BaseButton>
      <BaseButton variant="secondary" size="sm" @click="adicionando = false">Cancelar</BaseButton>
    </div>

    <template v-if="ambientes.length">
      <!-- Cabeçalho das colunas (some no celular, onde cada móvel vira um bloco). -->
      <div
        :class="['hidden border-t border-zinc-100 px-4 py-2.5 text-xs font-medium text-zinc-500', gradeMoveis(incluiCustos)]"
        aria-hidden="true"
      >
        <span class="pl-10">Móvel</span>
        <span>Medidas (L × A × P)</span>
        <span class="text-right">Qtd</span>
        <span>Produção</span>
        <span v-if="incluiCustos" class="text-right">Custo</span>
        <span class="text-right">Preço</span>
        <span />
      </div>

      <AmbienteCard
        v-for="(ambiente, indice) in ambientes"
        :key="ambiente.id"
        :ambiente="ambiente"
        :numero="indice + 1"
        :primeiro="indice === 0"
        :ultimo="indice === ambientes.length - 1"
        @subir="mover(indice, -1)"
        @descer="mover(indice, 1)"
      />

      <footer class="flex flex-wrap justify-end gap-x-8 gap-y-1 border-t border-zinc-100 bg-zinc-50/80 px-6 py-3.5 text-sm text-zinc-500">
        <span v-if="incluiCustos">Custo <strong class="ml-1.5 font-semibold tabular-nums text-zinc-700">{{ formatCurrency(custoMoveisCentavos) }}</strong></span>
        <span>Total dos móveis <strong class="ml-1.5 font-bold tabular-nums text-zinc-900">{{ formatCurrency(totalMoveisCentavos) }}</strong></span>
      </footer>
    </template>

    <p v-else-if="!adicionando" class="border-t border-zinc-100 px-6 py-8 text-center text-sm text-zinc-500">
      Nenhum ambiente ainda. Comece por "Novo ambiente" (ex.: Cozinha, Dormitório casal)
      ou, para um móvel solto, por "Móvel avulso".
    </p>
  </section>
</template>
