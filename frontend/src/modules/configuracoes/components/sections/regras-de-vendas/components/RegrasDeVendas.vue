<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'

const configStore = useConfiguracoesStore()
const {
  permitirDesconto,
  descontoMaximoPercent,
  exigirClienteIdentificado,
  valorMinimoVenda,
  permitirParcelamento,
  parcelasMaximas,
  permitirVendaEstoqueZerado,
  controlarCaixa,
  exigirCaixaAberto,
  fechamentoCego,
  requerPinAbrirCaixa,
  usarFilaDoCaixa,
  usarEmbalagens,
  regraEmbalagemAvulsas,
  regraFaixasQuantidade,
  regraLevePague,
  regraConflito,
  regraOrdem,
  bloquearDescontoComRegra,
} = storeToRefs(configStore)

const NOMES_REGRA: Record<string, string> = {
  R1: 'Preço de fardo nas avulsas',
  R2: 'A partir de N unidades',
  R3: 'Leve X, pague Y',
}

function valoresDoStore() {
  return {
    vendas: {
      permitir_desconto: permitirDesconto.value,
      desconto_maximo_percent: descontoMaximoPercent.value,
      exigir_cliente_identificado: exigirClienteIdentificado.value,
      valor_minimo_venda_reais: (valorMinimoVenda.value / 100) as number,
      permitir_parcelamento: permitirParcelamento.value,
      parcelas_maximas: parcelasMaximas.value,
      controlar_caixa: controlarCaixa.value,
      exigir_caixa_aberto: exigirCaixaAberto.value,
      fechamento_cego: fechamentoCego.value,
      requer_pin_abrir_caixa: requerPinAbrirCaixa.value,
      usar_fila_do_caixa: usarFilaDoCaixa.value,
      regra_embalagem_avulsas: regraEmbalagemAvulsas.value,
      regra_faixas_quantidade: regraFaixasQuantidade.value,
      regra_leve_pague: regraLevePague.value,
      regra_conflito: regraConflito.value,
      regra_ordem: regraOrdem.value,
      bloquear_desconto_com_regra: bloquearDescontoComRegra.value,
    },
    estoque: {
      permitir_venda_estoque_zerado: permitirVendaEstoqueZerado.value,
    },
  }
}

const form = reactive(valoresDoStore())

function resetar() {
  Object.assign(form.vendas, valoresDoStore().vendas)
  Object.assign(form.estoque, valoresDoStore().estoque)
}

watch(() => configStore.configVendas, () => {
  Object.assign(form.vendas, valoresDoStore().vendas)
})

watch(() => configStore.configProdutos, () => {
  Object.assign(form.estoque, valoresDoStore().estoque)
})

const regrasLigadas = computed(
  () =>
    [form.vendas.regra_embalagem_avulsas, form.vendas.regra_faixas_quantidade, form.vendas.regra_leve_pague]
      .filter(Boolean).length,
)

const ordem = computed(() => form.vendas.regra_ordem.split(','))

function mover(i: number, passo: number) {
  const nova = [...ordem.value]
  ;[nova[i], nova[i + passo]] = [nova[i + passo], nova[i]]
  form.vendas.regra_ordem = nova.join(',')
}

const isDirty = computed(
  () => JSON.stringify({ vendas: { ...form.vendas }, estoque: { ...form.estoque } }) !== JSON.stringify(valoresDoStore()),
)

defineExpose({
  isDirty,
  resetar,
  get form() {
    return {
      vendas: {
        permitir_desconto: form.vendas.permitir_desconto,
        desconto_maximo_percent: form.vendas.desconto_maximo_percent,
        exigir_cliente_identificado: form.vendas.exigir_cliente_identificado,
        valor_minimo_venda: Math.round(form.vendas.valor_minimo_venda_reais * 100),
        permitir_parcelamento: form.vendas.permitir_parcelamento,
        parcelas_maximas: form.vendas.parcelas_maximas,
        controlar_caixa: form.vendas.controlar_caixa,
        exigir_caixa_aberto: form.vendas.exigir_caixa_aberto,
        fechamento_cego: form.vendas.fechamento_cego,
        requer_pin_abrir_caixa: form.vendas.requer_pin_abrir_caixa,
        usar_fila_do_caixa: form.vendas.usar_fila_do_caixa,
        regra_embalagem_avulsas: form.vendas.regra_embalagem_avulsas,
        regra_faixas_quantidade: form.vendas.regra_faixas_quantidade,
        regra_leve_pague: form.vendas.regra_leve_pague,
        regra_conflito: form.vendas.regra_conflito,
        regra_ordem: form.vendas.regra_ordem,
        bloquear_desconto_com_regra: form.vendas.bloquear_desconto_com_regra,
      },
      estoque: {
        permitir_venda_estoque_zerado: form.estoque.permitir_venda_estoque_zerado,
      },
    }
  },
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Regras de Vendas</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Defina as regras e limitações para o processo de vendas</p>
    </div>

    <!-- Descontos -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Descontos</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Permitir desconto em vendas</p>
          <p class="text-xs text-zinc-500 mt-0.5">Habilita o campo de desconto no carrinho</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.vendas.permitir_desconto ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.permitir_desconto = !form.vendas.permitir_desconto"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.permitir_desconto ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="py-3 border-b border-zinc-100">
        <label class="text-xs font-medium text-zinc-600">Desconto máximo permitido (%) — 0 = bloqueia todo desconto</label>
        <input
          v-model.number="form.vendas.desconto_maximo_percent"
          type="number"
          min="0"
          max="100"
          :disabled="!form.vendas.permitir_desconto"
          class="mt-1.5 w-full border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700 focus:outline-none focus:ring-2 focus:ring-brand-primary/30 disabled:opacity-40 disabled:cursor-not-allowed"
        />
      </div>
    </div>

    <!-- Regras de preço por quantidade (plano de embalagens, §6.1). "Quem dita
         a regra de venda é quem está vendendo": o sistema oferece as três, o
         dono liga as que usa. Todas nascem desligadas. O cadastro de cada regra
         fica no produto; aqui só se liga e se escolhe o que vale no conflito. -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Preço por quantidade</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Avulsas que completam um fardo cobram o preço do fardo</p>
          <p class="text-xs text-zinc-500 mt-0.5">17 latas com fardo de 15 = 1 fardo + 2 unidades. Marque "aplicar às avulsas" na embalagem do produto</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.vendas.regra_embalagem_avulsas ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.regra_embalagem_avulsas = !form.vendas.regra_embalagem_avulsas"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.regra_embalagem_avulsas ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <p
        v-if="form.vendas.regra_embalagem_avulsas && !usarEmbalagens"
        class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-2.5 mt-2"
      >
        Esta regra só vale com <strong class="font-semibold">Vender e receber em fardo, caixa ou pack</strong>
        ligado em Produtos e Estoque.
      </p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Preço "a partir de N unidades"</p>
          <p class="text-xs text-zinc-500 mt-0.5">Ex.: a partir de 6 un, R$ 3,80 cada. As faixas ficam no cadastro do produto</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.vendas.regra_faixas_quantidade ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.regra_faixas_quantidade = !form.vendas.regra_faixas_quantidade"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.regra_faixas_quantidade ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Leve X, pague Y</p>
          <p class="text-xs text-zinc-500 mt-0.5">Promoção com início e fim, cadastrada no produto. O item grátis sai como desconto</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.vendas.regra_leve_pague ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.regra_leve_pague = !form.vendas.regra_leve_pague"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.regra_leve_pague ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div v-if="regrasLigadas > 1" class="py-3 border-b border-zinc-100">
        <p class="text-sm font-medium text-zinc-800">Quando mais de uma regra serve</p>
        <p class="text-xs text-zinc-500 mt-0.5">As regras não somam: vale uma por produto</p>
        <div class="mt-2 flex flex-col gap-1.5">
          <label class="flex items-center gap-2 text-sm text-zinc-700 cursor-pointer">
            <input v-model="form.vendas.regra_conflito" type="radio" value="MENOR_PRECO" class="accent-brand-primary" />
            Cobrar o menor preço para o cliente
          </label>
          <label class="flex items-center gap-2 text-sm text-zinc-700 cursor-pointer">
            <input v-model="form.vendas.regra_conflito" type="radio" value="ORDEM" class="accent-brand-primary" />
            Seguir esta ordem
          </label>
        </div>
        <ol class="mt-2 flex flex-col gap-1">
          <li
            v-for="(regra, i) in ordem"
            :key="regra"
            class="flex items-center justify-between gap-2 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-sm text-zinc-700"
          >
            <span><span class="text-zinc-400 mr-1.5">{{ i + 1 }}.</span>{{ NOMES_REGRA[regra] }}</span>
            <span class="flex gap-1">
              <button
                type="button"
                class="px-1.5 text-zinc-500 hover:text-zinc-900 disabled:opacity-30"
                :disabled="i === 0"
                :aria-label="`Subir ${NOMES_REGRA[regra]}`"
                @click="mover(i, -1)"
              >↑</button>
              <button
                type="button"
                class="px-1.5 text-zinc-500 hover:text-zinc-900 disabled:opacity-30"
                :disabled="i === ordem.length - 1"
                :aria-label="`Descer ${NOMES_REGRA[regra]}`"
                @click="mover(i, 1)"
              >↓</button>
            </span>
          </li>
        </ol>
        <p class="text-xs text-zinc-500 mt-1.5">
          {{ form.vendas.regra_conflito === 'ORDEM'
            ? 'Vale a primeira da lista que servir.'
            : 'A ordem só desempata quando duas regras dão o mesmo preço.' }}
        </p>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Item com regra não aceita desconto manual</p>
          <p class="text-xs text-zinc-500 mt-0.5">O desconto do operador não vale em cima do preço da regra</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.vendas.bloquear_desconto_com_regra ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.bloquear_desconto_com_regra = !form.vendas.bloquear_desconto_com_regra"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.bloquear_desconto_com_regra ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>

    <!-- Controle de Caixa -->
    <!-- Chaves por EMPRESA, e não por segmento: quem tem balcão e recebe
         dinheiro na mão pode querer o controle, seja adega, mercado ou oficina.
         Todas nascem desligadas — a segurança é o padrão, não esconder a opção. -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Controle de Caixa</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Usar controle de caixa</p>
          <p class="text-xs text-zinc-500 mt-0.5">Abertura com troco, sangria, suprimento e fechamento conferido</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.vendas.controlar_caixa ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.controlar_caixa = !form.vendas.controlar_caixa"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.controlar_caixa ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir caixa aberto para vender</p>
          <p class="text-xs text-zinc-500 mt-0.5">Sem um turno aberto, a venda não é finalizada</p>
        </div>
        <button
          type="button"
          :disabled="!form.vendas.controlar_caixa"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 shrink-0', !form.vendas.controlar_caixa ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer', form.vendas.exigir_caixa_aberto ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.controlar_caixa && (form.vendas.exigir_caixa_aberto = !form.vendas.exigir_caixa_aberto)"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.exigir_caixa_aberto ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Fechamento às cegas</p>
          <p class="text-xs text-zinc-500 mt-0.5">O operador conta a gaveta sem ver o valor esperado</p>
        </div>
        <button
          type="button"
          :disabled="!form.vendas.controlar_caixa"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 shrink-0', !form.vendas.controlar_caixa ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer', form.vendas.fechamento_cego ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.controlar_caixa && (form.vendas.fechamento_cego = !form.vendas.fechamento_cego)"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.fechamento_cego ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <!-- Abrir o turno e declarar o troco inicial, e o troco inicial e a base
           contra a qual o fechamento vai acusar falta ou sobra. Quem declara a
           base sozinho escolhe, na pratica, o resultado da propria conferencia.
           Fechar NAO pede PIN: quem abriu precisa conseguir fechar, senao a
           gaveta fica aberta ate o dia seguinte. -->
      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir PIN para abrir o caixa</p>
          <p class="text-xs text-zinc-500 mt-0.5">Um supervisor libera a abertura; fechar não pede PIN</p>
        </div>
        <button
          type="button"
          :disabled="!form.vendas.controlar_caixa"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 shrink-0', !form.vendas.controlar_caixa ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer', form.vendas.requer_pin_abrir_caixa ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.controlar_caixa && (form.vendas.requer_pin_abrir_caixa = !form.vendas.requer_pin_abrir_caixa)"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.requer_pin_abrir_caixa ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <!-- Separada de "Usar controle de caixa" porque sao perguntas
           diferentes: uma e "esta loja controla a gaveta", a outra e "quem monta
           a venda e quem recebe sao pessoas diferentes". Numa loja de um PC so a
           segunda resposta e nao, e o botao seria um comando que nunca serve. -->
      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Fila do caixa</p>
          <p class="text-xs text-zinc-500 mt-0.5">O atendente monta a venda e entrega; o caixa recebe</p>
        </div>
        <button
          type="button"
          :disabled="!form.vendas.controlar_caixa"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 shrink-0', !form.vendas.controlar_caixa ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer', form.vendas.usar_fila_do_caixa ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.controlar_caixa && (form.vendas.usar_fila_do_caixa = !form.vendas.usar_fila_do_caixa)"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.usar_fila_do_caixa ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <!-- O PIN conferido e o mesmo de Seguranca. Sem ele cadastrado, a chave
           acima trava a abertura para quem nao e gerente — e sem caixa aberto a
           loja nao vende. Por isso o aviso e condicional, e nao nota de rodape. -->
      <p
        v-if="form.vendas.requer_pin_abrir_caixa"
        class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-2.5 mt-3"
      >
        Use o mesmo PIN de gerente cadastrado em
        <strong class="font-semibold">Segurança</strong>. Sem PIN cadastrado, quem não for
        gerente não conseguirá abrir o caixa.
      </p>

      <p class="text-xs text-zinc-500 mt-3">
        A exigência de PIN para sangria fica em
        <strong class="text-zinc-700">Segurança</strong>, junto das outras
        aprovações de gerente.
      </p>
    </div>

    <!-- Estoque e Clientes -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Estoque e Clientes</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Permitir venda sem estoque</p>
          <p class="text-xs text-zinc-500 mt-0.5">Vende mesmo quando o produto está zerado</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.estoque.permitir_venda_estoque_zerado ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.estoque.permitir_venda_estoque_zerado = !form.estoque.permitir_venda_estoque_zerado"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.estoque.permitir_venda_estoque_zerado ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir cliente identificado</p>
          <p class="text-xs text-zinc-500 mt-0.5">Toda venda deve ter um cliente vinculado</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.vendas.exigir_cliente_identificado ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.exigir_cliente_identificado = !form.vendas.exigir_cliente_identificado"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.exigir_cliente_identificado ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="py-3 border-b border-zinc-100">
        <label class="text-xs font-medium text-zinc-600">Valor mínimo de venda — 0 = sem mínimo</label>
        <input
          v-model.number="form.vendas.valor_minimo_venda_reais"
          type="number"
          min="0"
          step="0.01"
          placeholder="0,00"
          class="mt-1.5 w-full border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700 focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
        />
      </div>
    </div>

    <!-- Pagamentos -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Pagamentos</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Permitir parcelamento</p>
          <p class="text-xs text-zinc-500 mt-0.5">Habilita pagamentos parcelados nas vendas</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.vendas.permitir_parcelamento ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.vendas.permitir_parcelamento = !form.vendas.permitir_parcelamento"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.vendas.permitir_parcelamento ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="py-3 border-b border-zinc-100">
        <label class="text-xs font-medium text-zinc-600">Máximo de parcelas (1–48)</label>
        <input
          v-model.number="form.vendas.parcelas_maximas"
          type="number"
          min="1"
          max="48"
          :disabled="!form.vendas.permitir_parcelamento"
          class="mt-1.5 w-full border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700 focus:outline-none focus:ring-2 focus:ring-brand-primary/30 disabled:opacity-40 disabled:cursor-not-allowed"
        />
      </div>
    </div>
  </div>
</template>
