import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getConfiguracoesClientes, getConfiguracoesProdutos } from '@/modules/configuracoes/services/configuracoes.service'
import type { ConfiguracaoClientesRead, ConfiguracaoProdutosRead } from '@/modules/configuracoes/schemas/configuracoes.schema'

export const useConfiguracoesStore = defineStore('configuracoes', () => {
  const configClientes = ref<ConfiguracaoClientesRead | null>(null)
  const configProdutos = ref<ConfiguracaoProdutosRead | null>(null)

  async function carregarConfiguracoes() {
    try {
      const [clientes, produtos] = await Promise.all([
        getConfiguracoesClientes(),
        getConfiguracoesProdutos(),
      ])
      configClientes.value = clientes
      configProdutos.value = produtos
    } catch {
      // silencioso — usa os defaults dos computed abaixo
    }
  }

  // ── Clientes: campos obrigatórios ──
  const exigirCpfPf = computed(() => configClientes.value?.exigir_cpf_pf ?? false)
  const exigirCnpjPj = computed(() => configClientes.value?.exigir_cnpj_pj ?? false)
  const exigirCelular = computed(() => configClientes.value?.exigir_celular ?? true)
  const exigirRgPf = computed(() => configClientes.value?.exigir_rg_pf ?? false)
  const exigirIePj = computed(() => configClientes.value?.exigir_ie_pj ?? false)
  const exigirEmail = computed(() => configClientes.value?.exigir_email ?? false)
  const exigirEndereco = computed(() => configClientes.value?.exigir_endereco ?? false)

  // ── Clientes: exibição do formulário ──
  const tipoPessoaPadrao = computed(() => configClientes.value?.tipo_pessoa_padrao ?? 'PF')
  const exibirGenero = computed(() => configClientes.value?.exibir_genero ?? true)
  const exibirDataNascimento = computed(() => configClientes.value?.exibir_data_nascimento ?? true)

  // ── Clientes: comportamento ──
  const bloquearFaturamentoInativo = computed(() => configClientes.value?.bloquear_faturamento_inativo ?? false)
  const oferecerReativacaoRapida = computed(() => configClientes.value?.oferecer_reativacao_rapida ?? false)

  // ── Clientes: controle financeiro ──
  const ativarLimiteCredito = computed(() => configClientes.value?.ativar_limite_credito ?? false)
  const bloquearVendaLimite = computed(() => configClientes.value?.bloquear_venda_limite ?? false)

  // ── Produtos: campos obrigatórios no cadastro ──
  const exigirCodigoBarras = computed(() => configProdutos.value?.exigir_codigo_barras ?? false)
  const exigirCategoria = computed(() => configProdutos.value?.exigir_categoria ?? false)
  const exigirPrecoCusto = computed(() => configProdutos.value?.exigir_preco_custo ?? false)

  // ── Produtos: preços e exibição ──
  const margemLucroPadrao = computed(() => configProdutos.value?.margem_lucro_padrao ?? 0)
  const utilizarPrecoAtacado = computed(() => configProdutos.value?.utilizar_preco_atacado ?? true)

  // ── Produtos: controle de estoque ──
  const permitirVendaEstoqueZerado = computed(() => configProdutos.value?.permitir_venda_estoque_zerado ?? false)
  const quantidadeMinimaPadrao = computed(() => configProdutos.value?.quantidade_minima_padrao ?? 5)
  const unidadeMedidaPadrao = computed(() => configProdutos.value?.unidade_medida_padrao ?? 'UN')

  return {
    configClientes,
    configProdutos,
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

    exigirCodigoBarras,
    exigirCategoria,
    exigirPrecoCusto,

    margemLucroPadrao,
    utilizarPrecoAtacado,

    permitirVendaEstoqueZerado,
    quantidadeMinimaPadrao,
    unidadeMedidaPadrao,
  }
})
