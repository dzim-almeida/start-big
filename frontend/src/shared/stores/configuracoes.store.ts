import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getConfiguracoesClientes } from '@/modules/configuracoes/services/configuracoes.service'
import type { ConfiguracaoClientesRead } from '@/modules/configuracoes/schemas/configuracoes.schema'

export const useConfiguracoesStore = defineStore('configuracoes', () => {
  const configClientes = ref<ConfiguracaoClientesRead | null>(null)

  async function carregarConfiguracoes() {
    try {
      configClientes.value = await getConfiguracoesClientes()
    } catch {
      // silencioso — usa os defaults do computed abaixo
    }
  }

  // Campos obrigatórios
  const exigirCpfPf = computed(() => configClientes.value?.exigir_cpf_pf ?? false)
  const exigirCnpjPj = computed(() => configClientes.value?.exigir_cnpj_pj ?? false)
  const exigirCelular = computed(() => configClientes.value?.exigir_celular ?? true)
  const exigirRgPf = computed(() => configClientes.value?.exigir_rg_pf ?? false)
  const exigirIePj = computed(() => configClientes.value?.exigir_ie_pj ?? false)
  const exigirEmail = computed(() => configClientes.value?.exigir_email ?? false)
  const exigirEndereco = computed(() => configClientes.value?.exigir_endereco ?? false)

  // Exibição do formulário
  const tipoPessoaPadrao = computed(() => configClientes.value?.tipo_pessoa_padrao ?? 'PF')
  const exibirGenero = computed(() => configClientes.value?.exibir_genero ?? true)
  const exibirDataNascimento = computed(() => configClientes.value?.exibir_data_nascimento ?? true)

  // Comportamento
  const bloquearFaturamentoInativo = computed(() => configClientes.value?.bloquear_faturamento_inativo ?? false)
  const oferecerReativacaoRapida = computed(() => configClientes.value?.oferecer_reativacao_rapida ?? false)

  // Controle financeiro
  const ativarLimiteCredito = computed(() => configClientes.value?.ativar_limite_credito ?? false)
  const bloquearVendaLimite = computed(() => configClientes.value?.bloquear_venda_limite ?? false)

  return {
    configClientes,
    carregarConfiguracoes,

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
  }
})
