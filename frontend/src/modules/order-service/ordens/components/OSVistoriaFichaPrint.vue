<script setup lang="ts">
/**
 * @fileoverview Ficha de Vistoria imprimível (A4), em branco para preenchimento
 * manual no veículo. Dirigida pelo contrato do segmento (/definicao-campos):
 * lista os acessórios e o checklist corretos sem hardcode.
 *
 * Recebe as PEÇAS (cliente + objeto) em vez de uma OS pronta, para funcionar
 * também ANTES da OS existir (modo criação): imprime com o que já está no form.
 */
import { computed } from 'vue';
import { User } from 'lucide-vue-next';

import {
  useCompanyPrintInfo,
  getClienteNome,
  getClienteDoc,
  getClientePhone,
  formatPrintDate,
  formatPrintDoc,
  formatPrintPhone,
} from '@/shared/utils/print.utils';

import PrintCompanyHeader from '@/shared/components/print/a4/PrintCompanyHeader.vue';
import PrintSignatures from '@/shared/components/print/a4/PrintSignatures.vue';
import PrintFooter from '@/shared/components/print/a4/PrintFooter.vue';

import { useOSFieldDefinition } from '../composables/request/useOSFieldDefinition.queries';
import { useObjetoLabels } from '../composables/useObjetoLabels';

interface FichaObjeto {
  marca?: string | null;
  modelo?: string | null;
  numero_serie?: string | null;
  cor?: string | null;
  dados_adicionais?: Record<string, unknown> | null;
}

const props = defineProps<{
  cliente: Record<string, unknown> | null;
  objeto: FichaObjeto | null;
  numeroOs?: string | null;
  dataOs?: string | null;
  tipo: 'ENTRADA' | 'SAIDA';
}>();

const { companyInfo } = useCompanyPrintInfo();
const { data } = useOSFieldDefinition();
const { objetoIcon, labelIdentificador } = useObjetoLabels();

const definicao = computed(() => data.value?.definicao ?? null);
const acessorios = computed<string[]>(() => definicao.value?.acessorios ?? []);
const grupos = computed(() => definicao.value?.vistoria ?? []);

const titulo = computed(() =>
  props.tipo === 'ENTRADA' ? 'FICHA DE VISTORIA DE ENTRADA' : 'FICHA DE VISTORIA DE SAÍDA',
);
const kmLabel = computed(() => (props.tipo === 'ENTRADA' ? 'KM de Entrada' : 'KM de Saída'));
const numeroExibicao = computed(() => props.numeroOs || '—');
const dataExibicao = computed(() => (props.dataOs ? formatPrintDate(props.dataOs) : formatPrintDate(new Date().toISOString())));

const objetoDados = computed<Record<string, unknown>>(() => props.objeto?.dados_adicionais ?? {});

/** Converte o slug do contrato (ex: chave_de_roda) em rótulo (Chave de roda). */
function rotulo(slug: string): string {
  const s = slug.replace(/_/g, ' ');
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function dado(chave: string): string {
  const v = objetoDados.value[chave];
  return v === null || v === undefined ? '' : String(v);
}

const niveisCombustivel = ['Reserva', '1/4', '1/2', '3/4', 'Cheio'];
</script>

<template>
  <Teleport to="body">
    <div class="print-container hidden print:block bg-white text-black font-sans leading-tight">
      <PrintCompanyHeader
        :company="companyInfo"
        document-label="Número da O.S."
        :document-number="numeroExibicao"
        date-label="Data"
        :date-value="dataExibicao"
      />

      <!-- Título -->
      <div class="text-center py-2 mb-3 border-y-2 border-slate-200 bg-slate-50">
        <h2 class="text-lg font-black text-slate-800 uppercase tracking-widest">{{ titulo }}</h2>
      </div>

      <!-- Cliente + Veículo -->
      <div class="grid grid-cols-2 gap-4 mb-3">
        <div class="border border-slate-300 rounded-lg overflow-hidden">
          <div class="bg-slate-100 px-3 py-1.5 border-b border-slate-200 flex items-center gap-2">
            <User :size="14" class="text-slate-500" />
            <h3 class="text-xs font-bold uppercase text-slate-700">Dados do Cliente</h3>
          </div>
          <div class="p-3 text-xs space-y-1.5">
            <p><span class="font-bold text-slate-600">Nome:</span> {{ cliente ? getClienteNome(cliente as any) : '—' }}</p>
            <div class="flex gap-4">
              <p><span class="font-bold text-slate-600">CPF/CNPJ:</span> {{ formatPrintDoc(getClienteDoc(cliente as any)) }}</p>
              <p><span class="font-bold text-slate-600">Telefone:</span> {{ formatPrintPhone(getClientePhone(cliente as any)) }}</p>
            </div>
          </div>
        </div>

        <div class="border border-slate-300 rounded-lg overflow-hidden">
          <div class="bg-slate-100 px-3 py-1.5 border-b border-slate-200 flex items-center gap-2">
            <component :is="objetoIcon" :size="14" class="text-slate-500" />
            <h3 class="text-xs font-bold uppercase text-slate-700">Dados do Veículo</h3>
          </div>
          <div class="p-3 text-xs">
            <div class="grid grid-cols-2 gap-x-4 gap-y-1.5">
              <p><span class="font-bold text-slate-600">Marca:</span> {{ objeto?.marca || '-' }}</p>
              <p><span class="font-bold text-slate-600">Modelo:</span> {{ objeto?.modelo || '-' }}</p>
              <p><span class="font-bold text-slate-600">{{ labelIdentificador }}:</span> {{ objeto?.numero_serie || '-' }}</p>
              <p><span class="font-bold text-slate-600">Cor:</span> {{ objeto?.cor || '-' }}</p>
              <p v-if="dado('chassi')"><span class="font-bold text-slate-600">Chassi:</span> {{ dado('chassi') }}</p>
              <p v-if="dado('ano')"><span class="font-bold text-slate-600">Ano:</span> {{ dado('ano') }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Check-in: KM + combustível (em branco) -->
      <div class="border border-slate-300 rounded-lg mb-3 p-3 flex flex-wrap items-center gap-x-8 gap-y-2 text-xs">
        <div class="flex items-center gap-2">
          <span class="font-bold text-slate-600">{{ kmLabel }}:</span>
          <span class="inline-block w-24 border-b border-slate-400">&nbsp;</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="font-bold text-slate-600">Combustível:</span>
          <span v-for="n in niveisCombustivel" :key="n" class="inline-flex items-center gap-1">
            <span class="inline-block w-3 h-3 rounded-full border border-slate-500"></span>{{ n }}
          </span>
        </div>
      </div>

      <!-- Acessórios presentes -->
      <div v-if="acessorios.length" class="mb-3">
        <h3 class="text-xs font-bold uppercase text-slate-700 border-b border-slate-200 pb-1 mb-2">Acessórios Presentes</h3>
        <div class="grid grid-cols-4 gap-x-4 gap-y-1.5 text-xs">
          <span v-for="ac in acessorios" :key="ac" class="flex items-center gap-1.5">
            <span class="inline-block w-3 h-3 border border-slate-500 shrink-0"></span>{{ rotulo(ac) }}
          </span>
        </div>
      </div>

      <!-- Checklist de inspeção -->
      <div v-if="grupos.length" class="mb-3">
        <h3 class="text-xs font-bold uppercase text-slate-700 border-b border-slate-200 pb-1 mb-2">Checklist de Inspeção</h3>
        <div class="grid grid-cols-2 gap-x-6 gap-y-3">
          <div v-for="grupo in grupos" :key="grupo.titulo" class="break-inside-avoid">
            <h4 class="text-[11px] font-bold text-slate-500 uppercase mb-1">{{ grupo.titulo }}</h4>
            <div class="space-y-0.5">
              <div
                v-for="item in grupo.itens"
                :key="item"
                class="flex items-center justify-between text-xs border-b border-dotted border-slate-200 py-0.5"
              >
                <span class="text-slate-700 truncate pr-2">{{ rotulo(item) }}</span>
                <span class="flex items-center gap-2 shrink-0 text-[10px] text-slate-500">
                  <span class="flex items-center gap-0.5"><span class="inline-block w-2.5 h-2.5 border border-slate-500"></span>OK</span>
                  <span class="flex items-center gap-0.5"><span class="inline-block w-2.5 h-2.5 border border-slate-500"></span>N/OK</span>
                  <span class="flex items-center gap-0.5"><span class="inline-block w-2.5 h-2.5 border border-slate-500"></span>Reparar</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Diagrama do veículo + observações -->
      <div class="grid grid-cols-2 gap-4 mb-3">
        <div class="border border-slate-300 rounded-lg p-3">
          <h3 class="text-xs font-bold uppercase text-slate-700 mb-1">Avarias (marque no diagrama)</h3>
          <p class="text-[10px] text-slate-400 mb-2">Marque com <strong>X</strong> os pontos com risco, amassado ou trinca.</p>
          <svg viewBox="0 0 180 320" class="w-full max-w-37.5 mx-auto">
            <path
              d="M30 60 C30 35 50 22 90 22 C130 22 150 35 150 60 L150 260 C150 285 130 298 90 298 C50 298 30 285 30 260 Z"
              fill="none" stroke="#334155" stroke-width="2.5"
            />
            <path d="M48 70 C60 58 120 58 132 70 L124 100 L56 100 Z" fill="none" stroke="#94a3b8" stroke-width="1.5" />
            <rect x="56" y="100" width="68" height="115" rx="6" fill="none" stroke="#94a3b8" stroke-width="1.5" />
            <path d="M56 215 L124 215 L132 245 C120 257 60 257 48 245 Z" fill="none" stroke="#94a3b8" stroke-width="1.5" />
            <rect x="18" y="75" width="14" height="36" rx="4" fill="#475569" />
            <rect x="148" y="75" width="14" height="36" rx="4" fill="#475569" />
            <rect x="18" y="210" width="14" height="36" rx="4" fill="#475569" />
            <rect x="148" y="210" width="14" height="36" rx="4" fill="#475569" />
            <rect x="20" y="116" width="10" height="6" rx="2" fill="#475569" />
            <rect x="150" y="116" width="10" height="6" rx="2" fill="#475569" />
            <text x="90" y="15" text-anchor="middle" font-size="9" fill="#64748b" font-weight="bold">FRENTE</text>
            <text x="90" y="314" text-anchor="middle" font-size="9" fill="#64748b" font-weight="bold">TRASEIRA</text>
          </svg>
        </div>
        <div class="border border-slate-300 rounded-lg p-3">
          <h3 class="text-xs font-bold uppercase text-slate-700 mb-2">Observações</h3>
          <div class="space-y-4 pt-1">
            <div v-for="n in 6" :key="n" class="border-b border-slate-300"></div>
          </div>
        </div>
      </div>

      <!-- Assinaturas -->
      <PrintSignatures
        left-label="Responsável (Oficina)"
        right-label="Cliente / Responsável"
        :right-name="cliente ? getClienteNome(cliente as any) : undefined"
      />

      <PrintFooter />
    </div>
  </Teleport>
</template>
