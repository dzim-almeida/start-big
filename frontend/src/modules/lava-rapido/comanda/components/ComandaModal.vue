<script setup lang="ts">
/**
 * @component ComandaModal
 * @description "Nova entrada" do lava-rápido (Spec 03B, SPEC-00 U2), no
 * PADRÃO DA OS da casa:
 *   - em cima, o cartão de controles de sempre (Situação, Responsável,
 *     Prioridade, Previsão) — `OSControlsCard`;
 *   - na lateral, o Resumo da OS (subtotal, adiantamento, deslocamento, valor
 *     a pagar) e os Dados do Cliente — `OSSummaryCard` e `OSClientCard`;
 *   - no corpo, numa tela só e sem abas: Veículo, Serviços (botões com o
 *     preço do porte + a lista do que foi escolhido), Lavadores e Avarias.
 * O documento gravado é a OS de sempre; ela entra no pátio em "Aguardando".
 */
import { computed, ref, watch } from 'vue';
import { Camera, CarFront, CheckCircle2, Droplets, ShieldAlert, Trash2, UserSearch, Users, X } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSectionCard from '@/shared/components/layout/SectionCard/BaseSectionCard.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import OSClienteSearchModal from '@/modules/order-service/ordens/components/OSClienteSearchModal.vue';
import OSClientCard from '@/modules/order-service/ordens/components/form/OSClientCard.vue';
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
const emit = defineEmits<{ close: []; criada: [numeroOs: string] }>();

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
watch(() => props.isOpen, async (aberta) => {
  if (!aberta) return;
  c.limpar();
  if (props.agendamento) c.preencherDeAgendamento(props.agendamento);
  await c.aplicarEntrada(props.cliente ?? null, props.objeto ?? null);
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

// --- Fotos ---------------------------------------------------------------------------
const inputFoto = ref<HTMLInputElement | null>(null);
function adicionarFotos(evento: Event) {
  const arquivos = Array.from((evento.target as HTMLInputElement).files ?? []);
  c.fotos.value = [...c.fotos.value, ...arquivos.filter((f) => f.type.startsWith('image/'))];
  if (inputFoto.value) inputFoto.value.value = '';
}

// --- Salvar --------------------------------------------------------------------------
async function entrar() {
  if (c.faltando.value.length) {
    toast.error(`Preencha: ${c.faltando.value.join(', ')}.`);
    return;
  }
  try {
    const { numero_os, avisos } = await c.salvar();
    if (avisos.length) toast.error(`Lavagem aberta (${numero_os}), mas não foi possível gravar ${avisos.join(', ')}.`);
    else toast.success(`Lavagem aberta: ${numero_os}.`);
    emit('criada', numero_os);
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
        <!-- ============ Corpo: veículo, serviços, lavadores, avarias ============ -->
        <div class="space-y-4">
          <BaseSectionCard titulo="Veículo" descricao="Digite a placa: se o veículo já veio, ele e o dono aparecem">
            <template #cabecalho>
              <div class="flex items-center gap-2">
                <CarFront :size="18" class="text-brand-primary" />
                <div>
                  <h2 class="text-base font-semibold text-zinc-900">Veículo</h2>
                  <p class="text-xs text-zinc-500">Digite a placa: se o veículo já veio, ele e o dono aparecem</p>
                </div>
              </div>
            </template>

            <div class="space-y-4">
              <div class="grid grid-cols-12 items-end gap-3">
                <div class="col-span-12 sm:col-span-5">
                  <BaseInput
                    v-model="c.placa.value"
                    :label="c.placaObrigatoria.value ? 'Placa' : 'Placa (se tiver)'"
                    placeholder="ABC1D23"
                    data-testid="comanda-placa"
                  />
                </div>
                <div class="col-span-12 pb-2 text-sm sm:col-span-7">
                  <span v-if="c.buscandoPlaca.value" class="text-zinc-400">Procurando…</span>
                  <span v-else-if="c.veiculo.value" class="flex items-center gap-1 font-medium text-emerald-700">
                    <CheckCircle2 :size="16" /> Já veio aqui: {{ c.veiculo.value.modelo }}
                  </span>
                  <span v-else-if="c.placa.value.length >= 7" class="text-zinc-500">Veículo novo</span>
                </div>
              </div>

              <div class="flex flex-wrap gap-2">
                <button
                  v-for="t in c.tiposDeVeiculo.value"
                  :key="t.value"
                  type="button"
                  class="rounded-full border px-3.5 py-1.5 text-sm font-semibold transition-colors"
                  :class="chip(c.tipo.value === t.value)"
                  @click="c.tipo.value = t.value"
                >
                  {{ t.label }}
                </button>
              </div>

              <div>
                <p class="mb-1.5 text-xs font-medium text-zinc-600">Porte</p>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="p in c.portesDoTipo.value"
                    :key="p.id"
                    type="button"
                    class="rounded-lg border px-3 py-1.5 text-sm transition-colors"
                    :class="chip(c.porteId.value === p.id)"
                    @click="c.porteId.value = p.id"
                  >
                    {{ p.nome }}
                  </button>
                  <span v-if="!c.portesDoTipo.value.length" class="text-sm text-zinc-400">
                    Nenhum porte ativo. Configure em Configurações › Lava-Rápido.
                  </span>
                </div>
              </div>

              <div class="grid grid-cols-12 gap-3">
                <div class="col-span-12 sm:col-span-5">
                  <BaseInput v-model="c.modelo.value" :label="rotuloModelo" :placeholder="placeholderModelo" required />
                </div>
                <div class="col-span-6 sm:col-span-4"><BaseInput v-model="c.marca.value" label="Marca" /></div>
                <div class="col-span-6 sm:col-span-3"><BaseInput v-model="c.cor.value" label="Cor" placeholder="Prata" /></div>
              </div>
            </div>
          </BaseSectionCard>

          <!-- Serviços: botões do porte + a lista do que foi escolhido -->
          <BaseSectionCard>
            <template #cabecalho>
              <div class="flex items-center gap-2">
                <Droplets :size="18" class="text-brand-primary" />
                <div>
                  <h2 class="text-base font-semibold text-zinc-900">Serviços</h2>
                  <p class="text-xs text-zinc-500">O preço é o do porte; pode ser ajustado na lista</p>
                </div>
              </div>
            </template>

            <p v-if="!c.porteId.value" class="text-sm text-zinc-400">Escolha o porte do veículo para ver os serviços e os preços.</p>
            <p v-else-if="c.carregandoServicos.value" class="text-sm text-zinc-400">Carregando…</p>
            <p v-else-if="!(c.servicosDoPorte.value ?? []).length" class="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
              Nenhum serviço cadastrado. Cadastre suas lavagens na aba <strong>Cadastro de Serviços</strong>
              (com o preço de cada porte) e elas aparecem aqui.
            </p>
            <template v-else>
              <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
                <button
                  v-for="s in c.servicosDoPorte.value ?? []"
                  :key="s.servico_id"
                  type="button"
                  class="flex items-center justify-between rounded-xl border px-3.5 py-2.5 text-left transition-colors"
                  :class="chip(s.servico_id in c.selecionados.value)"
                  @click="c.alternarServico(s.servico_id, s.valor)"
                >
                  <span class="text-sm font-medium">{{ s.descricao }}</span>
                  <span class="text-sm font-bold tabular-nums">{{ reais(s.valor) }}</span>
                </button>
              </div>

              <div v-if="c.itens.value.length" class="mt-4 rounded-xl border border-zinc-100">
                <p class="border-b border-zinc-100 px-4 py-2 text-xs text-slate-500">Serviços adicionados</p>
                <ul class="divide-y divide-zinc-100">
                  <li v-for="item in c.itens.value" :key="item.servico_id" class="flex items-center gap-3 px-4 py-2">
                    <span class="flex-1 text-sm font-medium text-zinc-800">{{ item.nome }}</span>
                    <div class="w-36">
                      <MoneyInput
                        :model-value="item.valor / 100"
                        @update:model-value="c.mudarPreco(item.servico_id, ($event ?? 0) * 100)"
                      />
                    </div>
                    <button
                      type="button"
                      class="p-1.5 text-zinc-400 hover:text-red-600"
                      title="Remover"
                      @click="c.alternarServico(item.servico_id, item.valor)"
                    >
                      <Trash2 :size="15" />
                    </button>
                  </li>
                </ul>
              </div>
            </template>
          </BaseSectionCard>

          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <BaseSectionCard>
              <template #cabecalho>
                <div class="flex items-center gap-2">
                  <Users :size="18" class="text-brand-primary" />
                  <h2 class="text-base font-semibold text-zinc-900">Lavadores</h2>
                </div>
              </template>
              <SeletorLavadores v-model="c.lavadores.value" />
            </BaseSectionCard>

            <BaseSectionCard>
              <template #cabecalho>
                <div class="flex items-center gap-2">
                  <ShieldAlert :size="18" class="text-brand-primary" />
                  <h2 class="text-base font-semibold text-zinc-900">Avarias na chegada</h2>
                </div>
              </template>
              <div class="flex flex-wrap gap-1.5">
                <button
                  v-for="avaria in c.avariasDoTipo.value"
                  :key="avaria"
                  type="button"
                  class="rounded-lg border px-2.5 py-1 text-xs transition-colors"
                  :class="c.avarias.value.includes(avaria)
                    ? 'border-amber-500 bg-amber-50 font-semibold text-amber-800'
                    : 'border-zinc-200 bg-white text-zinc-600 hover:border-amber-400'"
                  @click="c.alternarAvaria(avaria)"
                >
                  {{ avaria }}
                </button>
              </div>
              <div class="mt-3 flex flex-wrap items-center gap-2">
                <input ref="inputFoto" type="file" accept="image/*" multiple capture="environment" class="hidden" @change="adicionarFotos" />
                <BaseButton size="sm" variant="ghost" @click="inputFoto?.click()">
                  <Camera :size="14" class="mr-1" /> Foto
                </BaseButton>
                <span v-for="(foto, i) in c.fotos.value" :key="i" class="flex items-center gap-1 rounded-md bg-zinc-100 px-2 py-1 text-xs text-zinc-600">
                  {{ foto.name.slice(0, 14) }}
                  <button type="button" @click="c.fotos.value = c.fotos.value.filter((_, j) => j !== i)"><X :size="12" /></button>
                </span>
              </div>
            </BaseSectionCard>
          </div>

          <BaseInput
            v-model="c.observacao.value"
            label="Observação / pertences"
            placeholder="Ex: óculos no porta-luvas, cuidado com o adesivo do capô"
          />
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
          <template v-if="c.faltando.value.length">Falta: {{ c.faltando.value.join(', ') }}</template>
        </p>
        <div class="flex gap-3">
          <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
          <BaseButton :is-loading="c.salvando.value" data-testid="comanda-entrar" @click="entrar">Entrar no pátio</BaseButton>
        </div>
      </div>
    </template>
  </BaseModal>

  <!-- Trocar/selecionar cliente: a busca de sempre (nome, telefone, CPF ou placa) -->
  <OSClienteSearchModal
    :is-open="trocandoCliente"
    @close="trocandoCliente = false"
    @select-cliente="clienteTrocado"
    @select-objeto="veiculoTrocado"
  />
</template>
