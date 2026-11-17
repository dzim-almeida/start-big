<!--
  FIXTURE do cenário 10 (revisão de código). NÃO faz parte da aplicação.
  ARQUIVO: ProdutoLista.vue
  DESCRIÇÃO: lista de produtos com busca.
-->
<script setup lang="ts">
import { ref, onMounted } from 'vue'; // ref = valor reativo; onMounted = roda quando a tela abre
import axios from 'axios'; // biblioteca para chamar a API

// Tipo de um produto como a tela usa
interface Produto {
  id: number;
  nome: string;
  preco_venda: number;
}

const produtos = ref<Produto[]>([]); // lista mostrada na tela
const busca = ref(''); // texto digitado no campo de busca
const carregando = ref(false); // true enquanto espera a resposta da API

// Busca os produtos na API, enviando o texto da busca
async function carregar() {
  carregando.value = true;
  const resposta = await axios.get('http://localhost:8000/api/v1/produtos/', {
    params: { buscar: busca.value },
  });
  produtos.value = resposta.data.items;
  carregando.value = false;
}

// Ao abrir a tela, carrega a lista pela primeira vez
onMounted(carregar);
</script>

<template>
  <div class="p-4">
    <!-- Campo de busca: ao apertar Enter, recarrega a lista -->
    <input v-model="busca" placeholder="Buscar produto" @keyup.enter="carregar" />

    <p v-if="carregando">Carregando...</p>

    <ul>
      <!-- Uma linha para cada produto da lista -->
      <li v-for="produto in produtos" :key="produto.id">
        <span v-html="produto.nome"></span>
        <strong>R$ {{ produto.preco_venda.toFixed(2) }}</strong>
      </li>
    </ul>
  </div>
</template>
