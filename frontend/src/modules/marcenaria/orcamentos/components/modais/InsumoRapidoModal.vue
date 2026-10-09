<script setup lang="ts">
/**
 * @component InsumoRapidoModal
 * @description Cadastro rápido de insumo sem sair do orçamento (Spec 06B
 * D31-D35; SPEC-00 T4).
 *
 * Nome, código (sugerido "INS-…", editável), unidade, custo de compra, preço
 * de venda (vazio = igual ao custo) e "Sofre perda". Respeita as regras do
 * cadastro de produto da loja (categoria e código de barras obrigatórios).
 * Ao salvar, o produto entra no móvel na hora.
 */
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { createProduto } from '@/modules/products/inventory/services/product.service';
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';
import { UNIDADE_PRODUTO_OPTIONS } from '@/shared/constants/fiscal.constants';
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store';

import { insumoRapidoSchema, insumoRapidoVazio, paraProdutoCreate, type InsumoRapidoForm } from '../../schemas/insumoRapido.schema';
import { campoDoErro, mensagemDoErro } from '../../utils/erros';

const props = defineProps<{
  isOpen: boolean;
  /** O que o usuário digitou na busca (vira o nome sugerido). */
  nomeInicial: string;
}>();

const emit = defineEmits<{ close: []; criado: [produto: ProdutoRead] }>();

// Regras do cadastro de produto da loja (D34).
const { exigirCategoria, exigirCodigoBarras, unidadeMedidaPadrao } = storeToRefs(useConfiguracoesStore());

const form = ref<InsumoRapidoForm>(insumoRapidoVazio('', 'UN'));
const erros = ref<Record<string, string>>({});
const erroGeral = ref('');
const gravando = ref(false);
const tentouSalvar = ref(false);                         // só mostra erro depois do primeiro "Salvar"

// Cada abertura começa com o nome da busca e um código novo (`immediate`: também se já nascer aberto).
watch(() => props.isOpen, (aberto) => {
  if (!aberto) return;
  form.value = insumoRapidoVazio(props.nomeInicial, unidadeMedidaPadrao.value);
  erros.value = {};
  erroGeral.value = '';
  tentouSalvar.value = false;
}, { immediate: true });

const schema = computed(() => insumoRapidoSchema({ categoria: exigirCategoria.value, codigoBarras: exigirCodigoBarras.value }));

/** Valida e devolve os erros por campo (mesmo formato dos outros formulários). */
function validar(): boolean {
  const resultado = schema.value.safeParse(form.value);
  if (resultado.success) {
    erros.value = {};
    return true;
  }
  erros.value = Object.fromEntries(resultado.error.issues.map((issue) => [String(issue.path[0]), issue.message]));
  return false;
}
watch(form, () => { if (tentouSalvar.value) validar(); }, { deep: true });

/** Preço de venda: o campo de dinheiro dá 0 quando vazio; 0 aqui = "não informado". */
const precoVenda = computed({
  get: () => form.value.preco_venda_reais ?? 0,
  set: (reais: number | null | undefined) => { form.value.preco_venda_reais = reais ? reais : null; },
});

async function salvar() {
  tentouSalvar.value = true;
  erroGeral.value = '';
  if (!validar()) return;
  gravando.value = true;
  try {
    const produto = await createProduto(paraProdutoCreate(form.value));
    emit('criado', produto);                              // o editor põe no móvel
    emit('close');
  } catch (erro) {
    // Código repetido (409 com campo "codigo_produto"): erro no campo (D32).
    const campo = campoDoErro(erro);
    if (campo === 'codigo_produto') erros.value = { ...erros.value, codigo: mensagemDoErro(erro) };
    else if (campo === 'codigo_barras') erros.value = { ...erros.value, codigo_barras: mensagemDoErro(erro) };
    else erroGeral.value = mensagemDoErro(erro, 'Não foi possível cadastrar o insumo.');
  } finally {
    gravando.value = false;
  }
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Cadastrar insumo novo" subtitle="O cadastro completo (fotos, fiscal, fornecedor) fica na tela de Produtos." size="md" overlay @close="emit('close')">
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div class="md:col-span-2">
        <BaseInput v-model="form.nome" label="Nome" required :error="erros.nome" />
      </div>
      <BaseInput v-model="form.codigo" label="Código" required :error="erros.codigo" />
      <BaseSelect v-model="form.unidade" label="Unidade" required :options="UNIDADE_PRODUTO_OPTIONS" :error="erros.unidade" />
      <MoneyInput v-model="form.custo_reais" label="Custo de compra" required :error="erros.custo_reais" />
      <div>
        <MoneyInput v-model="precoVenda" label="Preço de venda" :error="erros.preco_venda_reais" />
        <p class="mt-1 text-[11px] text-zinc-400">
          Se a loja também vende este item no balcão, informe o preço. Sem ele, o preço de venda fica igual ao custo.
        </p>
      </div>
      <BaseInput v-if="exigirCategoria" v-model="form.categoria" label="Categoria" required :error="erros.categoria" />
      <BaseInput v-if="exigirCodigoBarras" v-model="form.codigo_barras" label="Código de barras" required :error="erros.codigo_barras" />
      <div class="md:col-span-2">
        <BaseCheckbox v-model="form.sofre_perda" label="Sofre perda no orçamento (chapas, fitas)" />
      </div>
    </div>
    <p v-if="erroGeral" class="mt-3 text-sm text-red-600" role="alert">{{ erroGeral }}</p>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton variant="primary" :is-loading="gravando" data-testid="salvar-insumo-rapido" @click="salvar">Cadastrar e incluir</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
