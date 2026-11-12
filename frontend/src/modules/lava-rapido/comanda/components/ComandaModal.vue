<script setup lang="ts">
/**
 * @component ComandaModal
 * @description "Nova entrada" do lava-rápido: a comanda de UMA tela, sem abas
 * (Spec 03B, SPEC-00 U2).
 *
 * Ordem do balcão: placa → veículo e dono aparecem (segunda visita) → tipo →
 * porte → serviços com o preço do porte → lavador → avarias e fotos → Entrar.
 * Tipo, porte, serviço e lavador são BOTÕES, não lista suspensa: um toque.
 * O documento gravado é a OS de sempre; ela entra no pátio em "Aguardando".
 */
import { computed, ref, watch } from 'vue';
import { Camera, CheckCircle2, UserPlus, X } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';

import SeletorLavadores from '../../shared/components/SeletorLavadores.vue';
import { horaLocal, reais } from '../../shared/utils/lavaRapido';
import { nomeDoCliente, useComanda } from '../composables/useComanda';

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits<{ close: []; criada: [numeroOs: string] }>();

const c = useComanda();
const toast = useToast();

// Abriu de novo: comanda limpa.
watch(() => props.isOpen, (aberta) => { if (aberta) c.limpar(); });

// --- Cliente novo (placa que o sistema não conhece) -------------------------------
const novoNome = ref('');
const novoCelular = ref('');
const cadastrandoCliente = ref(false);
function confirmarClienteNovo() {
  if (!novoNome.value.trim()) return;
  c.clienteNovo(novoNome.value.trim(), novoCelular.value);
  cadastrandoCliente.value = false;
}
function trocarCliente() {
  c.cliente.value = null;
  novoNome.value = '';
  novoCelular.value = '';
}

// --- Fotos --------------------------------------------------------------------------
const inputFoto = ref<HTMLInputElement | null>(null);
function adicionarFotos(evento: Event) {
  const arquivos = Array.from((evento.target as HTMLInputElement).files ?? []);
  c.fotos.value = [...c.fotos.value, ...arquivos.filter((f) => f.type.startsWith('image/'))];
  if (inputFoto.value) inputFoto.value.value = '';
}

// --- Salvar -------------------------------------------------------------------------
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
const placeholderModelo = computed(() => {
  if (c.tipo.value === 'moto') return 'Ex: CG 160 preta';
  if (c.tipo.value === 'pesado') return 'Ex: Scania R450';
  if (c.tipo.value === 'bicicleta') return 'Ex: Caloi aro 29';
  if (c.tipo.value === 'outros') return 'Ex: Lancha 21 pés';
  return 'Ex: Gol';
});

/** Classe dos botões de escolha (tipo, porte, serviço, avaria). */
function chip(ativo: boolean): string {
  return ativo
    ? 'border-brand-primary bg-brand-primary text-white'
    : 'border-zinc-200 bg-white text-zinc-700 hover:border-brand-primary hover:text-brand-primary';
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Nova entrada" subtitle="Lavagem: do balcão ao pátio" size="4xl" @close="emit('close')">
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-5">
      <!-- ===================== Coluna 1: veículo, cliente e serviços ===================== -->
      <div class="flex flex-col gap-5 lg:col-span-3">
        <!-- Placa -->
        <section class="flex flex-col gap-2">
          <div class="grid grid-cols-12 gap-3">
            <div class="col-span-12 sm:col-span-5">
              <BaseInput
                v-model="c.placa.value"
                :label="c.placaObrigatoria.value ? 'Placa' : 'Placa (se tiver)'"
                placeholder="ABC1D23"
                data-testid="comanda-placa"
              />
            </div>
            <div class="col-span-12 flex items-end pb-2 text-sm sm:col-span-7">
              <span v-if="c.buscandoPlaca.value" class="text-zinc-400">Procurando…</span>
              <span v-else-if="c.veiculo.value" class="flex items-center gap-1 font-medium text-emerald-700">
                <CheckCircle2 :size="16" /> Já veio aqui: {{ c.veiculo.value.modelo }} de {{ c.veiculo.value.cliente_nome }}
              </span>
              <span v-else-if="c.placa.value.length >= 7" class="text-zinc-500">Veículo novo</span>
            </div>
          </div>
        </section>

        <!-- Cliente -->
        <section class="flex flex-col gap-2">
          <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Cliente</p>
          <div v-if="c.cliente.value" class="flex items-center justify-between rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-2.5">
            <div>
              <p class="text-sm font-semibold text-zinc-800">{{ c.cliente.value.nome }}</p>
              <p class="text-xs text-zinc-500">
                {{ c.cliente.value.id ? 'Cliente cadastrado' : `Novo cliente${c.cliente.value.celular ? ' · ' + c.cliente.value.celular : ''}` }}
              </p>
            </div>
            <button type="button" class="text-xs font-semibold text-brand-primary hover:underline" @click="trocarCliente">Trocar</button>
          </div>

          <template v-else-if="!cadastrandoCliente">
            <BaseInput v-model="c.buscaCliente.value" placeholder="Buscar cliente por nome, telefone ou CPF" />
            <ul v-if="c.clientesAchados.value.length" class="divide-y divide-zinc-100 rounded-xl border border-zinc-200 bg-white">
              <li v-for="achado in c.clientesAchados.value" :key="achado.id">
                <button type="button" class="w-full px-4 py-2 text-left text-sm hover:bg-zinc-50" @click="c.escolherCliente(achado)">
                  {{ nomeDoCliente(achado) }}
                </button>
              </li>
            </ul>
            <button
              type="button"
              class="flex items-center gap-1.5 self-start text-sm font-semibold text-brand-primary hover:underline"
              @click="cadastrandoCliente = true; novoNome = c.buscaCliente.value"
            >
              <UserPlus :size="15" /> Cliente novo
            </button>
          </template>

          <div v-else class="grid grid-cols-12 items-end gap-3 rounded-xl border border-zinc-200 p-3">
            <div class="col-span-12 sm:col-span-6"><BaseInput v-model="novoNome" label="Nome" placeholder="Nome do cliente" /></div>
            <div class="col-span-8 sm:col-span-4">
              <BaseInput v-model="novoCelular" label="Celular" placeholder="(88) 99999-9999" inputmode="tel" />
            </div>
            <div class="col-span-4 flex gap-1 pb-0.5 sm:col-span-2">
              <BaseButton size="sm" :disabled="!novoNome.trim()" @click="confirmarClienteNovo">OK</BaseButton>
              <button type="button" class="p-2 text-zinc-400 hover:text-zinc-700" @click="cadastrandoCliente = false"><X :size="16" /></button>
            </div>
          </div>
        </section>

        <!-- Tipo e porte -->
        <section class="flex flex-col gap-2">
          <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Veículo</p>
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
          <div class="grid grid-cols-12 gap-3">
            <div class="col-span-12 sm:col-span-5">
              <BaseInput v-model="c.modelo.value" :label="rotuloModelo" :placeholder="placeholderModelo" />
            </div>
            <div class="col-span-6 sm:col-span-4"><BaseInput v-model="c.marca.value" label="Marca (opcional)" /></div>
            <div class="col-span-6 sm:col-span-3"><BaseInput v-model="c.cor.value" label="Cor" placeholder="Prata" /></div>
          </div>
        </section>

        <!-- Serviços -->
        <section class="flex flex-col gap-2">
          <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Serviços</p>
          <p v-if="!c.porteId.value" class="text-sm text-zinc-400">Escolha o porte para ver os preços.</p>
          <p v-else-if="c.carregandoServicos.value" class="text-sm text-zinc-400">Carregando…</p>
          <div v-else class="grid grid-cols-1 gap-2 sm:grid-cols-2">
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
        </section>
      </div>

      <!-- ===================== Coluna 2: lavador, avarias e resumo ===================== -->
      <div class="flex flex-col gap-5 lg:col-span-2">
        <section class="flex flex-col gap-2">
          <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Lavador</p>
          <SeletorLavadores v-model="c.lavadores.value" />
        </section>

        <section class="flex flex-col gap-2">
          <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Avarias na chegada</p>
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
          <div class="flex flex-wrap items-center gap-2">
            <input ref="inputFoto" type="file" accept="image/*" multiple capture="environment" class="hidden" @change="adicionarFotos" />
            <BaseButton size="sm" variant="ghost" @click="inputFoto?.click()">
              <Camera :size="14" class="mr-1" /> Foto
            </BaseButton>
            <span v-for="(foto, i) in c.fotos.value" :key="i" class="flex items-center gap-1 rounded-md bg-zinc-100 px-2 py-1 text-xs text-zinc-600">
              {{ foto.name.slice(0, 14) }}
              <button type="button" @click="c.fotos.value = c.fotos.value.filter((_, j) => j !== i)"><X :size="12" /></button>
            </span>
          </div>
        </section>

        <section>
          <BaseInput
            v-model="c.observacao.value"
            label="Observação / pertences"
            placeholder="Ex: óculos no porta-luvas, cuidado com o adesivo"
          />
        </section>

        <!-- Resumo -->
        <section class="mt-auto rounded-2xl bg-zinc-50 p-4">
          <ul class="flex flex-col gap-1 text-sm">
            <li v-for="item in c.itens.value" :key="item.servico_id" class="flex justify-between gap-2">
              <span class="text-zinc-700">{{ item.nome }}</span>
              <span class="tabular-nums text-zinc-700">{{ reais(item.valor) }}</span>
            </li>
          </ul>
          <div class="mt-3 flex items-end justify-between border-t border-zinc-200 pt-3">
            <div class="text-xs text-zinc-500">
              <span v-if="c.previsao.value">Pronto às <strong class="text-zinc-800">{{ horaLocal(c.previsao.value.toISOString()) }}</strong></span>
            </div>
            <p class="text-2xl font-bold tabular-nums text-zinc-900">{{ reais(c.total.value) }}</p>
          </div>
        </section>
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
</template>
