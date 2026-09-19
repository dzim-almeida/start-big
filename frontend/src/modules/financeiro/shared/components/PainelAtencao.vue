<script setup lang="ts">
/**
 * "Onde a loja está precisando de atenção."
 *
 * O backend manda só o CÓDIGO e os números; a frase e o destino moram aqui. É
 * o que permite mudar a redação, o rótulo por segmento e o idioma sem tocar em
 * regra de negócio — e o que impede a tela de virar um tradutor de enum.
 *
 * REGRA DE OURO: todo alerta aponta para o lugar que resolve. Aviso sem ação é
 * o que faz um painel destes morrer — quem vê aviso todo dia para de ler, e
 * some junto o aviso que importava. Lista vazia é boa notícia, e some da tela.
 */
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { AlertTriangle, ArrowRight, BellOff, CircleAlert, X } from 'lucide-vue-next';

import { formatCurrency } from '@/shared/utils/finance';
import { formatDataPura } from '@/shared/utils/date.utils';

import { useAdiarAlerta } from '../composables/useFinanceiro';
import type { AlertaFinanceiro } from '../schemas/financeiro.schema';

const props = defineProps<{ alertas: AlertaFinanceiro[] }>();
const emit = defineEmits<{ informarSaldo: [] }>();

const router = useRouter();
const adiar = useAdiarAlerta();

interface Texto {
  titulo: string;
  detalhe: string;
  acao?: string;
  rota?: string;
  // O recorte que a tela de destino deve aplicar ao abrir. É o que separa
  // "abri a lista" de "achei a conta": o alerta sabe quais linhas o
  // originaram, e seria desperdício fazer o dono procurar de novo.
  query?: Record<string, string>;
  evento?: 'informarSaldo';
}

/** "ontem", "há 12 dias", "há 3 meses" — o texto que gradua a urgência. */
function haQuantoTempo(dias?: number | null): string {
  const d = dias ?? 0;
  if (d <= 0) return 'hoje';
  if (d === 1) return 'ontem';
  if (d < 60) return `há ${d} dias`;
  return `há ${Math.floor(d / 30)} meses`;
}

function emQuantoTempo(dias?: number | null): string {
  const d = dias ?? 0;
  if (d <= 0) return 'Hoje';
  if (d === 1) return 'Amanhã';
  return `Em ${d} dias`;
}

function traduzir(alerta: AlertaFinanceiro): Texto | null {
  const valor = formatCurrency(Math.abs(alerta.valor ?? 0));

  switch (alerta.codigo) {
    case 'CAIXA_NEGATIVO':
      return {
        titulo: `O dinheiro acaba em ${formatDataPura(alerta.data ?? '')}`,
        detalhe: `${emQuantoTempo(alerta.quantidade)}, pelo que está agendado, o saldo fica negativo e chega a ${valor}. Dá para adiar uma conta, cobrar um fiado ou reforçar o caixa até lá.`,
        acao: 'Ver a projeção',
        rota: 'finance-cashflow',
      };
    case 'CONTAS_VENCIDAS':
      return {
        titulo: `${valor} em contas vencidas`,
        // O TEMPO é metade da gravidade, não enfeite: R$ 80 vencidos ontem e
        // R$ 80 vencidos há três meses são problemas diferentes.
        detalhe: `A mais antiga venceu ${haQuantoTempo(alerta.quantidade)}. Quanto mais tempo, maior a multa.`,
        acao: 'Ver as vencidas',
        rota: 'finance-payable',
        query: { filtro: 'vencidas' },
      };
    case 'FIADO_ATRASADO':
      return {
        titulo: `${valor} atrasado a receber`,
        detalhe: `O mais antigo venceu ${haQuantoTempo(alerta.quantidade)}. Cobrar cedo é o que separa atraso de calote.`,
        acao: 'Ver quem está devendo',
        rota: 'finance-receivable',
        query: { filtro: 'vencidas' },
      };
    case 'MES_NO_VERMELHO':
      return {
        titulo: `O mês está negativo em ${valor}`,
        detalhe: 'Saiu mais do que entrou no período. Veja abaixo para onde o dinheiro foi.',
      };
    case 'SALDO_NUNCA_INFORMADO':
      return {
        titulo: 'O sistema não sabe quanto você tem hoje',
        detalhe: 'Sem esse número não há projeção possível — e ele é o único que só você tem.',
        acao: 'Informar saldo',
        evento: 'informarSaldo',
      };
    case 'SALDO_DESATUALIZADO':
      return {
        titulo: `Saldo informado há ${alerta.quantidade} dias`,
        detalhe: 'O saldo não anda sozinho: dar baixa numa conta não o move. Confira e atualize.',
        acao: 'Atualizar saldo',
        evento: 'informarSaldo',
      };
    // --- TENDÊNCIA: o que a série sabe e a fotografia do mês não sabe ---
    case 'RECEITA_CAINDO':
      return {
        titulo: `Sua receita cai há ${alerta.quantidade} meses seguidos`,
        detalhe: `São ${valor} a menos do que no início da sequência. Um mês ruim acontece; três em fila é direção.`,
        acao: 'Ver a série',
        rota: 'finance-analysis',
      };
    case 'ORIGEM_CAINDO':
      return {
        titulo: `${alerta.rotulo} caiu ${alerta.quantidade}%`,
        detalhe: `São ${valor} a menos que a média dos últimos meses. O total pode até estar segurando — esta perna não está.`,
        acao: 'Ver a série',
        rota: 'finance-analysis',
      };
    case 'DEPENDENCIA_DE_ORIGEM':
      return {
        titulo: `${alerta.quantidade}% do seu dinheiro vem de ${alerta.rotulo}`,
        detalhe: 'Uma semana parada nessa frente para o seu caixa inteiro. Não é erro — é risco concentrado.',
        acao: 'Ver a série',
        rota: 'finance-analysis',
      };
    case 'CUSTO_SUBINDO_MAIS':
      return {
        titulo: `Seu custo subiu ${alerta.quantidade}% mais rápido que a receita`,
        detalhe: `São ${valor} a mais por mês que há três meses. Vender mais não resolve enquanto o custo correr na frente.`,
        acao: 'Ver para onde foi',
        rota: 'finance-payable',
      };
    case 'RECEBIMENTO_LENTO':
      return {
        titulo: `Seu cliente está levando ${alerta.quantidade} dias para pagar`,
        detalhe: `Era ${alerta.valor} dias na média dos meses anteriores. O dinheiro está sendo faturado e demorando mais a entrar.`,
        acao: 'Ver quem deve',
        rota: 'finance-receivable',
      };

    case 'DESPESA_SEM_CATEGORIA':
      return {
        titulo: `${valor} gastos sem categoria`,
        detalhe: 'Enquanto a maior fatia se chamar "Sem categoria", o resumo não diz para onde o dinheiro foi.',
        acao: 'Classificar',
        rota: 'finance-payable',
        query: { filtro: 'sem-categoria' },
      };
    // Código desconhecido não vira linha em branco: some. Um backend mais novo
    // que este frontend não deve desenhar caixa vazia na tela do lojista.
    default:
      return null;
  }
}

const itens = computed(() =>
  props.alertas
    .map((alerta) => ({ alerta, texto: traduzir(alerta) }))
    .filter((item): item is { alerta: AlertaFinanceiro; texto: Texto } => item.texto !== null),
);

function agir(item: { alerta: AlertaFinanceiro; texto: Texto }) {
  if (item.texto.evento) return emit(item.texto.evento);
  if (item.texto.rota) {
    router.push({ name: item.texto.rota, query: item.texto.query });
  }
}

// --- Por quanto tempo calar ---
//
// O backend sempre aceitou de 1 a 90 dias; a tela é que mandava 7 fixo. Sete
// dias serve para "resolvo semana que vem", e é pouco para o aviso que o dono
// LEU e decidiu conviver — concentração de receita, por exemplo, não é defeito
// a corrigir, é risco a acompanhar. Sem um prazo longo, a única saída era
// engolir o mesmo aviso toda semana, e é assim que o painel inteiro vira
// ruído.
const PRAZOS = [
  { dias: 7, rotulo: '7 dias' },
  { dias: 30, rotulo: '30 dias' },
  { dias: 90, rotulo: '90 dias' },
] as const;

/** Código do alerta que está com os prazos abertos (null = nenhum). */
const escolhendoPrazo = ref<string | null>(null);

function adiarPor(codigo: string, dias: number) {
  adiar.mutate({ codigo, dias });
  escolhendoPrazo.value = null;
}
</script>

<template>
  <section v-if="itens.length" class="rounded-2xl border border-zinc-100 bg-white p-5 shadow-sm">
    <h3 class="flex items-center gap-2 text-sm font-bold text-zinc-800">
      <CircleAlert :size="16" class="text-amber-500" /> Precisa de atenção
    </h3>

    <ul class="mt-4 flex flex-col divide-y divide-zinc-100">
      <li
        v-for="item in itens"
        :key="item.alerta.codigo"
        class="flex flex-wrap items-start justify-between gap-3 py-3 first:pt-0 last:pb-0"
      >
        <div class="flex min-w-0 gap-3">
          <!-- A cor é o único peso visual que separa "resolva hoje" de
               "resolva esta semana". Ícone igual para os dois deixaria o
               painel achatado. -->
          <AlertTriangle
            :size="16"
            class="mt-0.5 shrink-0"
            :class="item.alerta.severidade === 'CRITICO' ? 'text-rose-500' : 'text-amber-500'"
          />
          <div class="min-w-0">
            <p
              class="text-sm font-semibold"
              :class="item.alerta.severidade === 'CRITICO' ? 'text-rose-700' : 'text-zinc-800'"
            >
              {{ item.texto.titulo }}
            </p>
            <p class="mt-0.5 text-xs text-zinc-500">{{ item.texto.detalhe }}</p>
          </div>
        </div>

        <div class="flex shrink-0 items-center gap-4">
          <!-- ADIAR, e nunca "dispensar": o aviso volta ao fim do prazo se o
               problema continuar. Sem esta saída, o alerta que o dono decidiu
               não resolver grita todos os dias — e é assim que ele aprende a
               ignorar o painel inteiro.
               Não existe "resolvido" porque não precisa existir: a lista é
               recalculada a cada abertura, então o alerta do problema resolvido
               não chega a nascer. Um botão "resolvido" só serviria para
               esconder problema que continua de pé. -->
          <div v-if="escolhendoPrazo === item.alerta.codigo" class="flex items-center gap-2">
            <span class="text-xs text-zinc-400">Calar por</span>
            <button
              v-for="prazo in PRAZOS"
              :key="prazo.dias"
              type="button"
              class="rounded-md border border-zinc-200 px-2 py-0.5 text-xs font-medium text-zinc-600 cursor-pointer hover:border-zinc-400 hover:text-zinc-900"
              :disabled="adiar.isPending.value"
              @click="adiarPor(item.alerta.codigo, prazo.dias)"
            >
              {{ prazo.rotulo }}
            </button>
            <button
              type="button"
              class="text-zinc-300 cursor-pointer hover:text-zinc-600"
              title="Cancelar"
              @click="escolhendoPrazo = null"
            >
              <X :size="13" />
            </button>
          </div>

          <button
            v-else
            type="button"
            class="flex items-center gap-1 text-xs font-medium text-zinc-400 cursor-pointer hover:text-zinc-700"
            title="Calar este aviso por um tempo"
            :disabled="adiar.isPending.value"
            @click="escolhendoPrazo = item.alerta.codigo"
          >
            <BellOff :size="13" /> Adiar
          </button>

          <button
            v-if="item.texto.acao"
            type="button"
            class="flex items-center gap-1 text-xs font-semibold text-brand-primary cursor-pointer hover:underline underline-offset-2"
            @click="agir(item)"
          >
            {{ item.texto.acao }} <ArrowRight :size="13" />
          </button>
        </div>
      </li>
    </ul>

    <!-- A frase antiga ("ele volta — com o número daquele dia, não com o de
         hoje") respondia a pergunta errada, e de forma ambígua: "daquele dia"
         lia como o número de quando se adiou, que é justamente o contrário do
         que o backend faz. A dúvida real de quem olha o painel é outra — "e se
         eu já resolvi, vai me encher de novo?" — e é ela que esta versão
         responde, na primeira linha. -->
    <p class="mt-3 text-xs text-zinc-400">
      <span class="font-medium text-zinc-500">Resolveu? O aviso some sozinho.</span>
      Esta lista é recalculada toda vez que a tela abre, então o problema resolvido não
      volta a aparecer. <span class="font-medium text-zinc-500">Adiar</span> é para o
      aviso que você leu e decidiu não tratar agora: ele cala pelo prazo escolhido e só
      reaparece no fim dele, com o número daquele momento, se o problema ainda existir.
    </p>
  </section>
</template>
