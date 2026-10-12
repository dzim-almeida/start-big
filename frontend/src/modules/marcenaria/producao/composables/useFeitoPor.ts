/**
 * @fileoverview "Feito por" da aba Produção (Spec 12B D6).
 *
 * O computador da fábrica costuma ter UM usuário, usado por várias pessoas.
 * O padrão é o funcionário do usuário logado; trocar no select vale para a
 * SESSÃO inteira (todas as OS abertas depois), até fechar o sistema. Por
 * isso o estado fica fora da função: é um só para o app todo.
 */
import { computed, ref } from 'vue';

import { useAuthStore } from '@/shared/stores/auth.store';

/** `undefined` = ninguém trocou nesta sessão: vale o usuário logado. */
const escolhido = ref<number | null | undefined>(undefined);

export function useFeitoPor() {
  const auth = useAuthStore();
  /** O funcionário que vai como responsável (null = o backend usa o do usuário logado). */
  const feitoPor = computed<number | null>({
    get: () => (escolhido.value === undefined ? (auth.userData?.funcionario_id ?? null) : escolhido.value),
    set: (valor) => { escolhido.value = valor; },
  });
  return { feitoPor };
}

/** Para os testes: volta ao padrão (o usuário logado). */
export function limparFeitoPor() {
  escolhido.value = undefined;
}
