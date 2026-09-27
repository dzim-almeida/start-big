/**
 * @fileoverview Desfazer/refazer do editor: uma pilha de fotografias da lista.
 *
 * Quem edita chama `registrar()` ao TERMINAR um gesto (soltar o mouse, sair
 * de um campo) — e não a cada pixel do arraste, senão um Ctrl+Z desfaria
 * meio milímetro.
 */

import { computed, ref, type Ref } from 'vue';

const LIMITE = 100;

export function useHistorico<T>(atual: Ref<T>) {
  const copiar = (valor: T): T => JSON.parse(JSON.stringify(valor));

  const passado = ref<T[]>([]) as Ref<T[]>;
  const futuro = ref<T[]>([]) as Ref<T[]>;
  let ultimo = copiar(atual.value);

  /** Fotografa o estado atual, se ele mudou desde a última fotografia. */
  function registrar() {
    const agora = JSON.stringify(atual.value);
    if (agora === JSON.stringify(ultimo)) return;
    passado.value = [...passado.value, ultimo].slice(-LIMITE);
    futuro.value = [];
    ultimo = JSON.parse(agora);
  }

  function desfazer() {
    const anterior = passado.value[passado.value.length - 1];
    if (anterior === undefined) return;
    passado.value = passado.value.slice(0, -1);
    futuro.value = [...futuro.value, copiar(atual.value)];
    atual.value = copiar(anterior);
    ultimo = copiar(anterior);
  }

  function refazer() {
    const proximo = futuro.value[futuro.value.length - 1];
    if (proximo === undefined) return;
    futuro.value = futuro.value.slice(0, -1);
    passado.value = [...passado.value, copiar(atual.value)];
    atual.value = copiar(proximo);
    ultimo = copiar(proximo);
  }

  /** Recomeça do zero (ex.: o layout foi regerado pelo automático). */
  function reiniciar() {
    passado.value = [];
    futuro.value = [];
    ultimo = copiar(atual.value);
  }

  return {
    registrar,
    desfazer,
    refazer,
    reiniciar,
    podeDesfazer: computed(() => passado.value.length > 0),
    podeRefazer: computed(() => futuro.value.length > 0),
  };
}
