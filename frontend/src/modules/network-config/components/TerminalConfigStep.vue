<script setup lang="ts">
import { useForm } from 'vee-validate'
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue'
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue'
import { useNetworkConfig } from '../composables/useNetworkConfig'
import { terminalConfigTypedSchema } from '../schemas/network-config.schema'

const { configurarTerminal, voltar } = useNetworkConfig()

const { defineField, handleSubmit, errors } = useForm({
  validationSchema: terminalConfigTypedSchema,
  initialValues: {
    serverIp: '',
    serverPort: 8080,
  },
})

const [serverIp, serverIpAttrs] = defineField('serverIp')
const [serverPort, serverPortAttrs] = defineField('serverPort')

const onSubmit = handleSubmit(async (values) => {
  await configurarTerminal(values.serverIp, values.serverPort)
})
</script>

<template>
  <div class="space-y-5">
    <div>
      <h2 class="text-lg font-bold text-gray-800">Conectar ao Servidor</h2>
      <p class="text-sm text-gray-500 mt-1">
        Informe o endereço do servidor na rede local.
      </p>
    </div>

    <!-- Tip card -->
    <div class="flex items-start gap-2.5 p-3 bg-amber-50 border border-amber-100 rounded-xl">
      <svg class="w-5 h-5 text-amber-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
      <p class="text-xs text-amber-700">
        Verifique o IP e a porta nas configurações do ERP no computador que está atuando como servidor.
      </p>
    </div>

    <form class="space-y-4" @submit.prevent="onSubmit">
      <BaseInput
        v-model="serverIp"
        v-bind="serverIpAttrs"
        label="IP do Servidor"
        placeholder="Ex: 192.168.1.100"
        :error="errors.serverIp"
      />

      <BaseInput
        v-model="serverPort"
        v-bind="serverPortAttrs"
        type="number"
        label="Porta"
        placeholder="Ex: 8080"
        :error="errors.serverPort"
      />

      <div class="flex gap-3 pt-2">
        <BaseButton variant="secondary" type="button" @click="voltar">
          Voltar
        </BaseButton>
        <BaseButton class="flex-1" type="submit">
          Conectar
        </BaseButton>
      </div>
    </form>
  </div>
</template>
