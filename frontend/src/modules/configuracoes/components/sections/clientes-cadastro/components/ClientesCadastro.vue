<script setup lang="ts">
import { reactive, watch } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'

const configStore = useConfiguracoesStore()
const {
  exigirCpfPf,
  exigirCnpjPj,
  exigirCelular,
  exigirRgPf,
  exigirIePj,
  exigirEmail,
  exigirEndereco,
  tipoPessoaPadrao,
  exibirGenero,
  exibirDataNascimento,
  bloquearFaturamentoInativo,
  oferecerReativacaoRapida,
  ativarLimiteCredito,
  bloquearVendaLimite,
} = storeToRefs(configStore)

const form = reactive({
  exigir_cpf_pf: exigirCpfPf.value,
  exigir_cnpj_pj: exigirCnpjPj.value,
  exigir_celular: exigirCelular.value,
  exigir_rg_pf: exigirRgPf.value,
  exigir_ie_pj: exigirIePj.value,
  exigir_email: exigirEmail.value,
  exigir_endereco: exigirEndereco.value,
  tipo_pessoa_padrao: tipoPessoaPadrao.value as 'PF' | 'PJ',
  exibir_genero: exibirGenero.value,
  exibir_data_nascimento: exibirDataNascimento.value,
  bloquear_faturamento_inativo: bloquearFaturamentoInativo.value,
  oferecer_reativacao_rapida: oferecerReativacaoRapida.value,
  ativar_limite_credito: ativarLimiteCredito.value,
  bloquear_venda_limite: bloquearVendaLimite.value,
})

// Sincroniza quando o store carrega os dados da API
watch(() => configStore.configClientes, () => {
  form.exigir_cpf_pf = exigirCpfPf.value
  form.exigir_cnpj_pj = exigirCnpjPj.value
  form.exigir_celular = exigirCelular.value
  form.exigir_rg_pf = exigirRgPf.value
  form.exigir_ie_pj = exigirIePj.value
  form.exigir_email = exigirEmail.value
  form.exigir_endereco = exigirEndereco.value
  form.tipo_pessoa_padrao = tipoPessoaPadrao.value as 'PF' | 'PJ'
  form.exibir_genero = exibirGenero.value
  form.exibir_data_nascimento = exibirDataNascimento.value
  form.bloquear_faturamento_inativo = bloquearFaturamentoInativo.value
  form.oferecer_reativacao_rapida = oferecerReativacaoRapida.value
  form.ativar_limite_credito = ativarLimiteCredito.value
  form.bloquear_venda_limite = bloquearVendaLimite.value
})

defineExpose({ form })
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Clientes e Cadastro</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Configure os campos, comportamentos e regras do cadastro de clientes</p>
    </div>

    <!-- Campos Obrigatórios -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">Campos Obrigatórios</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir CPF no cadastro de Pessoa Física</p>
          <p class="text-xs text-zinc-500 mt-0.5">CPF se torna obrigatório ao cadastrar um cliente PF</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exigir_cpf_pf ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exigir_cpf_pf = !form.exigir_cpf_pf"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exigir_cpf_pf ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir CNPJ no cadastro de Pessoa Jurídica</p>
          <p class="text-xs text-zinc-500 mt-0.5">CNPJ se torna obrigatório ao cadastrar um cliente PJ</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exigir_cnpj_pj ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exigir_cnpj_pj = !form.exigir_cnpj_pj"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exigir_cnpj_pj ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir Celular no cadastro</p>
          <p class="text-xs text-zinc-500 mt-0.5">Celular/WhatsApp se torna obrigatório para todos os clientes</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exigir_celular ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exigir_celular = !form.exigir_celular"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exigir_celular ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir RG no cadastro de Pessoa Física</p>
          <p class="text-xs text-zinc-500 mt-0.5">RG se torna obrigatório ao cadastrar um cliente PF</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exigir_rg_pf ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exigir_rg_pf = !form.exigir_rg_pf"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exigir_rg_pf ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir Inscrição Estadual no cadastro de Pessoa Jurídica</p>
          <p class="text-xs text-zinc-500 mt-0.5">IE se torna obrigatória ao cadastrar um cliente PJ</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exigir_ie_pj ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exigir_ie_pj = !form.exigir_ie_pj"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exigir_ie_pj ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>p

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir e-mail no cadastro</p>
          <p class="text-xs text-zinc-500 mt-0.5">E-mail se torna obrigatório para todos os clientes</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exigir_email ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exigir_email = !form.exigir_email"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exigir_email ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exigir endereço no cadastro</p>
          <p class="text-xs text-zinc-500 mt-0.5">Pelo menos um endereço deve ser informado</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exigir_endereco ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exigir_endereco = !form.exigir_endereco"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exigir_endereco ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>

    <!-- Exibição do Formulário -->
    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Exibição do Formulário</p>

      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-medium text-zinc-600">Tipo de pessoa padrão ao criar cliente</label>
        <div class="relative">
          <select
            v-model="form.tipo_pessoa_padrao"
            class="w-full appearance-none border border-zinc-200 rounded-lg px-3 py-2.5 bg-zinc-50 text-sm text-zinc-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          >
            <option value="PF">Pessoa Física (PF)</option>
            <option value="PJ">Pessoa Jurídica (PJ)</option>
          </select>
          <ChevronDown :size="14" class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none" />
        </div>
      </div>

      <div class="flex items-center justify-between py-3 border-t border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exibir campo Gênero</p>
          <p class="text-xs text-zinc-500 mt-0.5">Mostra o campo de gênero no formulário de PF</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exibir_genero ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exibir_genero = !form.exibir_genero"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exibir_genero ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-t border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Exibir campo Data de Nascimento</p>
          <p class="text-xs text-zinc-500 mt-0.5">Mostra o campo de data de nascimento no formulário de PF</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.exibir_data_nascimento ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.exibir_data_nascimento = !form.exibir_data_nascimento"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.exibir_data_nascimento ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>

    <!-- Comportamento -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">Comportamento</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Bloquear faturamento para clientes inativos</p>
          <p class="text-xs text-zinc-500 mt-0.5">Impede vendas e OS para clientes com cadastro inativo</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.bloquear_faturamento_inativo ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.bloquear_faturamento_inativo = !form.bloquear_faturamento_inativo"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.bloquear_faturamento_inativo ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Oferecer reativação rápida ao tentar vender para inativo</p>
          <p class="text-xs text-zinc-500 mt-0.5">Exibe botão de reativação direto na tela de venda</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.oferecer_reativacao_rapida ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.oferecer_reativacao_rapida = !form.oferecer_reativacao_rapida"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.oferecer_reativacao_rapida ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>

    <!-- Controle Financeiro -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">Controle Financeiro</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Ativar limite de crédito por cliente</p>
          <p class="text-xs text-zinc-500 mt-0.5">Permite definir um valor máximo de crédito por cliente</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.ativar_limite_credito ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.ativar_limite_credito = !form.ativar_limite_credito"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.ativar_limite_credito ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Bloquear venda ao atingir limite de crédito</p>
          <p class="text-xs text-zinc-500 mt-0.5">Impede novas vendas quando o limite do cliente for atingido</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.bloquear_venda_limite ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.bloquear_venda_limite = !form.bloquear_venda_limite"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.bloquear_venda_limite ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>
  </div>
</template>
