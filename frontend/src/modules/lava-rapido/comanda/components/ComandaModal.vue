<script setup lang="ts">
/**
 * @component ComandaModal
 * @description "Nova entrada" do lava-rápido (Spec 03B, SPEC-00 U2), no
 * PADRÃO DA OS da casa:
 *   - em cima, o cartão de controles de sempre (Situação, Responsável,
 *     Prioridade, Previsão) — `OSControlsCard`;
 *   - na lateral, o Resumo da OS (subtotal, adiantamento, deslocamento, valor
 *     a pagar) e os Dados do Cliente — `OSSummaryCard` e `OSClientCard`;
 *   - no corpo, em abas: Veículo (porte, lavagens, lavadores e avarias),
 *     Produtos e Avulsos, e Fotos (opcional — a galeria da OS).
 * O documento gravado é a OS de sempre; ela entra no pátio em "Aguardando".
 */
import { computed, onUnmounted, ref, watch } from 'vue';
import {
  Camera, CarFront, CheckCircle2, Droplets, Package, Pencil, Plus, Printer, Search, ShieldAlert, Trash2, UserSearch, Users,
} from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSectionCard from '@/shared/components/layout/SectionCard/BaseSectionCard.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import OSClienteSearchModal from '@/modules/order-service/ordens/components/OSClienteSearchModal.vue';
import OSClientCard from '@/modules/order-service/ordens/components/form/OSClientCard.vue';
import OSItemFormModal from '@/modules/order-service/ordens/components/form/OSItemFormModal.vue';
import OSFotoGallery, { type PendingPhoto } from '@/modules/order-service/ordens/components/form/OSFotoGallery.vue';
import type { OsItemCreateSchemaDataType } from '@/modules/order-service/ordens/schemas/relationship/osItem.schema';
import OSControlsCard from '@/modules/order-service/ordens/components/form/OSControlsCard.vue';
import OSSummaryCard from '@/modules/order-service/ordens/components/form/OSSummaryCard.vue';
import { useOSSelectOptions } from '@/modules/order-service/ordens/composables/modal/useOSSelectOptions';
import type { CustomerUnionReadSchemaDataType } from '@/modules/order-service/ordens/schemas/relationship/customer/customer.schema';
import type { ObjetoBuscaItemDataType } from '@/modules/order-service/ordens/schemas/relationship/objetoBusca.schema';
import { getCustomerByIdForOS } from '@/modules/order-service/ordens/services/relationship/osRelationshipGet.service';
import type { OsPriorityEnumDataType } from '@/modules/order-service/ordens/schemas/enums/osEnums.schema';
import { useToast } from '@/shared/composables/useToast';
import { useAuthStore } from '@/shared/stores/auth.store';
import { getErrorMessage } from '@/shared/utils/error.utils';

import SeletorLavadores from '../../shared/components/SeletorLavadores.vue';
import type { Agendamento } from '../../shared/schemas/agenda.schema';
import { horaLocal, reais } from '../../shared/utils/lavaRapido';
import { useComanda } from '../composables/useComanda';

const props = defineProps<{
  isOpen: boolean;
  /** Escolhido na busca de cliente/placa ANTES da comanda (padrão da OS). */
  cliente?: CustomerUnionReadSchemaDataType | null;
  /** Veículo achado pela placa na busca (o dono vem em `cliente`). */
  objeto?: ObjetoBuscaItemDataType | null;
  /** Cliente agendado que chegou (Spec 08B): a comanda abre com o combinado. */
  agendamento?: Agendamento | null;
}>();
/** `imprimir`: true no "Entrar e imprimir" — quem hospeda a comanda imprime a via de entrada. */
const emit = defineEmits<{ close: []; criada: [numeroOs: string, imprimir: boolean] }>();

const c = useComanda();
const toast = useToast();
const authStore = useAuthStore();

// Opções do cartão de controles: as MESMAS da OS (status do segmento, equipe, prioridade).
const { funcionariosOptions, statusOptions, prioridadeOptions } = useOSSelectOptions({
  currentStatus: computed(() => 'ABERTA'),
  ativo: computed(() => props.isOpen),
});

/** Quem pode escolher o responsável: a mesma regra do formulário de OS. */
const podeEscolherResponsavel = computed(() => {
  const p = authStore.userData?.cargo?.permissoes;
  return p?.['all'] === true || p?.['funcionario'] === true;
});


// --- Abertura: o cliente (e o veículo) já vêm da busca ---------------------------
// `immediate`: a comanda pode nascer já aberta (tela trocada e devolvida).
watch(() => props.isOpen, async (aberta) => {
  if (!aberta) return;
  c.limpar();
  if (props.agendamento) c.preencherDeAgendamento(props.agendamento);
  await c.aplicarEntrada(props.cliente ?? null, props.objeto ?? null);
}, { immediate: true });

// Cliente/veículo que chegam com a comanda JÁ aberta também valem.
watch(() => [props.cliente, props.objeto] as const, async ([cliente, objeto], antes) => {
  if (!props.isOpen || !antes) return;
  if (cliente && cliente !== antes[0]) c.cliente.value = cliente;
  if (objeto && objeto !== antes[1]) await c.aplicarEntrada(cliente ?? c.cliente.value, objeto);
});

// "Trocar" no cartão do cliente: a MESMA busca de cliente/placa da OS.
const trocandoCliente = ref(false);
function clienteTrocado(cliente: CustomerUnionReadSchemaDataType) {
  c.cliente.value = cliente;
  trocandoCliente.value = false;
}
async function veiculoTrocado(objeto: ObjetoBuscaItemDataType) {
  trocandoCliente.value = false;
  try {
    await c.aplicarEntrada(await getCustomerByIdForOS(objeto.cliente_id), objeto);
  } catch {
    toast.error('Não foi possível carregar o dono do veículo.');
  }
}
function clienteAtualizado(cliente: CustomerUnionReadSchemaDataType) {
  c.cliente.value = cliente;
}

// --- Abas (padrão da OS): o cadastro e os itens ----------------------------------------
const ABAS = [
  { id: 'veiculo', rotulo: 'Veículo', icone: CarFront },
  { id: 'servicos', rotulo: 'Produtos e Avulsos', icone: Package },
  { id: 'fotos', rotulo: 'Fotos', icone: Camera },
] as const;
const abaAtiva = ref<(typeof ABAS)[number]['id']>('veiculo');
watch(() => props.isOpen, (aberta) => { if (aberta) abaAtiva.value = 'veiculo'; });
// As lavagens ficam na aba Veículo; aqui contam só produtos e avulsos.
const totalDeItens = computed(() => c.extras.value.length);

// --- Serviços: busca em vez de uma linha por serviço (a loja pode ter 100) -------------
const buscaServico = ref('');
const listaAberta = ref(false);
const semAcento = (t: string) => t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
/** O que ainda não foi escolhido e bate com o que foi digitado. */
const servicosDisponiveis = computed(() => {
  const termo = semAcento(buscaServico.value.trim());
  return (c.servicosDoPorte.value ?? []).filter((s) =>
    !(s.servico_id in c.selecionados.value) && (!termo || semAcento(s.descricao).includes(termo)));
});
function incluirServico(servicoId: number, valor: number) {
  if (!(servicoId in c.selecionados.value)) c.alternarServico(servicoId, valor);
  buscaServico.value = '';
}
watch(() => props.isOpen, (aberta) => { if (aberta) buscaServico.value = ''; });

// --- Produto ou serviço avulso: o modal de item da OS -----------------------------------
const itemAberto = ref(false);
const itemEditando = ref<number | null>(null);
const itemInicial = computed(() =>
  itemEditando.value === null ? null : c.extras.value[itemEditando.value] ?? null);
function abrirItem(indice: number | null) {
  itemEditando.value = indice;
  itemAberto.value = true;
}
function salvarItem(item: OsItemCreateSchemaDataType) {
  const lista = [...c.extras.value];
  if (itemEditando.value === null) lista.push(item);
  else lista[itemEditando.value] = item;
  c.extras.value = lista;
  itemAberto.value = false;
}
function removerItem(indice: number) {
  c.extras.value = c.extras.value.filter((_, i) => i !== indice);
}

// --- Fotos (aba opcional): a galeria da OS, com miniatura e tela cheia ---------------
// Cada arquivo ganha uma URL de pré-visualização, liberada quando a foto sai.
const previas = new Map<File, string>();
const fotosPendentes = computed<PendingPhoto[]>(() =>
  c.fotos.value.map((file) => {
    let url = previas.get(file);
    if (!url) { url = URL.createObjectURL(file); previas.set(file, url); }
    return { file, previewUrl: url, nome_arquivo: file.name };
  }));
watch(c.fotos, (fotos) => {
  for (const [file, url] of previas) {
    if (!fotos.includes(file)) { URL.revokeObjectURL(url); previas.delete(file); }
  }
});
onUnmounted(() => { for (const url of previas.values()) URL.revokeObjectURL(url); previas.clear(); });
function adicionarFoto(file: File) {
  c.fotos.value = [...c.fotos.value, file];
}
function removerFoto(indice: number) {
  c.fotos.value = c.fotos.value.filter((_, i) => i !== indice);
}

// --- Salvar --------------------------------------------------------------------------
async function entrar(imprimir = false) {
  if (c.faltando.value.length) {
    toast.error(`Preencha: ${c.faltando.value.join(', ')}.`);
    return;
  }
  try {
    const { numero_os, avisos } = await c.salvar();
    if (avisos.length) toast.error(`Lavagem aberta (${numero_os}), mas não foi possível gravar ${avisos.join(', ')}.`);
    else toast.success(`Lavagem aberta: ${numero_os}.`);
    emit('criada', numero_os, imprimir);
    emit('close');
  } catch (erro) {
    toast.error(getErrorMessage(erro as never, 'Não foi possível abrir a lavagem.') as string);
  }
}

const rotuloModelo = computed(() => (c.tipo.value === 'outros' ? 'Descrição' : 'Modelo'));
const placeholderModelo = computed(() => ({
  moto: 'Ex: CG 160', pesado: 'Ex: Scania R450', bicicleta: 'Ex: Caloi aro 29', outros: 'Ex: Lancha 21 pés',
} as Record<string, string>)[c.tipo.value] ?? 'Ex: Gol');

/** Classe dos botões de escolha (tipo, porte, serviço). */
function chip(ativo: boolean): string {
  return ativo
    ? 'border-brand-primary bg-brand-primary text-white'
    : 'border-zinc-200 bg-white text-zinc-700 hover:border-brand-primary hover:text-brand-primary';
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Nova entrada" subtitle="Lavagem: do balcão ao pátio" size="4xl" @close="emit('close')">
    <div class="space-y-4">
      <!-- Controles de sempre: Situação, Responsável, Prioridade, Previsão -->
      <OSControlsCard
        status="ABERTA"
        is-create-mode
        :funcionario-id="c.responsavelId.value"
        :prioridade="c.prioridade.value"
        :data-previsao="c.dataPrevisao.value"
        :status-options="statusOptions"
        :prioridade-options="prioridadeOptions"
        :funcionarios-options="funcionariosOptions"
        :can-select-tecnico="podeEscolherResponsavel"
        @update:funcionario-id="c.responsavelId.value = $event"
        @update:prioridade="c.prioridade.value = $event as OsPriorityEnumDataType"
        @update:data-previsao="c.mudarDataPrevisao"
      />

      <div class="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1fr_400px]">
        <!-- ============ Corpo em abas, no padrão da OS ============ -->
        <div>
          <div role="tablist" class="mb-4 flex gap-1 rounded-xl bg-slate-100 p-1">
            <button
              v-for="aba in ABAS"
              :key="aba.id"
              type="button"
              role="tab"
              :aria-selected="abaAtiva === aba.id"
              :class="[
                'flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-bold transition-all',
                abaAtiva === aba.id ? 'bg-white text-brand-primary shadow-sm' : 'text-slate-500 hover:text-slate-700',
              ]"
              @click="abaAtiva = aba.id"
            >
              <component :is="aba.icone" :size="16" />
              {{ aba.rotulo }}
              <span
                v-if="aba.id === 'servicos' && totalDeItens"
                class="rounded-full bg-brand-primary px-1.5 text-[11px] text-white"
              >{{ totalDeItens }}</span>
              <span
                v-if="aba.id === 'fotos' && c.fotos.value.length"
                class="rounded-full bg-brand-primary px-1.5 text-[11px] text-white"
              >{{ c.fotos.value.length }}</span>
            </button>
          </div>

          <div v-show="abaAtiva === 'veiculo'" class="space-y-4">
          <!-- 1. Veículo -->
          <BaseSectionCard class="overflow-visible!">
            <template #cabecalho>
              <div class="flex items-center gap-3">
                <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-primary-light text-brand-primary"><CarFront :size="16" /></span>
                <div>
                  <h2 class="text-base font-semibold text-zinc-900">Veículo</h2>
                  <p class="text-xs text-zinc-500">Opcional: preencha só o que o cliente quiser informar.</p>
                </div>
              </div>
            </template>

            <div class="space-y-4">
              <div class="grid grid-cols-12 items-end gap-3">
                <div class="col-span-12 sm:col-span-4">
                  <BaseInput
                    v-model="c.placa.value"
                    :label="c.placaObrigatoria.value ? 'Placa' : 'Placa (se tiver)'"
                    placeholder="ABC1D23"
                    :required="c.placaObrigatoria.value"
                    data-testid="comanda-placa"
                  />
                </div>
                <div class="col-span-12 pb-2 text-sm sm:col-span-8">
                  <span v-if="c.buscandoPlaca.value" class="text-zinc-400">Procurando…</span>
                  <span v-else-if="c.veiculo.value" class="flex items-center gap-1 font-medium text-emerald-700">
                    <CheckCircle2 :size="16" /> Já veio aqui: {{ c.veiculo.value.modelo }}
                  </span>
                  <span v-else-if="c.placa.value.length >= 7" class="text-zinc-500">Veículo novo</span>
                </div>
              </div>

              <div class="grid grid-cols-12 gap-3">
                <div class="col-span-12 sm:col-span-4">
                  <BaseSelect v-model="c.tipo.value" label="Tipo" :options="c.tiposDeVeiculo.value" />
                </div>
                <div class="col-span-12 sm:col-span-8">
                  <p class="mb-1 text-sm font-medium text-gray-700">Porte</p>
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="p in c.portesDoTipo.value"
                      :key="p.id"
                      type="button"
                      class="rounded-lg border px-3 py-2 text-sm transition-colors"
                      :class="chip(c.porteId.value === p.id)"
                      :title="c.porteId.value === p.id ? 'Clique de novo para tirar o porte' : undefined"
                      @click="c.porteId.value = c.porteId.value === p.id ? null : p.id"
                    >
                      {{ p.nome }}
                    </button>
                    <span v-if="!c.portesDoTipo.value.length" class="text-sm text-zinc-400">
                      Nenhum porte ativo. Configure em Configurações › Lava-Rápido.
                    </span>
                  </div>
                </div>
              </div>

              <div class="grid grid-cols-12 gap-3">
                <div class="col-span-12 sm:col-span-5">
                  <BaseInput v-model="c.modelo.value" :label="rotuloModelo" :placeholder="placeholderModelo" />
                </div>
                <div class="col-span-6 sm:col-span-4"><BaseInput v-model="c.marca.value" label="Marca" /></div>
                <div class="col-span-6 sm:col-span-3"><BaseInput v-model="c.cor.value" label="Cor" placeholder="Prata" /></div>
              </div>
            </div>
          </BaseSectionCard>

          <!-- 2. Serviços: busca para adicionar; só os escolhidos na tela, com o preço editável -->
          <BaseSectionCard class="overflow-visible!">
            <template #cabecalho>
              <div class="flex items-center gap-3">
                <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-primary-light text-brand-primary"><Droplets :size="16" /></span>
                <div>
                  <h2 class="text-base font-semibold text-zinc-900">
                    Lavagens<template v-if="c.porteId.value"> do porte: {{ c.portesDoTipo.value.find((p) => p.id === c.porteId.value)?.nome }}</template>
                  </h2>
                  <p class="text-xs text-zinc-500">Busque e adicione o que vai ser feito. O preço é o do cadastro e pode ser ajustado.</p>
                </div>
              </div>
            </template>

            <p v-if="c.carregandoServicos.value" class="text-sm text-zinc-400">Carregando…</p>
            <p v-else-if="!(c.servicosDoPorte.value ?? []).length" class="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
              Nenhum serviço cadastrado. Cadastre suas lavagens na aba <strong>Cadastro de Serviços</strong>
              e elas aparecem aqui.
            </p>
            <div v-else class="space-y-3">
              <!-- Busca: com 100 serviços, só uma lista curta do que foi digitado -->
              <div class="relative">
                <Search :size="16" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
                <input
                  v-model="buscaServico"
                  type="text"
                  placeholder="Buscar serviço para adicionar…"
                  class="w-full rounded-lg border border-zinc-300 py-2 pl-9 pr-3 text-sm focus:border-brand-primary focus:outline-none"
                  data-testid="comanda-busca-servico"
                  @focus="listaAberta = true"
                  @blur="listaAberta = false"
                  @keydown.esc="listaAberta = false"
                />
                <ul
                  v-if="listaAberta"
                  class="absolute z-20 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-zinc-200 bg-white py-1 shadow-lg"
                >
                  <li
                    v-for="s in servicosDisponiveis"
                    :key="s.servico_id"
                    class="flex cursor-pointer items-center justify-between gap-3 px-3 py-2 text-sm hover:bg-brand-primary-light/60"
                    @mousedown.prevent="incluirServico(s.servico_id, s.valor)"
                  >
                    <span class="text-zinc-800">{{ s.descricao }}</span>
                    <span class="tabular-nums text-zinc-600">{{ reais(s.valor) }}</span>
                  </li>
                  <li v-if="!servicosDisponiveis.length" class="px-3 py-2 text-sm text-zinc-400">
                    {{ buscaServico ? 'Nenhum serviço com esse nome.' : 'Todos os serviços já foram adicionados.' }}
                  </li>
                </ul>
              </div>

              <!-- Só o que foi escolhido, com o preço ajustável -->
              <ul v-if="c.itens.value.length" class="divide-y divide-zinc-100 rounded-xl border border-zinc-200">
                <li v-for="item in c.itens.value" :key="item.servico_id" class="flex items-center gap-3 px-4 py-2">
                  <span class="flex-1 text-sm font-medium text-zinc-800">{{ item.nome }}</span>
                  <div class="w-36">
                    <MoneyInput
                      :model-value="item.valor / 100"
                      @update:model-value="c.mudarPreco(item.servico_id, ($event ?? 0) * 100)"
                    />
                  </div>
                  <button type="button" class="p-1.5 text-zinc-400 hover:text-red-600" title="Remover" @click="c.alternarServico(item.servico_id, item.valor)">
                    <Trash2 :size="14" />
                  </button>
                </li>
              </ul>
              <p v-else class="text-sm text-zinc-400">Nenhum serviço adicionado.</p>
            </div>
          </BaseSectionCard>

          <!-- 3. Quem vai lavar -->
          <BaseSectionCard class="overflow-visible!">
            <template #cabecalho>
              <div class="flex items-center gap-3">
                <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-primary-light text-brand-primary"><Users :size="16" /></span>
                <div>
                  <h2 class="text-base font-semibold text-zinc-900">Quem vai lavar</h2>
                  <p class="text-xs text-zinc-500">A comissão segue a regra do cargo (dividir ou inteira).</p>
                </div>
              </div>
            </template>
            <SeletorLavadores v-model="c.lavadores.value" />
          </BaseSectionCard>

          <!-- 4. Avarias e observação (opcional) -->
          <BaseSectionCard>
            <template #cabecalho>
              <div class="flex items-center gap-3">
                <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-zinc-100 text-zinc-500"><ShieldAlert :size="16" /></span>
                <div>
                  <h2 class="text-base font-semibold text-zinc-900">Avarias na chegada <span class="text-xs font-normal text-zinc-400">(opcional)</span></h2>
                  <p class="text-xs text-zinc-500">Marque só o que o veículo já tem. Protege a loja de reclamação.</p>
                </div>
              </div>
            </template>

            <div class="grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-2 lg:grid-cols-3">
              <BaseCheckbox
                v-for="avaria in c.avariasDoTipo.value"
                :key="avaria"
                :model-value="c.avarias.value.includes(avaria)"
                :label="avaria"
                @update:model-value="c.alternarAvaria(avaria)"
              />
            </div>

            <div class="mt-4">
              <BaseInput
                v-model="c.observacao.value"
                label="Observação / pertences"
                placeholder="Ex: óculos no porta-luvas, cuidado com o adesivo do capô"
              />
            </div>
          </BaseSectionCard>
          </div>

          <div v-show="abaAtiva === 'servicos'" class="space-y-4">

          <!-- Produtos e serviços avulsos: o modal de item da OS de sempre -->
          <BaseSectionCard>
            <template #cabecalho>
              <div class="flex w-full items-center gap-3">
                <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-primary-light text-brand-primary"><Package :size="16" /></span>
                <div class="flex-1">
                  <h2 class="text-base font-semibold text-zinc-900">Produtos e outros serviços</h2>
                  <p class="text-xs text-zinc-500">Cera, aromatizante, pretinho, flanela… do estoque, ou um serviço avulso.</p>
                </div>
                <BaseButton size="sm" variant="ghost" @click="abrirItem(null)">
                  <Plus :size="14" class="mr-1" /> Adicionar
                </BaseButton>
              </div>
            </template>

            <p v-if="!c.extras.value.length" class="text-sm text-zinc-400">Nenhum produto ou serviço avulso.</p>
            <ul v-else class="divide-y divide-zinc-100 rounded-xl border border-zinc-200">
              <li v-for="(extra, i) in c.extras.value" :key="i" class="flex items-center gap-3 px-4 py-2.5">
                <span
                  class="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase"
                  :class="extra.tipo === 'PRODUTO' ? 'bg-sky-50 text-sky-700' : 'bg-violet-50 text-violet-700'"
                >
                  {{ extra.tipo === 'PRODUTO' ? 'Produto' : 'Serviço' }}
                </span>
                <span class="flex-1 text-sm font-medium text-zinc-800">{{ extra.nome }}</span>
                <span class="text-xs text-zinc-500">{{ extra.quantidade }} × {{ reais(extra.valor_unitario) }}</span>
                <span class="w-24 text-right text-sm font-semibold tabular-nums text-zinc-800">{{ reais(c.valorDoExtra(extra)) }}</span>
                <button type="button" class="p-1.5 text-zinc-400 hover:text-brand-primary" title="Editar" @click="abrirItem(i)">
                  <Pencil :size="14" />
                </button>
                <button type="button" class="p-1.5 text-zinc-400 hover:text-red-600" title="Remover" @click="removerItem(i)">
                  <Trash2 :size="14" />
                </button>
              </li>
            </ul>
          </BaseSectionCard>

          </div>

          <!-- Fotos (opcional): a galeria da OS, com miniatura e foto em tela cheia -->
          <div v-show="abaAtiva === 'fotos'">
            <BaseSectionCard>
              <OSFotoGallery
                :fotos="[]"
                :pending-photos="fotosPendentes"
                @add-photo="adicionarFoto"
                @remove-pending="removerFoto"
              />
            </BaseSectionCard>
          </div>
        </div>

        <!-- ============ Lateral: resumo de cobrança e cliente (padrão da OS) ============ -->
        <div class="space-y-4">
          <OSSummaryCard
            :subtotal="c.subtotal.value"
            :valor-entrega="c.taxaEntrega.value"
            :valor-desconto="0"
            :valor-total="c.total.value"
            :valor-entrada="c.valorEntrada.value"
            :forma-pagamento-entrada-id="c.formaPagamentoEntradaId.value"
            :is-locked="false"
            @update:valor-entrada="c.valorEntrada.value = $event"
            @update:valor-entrega="c.taxaEntrega.value = $event"
            @update:forma-pagamento-entrada-id="c.formaPagamentoEntradaId.value = $event"
          />
          <p v-if="c.previsao.value" class="-mt-2 px-1 text-xs text-zinc-500">
            Pronto previsto às <strong class="text-zinc-800">{{ horaLocal(c.previsao.value.toISOString()) }}</strong>
          </p>

          <OSClientCard
            v-if="c.cliente.value"
            :cliente="c.cliente.value"
            @change-cliente="trocandoCliente = true"
            @update-cliente="clienteAtualizado"
          />
          <BaseSectionCard v-else titulo="Dados do cliente">
            <BaseButton variant="ghost" class="w-full" @click="trocandoCliente = true">
              <UserSearch :size="16" class="mr-1" /> Selecionar cliente
            </BaseButton>
          </BaseSectionCard>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex w-full flex-wrap items-center justify-between gap-3">
        <p class="text-xs text-zinc-500">
          <span v-if="c.faltando.value.length" class="text-amber-700">
            Para entrar no pátio, falta: <strong>{{ c.faltando.value.join(', ') }}</strong>
          </span>
          <span v-else class="text-emerald-700">Tudo pronto. Total {{ reais(c.total.value) }}</span>
        </p>
        <div class="flex gap-3">
          <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
          <BaseButton
            variant="secondary"
            :disabled="c.salvando.value"
            data-testid="comanda-entrar-imprimir"
            @click="entrar(true)"
          >
            <Printer :size="16" class="mr-1" /> Entrar e imprimir
          </BaseButton>
          <BaseButton :is-loading="c.salvando.value" data-testid="comanda-entrar" @click="entrar()">Entrar no pátio</BaseButton>
        </div>
      </div>
    </template>
  </BaseModal>

  <OSItemFormModal :is-open="itemAberto" :item="itemInicial" @close="itemAberto = false" @save="salvarItem" />

  <!-- Trocar/selecionar cliente: a busca de sempre (nome, telefone, CPF ou placa) -->
  <OSClienteSearchModal
    :is-open="trocandoCliente"
    @close="trocandoCliente = false"
    @select-cliente="clienteTrocado"
    @select-objeto="veiculoTrocado"
  />
</template>
