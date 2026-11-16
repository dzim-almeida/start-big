/**
 * @fileoverview Reconhece uma leitura vinda de um leitor de código de barras
 * que "digita" (Spec 10B §7.2, D14, D17).
 *
 * O leitor USB se comporta como um teclado: manda os caracteres muito rápido
 * (menos de 30 ms entre eles) e termina com Enter. Uma pessoa digitando é mais
 * lenta, então o campo continua funcionando como campo comum.
 *
 * Este ouvinte cobre o caso em que o foco SAIU do campo "Ler código" (o erro
 * mais comum de balcão): a leitura completa é entregue do mesmo jeito. O que
 * é digitado DENTRO do campo é tratado pelo próprio campo (`ignorar`), para a
 * mesma leitura não chegar duas vezes.
 */
import type { Ref } from 'vue';
import { useEventListener } from '@vueuse/core';

/** Intervalo máximo entre duas teclas da MESMA leitura (ms). */
export const INTERVALO_LEITOR_MS = 30;
/** Códigos curtos demais são digitação, não leitura. */
export const TAMANHO_MINIMO = 4;

export function useLeitorCodigo(
  aoLer: (codigo: string) => void,
  ativo: Ref<boolean>,
  ignorar?: Ref<HTMLElement | null>,
) {
  let buffer = '';                                   // caracteres da leitura em curso
  let ultimo = 0;                                    // instante da última tecla (ms)

  useEventListener(document, 'keydown', (evento: KeyboardEvent) => {
    if (!ativo.value) return;                        // aba fechada ou modal aberto: não captura
    if (ignorar?.value && evento.target === ignorar.value) return;   // o campo trata o que é dele
    const agora = performance.now();
    if (agora - ultimo > INTERVALO_LEITOR_MS) buffer = '';             // pausa longa: outra leitura
    ultimo = agora;
    if (evento.key === 'Enter' && buffer.length >= TAMANHO_MINIMO) {
      const codigo = buffer;
      buffer = '';
      evento.preventDefault();                       // o Enter do leitor não confirma outra coisa
      aoLer(codigo);
    } else if (evento.key.length === 1) {
      buffer += evento.key;                          // só caracteres visíveis entram no código
    }
  });
}

/**
 * Bipe curto de erro (D15): o marceneiro está olhando para a chapa, não para
 * a tela. Sem permissão de áudio no navegador, fica só a mensagem.
 */
export function tocarSomDeErro(): void {
  try {
    const Contexto = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Contexto) return;
    const audio = new Contexto();
    const oscilador = audio.createOscillator();
    oscilador.type = 'square';
    oscilador.frequency.value = 220;                 // grave: soa como "errado"
    oscilador.connect(audio.destination);
    oscilador.start();
    oscilador.stop(audio.currentTime + 0.15);
    oscilador.onended = () => { void audio.close(); };
  } catch {
    // Sem som: a mensagem na tela basta.
  }
}
