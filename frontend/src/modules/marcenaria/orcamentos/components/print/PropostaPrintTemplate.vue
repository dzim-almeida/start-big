<script setup lang="ts">
/**
 * @component PropostaPrintTemplate
 * @description A proposta comercial em A4 (Spec 07 §6.2): o documento que o
 * cliente recebe, assina e guarda. Sai pelo mesmo caminho de impressão de OS
 * e vendas; o "Salvar como PDF" do diálogo gera o arquivo (D1).
 *
 * Recebe SÓ `DadosProposta` (D3), nunca o detalhe: não há como imprimir
 * custo, margem, insumo, parâmetro ou preço por móvel, nem por engano, nem
 * para o master.
 *
 * Preto e branco (o `check:print-bw` barra cor): a faixa de status é texto
 * com borda, sem cor.
 */
import { computed } from 'vue';

import PrintCompanyHeader from '@/shared/components/print/a4/PrintCompanyHeader.vue';
import PrintFooter from '@/shared/components/print/a4/PrintFooter.vue';
import PrintSignatures from '@/shared/components/print/a4/PrintSignatures.vue';
import { formatCurrency } from '@/shared/utils/finance';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';

import type { DadosProposta } from '../../utils/dadosProposta';

const props = defineProps<{ dados: DadosProposta }>();

// Logo, CNPJ e contato da empresa (o mesmo cabeçalho das vias de OS e venda).
const { companyInfo } = useCompanyPrintInfo();

/** Linhas de contato do cliente, só as preenchidas, separadas por "·". */
const contatoCliente = computed(() =>
  [props.dados.cliente.telefone, props.dados.cliente.email, props.dados.cliente.endereco].filter(Boolean).join(' · '),
);
const projeto = computed(() =>
  [props.dados.projeto.nome, props.dados.projeto.enderecoObra].filter(Boolean).join(' · '),
);
</script>

<template>
  <!-- Teleport: o print-a4.css esconde tudo o que não for filho direto do body. -->
  <Teleport to="body">
    <div class="print-container proposta hidden print:block bg-white text-black font-sans leading-snug" data-testid="proposta">
      <PrintCompanyHeader
        :company="companyInfo"
        :document-label="dados.titulo"
        :document-number="`${dados.codigo} · v${dados.versao}`"
        date-label="Emitida em"
        :date-value="dados.emitidaEm"
      />

      <!-- Proposta aprovada (08B D25): quando e qual OS. -->
      <p v-if="dados.aprovacaoTexto" class="mb-3 text-xs font-bold uppercase tracking-wider" data-testid="proposta-aprovacao">
        {{ dados.aprovacaoTexto }}
      </p>

      <!-- Faixa de status (D6): texto e borda, sem cor. -->
      <p v-if="dados.faixa" class="proposta-faixa mb-4 border-2 border-neutral-900 px-3 py-1.5 text-center text-sm font-black uppercase tracking-wider" data-testid="proposta-faixa">
        {{ dados.faixa }}
      </p>

      <!-- Cliente, projeto e consultor -->
      <section class="mb-4 grid grid-cols-[90px_1fr] gap-x-3 gap-y-1 border border-neutral-300 rounded-lg p-3 text-xs">
        <span class="font-bold uppercase text-neutral-600">Cliente</span>
        <span>
          <strong class="text-sm">{{ dados.cliente.nome || '—' }}</strong>
          <template v-if="dados.cliente.documento"> · {{ dados.cliente.documento }}</template>
          <span v-if="contatoCliente" class="block text-neutral-700">{{ contatoCliente }}</span>
        </span>
        <span class="font-bold uppercase text-neutral-600">Projeto</span>
        <span>{{ projeto || '—' }}</span>
        <template v-if="dados.vendedor">
          <span class="font-bold uppercase text-neutral-600">Consultor</span>
          <span>{{ dados.vendedor.nome }}<template v-if="dados.vendedor.telefone"> · {{ dados.vendedor.telefone }}</template></span>
        </template>
      </section>

      <!-- Ambientes e móveis: total por ambiente, nunca preço por móvel (T5) -->
      <section v-if="dados.ambientes.length" class="flex flex-col gap-4">
        <article v-for="ambiente in dados.ambientes" :key="ambiente.nome" class="ambiente">
          <div class="ambiente-titulo flex items-baseline justify-between border-b-2 border-neutral-900 pb-1">
            <h2 class="text-sm font-black uppercase tracking-wide">{{ ambiente.nome }}</h2>
            <span class="text-sm font-black tabular-nums">{{ formatCurrency(ambiente.totalCentavos) }}</span>
          </div>
          <div v-for="(movel, indice) in ambiente.moveis" :key="indice" class="movel border-b border-neutral-200 py-2 text-xs">
            <p class="flex justify-between gap-3">
              <strong class="text-[13px]">{{ movel.nome }}</strong>
              <!-- Quantidade só em destaque quando passa de 1 (D14). -->
              <strong v-if="movel.quantidade > 1" class="tabular-nums">{{ movel.quantidade }} un.</strong>
            </p>
            <p v-if="movel.descricao" class="text-neutral-700">{{ movel.descricao }}</p>
            <p v-if="movel.medidas" class="text-neutral-600">{{ movel.medidas }}</p>
          </div>
        </article>
      </section>
      <p v-else class="text-sm text-neutral-600">Nenhum móvel incluído.</p>

      <!-- Valores, condições e aceite: um bloco só, nunca dividido (D13) -->
      <section class="fechamento mt-5">
        <dl class="ml-auto w-72 text-xs">
          <div v-if="dados.instalacaoCentavos != null" class="flex justify-between py-0.5">
            <dt>Instalação e montagem</dt>
            <dd class="tabular-nums">{{ formatCurrency(dados.instalacaoCentavos) }}</dd>
          </div>
          <div class="flex justify-between py-0.5">
            <dt>Subtotal</dt>
            <dd class="tabular-nums">{{ formatCurrency(dados.subtotalCentavos) }}</dd>
          </div>
          <div v-if="dados.desconto" class="flex justify-between py-0.5">
            <dt>Desconto<template v-if="dados.desconto.percentualTexto"> ({{ dados.desconto.percentualTexto }})</template></dt>
            <dd class="tabular-nums">− {{ formatCurrency(dados.desconto.centavos) }}</dd>
          </div>
          <div class="mt-1 flex justify-between border-t-2 border-neutral-900 pt-1 text-sm font-black">
            <dt>TOTAL</dt>
            <dd class="tabular-nums" data-testid="proposta-total">{{ formatCurrency(dados.totalCentavos) }}</dd>
          </div>
        </dl>

        <div class="mt-4 text-xs">
          <p class="mb-1 text-[10px] font-bold uppercase tracking-widest text-neutral-600">Condições</p>
          <!-- Aprovada: o sinal já combinado, recebido ou a receber (08B D25). -->
          <p v-if="dados.sinal && dados.sinalSituacao">
            Sinal: {{ formatCurrency(dados.sinal.centavos) }}<template v-if="dados.sinal.percentualTexto"> ({{ dados.sinal.percentualTexto }})</template>
            — {{ dados.sinalSituacao }} · Saldo: {{ formatCurrency(dados.saldoCentavos) }}
          </p>
          <p v-else-if="dados.sinal">
            Sinal na aprovação: {{ formatCurrency(dados.sinal.centavos) }}<template v-if="dados.sinal.percentualTexto"> ({{ dados.sinal.percentualTexto }})</template>
            · Saldo: {{ formatCurrency(dados.saldoCentavos) }}
          </p>
          <p v-else>Total a pagar: {{ formatCurrency(dados.totalCentavos) }}</p>
          <p>Prazo de entrega: {{ dados.prazoEntregaDias }} dias corridos após a aprovação</p>
          <p v-if="dados.modo === 'proposta'">Validade: {{ dados.validadeTexto }}</p>
        </div>

        <!-- Observações com as quebras de linha digitadas (D15) -->
        <div v-if="dados.observacoes" class="mt-3 text-xs">
          <p class="mb-1 text-[10px] font-bold uppercase tracking-widest text-neutral-600">Observações</p>
          <p class="whitespace-pre-line" data-testid="proposta-observacoes">{{ dados.observacoes }}</p>
        </div>

        <!-- Aceite (D12) -->
        <p class="mt-6 text-xs">Declaro estar de acordo com esta proposta e autorizo a execução.</p>
        <PrintSignatures
          :left-label="dados.cliente.nome ? `Cliente: ${dados.cliente.nome}` : 'Cliente'"
          :right-label="companyInfo.nome"
          :right-name="dados.vendedor?.nome"
        />
        <p class="mt-4 text-xs">Data: ___/___/______</p>
      </section>

      <PrintFooter />
    </div>
  </Teleport>
</template>

<style>
/* Quebras de página (D13). Global como o print-a4.css, mas restrito a .proposta:
   as vias de OS e venda não são tocadas. */
@media print {
  .proposta .movel { break-inside: avoid; }                  /* móvel nunca dividido */
  .proposta .ambiente-titulo { break-after: avoid; }         /* título não fica sozinho no fim */
  .proposta .fechamento { break-inside: avoid; }             /* valores + condições + aceite juntos */
}
</style>
