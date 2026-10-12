<script setup lang="ts">
/**
 * @component DadosArquitetoSection
 * @description Dados do arquiteto / designer (marcenaria, Spec 09B D3).
 *
 * Nome, pessoa física (CPF) ou jurídica (CNPJ, com a consulta da Receita da
 * Spec 02), escritório, celular, telefone e e-mail. Endereço, dados bancários
 * e PIX (por onde o RT é pago) são as seções que todo fornecedor já tem.
 * Nenhum campo novo no banco: tudo existe na tabela de fornecedores.
 */
import { ref } from 'vue';
import { Ruler, Search } from 'lucide-vue-next';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import { ConsultaCnpjErro, buscarDadosCNPJ } from '@/shared/services/cnpj.service';
import { useToast } from '@/shared/composables/useToast';

import { useFornecedorForm } from '../../composables/useFornecedorForm';

defineProps<{ submitCount: number; disabled?: boolean }>();

const {
  nome, pessoa, cnpj, cpf, nome_fantasia, telefone, celular, email,
  logradouro, numero, bairro, cidade, estado, cep, errors,
} = useFornecedorForm();
const toast = useToast();

/** Máscaras de CPF e CNPJ enquanto digita (mesmas das outras seções). */
function digitarCpf(valor: string) {
  const d = valor.replace(/\D/g, '').slice(0, 11);
  cpf.value = d.replace(/^(\d{3})(\d)/, '$1.$2').replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3').replace(/\.(\d{3})(\d)/, '.$1-$2');
}
function digitarCnpj(valor: string) {
  const d = valor.replace(/\D/g, '').slice(0, 14);
  cnpj.value = d
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2');
}

// --- Consulta do CNPJ na Receita (Spec 02) -------------------------------------
const consultando = ref(false);

/** Preenche só o que está vazio: nunca apaga o que o usuário já digitou. */
async function consultarCnpj() {
  if ((cnpj.value ?? '').replace(/\D/g, '').length !== 14) {
    toast.error('Digite os 14 números do CNPJ para consultar.');
    return;
  }
  consultando.value = true;
  try {
    const dados = await buscarDadosCNPJ(cnpj.value);
    if (!nome.value) nome.value = dados.razao_social;
    if (!nome_fantasia.value) nome_fantasia.value = dados.nome_fantasia;
    if (!email.value) email.value = dados.email;
    // A Receita manda um número só: 11 dígitos é celular, 10 é fixo (as validações do cadastro).
    const fone = (dados.telefone ?? '').replace(/\D/g, '');
    if (fone.length === 11 && !celular.value) celular.value = fone;
    else if (fone.length === 10 && !telefone.value) telefone.value = fone;
    if (!logradouro.value) {
      logradouro.value = dados.logradouro;
      numero.value = dados.numero;
      bairro.value = dados.bairro;
      cidade.value = dados.cidade;
      estado.value = dados.estado;
      cep.value = dados.cep;
    }
    toast.success('Dados da Receita preenchidos.');
  } catch (erro) {
    // A Spec 02 separa "não existe" de "não deu para consultar agora".
    const naoEncontrado = erro instanceof ConsultaCnpjErro && erro.motivo === 'NAO_ENCONTRADO';
    toast.error(naoEncontrado ? 'CNPJ não encontrado na Receita.' : 'Consulta à Receita indisponível agora. Preencha à mão.');
  } finally {
    consultando.value = false;
  }
}
</script>

<template>
  <section>
    <div class="mb-6 flex items-center gap-3">
      <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-primary-light text-brand-primary">
        <LucideIcon :icon="Ruler" />
      </div>
      <h3 class="text-lg font-semibold text-zinc-800">Dados do Arquiteto / Designer</h3>
    </div>

    <div class="grid grid-cols-12 gap-4">
      <div class="col-span-12 md:col-span-7">
        <BaseInput v-model="nome" label="Nome" placeholder="Nome do arquiteto ou do escritório" :required="true" :error="submitCount > 0 ? errors.nome : ''" :disabled="disabled" />
      </div>

      <!-- Pessoa física ou jurídica -->
      <fieldset class="col-span-12 md:col-span-5" :disabled="disabled">
        <legend class="mb-2 text-sm font-medium text-zinc-700">Pessoa</legend>
        <div class="flex gap-4 text-sm">
          <label class="flex items-center gap-2"><input v-model="pessoa" type="radio" value="PJ" class="accent-brand-primary" data-testid="pessoa-pj" /> Jurídica (CNPJ)</label>
          <label class="flex items-center gap-2"><input v-model="pessoa" type="radio" value="PF" class="accent-brand-primary" data-testid="pessoa-pf" /> Física (CPF)</label>
        </div>
      </fieldset>

      <div v-if="pessoa === 'PF'" class="col-span-12 md:col-span-5">
        <BaseInput :model-value="cpf" label="CPF" placeholder="000.000.000-00" :required="true" :error="submitCount > 0 ? errors.cpf : ''" :disabled="disabled" @update:model-value="digitarCpf($event as string)" />
      </div>
      <div v-else class="col-span-12 flex items-end gap-2 md:col-span-6">
        <div class="flex-1">
          <BaseInput :model-value="cnpj" label="CNPJ" placeholder="00.000.000/0000-00" :required="true" :error="submitCount > 0 ? errors.cnpj : ''" :disabled="disabled" @update:model-value="digitarCnpj($event as string)" />
        </div>
        <BaseButton v-if="!disabled" type="button" variant="secondary" size="sm" :is-loading="consultando" @click="consultarCnpj">
          <Search :size="14" class="mr-1" /> Consultar
        </BaseButton>
      </div>

      <div class="col-span-12 md:col-span-6">
        <BaseInput v-model="nome_fantasia" label="Escritório" placeholder="Nome do escritório (se houver)" :disabled="disabled" />
      </div>
      <div class="col-span-12 md:col-span-4">
        <BaseInput v-model="celular" label="Celular" placeholder="(00) 00000-0000" mask="(##) #####-####" :error="submitCount > 0 ? errors.celular : ''" :disabled="disabled" />
      </div>
      <div class="col-span-12 md:col-span-4">
        <BaseInput v-model="telefone" label="Telefone" placeholder="(00) 0000-0000" mask="(##) ####-####" :error="submitCount > 0 ? errors.telefone : ''" :disabled="disabled" />
      </div>
      <div class="col-span-12 md:col-span-4">
        <BaseInput v-model="email" label="E-mail" type="email" placeholder="contato@escritorio.com" :error="submitCount > 0 ? errors.email : ''" :disabled="disabled" />
      </div>
    </div>
  </section>
</template>
