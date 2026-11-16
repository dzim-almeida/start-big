<script setup lang="ts">
/**
 * @fileoverview Destinatário da etiqueta de volume, editável na hora.
 *
 * Mudar aqui NÃO altera o cadastro do cliente: é o endereço de entrega desta
 * remessa (o cliente mora num lugar, a obra é em outro). O DANFE Simplificado
 * não usa estes campos — sai com o destinatário da nota.
 */
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import type { EnderecoEnvio, ParteEnvio } from '@/shared/etiquetas/envio';

const destinatario = defineModel<ParteEnvio>({ required: true });

function endereco(campo: keyof EnderecoEnvio, valor: unknown) {
  const atual: EnderecoEnvio = destinatario.value.endereco ?? {
    logradouro: '', numero: '', complemento: null, bairro: '', cidade: '', uf: '', cep: '',
  };
  destinatario.value = { ...destinatario.value, endereco: { ...atual, [campo]: String(valor ?? '') } };
}

function parte(campo: 'nome' | 'documento' | 'telefone', valor: unknown) {
  destinatario.value = { ...destinatario.value, [campo]: String(valor ?? '') };
}
</script>

<template>
  <div class="space-y-4">
    <div class="grid grid-cols-1 sm:grid-cols-6 gap-4">
      <BaseInput
        class="sm:col-span-4"
        :model-value="destinatario.nome"
        label="Nome"
        @update:model-value="parte('nome', $event)"
      />
      <BaseInput
        class="sm:col-span-2"
        :model-value="destinatario.documento ?? ''"
        label="CPF/CNPJ"
        @update:model-value="parte('documento', $event)"
      />
      <BaseInput
        class="sm:col-span-4"
        :model-value="destinatario.endereco?.logradouro ?? ''"
        label="Rua"
        @update:model-value="endereco('logradouro', $event)"
      />
      <BaseInput
        class="sm:col-span-2"
        :model-value="destinatario.endereco?.numero ?? ''"
        label="Número"
        @update:model-value="endereco('numero', $event)"
      />
      <BaseInput
        class="sm:col-span-3"
        :model-value="destinatario.endereco?.complemento ?? ''"
        label="Complemento"
        @update:model-value="endereco('complemento', $event)"
      />
      <BaseInput
        class="sm:col-span-3"
        :model-value="destinatario.endereco?.bairro ?? ''"
        label="Bairro"
        @update:model-value="endereco('bairro', $event)"
      />
      <BaseInput
        class="sm:col-span-3"
        :model-value="destinatario.endereco?.cidade ?? ''"
        label="Cidade"
        @update:model-value="endereco('cidade', $event)"
      />
      <BaseInput
        class="sm:col-span-1"
        :model-value="destinatario.endereco?.uf ?? ''"
        label="UF"
        @update:model-value="endereco('uf', String($event ?? '').toUpperCase().slice(0, 2))"
      />
      <BaseInput
        class="sm:col-span-2"
        :model-value="destinatario.endereco?.cep ?? ''"
        label="CEP"
        @update:model-value="endereco('cep', $event)"
      />
      <BaseInput
        class="sm:col-span-3"
        :model-value="destinatario.telefone ?? ''"
        label="Telefone"
        @update:model-value="parte('telefone', $event)"
      />
    </div>
    <p class="text-xs text-zinc-400">
      Alterar aqui muda só esta etiqueta — o cadastro do cliente continua como está.
    </p>
  </div>
</template>
