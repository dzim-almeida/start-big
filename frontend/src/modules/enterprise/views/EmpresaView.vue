<script setup lang="ts">
import EmpresaForm from '../components/EmpresaForm.vue';
</script>

<template>
  <div class="h-full flex flex-col p-6 overflow-y-auto">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
       <div>
         <h1 class="text-2xl font-bold text-gray-800">Minha Empresa</h1>
         <p class="text-sm text-gray-500 mt-1">Gerencie os dados da sua organização</p>
       </div>
    </div>

    <!-- Content -->
    <div class="flex-1">
       <EmpresaForm />
    </div>
  </div>
</template>
