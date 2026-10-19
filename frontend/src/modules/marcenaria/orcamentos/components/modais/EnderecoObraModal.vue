<script setup lang="ts">
/**
 * @component EnderecoObraModal
 * @description Endereço da obra em partes (remodelação item 2): CEP, rua,
 * número, complemento, bairro, cidade e UF. O CEP completo busca o resto
 * sozinho (ViaCEP, a mesma busca do cadastro). Ao confirmar, devolve o
 * endereço já montado num texto só (ver `montarEnderecoObra`).
 */
import { computed, reactive, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { useCepQuery } from '@/shared/composables/useCepLookup';
import { ESTADOS_BRASILEIROS } from '@/shared/constants/locations.constants';

import { LIMITE_ENDERECO_OBRA, camposVazios, montarEnderecoObra } from '../../utils/enderecoObra';

// `isOpen`: o modal está aberto? Quem abre e fecha é a tela de fora.
const props = defineProps<{ isOpen: boolean }>();
// `close`: fechou sem salvar. `confirmar`: devolve o endereço pronto em texto.
const emit = defineEmits<{ close: []; confirmar: [endereco: string] }>();

// Os campos do formulário. `reactive` faz a tela atualizar quando um campo muda.
const campos = reactive(camposVazios());

// Toda vez que o modal ABRE, os campos começam vazios (não sobra o endereço da última vez).
watch(() => props.isOpen, (aberto) => {
  if (aberto) Object.assign(campos, camposVazios());
});

// --- Busca do CEP ------------------------------------------------------------
// `useCepQuery` precisa de uma "ref"; este `computed` entrega o CEP digitado.
const cep = computed(() => campos.cep);
// Quando o CEP tem 8 dígitos, a busca roda sozinha e `dadosCep` recebe o resultado.
const { data: dadosCep, isLoading: buscandoCep, isError: cepNaoEncontrado } = useCepQuery(cep);

// Chegou o resultado do CEP: preenche rua, bairro, cidade e UF.
// (Número e complemento a busca não sabe; ficam com o usuário.)
watch(dadosCep, (dados) => {
  if (!dados) return;
  campos.logradouro = dados.logradouro || campos.logradouro;
  campos.bairro = dados.bairro || campos.bairro;
  campos.cidade = dados.localidade || campos.cidade;
  campos.estado = dados.uf || campos.estado;
});

// O BaseSelect devolve `string | number | undefined`; aqui a UF é sempre texto.
const uf = computed({
  get: () => campos.estado || undefined,
  set: (valor: string | number | undefined) => { campos.estado = valor == null ? '' : String(valor); },
});

// --- Validação -----------------------------------------------------------------
// Tentou confirmar? Só depois disso os erros aparecem (não grita antes de a pessoa digitar).
const tentouConfirmar = ref(false);
watch(() => props.isOpen, () => { tentouConfirmar.value = false; });

// O texto final, já montado, para mostrar a prévia e para conferir o tamanho.
const enderecoMontado = computed(() => montarEnderecoObra(campos));

// Rua é o mínimo para um endereço de obra fazer sentido.
const erroLogradouro = computed(() => (campos.logradouro.trim() ? '' : 'Informe a rua (logradouro).'));
// O banco aceita até 255 caracteres; avisa antes de o servidor recusar.
const erroTamanho = computed(() =>
  enderecoMontado.value.length > LIMITE_ENDERECO_OBRA
    ? `O endereço passou de ${LIMITE_ENDERECO_OBRA} caracteres. Encurte o complemento ou a rua.`
    : '',
);

function confirmar() {
  tentouConfirmar.value = true;
  if (erroLogradouro.value || erroTamanho.value) return;   // tem erro: fica no modal
  emit('confirmar', enderecoMontado.value);
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Endereço da obra"
    subtitle="Onde os móveis serão instalados. Pelo CEP, o resto vem sozinho."
    size="md"
    @close="emit('close')"
  >
    <div class="grid grid-cols-6 gap-4">
      <!-- CEP: a máscara "#####-###" põe o traço sozinha -->
      <div class="col-span-6 sm:col-span-2">
        <BaseInput v-model="campos.cep" label="CEP" placeholder="00000-000" mask="#####-###" inputmode="numeric" data-testid="obra-cep" />
        <p v-if="buscandoCep" class="mt-1 text-xs text-zinc-500">Buscando o CEP…</p>
        <p v-else-if="cepNaoEncontrado" class="mt-1 text-xs text-amber-700">CEP não encontrado. Preencha à mão.</p>
      </div>
      <div class="col-span-6 sm:col-span-4">
        <BaseInput
          v-model="campos.logradouro"
          label="Rua"
          placeholder="Rua, Avenida..."
          required
          :error="tentouConfirmar ? erroLogradouro : ''"
          data-testid="obra-logradouro"
        />
      </div>
      <div class="col-span-2">
        <BaseInput v-model="campos.numero" label="Número" placeholder="Nº" data-testid="obra-numero" />
      </div>
      <div class="col-span-4">
        <BaseInput v-model="campos.complemento" label="Complemento" placeholder="Apto, bloco, sala..." data-testid="obra-complemento" />
      </div>
      <div class="col-span-6 sm:col-span-2">
        <BaseInput v-model="campos.bairro" label="Bairro" placeholder="Bairro" data-testid="obra-bairro" />
      </div>
      <div class="col-span-4 sm:col-span-3">
        <BaseInput v-model="campos.cidade" label="Cidade" placeholder="Cidade" data-testid="obra-cidade" />
      </div>
      <div class="col-span-2 sm:col-span-1">
        <BaseSelect v-model="uf" label="UF" placeholder="UF" :options="ESTADOS_BRASILEIROS" />
      </div>
    </div>

    <!-- Prévia: exatamente o texto que vai para o orçamento e para a proposta -->
    <div v-if="enderecoMontado" class="mt-5 rounded-lg bg-zinc-50 px-3 py-2 text-sm text-zinc-700" data-testid="obra-previa">
      <span class="block text-xs font-medium text-zinc-500">Vai ficar assim:</span>
      {{ enderecoMontado }}
    </div>
    <p v-if="tentouConfirmar && erroTamanho" class="mt-2 text-xs text-red-600">{{ erroTamanho }}</p>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton variant="primary" data-testid="obra-confirmar" @click="confirmar">Usar este endereço</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
