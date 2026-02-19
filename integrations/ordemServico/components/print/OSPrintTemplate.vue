<!--
===========================================================================
ARQUIVO: OSPrintTemplate.vue
MODULO: Ordem de Servico
DESCRICAO: Template de impressao para OS. Gera documento formatado para A4
           com dados da empresa, cliente, equipamento e itens/pagamentos.
===========================================================================

PROPS:
- ordemServico: Dados completos da OS para impressao
- type: Tipo de documento ('ENTRADA' | 'SAIDA' | 'CANCELAMENTO')

TIPOS DE DOCUMENTO:
1. ENTRADA: Comprovante de entrada de equipamento
   - Dados do cliente e equipamento
   - Defeito relatado
   - Termo de condicoes de entrada

2. SAIDA: Recibo e termo de garantia
   - Laudo tecnico e solucao
   - Tabela de itens/servicos
   - Resumo financeiro e pagamentos
   - Termo de garantia (90 dias padrao)

3. CANCELAMENTO: Declaracao de cancelamento
   - Motivo do cancelamento
   - Termo de devolucao de equipamento

LAYOUT:
- Header: Logo + dados empresa | Numero da OS + datas
- Corpo: Cliente | Equipamento (2 colunas)
- Conteudo variavel por tipo
- Footer: Assinaturas + rodape

ESTILOS:
- Oculto na tela (hidden), visivel apenas em @media print
- Formatacao otimizada para impressao A4
===========================================================================
-->
<script setup lang="ts">
import { computed } from 'vue';
import {
  Smartphone,
  Phone,
  User,
  CheckCircle2,
  MapPin,
  FileText,
  CreditCard,
  Receipt,
  Building2
} from 'lucide-vue-next';
import type { OrdemServicoRead } from '../../types/ordemServico.types';
import { formatCurrency } from '@/shared/utils/finance';
import { useAuthStore } from '@/shared/store/auth.store';

const props = defineProps<{
  ordemServico: OrdemServicoRead | null;
  type: 'ENTRADA' | 'SAIDA' | 'CANCELAMENTO';
}>();

// ===========================================================================
// AUTH STORE - Dados da Empresa
// ===========================================================================
const authStore = useAuthStore();

/**
 * Corrige URL de imagem para apontar para o servidor correto
 * Imagens salvas com path relativo precisam do prefixo do backend
 */
const getImageUrl = (path: string | null | undefined): string | null => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    const cleanPath = path.replace(/^static\//, '');
    return `http://localhost:8000/static/${cleanPath}`;
};

// Dados da empresa vindos do cadastro (auth store)
const companyInfo = computed(() => {
  const empresa = authStore.empresa;

  // Monta endereco completo se disponivel
  const enderecoParts: string[] = [];
  if (empresa?.logradouro) {
    enderecoParts.push(empresa.logradouro);
    if (empresa.numero) enderecoParts.push(empresa.numero);
  }
  if (empresa?.bairro) enderecoParts.push(empresa.bairro);
  if (empresa?.cidade && empresa?.uf) {
    enderecoParts.push(`${empresa.cidade} - ${empresa.uf}`);
  }

  return {
    nome: empresa?.nome_fantasia || empresa?.razao_social || 'ASSISTÊNCIA TÉCNICA',
    razaoSocial: empresa?.razao_social || '',
    cnpj: empresa?.cnpj || '',
    endereco: enderecoParts.join(', ') || 'Endereço não cadastrado',
    contato: empresa?.telefone || empresa?.celular || '',
    email: empresa?.email || '',
    logo: getImageUrl(empresa?.url_logo)
  };
});

const title = computed(() => {
  if (props.type === 'ENTRADA') return 'COMPROVANTE DE ENTRADA DE EQUIPAMENTO';
  if (props.type === 'SAIDA') return 'RECIBO E TERMO DE GARANTIA';
  return 'DECLARAÇÃO DE CANCELAMENTO DE SERVIÇO';
});

const formatDate = (dateStr?: string | Date | null) => {
  if (!dateStr) return '__/__/____';
  return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
  });
};

const formatPhone = (phone?: string) => {
  if (!phone) return '';
  return phone.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
};

const formatDoc = (doc?: string) => {
    if (!doc) return '';
    return doc.length > 11 
        ? doc.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
        : doc.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

// Helpers Financeiros
const subtotal = computed(() => {
    if (!props.ordemServico) return 0;
    return props.ordemServico.itens.reduce((acc, item) => acc + (item.quantidade * item.valor_unitario), 0);
});

const totalPago = computed(() => {
    if (!props.ordemServico?.pagamentos) return 0;
    return props.ordemServico.pagamentos.reduce((acc, pg) => acc + pg.valor, 0);
});
</script>

<template>
  <div v-if="ordemServico" class="print-container hidden print:block bg-white text-black font-sans leading-tight">
    
    <!-- HEADER -->
    <header class="border border-slate-800 rounded-lg p-4 mb-4 flex justify-between items-start gap-4">
       <!-- Logo / Empresa -->
       <div class="flex items-start gap-4">
           <!-- Logo da Empresa -->
           <div class="w-24 h-24 bg-white border border-slate-300 rounded-lg flex items-center justify-center shrink-0 overflow-hidden">
               <img
                   v-if="companyInfo.logo"
                   :src="companyInfo.logo"
                   alt="Logo da Empresa"
                   class="w-full h-full object-contain p-1"
               />
               <Building2 v-else :size="32" class="text-slate-400" />
           </div>
           
           <div>
               <h1 class="text-xl font-black text-slate-900 uppercase tracking-tight">{{ companyInfo.nome }}</h1>
               <p class="text-[10px] uppercase font-bold text-slate-500 mb-1">{{ companyInfo.razaoSocial }}</p>
               
               <div class="text-xs text-slate-700 space-y-0.5 mt-2">
                   <p class="flex items-center gap-1.5"><MapPin :size="12" /> {{ companyInfo.endereco }}</p>
                   <p class="flex items-center gap-1.5"><FileText :size="12" /> CNPJ: {{ formatDoc(companyInfo.cnpj) }}</p>
                   <p class="flex items-center gap-1.5"><Phone :size="12" /> {{ companyInfo.contato }} | {{ companyInfo.email }}</p>
               </div>
           </div>
       </div>

       <!-- Dados da OS -->
       <div class="text-right min-w-37.5">
           <div class="bg-slate-900 text-white p-2 rounded-t-lg text-center">
               <p class="text-[10px] font-bold uppercase tracking-wider">Número da O.S.</p>
               <p class="text-2xl font-mono font-black">{{ ordemServico.numero || String(ordemServico.id).padStart(6, '0') }}</p>
           </div>
           <div class="border-x border-b border-slate-300 p-2 rounded-b-lg text-center bg-slate-50">
               <p class="text-[10px] font-bold text-slate-500 uppercase">Data Entrada</p>
               <p class="text-sm font-bold text-slate-800">{{ formatDate(ordemServico.data_criacao) }}</p>
           </div>
           <div v-if="ordemServico.data_finalizacao" class="mt-2 text-center">
                <p class="text-[10px] font-bold text-emerald-600 uppercase border border-emerald-200 bg-emerald-50 rounded px-1 py-0.5 inline-block">
                    FINALIZADA EM {{ formatDate(ordemServico.data_finalizacao) }}
                </p>
           </div>
       </div>
    </header>

    <!-- TÍTULO -->
    <div class="text-center py-2 mb-4 border-y-2 border-slate-200 bg-slate-50">
        <h2 class="text-lg font-black text-slate-800 uppercase tracking-widest">{{ title }}</h2>
    </div>

    <!-- INFORMAÇÕES PRINCIPAIS (Grid 2 Colunas) -->
    <div class="grid grid-cols-2 gap-4 mb-4">
        
        <!-- CLIENTE -->
        <div class="border border-slate-300 rounded-lg overflow-hidden">
            <div class="bg-slate-100 px-3 py-1.5 border-b border-slate-200 flex items-center gap-2">
                <User :size="14" class="text-slate-500" />
                <h3 class="text-xs font-bold uppercase text-slate-700">Dados do Cliente</h3>
            </div>
            <div class="p-3 text-xs space-y-1.5">
                <p><span class="font-bold text-slate-600">Nome:</span> {{ ordemServico.cliente?.nome || ordemServico.cliente?.razao_social || 'Consumidor' }}</p>
                <div class="flex gap-4">
                    <p><span class="font-bold text-slate-600">CPF/CNPJ:</span> {{ formatDoc(ordemServico.cliente?.cpf || ordemServico.cliente?.cnpj) }}</p>
                    <p><span class="font-bold text-slate-600">Telefone:</span> {{ formatPhone(ordemServico.cliente?.celular || ordemServico.cliente?.telefone) }}</p>
                </div>
                <!-- TODO: Endereço do cliente nao vem no resumo da OS atualmente, precisaria carregar. 
                     Se nao tiver, mostra placeholder ou nada. 
                     Para imprimir endereco completo, o backend precisa mandar endereco no ClienteResumo ou carregar full.
                     Por hora, assumimos que nao tem endereco no resumo. -->
                <p v-if="ordemServico.cliente?.id"><span class="font-bold text-slate-600">Cód. Cliente:</span> #{{ ordemServico.cliente.id }}</p>
            </div>
        </div>

        <!-- EQUIPAMENTO -->
        <div class="border border-slate-300 rounded-lg overflow-hidden">
            <div class="bg-slate-100 px-3 py-1.5 border-b border-slate-200 flex items-center gap-2">
                <Smartphone :size="14" class="text-slate-500" />
                <h3 class="text-xs font-bold uppercase text-slate-700">Dados do Equipamento</h3>
            </div>
            <div class="p-3 text-xs space-y-1.5">
                <p class="text-sm font-bold text-slate-900">{{ ordemServico.equipamento }}</p>
                <div class="grid grid-cols-2 gap-2">
                    <p><span class="font-bold text-slate-600">Marca:</span> {{ ordemServico.marca || '-' }}</p>
                    <p><span class="font-bold text-slate-600">Modelo:</span> {{ ordemServico.modelo || '-' }}</p>
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <p><span class="font-bold text-slate-600">Nº Série:</span> {{ ordemServico.numero_serie || '-' }}</p>
                    <p><span class="font-bold text-slate-600">Cor:</span> - </p> 
                </div>
            </div>
        </div>
    </div>

    <!-- DEFEITO E OBSERVAÇÕES -->
    <div class="mb-4 space-y-2">
        <div class="border border-slate-300 rounded-lg p-3 bg-slate-50/50">
            <p class="text-[10px] font-bold text-slate-500 uppercase mb-1">Defeito Relatado / Solicitação</p>
            <p class="text-xs text-slate-900 font-medium">{{ ordemServico.defeito_relatado }}</p>
        </div>
        
        <div v-if="ordemServico.observacoes" class="border border-dashed border-slate-300 rounded-lg p-3">
            <p class="text-[10px] font-bold text-slate-500 uppercase mb-1">Observações / Acessórios</p>
            <p class="text-xs text-slate-700 whitespace-pre-line">{{ ordemServico.observacoes }}</p>
        </div>
    </div>

    <!-- SEÇÃO DE SAÍDA / FINANCEIRO -->
    <template v-if="type === 'SAIDA'">
        
        <!-- LAUDO TÉCNICO -->
        <div v-if="ordemServico.solucao || ordemServico.diagnostico" class="mb-4 border border-slate-300 rounded-lg overflow-hidden">
             <div class="bg-slate-100 px-3 py-1.5 border-b border-slate-200 flex items-center gap-2">
                <CheckCircle2 :size="14" class="text-emerald-600" />
                <h3 class="text-xs font-bold uppercase text-slate-700">Laudo Técnico & Solução</h3>
            </div>
            <div class="p-3 text-xs space-y-2">
                 <div v-if="ordemServico.diagnostico">
                    <span class="font-bold text-slate-600 uppercase text-[10px]">Diagnóstico:</span>
                    <p class="text-slate-800">{{ ordemServico.diagnostico }}</p>
                 </div>
                 <div v-if="ordemServico.solucao" class="pt-2 border-t border-slate-100 mt-2">
                    <span class="font-bold text-emerald-600 uppercase text-[10px]">Solução Realizada:</span>
                    <p class="text-slate-900 font-medium">{{ ordemServico.solucao }}</p>
                 </div>
            </div>
        </div>

        <!-- TABELA DE ITENS -->
        <div class="mb-4" v-if="ordemServico.itens?.length">
             <table class="w-full text-xs text-left">
                <thead>
                    <tr class="border-b-2 border-slate-800">
                        <th class="py-2 pl-2 text-slate-600 uppercase font-bold w-[60%]">Descrição do Serviço / Peça</th>
                        <th class="py-2 text-center text-slate-600 uppercase font-bold w-[10%]">Qtd</th>
                        <th class="py-2 text-right text-slate-600 uppercase font-bold w-[15%]">Unit.</th>
                        <th class="py-2 pr-2 text-right text-slate-600 uppercase font-bold w-[15%]">Total</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-200">
                    <tr v-for="item in ordemServico.itens" :key="item.id">
                        <td class="py-2 pl-2 text-slate-800">{{ item.descricao }}</td>
                        <td class="py-2 text-center text-slate-600">{{ item.quantidade }}</td>
                        <td class="py-2 text-right text-slate-600">{{ formatCurrency(item.valor_unitario) }}</td>
                        <td class="py-2 pr-2 text-right font-bold text-slate-800">{{ formatCurrency(item.quantidade * item.valor_unitario) }}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- RESUMO FINANCEIRO E PAGAMENTOS -->
        <div class="grid grid-cols-2 gap-6 mb-4">
             <!-- Detalhes do Pagamento -->
             <div>
                 <p class="text-[10px] font-bold text-slate-500 uppercase mb-2 border-b border-slate-200 pb-1">Detalhes do Pagamento</p>
                 
                 <div v-if="ordemServico.pagamentos?.length" class="space-y-1.5">
                     <div v-for="pgto in ordemServico.pagamentos" :key="pgto.id" class="flex justify-between items-center text-xs bg-slate-50 p-1.5 rounded border border-slate-100">
                         <div class="flex items-center gap-2">
                             <CreditCard :size="12" class="text-slate-400" />
                             <span class="font-semibold text-slate-700">
                                {{ pgto.forma_pagamento?.nome || 'Pagamento' }}
                                <span v-if="pgto.parcelas > 1" class="text-[10px] text-slate-500 font-normal">({{ pgto.parcelas }}x)</span>
                             </span>
                         </div>
                         <span class="font-bold text-slate-800">{{ formatCurrency(pgto.valor) }}</span>
                     </div>
                 </div>
                 <div v-else class="text-xs text-slate-400 italic py-2">
                     Nenhum pagamento registrado.
                 </div>
             </div>

             <!-- Totais -->
             <div class="space-y-1 text-right">
                  <div class="flex justify-between text-xs text-slate-500">
                      <span>Subtotal:</span>
                      <span>{{ formatCurrency(subtotal) }}</span>
                  </div>
                  <div v-if="ordemServico.desconto > 0" class="flex justify-between text-xs text-red-600">
                      <span>Desconto:</span>
                      <span>- {{ formatCurrency(ordemServico.desconto) }}</span>
                  </div>
                  <div v-if="ordemServico.valor_entrada > 0" class="flex justify-between text-xs text-emerald-600">
                      <span>Entrada:</span>
                      <span>- {{ formatCurrency(ordemServico.valor_entrada) }}</span>
                  </div>
                  <div class="border-t border-slate-800 my-1 pt-1 flex justify-between items-end">
                      <span class="text-sm font-bold text-slate-900 uppercase">Total Pago:</span>
                      <span class="text-xl font-black text-slate-900 leading-none">{{ formatCurrency(totalPago) }}</span>
                  </div>
             </div>
        </div>

        <!-- GARANTIA -->
        <div class="border border-brand-primary/20 bg-brand-primary-light/50 rounded-lg p-3 text-[10px] text-slate-700 text-justify leading-relaxed mb-6">
            <div class="flex items-center gap-2 mb-1 font-bold text-brand-primary uppercase">
                <Receipt :size="12" />
                Termo de Garantia
            </div>
            A garantia é válida por <strong>90 (noventa) dias</strong> a contar desta data, cobrindo exclusivamente os serviços prestados e peças substituídas descritos neste documento. 
            A garantia <strong>NÃO COBRE</strong>: mau uso, contato com líquidos, quedas, oxidação, violação de selos de garantia ou intervenção de terceiros.
            <br/>
            IMPORTANTE: Equipamentos não retirados no prazo de 90 dias após notificação de conclusão serão considerados abandonados e poderão ser vendidos para custeio das despesas, conforme Art. 1.275 do Código Civil Brasileiro.
        </div>

    </template>

    <!-- SEÇÃO DE CANCELAMENTO -->
    <template v-else-if="type === 'CANCELAMENTO'">
      <div class="border border-red-200 bg-red-50/50 rounded-lg p-4 mb-6">
          <div class="flex items-center gap-2 mb-2 font-bold text-red-700 uppercase">
              <span class="p-1 bg-red-100 rounded">CANCELAMENTO</span>
              Motivo do Cancelamento
          </div>
          <p class="text-sm text-slate-900 font-medium">
             {{ (ordemServico as any).motivo_cancelamento || 'Motivo não informado.' }}
          </p>
      </div>

       <div class="border border-slate-200 bg-slate-50 rounded-lg p-3 text-[10px] text-slate-500 text-justify leading-relaxed mb-6">
          <strong class="text-slate-700 uppercase">Declaração:</strong> 
          Declaro para os devidos fins que a Ordem de Serviço acima identificada foi cancelada na presente data.
          O equipamento foi devolvido ao cliente no estado em que se encontrava, sem realização de reparos ou com reparos parciais conforme acordado, isentando a assistência técnica de garantias sobre serviços não concluídos.
      </div>
    </template>
    
    <!-- TERMO LEGAL (SOMENTE ENTRADA) -->
    <div v-else class="border border-slate-200 bg-slate-50 rounded-lg p-3 text-[10px] text-slate-500 text-justify leading-relaxed mb-8">
        <strong class="text-slate-700 uppercase">Condições de Entrada:</strong> 
        O cliente declara estar ciente que a empresa não se responsabiliza por perda de dados (backup é responsabilidade do cliente) nem por chips/cartões de memória deixados no aparelho.
        Autorizo a análise técnica do equipamento acima. Em caso de não aprovação do orçamento, estou ciente que poderá ser cobrada taxa de análise técnica.
    </div>

    <!-- ASSINATURAS -->
    <div class="grid grid-cols-2 gap-12 mt-auto pt-8">
        <div class="text-center">
            <div class="border-t border-slate-400 w-3/4 mx-auto pt-2"></div>
            <p class="text-[10px] font-bold text-slate-500 uppercase">Técnico Responsável</p>
        </div>
        <div class="text-center">
            <div class="border-t border-slate-400 w-3/4 mx-auto pt-2"></div>
            <p class="text-[10px] font-bold text-slate-500 uppercase">Assinatura do Cliente</p>
            <p class="text-[8px] text-slate-400">{{ ordemServico.cliente?.nome }}</p>
        </div>
    </div>
    
    <!-- FOOTER -->
    <div class="fixed bottom-0 left-0 w-full text-center border-t border-slate-100 py-1 bg-white">
        <p class="text-[8px] text-slate-400 uppercase tracking-wider">
            Emitido em {{ new Date().toLocaleString() }} • Sistema BigPDV
        </p>
    </div>

  </div>
</template>

<style>
@media print {
  @page {
    size: A4;
    margin: 0.5cm;
  }
  
  body {
    visibility: hidden;
    background: white;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  .print-container {
    visibility: visible;
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    margin: 0;
    padding: 20px;
    display: block !important;
    background: white;
    font-size: 12px; /* Base print size */
  }

  /* Force background colors */
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
</style>


