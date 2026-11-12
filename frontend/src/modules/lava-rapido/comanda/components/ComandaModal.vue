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
import { Camera, CheckCircle2, UserSearch, X } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSectionCard from '@/shared/components/layout/SectionCard/BaseSectionCard.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
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
        <!-- ============ Corpo: 1 Veículo · 2 Serviços · 3 Quem vai lavar · 4 Avarias ============ -->
        <div class="space-y-4">
          <!-- 1. Veículo -->
          <BaseSectionCard>
            <template #cabecalho>
              <div class="flex items-center gap-3">
                <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-primary text-xs font-bold text-white">1</span>
                <div>
                  <h2 class="text-base font-semibold text-zinc-900">Veículo</h2>
                  <p class="text-xs text-zinc-500">Placa, tipo e porte. O porte define o preço dos serviços.</p>
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
                  <p class="mb-1 text-sm font-medium text-gray-700">Porte <span class="text-red-600">*</span></p>
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="p in c.portesDoTipo.value"
                      :key="p.id"
                      type="button"
                      class="rounded-lg border px-3 py-2 text-sm transition-colors"
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

          <!-- 2. Serviços: uma lista só, marcar = incluir; o preço da linha marcada é editável -->
          <BaseSectionCard>
            <template #cabecalho>
              <div class="flex items-center gap-3">
                <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-primary text-xs font-bold text-white">2</span>
                <div>
                  <h2 class="text-base font-semibold text-zinc-900">Serviços</h2>
                  <p class="text-xs text-zinc-500">Marque o que vai ser feito. O preço é o do porte e pode ser ajustado.</p>
                </div>
              </div>
            </template>

            <p v-if="!c.porteId.value" class="text-sm text-zinc-400">Escolha o porte do veículo para ver os serviços.</p>
            <p v-else-if="c.carregandoServicos.value" class="text-sm text-zinc-400">Carregando…</p>
            <p v-else-if="!(c.servicosDoPorte.value ?? []).length" class="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
              Nenhum serviço cadastrado. Cadastre suas lavagens na aba <strong>Cadastro de Serviços</strong>
              (com o preço de cada porte) e elas aparecem aqui.
            </p>
            <ul v-else class="divide-y divide-zinc-100 rounded-xl border border-zinc-200">
              <li
                v-for="s in c.servicosDoPorte.value ?? []"
                :key="s.servico_id"
                class="flex items-center gap-3 px-4 py-2.5 transition-colors"
                :class="s.servico_id in c.selecionados.value ? 'bg-brand-primary-light/60' : 'hover:bg-zinc-50'"
              >
                <label class="flex flex-1 cursor-pointer items-center gap-3">
                  <input
                    type="checkbox"
                    class="h-4 w-4 cursor-pointer rounded border-zinc-300 accent-brand-primary"
                    :checked="s.servico_id in c.selecionados.value"
                    @change="c.alternarServico(s.servico_id, s.valor)"
                  />
                  <span class="text-sm font-medium text-zinc-800">{{ s.descricao }}</span>
                  <span v-if="s.duracao_minutos" class="text-xs text-zinc-400">{{ s.duracao_minutos }} min</span>
                </label>
                <div v-if="s.servico_id in c.selecionados.value" class="w-36">
                  <MoneyInput
                    :model-value="c.selecionados.value[s.servico_id] / 100"
                    @update:model-value="c.mudarPreco(s.servico_id, ($event ?? 0) * 100)"
                  />
                </div>
                <span v-else class="w-36 pr-3 text-right text-sm tabular-nums text-zinc-600">{{ reais(s.valor) }}</span>
              </li>
            </ul>
          </BaseSectionCard>

          <!-- 3. Quem vai lavar -->
          <BaseSectionCard>
            <template #cabecalho>
              <div class="flex items-center gap-3">
                <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-primary text-xs font-bold text-white">3</span>
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
                <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-200 text-xs font-bold text-zinc-600">4</span>
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

            <div class="mt-4 flex flex-wrap items-center gap-2 border-t border-zinc-100 pt-3">
              <input ref="inputFoto" type="file" accept="image/*" multiple capture="environment" class="hidden" @change="adicionarFotos" />
              <BaseButton size="sm" variant="ghost" @click="inputFoto?.click()">
                <Camera :size="14" class="mr-1" /> Adicionar foto
              </BaseButton>
              <span v-for="(foto, i) in c.fotos.value" :key="i" class="flex items-center gap-1 rounded-md bg-zinc-100 px-2 py-1 text-xs text-zinc-600">
                {{ foto.name.slice(0, 14) }}
                <button type="button" @click="c.fotos.value = c.fotos.value.filter((_, j) => j !== i)"><X :size="12" /></button>
              </span>
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
